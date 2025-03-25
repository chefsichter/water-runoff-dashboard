# Module importieren
from pathlib import Path

import xarray as xr
import panel as pn
import holoviews as hv
import hvplot.xarray  # erweitert xarray-Objekte um hvplot-Funktionen
import pandas as pd

# Panel und HoloViews initialisieren
pn.extension()
hv.extension('bokeh')

y
# Funktion 1: Dataset laden
def load_dataset(file_path: str) -> xr.Dataset:
    """Lädt ein NetCDF-Dataset und gibt es als xarray.Dataset zurück."""
    return xr.open_dataset(file_path)


# Funktion 2: Minimalen und maximalen Zeitstempel ermitteln
def get_time_range(ds: xr.Dataset) -> (pd.Timestamp, pd.Timestamp):
    """Gibt den frühesten und spätesten Zeitstempel des Datasets zurück."""
    time_coord = ds['time'].values
    return pd.Timestamp(time_coord[0]), pd.Timestamp(time_coord[-1])


# Funktion 3: Verfügbare Variablen ermitteln
def get_available_variables(ds: xr.Dataset) -> list:
    """
    Gibt eine Liste von Variablennamen zurück, die über die Dimensionen 'hru' und 'time' verfügen.
    """
    return [var for var in ds.data_vars if set(ds[var].dims) == {'hru', 'time'}]


# Funktion 4: Dropdown-Widget für die Variablenauswahl erstellen
def create_variable_widget(variables: list) -> pn.widgets.Select:
    """Erstellt ein Dropdown-Widget zur Auswahl einer Variable."""
    return pn.widgets.Select(name='Variable', options=variables, value=variables[0])


# Funktion 5: Slider für die HRU-Auswahl erstellen
def create_hru_widget(ds: xr.Dataset) -> pn.widgets.IntSlider:
    """Erstellt einen IntSlider zur Auswahl des HRU-Index."""
    num_hru = ds.dims['hru']
    return pn.widgets.IntSlider(name='HRU Index', start=0, end=num_hru - 1, step=1, value=0)


# Funktion 6: Datumsbereichs-Widget erstellen
def create_date_range_widget(start: pd.Timestamp, end: pd.Timestamp) -> pn.widgets.DateRangeSlider:
    """Erstellt ein DateRangeSlider-Widget zur Auswahl eines Zeitbereichs."""
    return pn.widgets.DateRangeSlider(name='Zeitbereich', start=start, end=end, value=(start, end))


# Funktion 7: Timeseries-Plot erstellen
def create_timeseries_plot(ds: xr.Dataset, variable: str, hru: int,
                           start: pd.Timestamp, end: pd.Timestamp) -> hv.Element:
    """
    Erstellt ein hvPlot-Zeitsereies-Diagramm für die ausgewählte Variable, den HRU-Index und den Zeitbereich.
    """
    # Datenausschnitt: für den gewählten HRU und den Zeitbereich
    data = ds[variable].isel(hru=hru).sel(time=slice(start, end))
    # Erstellen eines Liniendiagramms mittels hvplot
    return data.hvplot.line(x='time', y=variable, title=f"{variable} für HRU {hru}")


# Funktion 8: Dashboard zusammenbauen
def build_dashboard(ds: xr.Dataset) -> pn.Column:
    """
    Baut das interaktive Dashboard mit den erstellten Widgets und dem Plot zusammen.
    """
    # Verfügbare Variablen ermitteln und Widgets erstellen
    variables = get_available_variables(ds)
    var_widget = create_variable_widget(variables)
    hru_widget = create_hru_widget(ds)
    start, end = get_time_range(ds)
    date_widget = create_date_range_widget(start, end)

    # Update-Funktion: Aktualisiert den Plot basierend auf den Widget-Werten
    def update_plot(variable, hru, date_range):
        start_date, end_date = date_range
        return create_timeseries_plot(ds, variable, hru, start_date, end_date)

    # Mit pn.bind wird die Update-Funktion an die Widgets gebunden
    interactive_plot = pn.bind(update_plot, var_widget, hru_widget, date_widget)

    # Dashboard-Layout definieren: Widgets in einer Zeile und darunter der Plot
    dashboard = pn.Column(
        pn.Row(var_widget, hru_widget, date_widget),
        interactive_plot
    )
    return dashboard


# Beispielhafte Verwendung
if __name__ == '__main__':
    # Dataset laden (Pfad anpassen)
    script_dir = Path(__file__).resolve().parent
    ds = xr.open_dataset(script_dir.parent / "data" / "CHRUN" / "chrun.nc")
    # Dashboard erstellen
    dashboard = build_dashboard(ds)
    # Dashboard anzeigen (z.B. als Bokeh-Server-App oder in Jupyter)
    dashboard.show()
