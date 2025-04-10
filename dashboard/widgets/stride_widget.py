import panel as pn

def create_stride_widget(initial_day_stride):
    return pn.widgets.IntInput(
        name='↔️ Tage',
        value=initial_day_stride,
        width=80,
        margin=(5, 0)
    )
