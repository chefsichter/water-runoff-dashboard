import panel as pn
CSS_TOP_MARGIN = 34

def create_play_button():
    btn = pn.widgets.Button(name="Play", button_type="primary", width=60)
    btn.styles = {"margin-top": f"{CSS_TOP_MARGIN}px"}
    return btn