import os
import cartopy.crs as ccrs

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

from shapely.geometry import Point

hv.extension('bokeh')
pn.extension()


class CHRUNDashboard(param.Parameterized):
    """
    Das zentrale Dashboard-Objekt, das Panel-Widgets, Aggregationslogik und Visualisierung vereint.
    """
    # Auswahl der Variable: Verwende ObjectSelector statt Select
    variable = param.ObjectSelector(default=None, objects=[])
    # Stride in Tagen
    day_stride = param.Integer(default=7, bounds=(1, 3650))
    # Datumsauswahl als Python-Datum (param.CalendarDate akzeptiert nur date-Objekte)
    date = param.CalendarDate(default=pd.Timestamp("2000-01-01").date())

    # Play-Action
    play = param.Action(lambda x: x.param.trigger('play'), label='Play')
    playing = False  # interner Status

    # Referenzen auf Daten: ds = xarray Dataset, gdf = GeoDataFrame
    ds = param.ClassSelector(class_=object, default=None)
    gdf = param.ClassSelector(class_=object, default=None)
    time_vars = param.List(default=[])
    static_vars = param.List(default=[])
    time_min = param.CalendarDate(default=pd.Timestamp("2000-01-01").date())
    time_max = param.CalendarDate(default=pd.Timestamp("2100-01-01").date())

    # Tap-Stream zum Anklicken von Polygonen
    tap_stream = Tap(x=None, y=None, source=None)

    # Kolormap-Dictionary
    var_cmaps = param.Dict(default={})

    def __init__(self, **params):
        super().__init__(**params)
        # Tap-Stream initialisieren
        self.tap_stream = Tap(source=None, x=None, y=None)
        # Watcher setzen, um Änderungen zu behandeln
        self.param.watch(self.update_map, ['variable', 'day_stride', 'date'])
        self.param.watch(self.toggle_play, ['play'])

    def toggle_play(self, event):
        """Startet/Stoppt die Animation."""
        self.playing = not self.playing
        if self.playing:
            self._play_loop()

    def _play_loop(self):
        """Loop-Funktion für das Play-Widget."""
        if not self.playing:
            return

        current_date = pd.to_datetime(self.date)
        next_date = current_date + pd.Timedelta(days=self.day_stride)
        if next_date.date() > pd.to_datetime(self.time_max).date():
            self.playing = False
            return
        self.date = next_date.date()
        # Nächster Aufruf in 300ms
        pn.state.add_periodic_callback(self._play_loop, period=300, count=1)

    def update_map(self, *events):
        """
        Callback, wenn sich Variable, Stride oder Datum ändern.
        Hier kannst du weitere Logik ergänzen, um z. B. automatisch die Karte neu zu rendern.
        """
        pass

    def _get_cmap_for_var(self, var_name):
        """Gibt die passende Colormap zurück oder default."""
        if var_name in self.var_cmaps:
            return self.var_cmaps[var_name]
        return self.var_cmaps.get('*default*', 'Viridis')

    def _aggregate_data(self, var_name, start_date, day_stride):
        """
        Liefert ein DataArray mit aggregierten Werten pro hru:
        - Falls var_name eine Zeitdimension hat, summieren wir über [start_date, start_date+day_stride-1].
        - Andernfalls wird der statische Wert zurückgegeben.
        """
        da = self.ds[var_name]
        if 'time' in da.dims:
            start_date = pd.to_datetime(start_date)
            end_date = start_date + pd.Timedelta(days=day_stride - 1)
            sel_da = da.sel(time=slice(start_date, end_date))
            agg_da = sel_da.sum(dim='time')
        else:
            agg_da = da
        return agg_da

    @pn.depends('variable', 'day_stride', 'date', watch=False)
    def get_map(self):
        """Erzeugt die GeoViews-Karte mit den farbigen Polygonen."""
        var_name = self.variable
        start_date = self.date
        stride = self.day_stride

        if var_name is None:
            return hv.Curve([]).opts(width=600, height=500)

        # Aggregierte Daten holen
        agg_da = self._aggregate_data(var_name, start_date, stride)
        df_values = agg_da.to_series().to_frame(name=var_name)

        if "hru" in self.gdf.index.names:
            gdf2 = self.gdf.reset_index()
        else:
            gdf2 = self.gdf.copy()

        merged = gdf2.join(df_values, on="hru", how="inner")
        merged = merged.dropna(subset=[var_name])

        # Neu: Beim Erzeugen der Polygone den CRS angeben
        polys = gv.Polygons(
            merged,
            crs=ccrs.PlateCarree(),  # Die Daten liegen jetzt in Lat/Lon (EPSG:4326)
            vdims=[var_name, 'hru']
        ).opts(
            projection=ccrs.Mercator(),  # Beispiel: Darstellung in Mercator
            tools=['hover', 'tap'],
            color=var_name,
            cmap=self._get_cmap_for_var(var_name),
            colorbar=True,
            line_color='black',
            line_width=0.1,
            width=600,
            height=500,
            active_tools=['wheel_zoom']
        )

        self.tap_stream.source = polys
        return polys

    @pn.depends('variable', 'day_stride', 'date', 'tap_stream.x', 'tap_stream.y', watch=False)
    def get_table(self):
        """
        Erzeugt eine tabellarische Ansicht der Daten, die beim Klick auf ein Polygon angezeigt werden.
        """
        var_name = self.variable
        if var_name is None:
            return pn.pane.Markdown("Keine Variable ausgewählt.")

        # Aggregierte Daten holen
        agg_da = self._aggregate_data(var_name, self.date, self.day_stride)
        df_values = agg_da.to_series().to_frame(name=var_name)

        # Prüfen, ob ein Klick registriert wurde
        if self.tap_stream.x is not None and self.tap_stream.y is not None:
            click_point = Point(self.tap_stream.x, self.tap_stream.y)
            selected = self.gdf[self.gdf.geometry.contains(click_point)]
            if len(selected) > 0:
                hru_clicked = selected.iloc[0]['hru']
                row_data = {}
                # Statische Variablen
                for v in self.static_vars:
                    try:
                        val = float(self.ds[v].sel(hru=hru_clicked).values)
                        row_data[v] = val
                    except Exception:
                        row_data[v] = None
                # Zeitabhängige Variable
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

    def panel_view(self):
        """Erzeugt das komplette Panel-Layout des Dashboards."""
        var_widget = pn.widgets.Select(
            name='Variable',
            options=self.param.variable.objects,
            value=self.variable
        )
        stride_widget = pn.widgets.IntSlider(
            name='Stride (Tage)',
            start=1, end=3650,
            value=self.day_stride
        )
        date_widget = pn.widgets.DateSlider(
            name='Datum',
            start=pd.to_datetime(self.time_min),
            end=pd.to_datetime(self.time_max),
            value=pd.to_datetime(self.date)
        )
        play_button = pn.widgets.Button(name="Play/Stop", button_type="primary")

        # Einseitige Verknüpfung der Widgets mit den Parametern
        var_widget.link(self, value='variable', bidirectional=False)
        stride_widget.link(self, value='day_stride', bidirectional=False)
        date_widget.link(self, value='date', bidirectional=False)

        @pn.depends(play_button.param.clicks, watch=True)
        def _toggle_play(_):
            self.toggle_play(None)

        # Verwende get_map und get_table als reaktive Funktionen
        map_panel = self.get_map
        table_panel = self.get_table

        top_row = pn.Row(
            pn.Column(
                pn.pane.Markdown("### Combobox Auswahl Variablen"),
                var_widget,
                pn.pane.Markdown("### Inputbox Tage (Stride)"),
                stride_widget
            ),
            pn.Column(
                pn.pane.Markdown("### Zeitbereich (Datum)"),
                date_widget,
                play_button
            )
        )

        main_area = pn.Row(
            pn.Column(map_panel),
            pn.Column(
                pn.pane.Markdown("### Wichtige Daten / Einsichten"),
                table_panel,
                height=500,
                scroll=True
            )
        )

        return pn.Column(top_row, main_area)
