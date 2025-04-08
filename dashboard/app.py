from pathlib import Path

import panel as pn
from dashboard import CHRUNDashboard
from data_loader import (
    load_data,
    get_time_bounds,
    get_variable_lists,
    get_var_colormaps
)
import pandas as pd

def create_app():
    # Pfade anpassen
    script_dir = Path(__file__).resolve().parent
    netcdf_path = script_dir.parent / "data" / "CHRUN" / "chrun.nc"
    shapefile_path = script_dir.parent / "data" / "CHRUN" / "catchments" / 'catchments.shp'

    # Daten laden
    gdf, ds = load_data(shapefile_path, netcdf_path)
    time_min, time_max = get_time_bounds(ds)
    all_vars, time_vars, static_vars = get_variable_lists(ds)
    var_cmaps = get_var_colormaps()

    # Erzeuge ein Dictionary mit Variablenmetadaten
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

    bootstrap = pn.template.BootstrapTemplate(title="📊💧 Water Runoff Trends in Switzerland")
    # Dashboard instanziieren
    dashboard = CHRUNDashboard(
        bootstrap=bootstrap,
        script_dir=script_dir,
        ds=ds,
        gdf=gdf,
        all_vars=all_vars,
        time_vars=time_vars,
        static_vars=static_vars,
        var_metadata=var_metadata,
        var_cmaps=var_cmaps,
        variable=all_vars[0] if all_vars else None,  # default
        time_min=pd.to_datetime(time_min).date(),
        time_max=pd.to_datetime(time_max).date()
    )
    # Panel-Layout erzeugen
    bootstrap.main.append(dashboard.panel_view())

    # Optional: Du kannst auch Elemente im Sidebar oder Header hinzufügen, z. B. einen Info-Button
    # bootstrap.sidebar.append(your_sidebar_widgets)

    return bootstrap

if __name__ == "__main__":
    app = create_app()
    pn.serve(app, title="Water Runoff Trends", show=True, port=1961)
