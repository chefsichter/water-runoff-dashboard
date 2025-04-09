import asyncio
import os
import textwrap
from contextlib import contextmanager

from dashboard.config.settings import INIT_DAY_STRIDE, TIME_MIN, TIME_MAX

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


class MainView(param.Parameterized):
    # Alle Variablen sollen in der Combobox auswählbar sein.
    variable = param.ObjectSelector(default=None, objects=[])
    # Stride (Tage) über ein Inputfeld (IntInput) eingeben.
    day_stride = param.Integer(default=INIT_DAY_STRIDE, bounds=(1, 3650))
    # Wir verwenden nur noch einen Zeitbereich, nicht mehr ein einzelnes Datum:
    start_date = param.CalendarDate(default=pd.Timestamp("2000-01-01").date())
    end_date = param.CalendarDate(default=pd.Timestamp("2000-01-07").date())

    # Play/Pause-Action
    play = param.Action(lambda x: x.param.trigger('play'), label='Play')
    playing = False
    # Spielgeschwindigkeit in Millisekunden (Standard: 300 ms)
    play_speed = param.Number(default=300, bounds=(50, 2000))
    # Global max für den Farbbereich (wird nach Berechnung gesetzt)
    global_max = param.Number(default=0)

    # Daten
    ds = param.ClassSelector(class_=object, default=None)
    gdf = param.ClassSelector(class_=object, default=None)
    all_vars = param.List(default=[])
    time_vars = param.List(default=[])
    static_vars = param.List(default=[])
    time_min = param.CalendarDate(default=TIME_MIN)
    time_max = param.CalendarDate(default=TIME_MAX)

    # Tap-Stream für Klicks
    tap_stream = Tap(x=None, y=None, source=None)
    var_cmaps = param.Dict(default={})

    def __init__(self, **params):
        super().__init__(**params)
        # Setze die Auswahlmöglichkeiten: Hier sind all_vars (z.B. ["P", "T", ...]) enthalten.
        self.param.variable.objects = self.all_vars
        # Spinner als Ladeanzeige
        self.spinner = pn.indicators.LoadingSpinner(visible=False, width=50, height=50,
                                                    css_classes=["spinner-centered"])
        # Wir legen später den Time-Slider fest:
        self.date_range_slider = None

    @property
    def date_range(self):
        return self.start_date, self.end_date

    @date_range.setter
    def date_range(self, value):
        # Optional kannst du hier eine Validierung einbauen
        self.start_date, self.end_date = value

    @contextmanager
    def show_spinner(self):
        self.spinner.visible = True
        try:
            yield
        finally:
            self.spinner.visible = False

    @pn.depends('day_stride', watch=True)
    def update_date_range(self):
        # Aktualisiere das Standard-Zeitintervall, wenn day_stride geändert wird.
        start = self.date_range[0]
        if self.day_stride > 1:
            end = pd.to_datetime(start) + pd.Timedelta(days=self.day_stride - 1)
            self.date_range = (pd.to_datetime(start).date(), end.date())
        else:
            self.date_range = (pd.to_datetime(start).date(), pd.to_datetime(start).date())

    def get_start_date(self):
        return self.date_range[0]

    def compute_global_max(self):
        """
        Berechnet über den gesamten Datensatz (für die aktuell ausgewählte Variable und day_stride)
        den maximalen aggregierten Wert. Während der Berechnung wird ein Spinner angezeigt.
        """
        self.spinner.visible = True
        var_name = self.variable
        if var_name is None or var_name not in self.ds:
            self.global_max = 0
            self.spinner.visible = False
            return
        da = self.ds[var_name]
        if 'time' in da.dims:
            # Verwende xarray rolling, um das aggregierte Fenster zu berechnen:
            aggregated = da.rolling(time=self.day_stride, min_periods=self.day_stride).sum()
            self.global_max = float(aggregated.max())
        else:
            self.global_max = float(da.max())
        self.spinner.visible = False

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

    @pn.depends('variable', 'day_stride', 'start_date', 'end_date', watch=False)
    async def get_map(self):
        await asyncio.sleep(0.1)
        var_name = self.variable
        if var_name is None:
            return hv.Curve([]).opts(width=800, height=500)
        # Immer den Zeitbereich nutzen:
        time_value = self.date_range
        agg_da = self._aggregate_data(var_name, time_value, self.day_stride)
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
            height=500,
            active_tools=['wheel_zoom']
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
        with self.show_spinner():
            var_name = self.variable
            if var_name is None:
                return pn.pane.Markdown("Keine Variable ausgewählt.")
            # Immer den Zeitbereich verwenden:
            time_value = self.date_range
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

    def get_speed_widget(self):
        speed_input = pn.widgets.IntInput(
            name="Speed (ms)", value=int(self.play_speed), step=200, width=100
        )
        speed_input.link(self, value='play_speed', bidirectional=True)
        return speed_input

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
            value=(pd.Timestamp(self.date_range[0]), pd.Timestamp(self.date_range[1])),
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

        self.param.watch(lambda event: update_slider(), ['start_date', 'end_date'])

        return date_range_slider

    def panel_view(self):
        # Erzeuge den Zeitschieberegler (DateSlider)
        self.date_range_slider = self.get_date_range_slider()

        # Erzeuge den Play/Pause-Button
        self.play_button = pn.widgets.Button(name="Play", button_type="primary", width=60)
        self.play_button.on_click(lambda event: self.toggle_play(None))

        # Erzeuge Steuerungselemente für die Spielgeschwindigkeit
        speed_minus = pn.widgets.Button(name="-", button_type="warning", width=40)
        speed_plus = pn.widgets.Button(name="+", button_type="success", width=40)
        speed_label = pn.pane.Markdown(f"Speed: {self.play_speed} ms", width=100)
        speed_input = self.get_speed_widget()

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
            self.spinner,
            self.date_range_slider,
            self.play_button,
            speed_minus,
            speed_label,
            speed_plus,
            speed_input,
            sizing_mode="stretch_width"
        )

        # Aufbau des Hauptinhalts: Karte (Map) und Tabelle (Detailansicht)
        main_area = pn.Row(
            pn.Column(self.get_map),
            pn.Column(
                pn.pane.Markdown("### Wichtige Daten / Einsichten"),
                self.get_table,
                height=500,
                scroll=True
            )
        )

        # Rückgabe des kompletten Panels, das ausschließlich die dashboard‑relevanten Inhalte enthält.
        return pn.Column(controls, main_area)
