import asyncio
import os
from contextlib import contextmanager

import numpy as np

from dashboard.widgets.play_button import create_play_button
from dashboard.widgets.speed_widget import create_speed_widget
from dashboard.widgets.table_aggregation_widget import create_aggregation_widget

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
    play_speed = param.Number(default=300, bounds=(50, 2000))
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

    @property
    def date_range(self):
        return self.start_date, self.end_date

    @date_range.setter
    def date_range(self, value):
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
    def toggle_play(self, event):
        self.playing = not self.playing
        if self.playing:
            self.play_button.name = "Pause"
            self._play_loop()
        else:
            self.play_button.name = "Play"

    def _play_loop(self):
        if not self.playing:
            return
        if self.day_stride > 1:
            current_start = pd.to_datetime(self.date_range[0])
            next_start = current_start + pd.Timedelta(days=self.day_stride)
            if next_start.date() > pd.to_datetime(self.time_max).date():
                self.playing = False
                return
            new_range = (next_start.date(), (next_start + pd.Timedelta(days=self.day_stride - 1)).date())
            self.date_range = new_range
        else:
            current_date = pd.to_datetime(self.get_start_date())
            next_date = current_date + pd.Timedelta(days=1)
            if next_date.date() > pd.to_datetime(self.time_max).date():
                self.playing = False
                return
            self.date_range = (next_date.date(), next_date.date())
        # Verwende die aktuell eingestellte play_speed (in ms)
        curdoc().add_periodic_callback(self._play_loop, int(self.play_speed))

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
    
    @pn.depends('variable', 'day_stride', 'start_date', 'end_date', 'agg_method', watch=False)
    def get_map_shap_ds(self):
        """Zeigt SHAP-Werte für die aktuell gewählte Variable aus ds."""
        var_name = self.variable
        shap_var = self._map_shap_var(var_name)
        if shap_var is None or shap_var not in self.shap_ds.data_vars:
            return pn.pane.Markdown(f"Keine SHAP-Werte für Variable {var_name} vorhanden.", width=300)
        agg_da = self.aggregate_data(shap_var, self.date_range, self.shap_ds)
        if agg_da is None:
            return pn.pane.Markdown(f"Keine SHAP-Daten für {var_name} darstellbar.", width=300)
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
        return polys

    @pn.depends('day_stride', 'start_date', 'end_date', 'agg_method', watch=False)
    def get_map_run_off_diff(self):
        var_name = 'Y'
        agg_da = self.aggregate_data(var_name, self.date_range, self.shap_ds)
        if agg_da is None:
            return pn.pane.Markdown(f"Keine SHAP-Daten für {var_name} darstellbar.", width=300)
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
        vmin, vmax = np.percentile(values, [2, 98])  # oder [5, 95]
        opts['clim'] = (vmin, vmax)
        polys = gv.Polygons(merged, crs=ccrs.PlateCarree(), vdims=[var_name, 'hru']).opts(**opts)
        return polys

    @pn.depends('variable', 'day_stride', 'start_date', 'end_date', 'agg_method', watch=False)
    async def get_map(self):
        await asyncio.sleep(0.1)
        var_name = self.variable
        if var_name is None:
            return hv.Curve([]).opts(width=800, height=500)
        # Immer den Zeitbereich nutzen:
        time_value = self.date_range
        agg_da = self.aggregate_data(var_name, time_value, self.ds)
        df_values = agg_da.to_series().to_frame(name=var_name)
        merged = self.gdf.join(df_values, on="hru", how="inner")
        merged = merged.dropna(subset=[var_name])
        opts_dict = dict(
            projection=ccrs.Mercator(),
            tools=['hover', 'tap'],
            color=var_name,
            cmap=self._get_cmap_for_var(var_name), # Eingabe von Farbskala
            colorbar=True, # zeigt Farbskala neben der Karte
            line_color='black',
            line_width=0.1,
            width=800,
            height=500
        )
        if self.global_max > 0:
            opts_dict['clim'] = (0, self.global_max)
        polys = gv.Polygons(
            merged,  # Daten welche übergeben werden, muss geometry enthalten
            crs=ccrs.PlateCarree(), # einfache Projektion, bei der lat/lon direkt als X/Y interpretiert werden,
            # das entspricht EPSG:4326 (Breitengrad/Längengrad). Sehr wichtig: Das ist nicht die Darstellung,
            # sondern das Koordinatensystem der Daten!
            vdims=[var_name, 'hru'] # Welche Variablen für Farbe, Hover, Klicks genutzt werden
        ).opts(**opts_dict)
        self.tap_stream.source = polys
        return polys

    @pn.depends('tap_stream.x', 'tap_stream.y', watch=False)
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

        # Erzeuge den Play/Pause-Button
        self.play_button = create_play_button()
        self.play_button.on_click(lambda event: self.toggle_play(None))

        # Erzeuge Steuerungselemente für die Spielgeschwindigkeit
        speed_minus = pn.widgets.Button(name="-", button_type="warning", width=40)
        speed_plus = pn.widgets.Button(name="+", button_type="success", width=40)
        speed_label = pn.pane.Markdown(f"Speed: {self.play_speed} ms", width=100)
        speed_input = create_speed_widget(self.play_speed)
        speed_input.link(self, value='play_speed', bidirectional=True)

        # Definition der Callbacks für Geschwindigkeitsanpassung
        def decrease_speed(event):
            new_speed = max(self.play_speed - 200, 50)
            self.play_speed = new_speed
            speed_label.object = f"Speed: {new_speed} ms"

        def increase_speed(event):
            new_speed = min(self.play_speed + 200, 2000)
            self.play_speed = new_speed
            speed_label.object = f"Speed: {new_speed} ms"

        speed_minus.on_click(decrease_speed)
        speed_plus.on_click(increase_speed)

        # Kombiniere die Steuerungselemente in eine horizontale Anordnung
        controls = pn.Row(
            self.date_range_slider,
            self.play_button,
            speed_minus,
            speed_label,
            speed_plus,
            speed_input,
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
            pn.pane.Markdown("### Ai4Good Sentiment Analyse"),
            maps_row
        )
    
        
