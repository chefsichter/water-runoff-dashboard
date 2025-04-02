import geopandas as gpd
import xarray as xr
from pathlib import Path

def load_data(shp_path, nc_path):
    """
    Lädt die Shapefile- und NetCDF-Daten und gibt (gdf, ds) zurück.
    - gdf: GeoDataFrame mit den Catchment-Polygonen
    - ds: xarray Dataset mit den Variablen
    """
    # Shapefile laden
    gdf = gpd.read_file(shp_path)

    # NetCDF laden
    ds = xr.open_dataset(nc_path)

    # Neu: Reprojektion von EPSG:21781 zu EPSG:4326
    if gdf.crs is not None and gdf.crs.to_string() == "EPSG:21781":
        gdf = gdf.to_crs(epsg=4326)

    return gdf, ds

def get_time_bounds(ds):
    """
    Ermittelt das erste und letzte Datum im Datensatz ds (Annahme: ds.time existiert).
    Gibt (time_min, time_max) als numpy.datetime64 oder pd.Timestamp zurück.
    """
    time_min = ds.time.values[0]
    time_max = ds.time.values[-1]
    return time_min, time_max

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
    return all_vars, time_vars, static_vars

def get_var_colormaps():
    """
    Gibt ein Dictionary zurück, das Variablennamen auf Colormaps mappt.
    """
    return {
        'P': 'Blues',            # z.B. Niederschlag
        'Qmm_mod': 'Blues',      # Runoff
        'Qmm_prevah': 'Blues',   # Runoff
        'T': 'Reds',             # Temperatur
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
