from pathlib import Path
import panel as pn
import holoviews as hv
import pandas as pd

from dashboard.css.custom_css import load_custom_css
from dashboard.views.main_view import MainView
from dashboard.views.modal_view import show_var_infos
from dashboard.views.sidebar_view import create_sidebar, create_sidebar_widgets
from dashboard.widgets.year_range_slider import set_map_bounds

# Widget-Funktionen importieren:

hv.extension("bokeh")
from data.data_loader import load_data, get_time_bounds, get_variable_lists, get_var_colormaps


def create_app():
    # Pfade anpassen:
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

    # MainView erzeugen
    main_view = MainView(
        ds=ds,
        gdf=gdf,
        all_vars=all_vars,
        time_vars=time_vars,
        static_vars=static_vars,
        var_cmaps=var_cmaps,
        variable=all_vars[0] if all_vars else None,
        time_min=time_min.date(),
        time_max=time_max.date()
    )
    
    # Widgets für Sidebar erstellen
    (end_date_picker,
     info_button,
     start_date_picker,
     stride_widget,
     var_widget, 
     year_range_slider) = create_sidebar_widgets(time_min, time_max, all_vars, var_metadata)

    # Verknüpfungen der Widgets
    var_widget.link(main_view, value='variable', bidirectional=True)
    info_button.on_click(lambda event: show_var_infos(bootstrap, var_metadata, var_widget.value))
    year_range_slider.param.watch(lambda event: set_map_bounds(event, main_view), 'value')
    start_date_picker.link(main_view, value='start_date', bidirectional=True)
    end_date_picker.link(main_view, value='end_date', bidirectional=True)
    stride_widget.link(main_view, value='day_stride', bidirectional=True)

    # Sidebar-Layout erstellen, indem die bereits erstellten Widgets übergeben werden
    sidebar = create_sidebar(var_widget, info_button, year_range_slider, start_date_picker, end_date_picker,
                             stride_widget)

    # Füge die einzelnen Teile zusammen
    bootstrap.sidebar.append(sidebar)
    bootstrap.main.append(main_view.panel_view())

    return bootstrap


if __name__ == "__main__":
    app = create_app()
    pn.serve(app, title="Water Runoff Trends", show=True, port=1961)
