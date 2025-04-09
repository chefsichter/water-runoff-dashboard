from pathlib import Path
import panel as pn
import holoviews as hv

from dashboard.css.custom_css import load_custom_css
from dashboard.config.settings import INIT_VAR, INIT_DAY_STRIDE, INIT_DATE_RANGE
from dashboard.views.main_view import MainView
from dashboard.views.modal_view import show_var_infos
from dashboard.views.sidebar_view import create_sidebar

hv.extension("bokeh")
import pandas as pd

from data.data_loader import load_data, get_time_bounds, get_variable_lists, get_var_colormaps

# Importiere die Modal‑Funktionen aus modal.py

def create_app():
    # Pfade anpassen
    script_dir = Path(__file__).resolve().parent
    netcdf_path = script_dir.parent / "data" / "CHRUN" / "chrun.nc"
    shapefile_path = script_dir.parent / "data" / "CHRUN" / "catchments" / 'catchments.shp'

    # Custom CSS laden (falls vorhanden)
    load_custom_css(script_dir)

    # Daten laden
    gdf, ds = load_data(shapefile_path, netcdf_path)
    time_min, time_max = get_time_bounds(ds)
    all_vars, time_vars, static_vars, var_metadata = get_variable_lists(ds)
    var_cmaps = get_var_colormaps()

    # Bootstrap-Template erzeugen
    bootstrap = pn.template.BootstrapTemplate(title="📊💧 Water Runoff Trends in Switzerland")

    # Dashboard instanziieren (ohne Modal‑Logik)
    main_view = MainView(
        ds=ds,
        gdf=gdf,
        all_vars=all_vars,
        time_vars=time_vars,
        static_vars=static_vars,
        var_cmaps=var_cmaps,
        variable=all_vars[0] if all_vars else None,
        time_min=pd.to_datetime(time_min).date(),
        time_max=pd.to_datetime(time_max).date()
    )

    # Sidebar initialisieren (ausgelagert in sidebar.py)
    info_button, var_widget, stride_widget, start_date_picker, end_date_picker, sidebar = create_sidebar(
        all_vars, var_metadata, INIT_VAR, INIT_DAY_STRIDE, INIT_DATE_RANGE
    )
    # Callback: Aktualisiere den Modal-Inhalt und öffne das Modal bei Klick auf den Info-Button
    def on_info_click(event):
        show_var_infos(bootstrap, var_metadata, var_widget.value)
    info_button.on_click(on_info_click)

    # Zentrale Linkings herstellen
    var_widget.link(main_view, value='variable', bidirectional=True)
    stride_widget.link(main_view, value='day_stride', bidirectional=True)
    start_date_picker.link(main_view, value='start_date', bidirectional=True)
    end_date_picker.link(main_view, value='end_date', bidirectional=True)

    # Füge die einzelnen Teile zusammen
    bootstrap.sidebar.append(sidebar)
    bootstrap.main.append(main_view.panel_view())

    return bootstrap

if __name__ == "__main__":
    app = create_app()
    pn.serve(app, title="Water Runoff Trends", show=True, port=1961)
