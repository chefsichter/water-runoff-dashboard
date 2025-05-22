import panel as pn

from dashboard.widgets.play_button import CSS_TOP_MARGIN


def create_speed_input_widget(initial_speed: object) -> object:
    return pn.widgets.IntInput(
        name="🏁 Speed (ms)",
        value=int(initial_speed),
        step=200,
        width=100,
        # margin=(5, 0)
    )

def create_speed_minus_widget():
    btn = pn.widgets.Button(name='-', button_type='warning', width=40)
    btn.styles = {"margin-top": f"{CSS_TOP_MARGIN}px"}
    return btn

def create_speed_plus_widget():
    btn = pn.widgets.Button(name='+', button_type='success', width=40)
    btn.styles = {"margin-top": f"{CSS_TOP_MARGIN}px"}
    return btn

def decrease_speed(speed_input, play_speed_bounds):
    new_speed = max(speed_input.value - 50, play_speed_bounds[0])
    speed_input.value = new_speed

def increase_speed(speed_input, play_speed_bounds):
    new_speed = min(speed_input.value + 50, play_speed_bounds[1])
    speed_input.value = new_speed
