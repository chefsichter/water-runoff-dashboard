# dashboard.py
from pathlib import Path

import panel as pn
import pandas as pd

from dashboard.load_data import load_netcdf_dataset, load_shapefile

pn.extension()

from data_preprocessing import update_geodf_with_height, update_geodf_with_variable
from visualization import create_3d_polygons


def get_time_indices(date_range, time_array):
    """Gibt die Indizes aller Zeitpunkte im time_array zurück, die innerhalb des date_range liegen."""
    start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
    return [i for i, t in enumerate(time_array) if (t >= start and t <= end)]


def build_dashboard(ds, geodf) -> pn.Column:
    """
    Baut ein Dashboard, das einen zentralen 3D-Graphen aller Catchments anzeigt.
    Enthalten sind:
      - Eine Variablenauswahl (nur 'P' für Niederschlag und 'T' für Temperatur)
      - Ein DateRangeSlider zur Auswahl des Gesamtzeitraums
      - Ein IntSlider (mit Player-Widget) zur Auswahl/Animation eines aktuellen Zeitindex
      - Ein RadioButton zur Auswahl des Zeitschritts (Tage vs. Wochen)
      - Der Titel des Charts zeigt das aktuelle Datum bzw. die Kalenderwoche an.
      - Die Höhen werden mit einem Flatten-Faktor von 0,033 skaliert (also etwa 1/3 der ursprünglichen Höhe)
    """
    # Variablenauswahl
    variable_options = ['P', 'T']
    variable_selector = pn.widgets.Select(name='Variable', options=variable_options, value=variable_options[0])

    # Zeitarray (als Pandas Timestamps)
    time_array = pd.to_datetime(ds['time'].values)

    # DateRangeSlider für den Gesamtzeitraum
    date_range_slider = pn.widgets.DateRangeSlider(
        name='Zeitraum', start=time_array[0], end=time_array[-1],
        value=(time_array[0], time_array[-1])
    )

    # Zunächst: alle Indizes des gesamten Zeitarrays innerhalb des ausgewählten Zeitraums
    time_indices = get_time_indices(date_range_slider.value, time_array)

    # IntSlider für den aktuellen Zeitindex
    time_index_slider = pn.widgets.IntSlider(name='Aktuelle Zeit', start=0, end=len(time_indices) - 1, value=0)

    # Player-Widget (arbeitet mit Integern)
    player = pn.widgets.Player(name='Play', start=0, end=len(time_indices) - 1, value=0, step=1, interval=500)

    # Verlinke Player und IntSlider (hier per Callback, da pn.link bzw. pn.links in deiner Version nicht verfügbar sind)
    def update_player(event):
        time_index_slider.value = event.new

    player.param.watch(update_player, 'value')

    # RadioButton zur Auswahl des Zeitschritts: 'Tage' (Step=1) oder 'Wochen' (Step=7)
    step_mode = pn.widgets.RadioButtonGroup(name='Zeitschritt', options=['Tage', 'Wochen'], value='Tage')

    def update_step_mode(event):
        player.step = 1 if event.new == 'Tage' else 7

    step_mode.param.watch(update_step_mode, 'value')

    # Aktualisiere den Indexbereich, wenn sich der DateRangeSlider ändert
    def update_time_index_range(event):
        nonlocal time_indices
        time_indices = get_time_indices(date_range_slider.value, time_array)
        new_end = max(len(time_indices) - 1, 0)
        time_index_slider.start = 0
        time_index_slider.end = new_end
        player.start = 0
        player.end = new_end
        time_index_slider.value = 0  # Reset auf Anfang

    date_range_slider.param.watch(update_time_index_range, 'value')

    def update_dashboard(variable, time_index, step_mode_value):
        # Bestimme den aktuellen Timestamp anhand des Zeitindex aus den selektierten Indizes
        if not time_indices:
            current_time = time_array[0]
        else:
            current_time = time_array[time_indices[time_index]]
        # Erzeuge einen lesbaren Titel:
        if step_mode_value == 'Wochen':
            iso = current_time.isocalendar()
            title_date = f"KW {iso.week}, {current_time.year}"
        else:
            title_date = current_time.strftime('%d.%m.%Y')
        # Aktualisiere das GeoDataFrame:
        updated_geodf = update_geodf_with_height(geodf, ds, flatten_factor=0.033)
        updated_geodf = update_geodf_with_variable(updated_geodf, ds, variable, current_time)
        # Erzeuge den 3D-Graphen (als Panel Plotly Pane)
        map_3d_pane = create_3d_polygons(updated_geodf, 'var_val', variable)
        # Aktualisiere den Titel im eingebetteten Plotly-Figure:
        fig = map_3d_pane.object
        fig.update_layout(title=f"3D Catchment Map - {title_date}")
        # Erstelle ein neues Plotly Pane, das den aktualisierten Figure enthält
        return pn.pane.Plotly(fig, sizing_mode='stretch_both')

    # Binde die Widgets an die Update-Funktion; dabei wird auch der Zeitschritt übergeben.
    interactive_map = pn.bind(update_dashboard, variable_selector, time_index_slider, step_mode)

    dashboard = pn.Column(
        pn.Row(variable_selector, date_range_slider, step_mode, player),
        time_index_slider,
        interactive_map
    )
    return dashboard


# ------------------------------
# Main: Anwendung starten
# ------------------------------
if __name__ == '__main__':
    import os

    # print(f"CONDA_PREFIX: {os.environ['CONDA_PREFIX']}")
    # os.environ['GDAL_DATA'] = os.path.join(os.environ['CONDA_PREFIX'], 'Library', 'share', 'gdal')
    os.environ['GDAL_DATA'] = r'C:\Users\felix\.conda\envs\ai4good\Library\share\gdal'

    # Pfade zu den Daten (bitte anpassen)
    notebook_dir = Path().absolute()
    netcdf_path = notebook_dir.parent / "data" / "CHRUN" / "chrun.nc"
    shapefile_path = notebook_dir.parent / "data" / "CHRUN" / "catchments" / 'catchments.shp'

    # Daten laden
    ds = load_netcdf_dataset(netcdf_path)
    geodf = load_shapefile(shapefile_path)
    # Dashboard erstellen und anzeigen
    dashboard = build_dashboard(ds, geodf)
    dashboard.show()  # In Jupyter evtl. .servable() verwenden
