import panel as pn

def create_speed_widget(initial_speed):
    return pn.widgets.IntInput(
        name="Speed (ms)",
        value=int(initial_speed),
        step=200,
        width=100
    )
