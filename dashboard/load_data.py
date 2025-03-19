# data_loading.py
import xarray as xr
import geopandas as gpd

def load_netcdf_dataset(file_path: str) -> xr.Dataset:
    """
    Lädt ein NetCDF-Dataset und gibt es als xarray.Dataset zurück.
    """
    return xr.open_dataset(file_path)

def load_shapefile(file_path: str) -> gpd.GeoDataFrame:
    """
    Lädt ein Shapefile und gibt es als GeoDataFrame zurück.
    """
    return gpd.read_file(file_path)
