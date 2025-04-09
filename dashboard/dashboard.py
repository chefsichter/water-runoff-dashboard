import asyncio
import os
import textwrap
from contextlib import contextmanager

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


class CHRUNDashboard(param.Parameterized):
    # Alle Variablen sollen in der Combobox auswählbar sein.
    variable = param.ObjectSelector(default=None, objects=[])
    # Stride (Tage) über ein Inputfeld (IntInput) eingeben.
    day_stride = param.Integer(default=7, bounds=(1, 3650))
    # Wir verwenden nur noch einen Zeitbereich, nicht mehr ein einzelnes Datum:
    date_range = param.Tuple(default=(pd.Timestamp("2000-01-01").date(),
                                      pd.Timestamp("2000-01-07").date()))
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
    time_min = param.CalendarDate(default=pd.Timestamp("2000-01-01").date())
    time_max = param.CalendarDate(default=pd.Timestamp("2100-01-01").date())

    # Tap-Stream für Klicks
    tap_stream = Tap(x=None, y=None, source=None)
    var_cmaps = param.Dict(default={})

    def __init__(self, **params):
        # Erwarte zusätzlich ein Dictionary mit Metadaten:
        self.bootstrap: pn.template.BootstrapTemplate = params.pop('bootstrap')
        self.var_metadata = params.pop('var_metadata', {})
        self.script_dir = params.pop('script_dir', None)
        super().__init__(**params)
        # Setze die Auswahlmöglichkeiten: Hier sind alle_vars (z.B. ["P", "T", ...]) enthalten.
        self.param.variable.objects = self.all_vars
        # Spinner als Ladeanzeige
        self.spinner = pn.indicators.LoadingSpinner(visible=False, width=50, height=50,
                                                    css_classes=["spinner-centered"])
        # Wir legen später den Time-Slider fest:
        self.time_slider = None
        # Erzeuge einen festen Container für den Modal-Inhalt und füge ihn in das Bootstrap-Template ein.
        self.modal_container = pn.Column(sizing_mode="stretch_width")
        self.bootstrap.modal.objects = [self.modal_container]

    def load_custom_css(self):
        if self.script_dir:
            css_path = self.script_dir / "css" / "custom.css"
            if css_path.exists():
                with open(css_path, "r") as f:
                    custom_css = f.read()
                pn.config.raw_css.append(custom_css)
            else:
                print(f"CSS-Datei nicht gefunden: {css_path}")
        else:
            print("Kein script_dir-Parameter übergeben. CSS konnte nicht geladen werden.")

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
        start = self.time_min
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

    @pn.depends('variable', 'day_stride', 'date_range', watch=False)
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

    @staticmethod
    def pretty_date_range(date_range):
        start, end = date_range
        if start == end:
            return f"🕒 Datum: {start.strftime('%d.%m.%Y')}"
        else:
            return f"🕒 Zeitraum: {start.strftime('%d.%m.')} – {end.strftime('%d.%m.%Y')}"

    @pn.depends('date_range', watch=True)
    def update_time_slider_label(self):
        self.time_slider.name = self.pretty_date_range(self.date_range)

    def get_time_slider(self):
        # Aktualisiere den Zeitbereich, wenn der Slider bewegt wird:
        def on_slider_change_update_date_range(event):
            new_start = event.new  # event.new ist bereits ein datetime.date
            new_end = (pd.to_datetime(new_start) + pd.Timedelta(days=self.day_stride - 1)).date()
            self.date_range = (new_start, new_end)

        # Erstelle einen DateSlider, der den Start des Zeitbereichs auswählt.
        time_slider = pn.widgets.DateSlider(
            name=self.pretty_date_range(self.date_range),
            start=pd.to_datetime(self.time_min),
            end=pd.to_datetime(self.time_max),
            value=pd.to_datetime(self.get_start_date()),
            show_value=False
        )

        time_slider.param.watch(on_slider_change_update_date_range, 'value')
        return time_slider

    def show_variable_info(self, event=None):
        """
        Zeigt einen modernen Modal-Dialog mit stylischen Emojis und Infos zur aktuell
        ausgewählten Variable an, wobei das im Bootstrap-Template integrierte Modal genutzt wird.
        """
        var_key = self.variable
        if var_key not in self.var_metadata:
            pn.state.notifications.error("❌ Keine Metadaten für diese Variable vorhanden.")
            return

        # Schließe zunächst das Modal, falls es bereits offen ist.
        self.bootstrap.close_modal()

        meta = self.var_metadata[var_key]
        # Erstelle einen dynamischen Header, der den gewünschten Titel anzeigt.
        modal_content = textwrap.dedent(f"""
            ### 🔍 Information: {var_key}
            | **Zusatzinformationen** |                    |
            | -------------------------- | ----------------------------- |
            | 🏷️ Variablenname          | {meta.get("name", "N/A")}      |
            | 🗺️ Bezeichnung           | {meta.get("long_name", "N/A")} |
            | ⚖️ Einheiten             | {meta.get("units", "N/A")}     |
            | 📐 Dimensionen           | {meta.get("dims", "N/A")}      |
            | 💾 Datentyp              | {meta.get("dtype", "N/A")}     |
            | 🗂️ Quelle              | {meta.get("source", "N/A")}    |
            | 🕓 Historie             | {meta.get("history", "N/A")}   |
        """)
        # Aktualisiere den Inhalt des fest definierten Modal-Containers
        self.modal_container.objects = [modal_content]
        # Öffne das Modal
        self.bootstrap.open_modal()

    def panel_view(self):
        # Erstelle ein Options-Dictionary: Schlüssel = Variablenname, Wert = long_name (sofern vorhanden)
        var_options = {
            self.var_metadata.get(var, {}).get("long_name", var): var
            for var in self.all_vars
        }
        var_widget = pn.widgets.Select(
            name='📊 Variable',
            options=var_options,
            value=self.variable
        )
        # Info-Button neben der Variablen-Auswahl
        info_button = pn.widgets.Button(name="ℹ️", width=30)
        info_button.on_click(self.show_variable_info)
        var_selector = pn.Row(var_widget, info_button)

        stride_widget = pn.widgets.IntInput(
            name='↔️ Tage',
            value=self.day_stride,
            width=100
        )
        self.time_slider = self.get_time_slider()

        self.play_button = pn.widgets.Button(name="Play", button_type="primary", width=60)
        self.play_button.on_click(lambda event: self.toggle_play(None))

        speed_minus = pn.widgets.Button(name="-", button_type="warning", width=40)
        speed_plus = pn.widgets.Button(name="+", button_type="success", width=40)
        speed_label = pn.pane.Markdown(f"Speed: {self.play_speed} ms", width=100)
        speed_input = self.get_speed_widget()

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

        controls = pn.Row(
            var_selector,
            stride_widget,
            self.spinner,
            self.time_slider,
            self.play_button,
            speed_minus,
            speed_label,
            speed_plus,
            speed_input,
            sizing_mode="stretch_width"
        )

        var_widget.link(self, value='variable', bidirectional=False)
        stride_widget.link(self, value='day_stride', bidirectional=True)

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


if __name__ == '__main__':
    dashboard = CHRUNDashboard()
