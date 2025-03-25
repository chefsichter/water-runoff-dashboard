import os

# PROJ_LIB setzen – passe den Pfad ggf. an deine Umgebung an
os.environ["PROJ_LIB"] = "/home/chefsichter/miniconda3/envs/ai4good/share/proj"

import param
import panel as pn
import pandas as pd
import numpy as np
import geopandas as gpd
import xarray as xr

import holoviews as hv
import geoviews as gv
from holoviews.streams import Tap
from bokeh.models import HoverTool
import cartopy.crs as ccrs
from shapely.geometry import Point

hv.extension('bokeh')
pn.extension()


class CHRUNDashboard(param.Parameterized):
    # Alle Variablen sollen in der Combobox auswählbar sein.
    variable = param.ObjectSelector(default=None, objects=[])
    # Stride (Tage) über ein Inputfeld (IntInput) eingeben.
    day_stride = param.Integer(default=7, bounds=(1, 3650))
    # Für einzelne Datumsauswahl (day_stride==1)
    date = param.CalendarDate(default=pd.Timestamp("2000-01-01").date())
    # Für Zeitintervall, wenn day_stride > 1
    date_range = param.Tuple(default=(pd.Timestamp("2000-01-01").date(),
                                      pd.Timestamp("2000-01-01").date()))
    # Play/Pause-Action
    play = param.Action(lambda x: x.param.trigger('play'), label='Play')
    playing = False
    # Spielgeschwindigkeit in Millisekunden (niedriger = schneller)
    play_speed = param.Number(default=300, bounds=(50, 2000))

    # Referenzen auf die Daten
    ds = param.ClassSelector(class_=object, default=None)
    gdf = param.ClassSelector(class_=object, default=None)
    time_vars = param.List(default=[])
    static_vars = param.List(default=[])
    time_min = param.CalendarDate(default=pd.Timestamp("2000-01-01").date())
    time_max = param.CalendarDate(default=pd.Timestamp("2100-01-01").date())

    # Tap-Stream zum Anklicken von Polygonen
    tap_stream = Tap(x=None, y=None, source=None)
    var_cmaps = param.Dict(default={})

    def __init__(self, **params):
        super().__init__(**params)
        self.tap_stream = Tap(source=None, x=None, y=None)
        self.param.watch(self.update_map, ['variable', 'day_stride', 'date', 'date_range'])
        self.param.watch(self.toggle_play, ['play'])
        self.param.watch(self.update_date_range, ['day_stride'])

    def update_map(self, *events):
        """
        Callback, wenn sich Variable, Stride oder Datum ändern.
        Hier kannst du weitere Logik ergänzen, um z. B. automatisch die Karte neu zu rendern.
        """
        pass

    def update_date_range(self, event):
        # Setze das Standard-Zeitintervall neu, wenn day_stride geändert wird.
        start = self.time_min
        if self.day_stride > 1:
            end = pd.to_datetime(start) + pd.Timedelta(days=self.day_stride - 1)
            self.date_range = (pd.to_datetime(start).date(), end.date())
        else:
            self.date_range = (pd.to_datetime(start).date(), pd.to_datetime(start).date())

    def toggle_play(self, event):
        self.playing = not self.playing
        if self.playing:
            self._play_loop()

    def _play_loop(self):
        if not self.playing:
            return
        # Bei day_stride > 1 wird das Zeitintervall verschoben,
        # ansonsten wird das Datum um 1 Tag erhöht.
        if self.day_stride > 1:
            current_start = pd.to_datetime(self.date_range[0])
            next_start = current_start + pd.Timedelta(days=self.day_stride)
            if next_start.date() > pd.to_datetime(self.time_max).date():
                self.playing = False
                return
            new_range = (next_start.date(), (next_start + pd.Timedelta(days=self.day_stride - 1)).date())
            self.date_range = new_range
        else:
            current_date = pd.to_datetime(self.date)
            next_date = current_date + pd.Timedelta(days=1)
            if next_date.date() > pd.to_datetime(self.time_max).date():
                self.playing = False
                return
            self.date = next_date.date()
        # Verwende die aktuell eingestellte play_speed (ms)
        pn.state.add_periodic_callback(self._play_loop, period=self.play_speed, count=1)

    def _get_cmap_for_var(self, var_name):
        if var_name in self.var_cmaps:
            return self.var_cmaps[var_name]
        return self.var_cmaps.get('*default*', 'Viridis')

    def _aggregate_data(self, var_name, time_value, day_stride):
        da = self.ds[var_name]
        if 'time' in da.dims:
            if isinstance(time_value, (list, tuple)):
                start_date = pd.to_datetime(time_value[0])
                end_date = pd.to_datetime(time_value[1])
            else:
                start_date = pd.to_datetime(time_value)
                if day_stride > 1:
                    end_date = start_date + pd.Timedelta(days=day_stride - 1)
                else:
                    end_date = start_date
            sel_da = da.sel(time=slice(start_date, end_date))
            agg_da = sel_da.sum(dim='time')
        else:
            agg_da = da
        return agg_da

    @pn.depends('variable', 'day_stride', 'date', 'date_range', watch=False)
    def get_map(self):
        var_name = self.variable
        if var_name is None:
            return hv.Curve([]).opts(width=800, height=500)
        # Wähle das Zeitargument: Wenn day_stride > 1, dann das Intervall, sonst das Einzel-Datum.
        time_value = self.date_range if self.day_stride > 1 else self.date
        agg_da = self._aggregate_data(var_name, time_value, self.day_stride)
        df_values = agg_da.to_series().to_frame(name=var_name)
        if "hru" in self.gdf.index.names:
            gdf2 = self.gdf.reset_index()
        else:
            gdf2 = self.gdf.copy()
        merged = gdf2.join(df_values, on="hru", how="inner")
        merged = merged.dropna(subset=[var_name])
        polys = gv.Polygons(
            merged,
            crs=ccrs.PlateCarree(),  # Die Daten liegen jetzt in EPSG:4326
            vdims=[var_name, 'hru']
        ).opts(
            projection=ccrs.Mercator(),
            tools=['hover', 'tap'],
            color=var_name,
            cmap=self._get_cmap_for_var(var_name),
            colorbar=True,
            line_color='black',
            line_width=0.1,
            width=800,
            height=500,
            active_tools=['wheel_zoom']
        )
        self.tap_stream.source = polys
        return polys

    @pn.depends('variable', 'day_stride', 'date', 'date_range', 'tap_stream.x', 'tap_stream.y', watch=False)
    def get_table(self):
        var_name = self.variable
        if var_name is None:
            return pn.pane.Markdown("Keine Variable ausgewählt.")
        time_value = self.date_range if self.day_stride > 1 else self.date
        agg_da = self._aggregate_data(var_name, time_value, self.day_stride)
        df_values = agg_da.to_series().to_frame(name=var_name)
        if self.tap_stream.x is not None and self.tap_stream.y is not None:
            click_point = Point(self.tap_stream.x, self.tap_stream.y)
            selected = self.gdf[self.gdf.geometry.contains(click_point)]
            if len(selected) > 0:
                hru_clicked = selected.iloc[0]['hru']
                row_data = {}
                for v in self.static_vars:
                    try:
                        val = float(self.ds[v].sel(hru=hru_clicked).values)
                        row_data[v] = val
                    except Exception:
                        row_data[v] = None
                if var_name in self.time_vars:
                    try:
                        row_data[var_name] = float(df_values.loc[hru_clicked][var_name])
                    except Exception:
                        row_data[var_name] = None
                else:
                    try:
                        row_data[var_name] = float(self.ds[var_name].sel(hru=hru_clicked).values)
                    except Exception:
                        row_data[var_name] = None
                table_df = pd.DataFrame.from_dict(row_data, orient='index', columns=['Wert'])
                table_df.index.name = 'Variable'
                return pn.widgets.DataFrame(table_df, height=400, width=300, fit_columns=True)
            else:
                return pn.pane.Markdown("Kein Polygon unter Klickpunkt gefunden.")
        else:
            return pn.pane.Markdown("Klicke auf ein Polygon, um Details zu sehen.")

    def get_time_widget(self):
        if self.day_stride > 1:
            time_widget = pn.widgets.DateRangeSlider(
                name='Zeitbereich',
                start=pd.to_datetime(self.time_min),
                end=pd.to_datetime(self.time_max),
                value=(pd.to_datetime(self.date_range[0]), pd.to_datetime(self.date_range[1]))
            )
            time_widget.link(self, value='date_range', bidirectional=True)
            return time_widget
        else:
            time_widget = pn.widgets.DateSlider(
                name='Datum',
                start=pd.to_datetime(self.time_min),
                end=pd.to_datetime(self.time_max),
                value=pd.to_datetime(self.date)
            )
            time_widget.link(self, value='date', bidirectional=True)
            return time_widget

    def panel_view(self):
        # Erstelle die Steuerelemente in einer Zeile:
        var_widget = pn.widgets.Select(
            name='Variable',
            options=self.param.variable.objects,
            value=self.variable
        )
        # Stride als IntInput statt Slider
        stride_widget = pn.widgets.IntInput(
            name='Stride (Tage)',
            value=self.day_stride,
            width=100
        )
        time_widget = self.get_time_widget()
        play_button = pn.widgets.Button(name="Play/Pause", button_type="primary")
        # Speed-Steuerung: Minus, Label, Plus
        speed_minus = pn.widgets.Button(name="-", button_type="warning", width=40)
        speed_plus = pn.widgets.Button(name="+", button_type="success", width=40)
        speed_label = pn.pane.Markdown(f"Speed: {self.play_speed} ms", width=100)

        def decrease_speed(event):
            new_speed = max(self.play_speed - 50, 50)
            self.play_speed = new_speed
            speed_label.object = f"Speed: {new_speed} ms"

        def increase_speed(event):
            new_speed = min(self.play_speed + 50, 2000)
            self.play_speed = new_speed
            speed_label.object = f"Speed: {new_speed} ms"

        speed_minus.on_click(decrease_speed)
        speed_plus.on_click(increase_speed)

        controls = pn.Row(
            var_widget,
            stride_widget,
            time_widget,
            play_button,
            speed_minus,
            speed_label,
            speed_plus,
            sizing_mode="stretch_width"
        )

        # Linkings
        var_widget.link(self, value='variable', bidirectional=False)
        stride_widget.link(self, value='day_stride', bidirectional=True)

        # time_widget wird in get_time_widget verlinkt

        play_button.on_click(lambda event: self.toggle_play(None))

        main_area = pn.Row(
            pn.Column(self.get_map),
            pn.Column(
                pn.pane.Markdown("### Wichtige Daten / Einsichten"),
                self.get_table,
                height=500,
                scroll=True
            )
        )

        return pn.Column(controls, main_area)
