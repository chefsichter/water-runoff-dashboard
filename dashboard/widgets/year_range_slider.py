import pandas as pd
import panel as pn

from dashboard.config.settings import YEAR_START_DATE, YEAR_END_DATE


def create_year_range_slider(min_year, max_year, start_year, end_year):
    return pn.widgets.IntRangeSlider(
        name="🧱 Jahresbereich",
        start=min_year,
        end=max_year,
        value=(start_year, end_year),
        step=1,
        sizing_mode='stretch_width',
        margin=(10,10,0,10)
    )

def set_map_bounds(event, main_view, adjust_start_for_stride=True):
    new_min_year, new_max_year = event.new
    new_time_min = pd.Timestamp(f"{new_min_year}-01-01").date()
    new_time_max = pd.Timestamp(f"{new_max_year}-12-31").date()

    # Aktuellen day_stride ermitteln (Annahme: day_stride = (end_date - start_date).days + 1)
    current_stride = main_view.day_stride

    # Stelle sicher, dass der aktuelle start_date innerhalb des neuen Bereichs liegt:
    if main_view.start_date < new_time_min:
        new_start = new_time_min
    elif main_view.start_date > new_time_max:
        new_start = new_time_max
    else:
        new_start = main_view.start_date

    # Berechne candidate_end als new_start + (current_stride - 1) Tage
    candidate_end = new_start + pd.Timedelta(days=current_stride - 1)
    if candidate_end <= new_time_max:
        new_end = candidate_end
    else:
        # Wenn der berechnete candidate_end außerhalb des neuen Bereichs liegt:
        if adjust_start_for_stride:
            # Optionale Anpassung: new_start so setzen, dass day_stride erhalten bleibt,
            # d.h. new_start = new_time_max - (current_stride - 1) Tage.
            new_start_candidate = new_time_max - pd.Timedelta(days=current_stride - 1)
            # Stelle sicher, dass new_start_candidate nicht unter new_time_min fällt:
            new_start = max(new_time_min, new_start_candidate)
            new_end = new_time_max
        else:
            # Ohne Anpassung: new_end einfach auf new_time_max setzen
            new_end = new_time_max

    # Update der MainView-Parameter in einem Schritt (atomar)
    main_view.param.update(
        time_min=new_time_min,
        time_max=new_time_max,
        start_date=new_start,
        end_date=new_end
    )

    # Aktualisiere den DateRangeSlider, falls vorhanden, mit dem berechneten Intervall.
    if main_view.date_range_slider is not None:
        main_view.date_range_slider.start = new_time_min
        main_view.date_range_slider.end = new_time_max
        main_view.date_range_slider.value = (pd.Timestamp(new_start), pd.Timestamp(new_end))
