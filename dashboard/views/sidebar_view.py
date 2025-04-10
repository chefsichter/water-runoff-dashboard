# sidebar.py
import panel as pn

from dashboard.config.settings import INIT_VAR, INIT_DAY_STRIDE, INIT_DATE_RANGE
from dashboard.widgets.date_picker import create_date_picker
from dashboard.widgets.info_button import create_info_button
from dashboard.widgets.stride_widget import create_stride_widget
from dashboard.widgets.variable_selector import create_variable_selector
from dashboard.widgets.year_range_slider import create_year_range_slider


def create_sidebar_widgets(time_min, time_max, all_vars, var_metadata):
    # Variablenselektion und Info-Button
    var_widget = create_variable_selector(all_vars, var_metadata, INIT_VAR)
    info_button = create_info_button()
    # Jahresbereichs-Slider (Benötigt den vollständigen Zeitraum)
    year_range_slider = create_year_range_slider(time_min.year, time_max.year)
    # Widget für die Anzahl der Tage (Stride) und DatePicker
    stride_widget = create_stride_widget(INIT_DAY_STRIDE)
    start_date_picker = create_date_picker("📅 Startdatum", INIT_DATE_RANGE[0])
    end_date_picker = create_date_picker("⌛ Enddatum", INIT_DATE_RANGE[1])
    return end_date_picker, info_button, start_date_picker, stride_widget, var_widget, year_range_slider


def create_sidebar(var_widget, info_button, year_range_slider, start_date_picker, end_date_picker, stride_widget):
    # Kombiniere Variablenselektion und Info-Button in einer Zeile
    var_selector = pn.Row(
        pn.Spacer(width=10),
        var_widget,
        pn.Spacer(width=10),
        info_button,
        pn.Spacer(width=10)
    )

    # Zeile mit DatePicker und Stride
    date_range_row = pn.Row(
        pn.Spacer(width=10),
        start_date_picker,
        pn.Spacer(width=10),
        end_date_picker,
        pn.Spacer(width=10),
        stride_widget,
        pn.Spacer(width=10),
        sizing_mode='stretch_width'
    )

    # Gesamtes Sidebar‑Layout
    sidebar = pn.Column(var_selector, year_range_slider, date_range_row, sizing_mode="stretch_width")
    return sidebar



