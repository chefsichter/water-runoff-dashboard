import geopandas as gpd
import pandas as pd
import xarray as xr
from pathlib import Path

def load_data(shp_path, nc_path, shap_ds_path):
    """
    Lädt die Shapefile- und NetCDF-Daten und gibt (gdf, ds) zurück.
    - gdf: GeoDataFrame mit den Catchment-Polygonen
    - ds: xarray Dataset mit den Variablen
    """
    # Shapefile laden
    gdf = gpd.read_file(shp_path)

    # NetCDF laden
    ds = xr.open_dataset(nc_path)
    shap_ds = xr.open_dataset(shap_ds_path)

    # Neu: Reprojektion von EPSG:21781 zu EPSG:4326
    if gdf.crs is not None and gdf.crs.to_string() == "EPSG:21781":
        gdf = gdf.to_crs(epsg=4326)

    return gdf, ds, shap_ds

def get_time_bounds(ds):
    """
    Ermittelt das erste und letzte Datum im Datensatz ds (Annahme: ds.time existiert).
    Gibt (time_min, time_max) als numpy.datetime64 oder pd.Timestamp zurück.
    """
    time_min = ds.time.values[0]
    time_max = ds.time.values[-1]
    return pd.to_datetime(time_min), pd.to_datetime(time_max)

def get_variable_lists(ds):
    """
    Gibt drei Listen zurück:
    - all_vars: alle Variablen im Dataset
    - time_vars: Variablen mit Dimension 'time'
    - static_vars: Variablen ohne Dimension 'time'
    """
    all_vars = list(ds.data_vars.keys())
    time_vars = [v for v in all_vars if 'time' in ds[v].dims]
    static_vars = [v for v in all_vars if 'time' not in ds[v].dims]
    # Dictionary mit Variablen-Metadaten erzeugen
    var_metadata = {}
    for var_name, var in ds.variables.items():
        var_metadata[var_name] = {
            "name": var_name,
            "long_name": var.attrs.get("long_name", "N/A"),
            "units": var.attrs.get("units", "N/A"),
            "dims": ", ".join(var.dims),
            "dtype": str(var.dtype),
            "source": var.attrs.get("source", "N/A"),
            "history": var.attrs.get("history", "N/A")
        }

    return all_vars, time_vars, static_vars, var_metadata

def get_var_colormaps():
    """
    Gibt ein Dictionary zurück, das Variablennamen auf Colormaps mappt.
    """
    return {
        'P': 'Blues',            # z.B. Niederschlag
        'Qmm_mod': 'Blues',      # Runoff
        'Qmm_prevah': 'Blues',   # Runoff
        'T': 'RdBu_r',           # Temperatur
        'abb': 'YlGnBu',
        'area': 'Greys',
        'atb': 'PuBu',
        'btk': 'YlGnBu',
        'dhm': 'viridis',
        'glm': 'PuBuGn',
        'kwt': 'PuBu',
        'pfc': 'YlGnBu',
        'frac_water': 'Blues',
        'frac_urban_areas': 'Greys',
        'frac_coniferous_forests': 'YlGn',
        'frac_deciduous_forests': 'YlGn',
        'frac_mixed_forests': 'YlGn',
        'frac_cereals': 'YlOrBr',
        'frac_pasture': 'YlGn',
        'frac_bush': 'YlOrBr',
        'frac_unknown': 'viridis',
        'frac_firn': 'viridis',
        'frac_bare_ice': 'Greys',
        'frac_rock': 'Greys',
        'frac_vegetables': 'YlOrBr',
        'frac_alpine_vegetation': 'viridis',
        'frac_wetlands': 'BuGn',
        'frac_sub_Alpine_meadow': 'YlGn',
        'frac_alpine_meadow': 'YlGn',
        'frac_bare_soil_vegetation': 'YlGnBu',
        'frac_grapes': 'YlOrBr',
        'slp': 'viridis',
        'hru': 'viridis',
        'time': 'viridis',
        '*default*': 'Viridis'
    }

if __name__ == "__main__":
    script_dir = Path(__file__).resolve().parent
    netcdf_path = script_dir.parent / "data" / "CHRUN" / "chrun.nc"
    shapefile_path = script_dir.parent / "data" / "CHRUN" / "catchments" / 'catchments.shp'
    gdf, ds = load_data(shapefile_path, netcdf_path)
    variable_list = get_variable_lists(ds)
    time_bounds = get_time_bounds(ds)
    # print(variable_list)
    # print(time_bounds)
    print(gdf.crs)
