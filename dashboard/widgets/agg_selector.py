import panel as pn

from dashboard.config.settings import INIT_AGG_METHOD


# Select-Widget für Aggregationsfunktion (Summe, Mittelwert, Max, Min)
def create_agg_selector():
    return pn.widgets.Select(
        name='🔢 Aggregation function',
        options=['sum', 'mean', 'max', 'min'],
        value=INIT_AGG_METHOD,
        sizing_mode='stretch_width'
    )