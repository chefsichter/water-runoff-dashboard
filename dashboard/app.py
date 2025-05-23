import os
import pyproj

# Umgebungsvariablen frühzeitig setzen
if "PROJ_LIB" not in os.environ:
    os.environ["PROJ_LIB"] = pyproj.datadir.get_data_dir()

# Falls nötig:
gdal_path = os.path.join(pyproj.datadir.get_data_dir(), "..", "gdal")
if os.path.exists(gdal_path):
    os.environ["GDAL_DATA"] = os.path.abspath(gdal_path)

from pathlib import Path
import panel as pn
from functools import partial

pn.extension('tabulator')
import holoviews as hv
hv.extension("bokeh")

from dashboard.widgets.speed_widget import decrease_speed, increase_speed
from dashboard.widgets.date_picker import on_start_change, on_end_change
from dashboard.config.settings import END_DATE, START_DATE, YEAR_START_DATE, YEAR_END_DATE, INIT_DAY_STRIDE
from dashboard.views.main_view import MainView
from dashboard.views.modal_view import show_var_infos
from dashboard.views.sidebar_view import create_sidebar, create_sidebar_widgets
from dashboard.widgets.year_range_slider import set_map_bounds
from dashboard.css.custom_css import load_custom_css
from dashboard.data.data_loader import load_data, get_time_bounds, get_variable_lists, get_var_colormaps

def create_app():
    # Pfade anpassen:
    script_dir = Path(__file__).resolve().parent
    netcdf_path = script_dir.parent / "data" / "CHRUN" / "chrun.nc"
    shapefile_path = script_dir.parent / "data" / "CHRUN" / "catchments" / 'catchments.shp'
    shap_ds_path = script_dir.parent / "data" / "model" / "shap_rnn.nc"

    # Custom CSS laden (falls vorhanden)
    load_custom_css()

    # Daten laden
    gdf, ds, shap_ds = load_data(shapefile_path, netcdf_path, shap_ds_path)
    time_min, time_max = get_time_bounds(ds)
    all_vars, time_vars, static_vars, var_metadata = get_variable_lists(ds)
    var_cmaps = get_var_colormaps()

    # Bootstrap-Template erzeugen
    bootstrap = pn.template.BootstrapTemplate(title="📊💧 Water Runoff Dashboard")

    # MainView erzeugen (inkl. Variable Metadata)
    main_view = MainView(
        var_metadata=var_metadata,
        ds=ds,
        shap_ds=shap_ds,
        gdf=gdf,
        all_vars=all_vars,
        time_vars=time_vars,
        static_vars=static_vars,
        var_cmaps=var_cmaps,
        variable=all_vars[0] if all_vars else None,
        start_date=START_DATE,
        end_date=END_DATE,
        time_min=YEAR_START_DATE,
        time_max=YEAR_END_DATE,
        day_stride=INIT_DAY_STRIDE,
    )

    # Widgets für Sidebar erstellen
    (end_date_picker,
     info_button,
     start_date_picker,
     stride_widget,
     var_selector,
     year_range_slider,
     agg_selector,
     play_button,
     speed_minus,
     speed_input,
     speed_plus
     ) = create_sidebar_widgets(
        time_min,
        time_max,
        YEAR_START_DATE,
        YEAR_END_DATE,
        START_DATE,
        END_DATE,
        all_vars,
        var_metadata
    )

    # Verknüpfungen der Widgets
    var_selector.link(main_view, value='variable', bidirectional=True)
    info_button.on_click(lambda event: show_var_infos(bootstrap, var_metadata, var_selector.value))
    year_range_slider.param.watch(lambda event: set_map_bounds(event, main_view), 'value')
    # Callbacks für gültige Datumsauswahl müssen VOR dem Linken registriert werden
    _on_start_change = partial(on_start_change,
                               start_date_picker=start_date_picker,
                               end_date_picker=end_date_picker)
    start_date_picker.param.watch(_on_start_change, 'value')
    _on_end_change = partial(on_end_change,
                             start_date_picker=start_date_picker,
                             end_date_picker=end_date_picker)
    end_date_picker.param.watch(_on_end_change, 'value')
    # Link date pickers to main view
    start_date_picker.link(main_view, value='start_date', bidirectional=True)
    end_date_picker.link(main_view, value='end_date', bidirectional=True)
    stride_widget.link(main_view, value='day_stride', bidirectional=True)
    agg_selector.link(main_view, value='agg_method', bidirectional=True)
    main_view.play_button = play_button
    play_button.on_click(lambda event: main_view.param.trigger('play'))
    speed_minus.on_click(lambda event: decrease_speed(speed_input, main_view.param.play_speed.bounds))
    speed_plus.on_click(lambda event: increase_speed(speed_input, main_view.param.play_speed.bounds))
    speed_input.link(main_view, value='play_speed', bidirectional=True)

    # Sidebar-Layout erstellen, indem die bereits erstellten Widgets übergeben werden
    sidebar = create_sidebar(
        var_selector,
        info_button,
        year_range_slider,
        start_date_picker,
        end_date_picker,
        stride_widget,
        agg_selector,
        play_button,
        speed_minus,
        speed_input,
        speed_plus
    )

    # Füge die einzelnen Teile zusammen
    bootstrap.sidebar.append(sidebar)
    bootstrap.main.append(main_view.panel_view())
    info_pane = pn.pane.HTML("", sizing_mode="stretch_width")
    bootstrap.modal.append(info_pane)

    return bootstrap


if __name__ == "__main__":
    # Serve the app via a factory to ensure a fresh Document per session
    pn.serve(create_app, title="Water Runoff Dashboard", show=True, port=1961)
