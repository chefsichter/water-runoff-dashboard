import panel as pn

def create_stride_widget(initial_day_stride, min_day_stride, max_day_stride):
    return pn.widgets.IntInput(
        name='↔️ Days',
        value=initial_day_stride,
        start=min_day_stride,
        end=max_day_stride,
        width=80,
        margin=(5, 0)
    )
