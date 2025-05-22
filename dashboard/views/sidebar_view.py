# sidebar.py
import panel as pn
from dashboard.widgets.play_button import create_play_button
from dashboard.widgets.speed_widget import create_speed_input_widget, create_speed_plus_widget, \
    create_speed_minus_widget

from dashboard.config.settings import INIT_VAR, INIT_DAY_STRIDE, MIN_DAY_STRIDE, MAX_DAY_STRIDE
from dashboard.widgets.agg_selector import create_agg_selector
from dashboard.widgets.date_picker import create_date_picker
from dashboard.widgets.info_button import create_info_button
from dashboard.widgets.stride_widget import create_stride_widget
from dashboard.widgets.var_selector import create_variable_selector
from dashboard.widgets.year_range_slider import create_year_range_slider


def create_sidebar_widgets(time_min, time_max, year_start_date, year_end_date, start_date, end_date, all_vars,
                           var_metadata):
    # Variablenselektion und Info-Button
    var_selector = create_variable_selector(all_vars, var_metadata, INIT_VAR)
    info_button = create_info_button()
    # Jahresbereichs-Slider (Benötigt den vollständigen Zeitraum)
    year_range_slider = create_year_range_slider(time_min.year, time_max.year, year_start_date.year, year_end_date.year)
    # Widget für die Anzahl der Tage (Stride) und DatePicker
    stride_widget = create_stride_widget(INIT_DAY_STRIDE, MIN_DAY_STRIDE, MAX_DAY_STRIDE)
    # Date pickers for start and end dates
    start_date_picker = create_date_picker("📅 Start date", start_date)
    end_date_picker   = create_date_picker("⌛ End date",   end_date)
    start_date_picker.end = end_date
    end_date_picker.start = start_date
    # aggregation selector
    agg_selector = create_agg_selector()
    # Play/Pause and Speed Controls
    play_button = create_play_button()
    speed_minus = create_speed_minus_widget()
    speed_plus = create_speed_plus_widget()
    speed_input = create_speed_input_widget(300)
    return (
        end_date_picker,
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
    )


def create_sidebar(
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
):
    # Kombiniere Variablenselektion und Info-Button in einer Zeile
    var_info_btn_row = pn.Row(
        pn.Spacer(width=10),
        var_selector,
        pn.Spacer(width=10),
        info_button,
        pn.Spacer(width=10),
        margin = (0,0,0,0)
    )
    map_section = pn.Column(
        pn.pane.Markdown("### 🧭 Map Settings",
                         margin=(0, 10)),
        var_info_btn_row,
        year_range_slider)

    # Zeile mit DatePicker und Stride
    aggregation_row = pn.Row(
        pn.Spacer(width=10),
        start_date_picker,
        pn.Spacer(width=10),
        end_date_picker,
        pn.Spacer(width=10),
        stride_widget,
        pn.Spacer(width=10),
        sizing_mode='stretch_width'
    )

    # Abschnitt "Karteneinstellungen"
    # Abschnitt Aggregationseinstellungen inklusive Funktionenauswahl
    aggregation_section = pn.Column(
        pn.pane.Markdown("### ∑ Aggregation Settings", margin=(15, 10, 0, 10)),
        aggregation_row,
        pn.Row(
            agg_selector,
            sizing_mode='stretch_width'
        )
    )

    # Gesamtes Sidebar‑Layout
    # Play/Pause- und Speed-Steuerung
    player_section = pn.Column(
        pn.pane.Markdown("### ▶️ Play Settings", margin=(15, 10, 0, 10)),
        pn.Row(
            play_button,
            speed_minus,
            speed_input,
            speed_plus,
            sizing_mode="stretch_width"
        ),
        sizing_mode="stretch_width"
    )
    # Gesamtes Sidebar-Layout
    sidebar = pn.Column(
        map_section,
        aggregation_section,
        player_section,
        sizing_mode="stretch_width"
    )
    return sidebar