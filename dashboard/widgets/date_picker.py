import panel as pn

def create_date_picker(name, initial_date):
    return pn.widgets.DatePicker(
        name=name,
        value=initial_date,
        sizing_mode='stretch_width',
        margin=(5, 0)
    )

# callback for start_date changes
def on_start_change(event, start_date_picker, end_date_picker):
    new, old = event.new, event.old
    # invalid if start > current end: revert to old
    if new > end_date_picker.value:
        start_date_picker.value = old
    else:
        # valid: update minimum for end picker
        end_date_picker.start = new

# callback for end_date changes
def on_end_change(event, start_date_picker, end_date_picker):
    new, old = event.new, event.old
    # invalid if end < current start: revert to old
    if new < start_date_picker.value:
        end_date_picker.value = old
    else:
        # valid: update maximum for start picker
        start_date_picker.end = new
