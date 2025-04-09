# sidebar.py
import panel as pn


def create_sidebar(all_vars, var_metadata, initial_variable, initial_day_stride, initial_date_range, full_date_range):
    # Erzeugen Sie ein Dictionary: Schlüssel = (falls vorhanden) long_name, Wert = Variablenname
    var_options = {
        var_metadata.get(var, {}).get("long_name", var): var
        for var in all_vars
    }
    # Auswahl des Werts und Info-Button
    var_widget = pn.widgets.Select(
        name='📊 Variable',
        options=var_options,
        value=initial_variable,
        margin=(5, 0),
        sizing_mode='stretch_width'
    )
    info_button = pn.widgets.Button(
        name="ℹ️", width=33, height=33, sizing_mode='fixed',
        align='end',
        margin=(5, 0)
    )
    # Kombination in einer Zeile
    var_selector = pn.Row(pn.Spacer(width=10),
                          var_widget,
                          pn.Spacer(width=10),
                          info_button,
                          pn.Spacer(width=10))

    # Neuer Jahrbereichs-Slider, der ausschließlich ganze Jahre anzeigt.
    min_year = full_date_range[0].year
    max_year = full_date_range[1].year
    year_range_slider = pn.widgets.IntRangeSlider(
        name="🧱 Jahresbereich",
        start=min_year,
        end=max_year,
        value=(min_year, max_year),
        step=1,
        sizing_mode='stretch_width'
    )

    # Widget für day_stride
    stride_widget = pn.widgets.IntInput(
        name='↔️ Tage',
        value=initial_day_stride,
        width=80,
        margin = (5, 0)
    )

    # Zwei zusätzliche Widgets für den Date Range (Start- und Enddatum)
    start_date_picker = pn.widgets.DatePicker(
        name="📅 Startdatum",
        value=initial_date_range[0],
        sizing_mode='stretch_width',
        margin = (5, 0)
    )
    end_date_picker = pn.widgets.DatePicker(
        name="⌛ Enddatum",
        value=initial_date_range[1],
        sizing_mode='stretch_width',
        margin=(5, 0)
    )
    date_range_row = pn.Row(pn.Spacer(width=10),
                            start_date_picker,
                            pn.Spacer(width=10),
                            end_date_picker,
                            pn.Spacer(width=10),
                            stride_widget,
                            pn.Spacer(width=10),
                            sizing_mode='stretch_width')

    sidebar = pn.Column(var_selector, year_range_slider, date_range_row, sizing_mode="stretch_width")

    # Rückgabe eines Columns
    return info_button, var_widget, stride_widget, start_date_picker, end_date_picker, year_range_slider, sidebar
