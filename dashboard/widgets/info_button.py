import panel as pn

def create_info_button():
    return pn.widgets.Button(
        name="ℹ️", width=33, height=33, sizing_mode='fixed',
        align='end',
        margin=(5, 0)
    )
