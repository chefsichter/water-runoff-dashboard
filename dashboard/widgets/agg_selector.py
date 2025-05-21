import panel as pn


# Select-Widget für Aggregationsfunktion (Summe, Mittelwert, Max, Min)
def create_agg_selector():
    return pn.widgets.Select(
        name='🔢 Aggregationsfunktion',
        options=['sum', 'mean', 'max', 'min'],
        value='sum',
        sizing_mode='stretch_width'
    )