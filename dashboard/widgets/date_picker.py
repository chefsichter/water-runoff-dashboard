import panel as pn

def create_date_picker(name, initial_date):
    return pn.widgets.DatePicker(
        name=name,
        value=initial_date,
        sizing_mode='stretch_width',
        margin=(5, 0)
    )
