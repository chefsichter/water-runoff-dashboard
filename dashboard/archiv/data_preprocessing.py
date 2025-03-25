# data_preprocessing.py
import geopandas as gpd
import pandas as pd
import xarray as xr

# data_preprocessing.py

def update_geodf_with_height(geodf, ds, flatten_factor=0.1):
    """
    Ergänzt das GeoDataFrame um eine Spalte 'dhm', wobei der NetCDF-Wert
    mit einem Flatten-Faktor multipliziert wird (für einen flacheren 3D-Effekt).
    """
    height_values = ds['dhm'].values * flatten_factor  # flatten_factor z. B. 0.1
    geodf_updated = geodf.copy()
    geodf_updated['dhm'] = height_values
    return geodf_updated

def update_geodf_with_variable(geodf, ds, variable: str, time_val) -> 'gpd.GeoDataFrame':
    """
    Fügt dem GeoDataFrame eine Spalte 'var_val' hinzu, die den Wert der ausgewählten Variable
    für jedes Catchment (hru) zum angegebenen Zeitpunkt enthält.
    Dabei wird time_val in einen Pandas-Timestamp umgewandelt und die Methode 'nearest' verwendet.
    """
    # Konvertiere time_val in einen Timestamp, falls es ein datetime.date ist
    time_val = pd.Timestamp(time_val)
    # Wähle den nächstliegenden Zeitpunkt im Dataset aus
    var_values = ds[variable].sel(time=time_val, method='nearest').values
    geodf_updated = geodf.copy()
    geodf_updated['var_val'] = var_values
    return geodf_updated