import asyncio
import os
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import pyproj

from dashboard.config.settings import MIN_DAY_STRIDE, MAX_DAY_STRIDE, INIT_SPEED_MS, INIT_AGG_METHOD
from dashboard.views.main_multiprocessing import init_global_vars, compute_map_df, compute_runoff_df, compute_shap_df
from dashboard.widgets.table_aggregation_widget import create_aggregation_widget

# Link Aggregationsfunktion an MainView
# PROJ_LIB setzen – passe den Pfad ggf. an deine Umgebung an
if "PROJ_LIB" not in os.environ:
    os.environ["PROJ_LIB"] = pyproj.datadir.get_data_dir()

import param
import panel as pn
import pandas as pd

import holoviews as hv
import geoviews as gv
from holoviews.streams import Tap
import cartopy.crs as ccrs
from shapely.geometry import Point

class MainView(param.Parameterized):
    # Alle Variablen sollen in der Combobox auswählbar sein.
    variable = param.ObjectSelector(default=None, objects=[])
    # Stride (Tage) über ein Inputfeld (IntInput) eingeben.
    day_stride = param.Integer(default=None, bounds=(MIN_DAY_STRIDE, MAX_DAY_STRIDE))
    # Wir verwenden nur noch einen Zeitbereich, nicht mehr ein einzelnes Datum:
    start_date = param.CalendarDate(default=None)
    end_date = param.CalendarDate(default=None)

    # Play/Pause-Action
    play = param.Action(lambda x: x.param.trigger('play'), label='Play')
    playing = False
    # Spielgeschwindigkeit in Millisekunden (Standard: 300 ms)
    play_speed = param.Number(default=INIT_SPEED_MS, bounds=(50, 100000))

    # Zeitbereich (für Slider)
    time_min = param.CalendarDate(default=None)
    time_max = param.CalendarDate(default=None)

    # Aggregationsfunktion für Zeitdimension (sum, mean, max, min)
    agg_method = param.ObjectSelector(
        default=INIT_AGG_METHOD,
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
        # Caches for map visualizations to avoid redundant recomputations
        self._cache_map = {}
        self._cache_map_shap = {}
        self._cache_map_diff = {}
        # Executor for asynchronous map building across processes (bypass GIL)
        # Use initializer to set up global datasets in worker processes
        self._executor = ProcessPoolExecutor(
            max_workers=os.cpu_count(),
            initializer=init_global_vars,
            initargs=(self.ds, self.shap_ds)
        )

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

    @pn.depends('variable', 'start_date', 'end_date', 'agg_method', watch=False)
    async def get_map_shap_ds(self):
        """Async SHAP-Karte für die aktuell gewählte Variable."""
        var_name = self.variable
        key = (var_name, self.start_date, self.end_date, self.agg_method)
        if key in self._cache_map_shap:
            return self._cache_map_shap[key]
        loop = asyncio.get_running_loop()
        df_values = await loop.run_in_executor(
            self._executor,
            compute_shap_df,
            var_name,
            self.date_range,
            self.agg_method
        )
        if df_values is None or df_values.empty:
            result = pn.pane.Markdown(f"Keine SHAP-Werte für Variable {var_name} vorhanden.", width=300)
        else:
            merged = self.gdf.join(df_values, on="hru", how="inner").dropna(subset=[var_name])
            if merged.empty:
                result = pn.pane.Markdown(f"Keine SHAP-Daten für {var_name} darstellbar.", width=300)
            else:
                opts = dict(
                    projection=ccrs.Mercator(),
                    tools=['hover'],
                    color=var_name,
                    cmap='coolwarm',
                    colorbar=True,
                    line_color='black',
                    line_width=0.1,
                    width=800,
                    height=500,
                    xformatter='%.2e',
                    yformatter='%.2e'
                )
                values = merged[var_name].values
                vmax = max(abs(values.max()), abs(values.min()))
                opts['clim'] = (-vmax, vmax)
                result = gv.Polygons(merged, crs=ccrs.PlateCarree(), vdims=[var_name, 'hru']).opts(**opts)
        self._cache_map_shap[key] = result
        return result

    @pn.depends('start_date', 'end_date', 'agg_method', watch=False)
    async def get_map_run_off_diff(self):
        """Async Runoff-Differenz-Karte."""
        key = (self.start_date, self.end_date, self.agg_method)
        if key in self._cache_map_diff:
            return self._cache_map_diff[key]
        var_name = 'Y'
        loop = asyncio.get_running_loop()
        df_values = await loop.run_in_executor(
            self._executor,
            compute_runoff_df,
            self.date_range,
            self.agg_method
        )
        if df_values is None or df_values.empty:
            result = pn.pane.Markdown(f"Keine SHAP-Daten für Runoff-Differenz darstellbar.", width=300)
        else:
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
                height=500,
                xformatter='%.2e',
                yformatter='%.2e'
            )
            values = merged[var_name].values
            vmin, vmax = np.percentile(values, [2, 98])
            opts['clim'] = (vmin, vmax)
            result = gv.Polygons(merged, crs=ccrs.PlateCarree(), vdims=[var_name, 'hru']).opts(**opts)
        self._cache_map_diff[key] = result
        return result

    @pn.depends('variable', 'start_date', 'end_date', 'agg_method', watch=False)
    async def get_map(self):
        """Async aggregierte Karte für die gewählte Variable."""
        var_name = self.variable
        if var_name is None:
            return hv.Curve([]).opts(width=800, height=500)
        key = (var_name, self.start_date, self.end_date, self.agg_method)
        if key in self._cache_map:
            return self._cache_map[key]
        loop = asyncio.get_running_loop()
        df_values = await loop.run_in_executor(
            self._executor,
            compute_map_df,
            var_name,
            self.date_range,
            self.agg_method
        )
        if df_values is None or df_values.empty:
            result = hv.Curve([]).opts(width=800, height=500)
        else:
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
                height=500,
                xformatter='%.2e',
                yformatter='%.2e'
            )
            result = gv.Polygons(merged, crs=ccrs.PlateCarree(), vdims=[var_name, 'hru']).opts(**opts)
        self._cache_map[key] = result
        self.tap_stream.source = result
        return result

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
                # No polygon under click point: show Markdown message
                return pn.pane.Markdown("No polygon found at the click location.", width=300)
        else:
            # Before clicking: show prompt
            return pn.pane.Markdown("Click on a polygon to see details.", width=300)

    def get_date_range_slider(self):
        """
        Erstellt einen DateRangeSlider, der den gesamten Zeitbereich auswählt.
        Das Widget liefert ein Tupel (start, end), das in den Parameter date_range
        (als Tuple von datetime.date) konvertiert und aktualisiert wird.
        """
        # Konvertiere initial den date_range-Wert in Timestamps, da der DateRangeSlider Timestamps verwendet.
        date_range_slider = pn.widgets.DateRangeSlider(
            name="🕒 Time Range",
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
            start_date = new_start.date() if hasattr(new_start, "date") else new_start
            end_date = new_end.date() if hasattr(new_end, "date") else new_end
            self.date_range = (start_date, end_date)

        date_range_slider.param.watch(update_dates, 'value')

        # Callback, um den Slider zu aktualisieren, wenn start_date oder end_date sich ändern.
        def update_slider(*events):
            if date_range_slider.value != (pd.Timestamp(self.start_date), pd.Timestamp(self.end_date)):
                date_range_slider.value = (pd.Timestamp(self.start_date), pd.Timestamp(self.end_date))

        self.param.watch(lambda *args, **kwargs: update_slider(), ['start_date', 'end_date'])

        return date_range_slider

    def _get_long_name(self, variable):
        meta = self.var_metadata.get(self.variable, {})
        long_name = meta.get('long_name') or self.variable
        return long_name

    @pn.depends('variable')
    def get_map1_title(self):
        return pn.panel(f"### Aggregated values for '{self._get_long_name(self.variable)}'")

    @pn.depends('variable')
    def get_map3_title(self):
        return pn.panel(f"### Aggregated SHAP values for '{self._get_long_name(self.variable)}'")

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
            pn.pane.Markdown("### 'HRU' aggregated values"),
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
                pn.pane.Markdown("### Aggregated absolute difference between the runoff models ('Y')"),
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
            pn.pane.Markdown("### Ai4Good Sensitivity Analysis"),
            maps_row,
            main_area
        )