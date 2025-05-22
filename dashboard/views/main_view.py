import asyncio
import os

import numpy as np

from dashboard.widgets.table_aggregation_widget import create_aggregation_widget

# Link Aggregationsfunktion an MainView
# PROJ_LIB setzen – passe den Pfad ggf. an deine Umgebung an
os.environ["PROJ_LIB"] = "/home/chefsichter/miniconda3/envs/ai4good/share/proj"

import param
import panel as pn
import pandas as pd

import holoviews as hv
import geoviews as gv
from holoviews.streams import Tap
import cartopy.crs as ccrs
from shapely.geometry import Point

from bokeh.io import curdoc
from dashboard.sensitivity_models import StaticSensitivity, RNNSensitivity

class MainView(param.Parameterized):
    # Alle Variablen sollen in der Combobox auswählbar sein.
    variable = param.ObjectSelector(default=None, objects=[])
    # Stride (Tage) über ein Inputfeld (IntInput) eingeben.
    day_stride = param.Integer(default=None, bounds=(1, 25000))
    # Wir verwenden nur noch einen Zeitbereich, nicht mehr ein einzelnes Datum:
    start_date = param.CalendarDate(default=None)
    end_date = param.CalendarDate(default=None)

    # Play/Pause-Action
    play = param.Action(lambda x: x.param.trigger('play'), label='Play')
    playing = False
    # Spielgeschwindigkeit in Millisekunden (Standard: 300 ms)
    play_speed = param.Number(default=300, bounds=(50, 10000))
    # Global max für den Farbbereich (wird nach Berechnung gesetzt)
    global_max = param.Number(default=0)

    # Zeitbereich (für Slider)
    time_min = param.CalendarDate(default=None)
    time_max = param.CalendarDate(default=None)

    # Aggregationsfunktion für Zeitdimension (sum, mean, max, min)
    agg_method = param.ObjectSelector(
        default='sum',
        objects=['sum', 'mean', 'max', 'min'],
        label='Aggregation'
    )

    # Tap-Stream für Klicks
    tap_stream = Tap(x=None, y=None, source=None)

    def __init__(self,
                 var_metadata,
                 ds,
                 shap_ds,
                 gdf,
                 all_vars,
                 time_vars,
                 static_vars,
                 var_cmaps,
                 **params):
        # Nicht-reaktive Daten und Konfiguration
        self.var_metadata = var_metadata
        self.ds = ds
        self.shap_ds = shap_ds
        self.gdf = gdf
        self.all_vars = all_vars
        self.time_vars = time_vars
        self.static_vars = static_vars
        self.var_cmaps = var_cmaps
        # Restliche Parameter initialisieren
        super().__init__(**params)
        # Variable Selector mit verfügbaren Variablen bestücken
        self.param.variable.objects = self.all_vars
        # Platzhalter für den DateRangeSlider
        self.date_range_slider = None
        # Sensitivity-Modelle
        self.snn = StaticSensitivity()
        self.rnn = RNNSensitivity()
        # Caches for map visualizations to avoid redundant recomputations
        self._cache_map = {}
        self._cache_map_shap = {}
        self._cache_map_diff = {}

    @property
    def date_range(self):
        return self.start_date, self.end_date

    @date_range.setter
    def date_range(self, value):
        with param.parameterized.batch_call_watchers(self):
            self.start_date, self.end_date = value


    @pn.depends('start_date', 'end_date', watch=True)
    def update_day_stride_from_date_range(self):
        # Berechne die Tagesdifferenz: (+1, damit beide Endpunkte eingeschlossen sind)
        computed_stride = (pd.to_datetime(self.end_date) - pd.to_datetime(self.start_date)).days + 1
        # Updaten, falls sich der Wert wirklich ändert
        if self.day_stride != computed_stride:
            self.day_stride = computed_stride

    @pn.depends('day_stride', watch=True)
    def update_date_range(self):
        # Nimm an, dass der Starttermin als master gilt und der Endtermin auf day_stride basiert.
        start = self.start_date
        computed_end = (pd.to_datetime(start) + pd.Timedelta(days=self.day_stride - 1)).date()
        if self.end_date != computed_end:
            self.end_date = computed_end

    def get_start_date(self):
        return self.date_range[0]

    def compute_global_max(self): # todo: remove
        """
        Berechnet über den gesamten Datensatz (für die aktuell ausgewählte Variable und day_stride)
        den maximalen aggregierten Wert. Während der Berechnung wird ein Spinner angezeigt.
        """
        var_name = self.variable
        if var_name is None or var_name not in self.ds:
            self.global_max = 0
            return
        da = self.ds[var_name]
        if 'time' in da.dims:
            # Verwende xarray rolling, um das aggregierte Fenster zu berechnen:
            aggregated = da.rolling(time=self.day_stride, min_periods=self.day_stride).sum()
            self.global_max = float(aggregated.max())
        else:
            self.global_max = float(da.max())

    @pn.depends('play', watch=True)
    def toggle_play(self):
        self.playing = not self.playing
        if self.playing:
            self.play_button.name = "Pause"
            asyncio.create_task(self._play_loop())
        else:
            self.play_button.name = "Play"

    async def _play_loop(self):
        # Show loading spinner
        pn.state._busy_counter += 1
        try:
            while self.playing:
                current_start = pd.to_datetime(self.get_start_date())
                next_start = current_start + pd.Timedelta(days=self.day_stride)

                if next_start.date() > pd.to_datetime(self.time_max).date():
                    self.playing = False
                    self.play_button.name = "Play"
                    break

                self.date_range = (next_start.date(), (next_start + pd.Timedelta(days=self.day_stride - 1)).date())

                # Warten, bis die UI Zeit hatte, zu reagieren
                await asyncio.sleep(self.play_speed / 1000.0)
        finally:
            # Decrement busy counter to hide spinner
            pn.state._busy_counter -= 1

    def _get_cmap_for_var(self, var_name):
        if var_name in self.var_cmaps:
            return self.var_cmaps[var_name]
        return self.var_cmaps.get('*default*', 'Viridis')

    def aggregate_data(self, var_name, time_value, dataset):
        da = dataset[var_name]
        if 'time' in da.dims:
            # Slice nach Zeitbereich (immer Tuple von zwei Daten)
            start_date, end_date = map(pd.to_datetime, time_value)
            sel_da = da.sel(time=slice(start_date, end_date))
            # Dynamische Aggregation entsprechend ausgewählter Methode
            try:
                agg_da = getattr(sel_da, self.agg_method)(dim='time')
            except Exception:
                agg_da = sel_da.sum(dim='time')
        else:
            agg_da = da
        return agg_da
    
    # Hilfsfunktion: Mappe ds-Variablennamen auf shap_ds-Variablen
    def _map_shap_var(self, var_name):
        # Direkter Name
        if var_name in self.shap_ds.data_vars:
            return var_name
        # Spezielle Zuordnungen
        mapping = {'P': 'sum_P', 'T': 'sum_T'}
        return mapping.get(var_name)
    
    @pn.depends('variable', 'start_date', 'end_date', 'agg_method', watch=False)
    def get_map_shap_ds(self):
        """Zeigt SHAP-Werte für die aktuell gewählte Variable aus ds (mit Cache)."""
        var_name = self.variable
        key = (var_name, self.start_date, self.end_date, self.agg_method)
        if key in self._cache_map_shap:
            return self._cache_map_shap[key]
        shap_var = self._map_shap_var(var_name)
        if shap_var is None or shap_var not in self.shap_ds.data_vars:
            pane = pn.pane.Markdown(f"Keine SHAP-Werte für Variable {var_name} vorhanden.", width=300)
            self._cache_map_shap[key] = pane
            return pane
        agg_da = self.aggregate_data(shap_var, self.date_range, self.shap_ds)
        if agg_da is None:
            pane = pn.pane.Markdown(f"Keine SHAP-Daten für {var_name} darstellbar.", width=300)
            self._cache_map_shap[key] = pane
            return pane
        df_values = agg_da.to_series().to_frame(name=var_name)
        merged = self.gdf.join(df_values, on="hru", how="inner").dropna(subset=[var_name])
        opts = dict(
            projection=ccrs.Mercator(),
            tools=['hover'],
            color=var_name,
            cmap='coolwarm',
            colorbar=True,
            line_color='black',
            line_width=0.1,
            width=800,
            height=500
        )
        vmax = max(abs(merged[var_name].max()), abs(merged[var_name].min()))
        opts['clim'] = (-vmax, vmax)
        polys = gv.Polygons(merged, crs=ccrs.PlateCarree(), vdims=[var_name, 'hru']).opts(**opts)
        self._cache_map_shap[key] = polys
        return polys

    @pn.depends('start_date', 'end_date', 'agg_method', watch=False)
    def get_map_run_off_diff(self):
        """Absolute Differenz der Runoff-Modelle ('Y') mit Cache."""
        key = (self.start_date, self.end_date, self.agg_method)
        if key in self._cache_map_diff:
            return self._cache_map_diff[key]
        var_name = 'Y'
        agg_da = self.aggregate_data(var_name, self.date_range, self.shap_ds)
        if agg_da is None:
            pane = pn.pane.Markdown(f"Keine SHAP-Daten für {var_name} darstellbar.", width=300)
            self._cache_map_diff[key] = pane
            return pane
        df_values = agg_da.to_series().to_frame(name=var_name)
        merged = self.gdf.join(df_values, on="hru", how="inner").dropna(subset=[var_name])
        opts = dict(
            projection=ccrs.Mercator(),
            tools=['hover'],
            color=var_name,
            cmap='YlGn',
            colorbar=True,
            line_color='black',
            line_width=0.1,
            width=800,
            height=500
        )
        values = merged[var_name].values
        vmin, vmax = np.percentile(values, [2, 98])
        opts['clim'] = (vmin, vmax)
        polys = gv.Polygons(merged, crs=ccrs.PlateCarree(), vdims=[var_name, 'hru']).opts(**opts)
        self._cache_map_diff[key] = polys
        return polys

    @pn.depends('variable', 'start_date', 'end_date', 'agg_method', watch=False)
    def get_map(self):
        """Aggregierte Karte für die gewählte Variable (mit Cache)."""
        var_name = self.variable
        if var_name is None:
            return hv.Curve([]).opts(width=800, height=500)
        # Cache-Key basierend auf Auswahl
        key = (var_name, self.start_date, self.end_date, self.agg_method)
        if key in self._cache_map:
            polys = self._cache_map[key]
        else:
            agg_da = self.aggregate_data(var_name, self.date_range, self.ds)
            df_values = agg_da.to_series().to_frame(name=var_name)
            merged = self.gdf.join(df_values, on="hru", how="inner").dropna(subset=[var_name])
            opts = dict(
                projection=ccrs.Mercator(),
                tools=['hover', 'tap'],
                color=var_name,
                cmap=self._get_cmap_for_var(var_name),
                colorbar=True,
                line_color='black',
                line_width=0.1,
                width=800,
                height=500
            )
            if self.global_max > 0:
                opts['clim'] = (0, self.global_max)
            polys = gv.Polygons(
                merged,
                crs=ccrs.PlateCarree(),
                vdims=[var_name, 'hru']
            ).opts(**opts)
            self._cache_map[key] = polys
        # Stream-Source aktualisieren
        self.tap_stream.source = polys
        return polys

    @pn.depends('tap_stream.x', 'tap_stream.y', 'agg_method', watch=False)
    def get_table(self):
        if self.tap_stream.x is not None and self.tap_stream.y is not None:
            # Prüfe Klick-Koordinaten
            click_point = Point(self.tap_stream.x, self.tap_stream.y)
            selected = self.gdf[self.gdf.geometry.contains(click_point)]
            if len(selected) > 0:
                hru_clicked = selected.iloc[0]['hru']
                # Aggregations-Widget (Tabelle mit Basiswerten)
                table_widget, table_hru = create_aggregation_widget(self, hru_clicked)
                # Bei Markdown-Fallback direkt zurückgeben
                if table_hru is None:
                    return table_widget
                # Aggregationstabelle mit Titel und voller Breite
                agg_panel = pn.Column(
                    table_widget,
                    sizing_mode="stretch_width"
                )
                return agg_panel
            else:
                # Kein Polygon unter Klickpunkt: nur Markdown ausgeben
                return pn.pane.Markdown("Kein Polygon unter Klickpunkt gefunden.", width=300)
        else:
            # Vor dem Klick: Hinweistext anzeigen
            return pn.pane.Markdown("Klicke auf ein Polygon, um Details zu sehen.", width=300)

    def get_date_range_slider(self):
        """
        Erstellt einen DateRangeSlider, der den gesamten Zeitbereich auswählt.
        Das Widget liefert ein Tupel (start, end), das in den Parameter date_range
        (als Tuple von datetime.date) konvertiert und aktualisiert wird.
        """
        # Konvertiere initial den date_range-Wert in Timestamps, da der DateRangeSlider Timestamps verwendet.
        date_range_slider = pn.widgets.DateRangeSlider(
            name=f"🕒 Zeitraum",
            start=pd.Timestamp(self.time_min),
            end=pd.Timestamp(self.time_max),
            value=(pd.Timestamp(self.start_date), pd.Timestamp(self.end_date)),
            show_value=True,
            sizing_mode="stretch_width"
        )

        # Callback, der beim Ändern des Sliders beide Parameter in MainView aktualisiert.
        def update_dates(event):
            new_start, new_end = event.new
            # Konvertiere zu date, falls nötig
            self.start_date = new_start.date() if hasattr(new_start, "date") else new_start
            self.end_date = new_end.date() if hasattr(new_end, "date") else new_end

        date_range_slider.param.watch(update_dates, 'value')

        # Callback, um den Slider zu aktualisieren, wenn start_date oder end_date sich ändern.
        def update_slider(*events):
            # Verhindert rekursive Updates, falls nötig.
            date_range_slider.value = (pd.Timestamp(self.start_date), pd.Timestamp(self.end_date))

        self.param.watch(lambda *args, **kwargs: update_slider(), ['start_date', 'end_date'])

        return date_range_slider

    def _get_long_name(self, variable):
        meta = self.var_metadata.get(self.variable, {})
        long_name = meta.get('long_name') or self.variable
        return long_name

    @pn.depends('variable')
    def get_map1_title(self):
        return pn.panel(f"### Aggregierte Werte für '{self._get_long_name(self.variable)}'")

    @pn.depends('variable')
    def get_map3_title(self):
        return pn.panel(f"### Aggregierte SHAP-Werte für '{self._get_long_name(self.variable)}'")

    def panel_view(self):
        # Erzeuge den Zeitschieberegler (DateSlider)
        self.date_range_slider = self.get_date_range_slider()

        # Nur DateRangeSlider in der Hauptansicht; Play/Speed Controls im Sidebar
        controls = pn.Row(
            self.date_range_slider,
            sizing_mode="stretch_width"
        )

        # Aufbau des Hauptinhalts: Karte (Map) und Tabelle (Detailansicht) mit gleicher Breite
        # Map-Panel responsiv in der Breite
        map1 = pn.panel(self.get_map,
                        linked_axes=False,
                        sizing_mode="scale_width")
        # Linke Spalte (Map) und rechte Spalte (Tabelle) gleichmäßig breiten
        left = pn.Column(
            self.get_map1_title,
            map1,
            sizing_mode="stretch_width",
        )
        right = pn.Column(
            pn.pane.Markdown("### Aggregierte Werte (per HRU)"),
            self.get_table,
            scroll=True,
        )
        main_area = pn.Row(
            left,
            right,
            sizing_mode="stretch_width"
        )

        # Erzeuge zweite Karte (absolute Differenz Y zwischen den Runoff-Modellen)
        map2 = pn.panel(
            self.get_map_run_off_diff,
            linked_axes=False,
            sizing_mode="scale_width"
        )
        # Erzeuge dritte Karte (SHAP-Werte für gewählte Variable)
        map3 = pn.panel(
            self.get_map_shap_ds,
            linked_axes=False,
            sizing_mode="scale_width"
        )

        # Packe Karte 2 und 3 nebeneinander mit passenden Titeln und korrektem Seitenverhältnis
        maps_row = pn.Row(
            pn.Column(
                pn.pane.Markdown("### Aggregierte absolute Differenz zwischen den Runoff-Modellen ('Y')"),
                map2,
                sizing_mode="stretch_width"
            ),
            pn.Column(
                self.get_map3_title,
                map3,
                sizing_mode="stretch_width"
            ),
            sizing_mode="stretch_width"
        )

        # gib alles in einer Column zurück
        return pn.Column(
            controls,
            main_area,
            pn.pane.Markdown("### Ai4Good Sensitivitätsanalyse"),
            maps_row
        )