import datetime
import pandas as pd

# Anfangsvariablen für Dashboard
INIT_VAR = "P"
INIT_DAY_STRIDE = 7
INIT_DATE_RANGE = (datetime.date(2020, 1, 1), datetime.date(2020, 12, 31))


# Default variablen für Dashboard, werden überschrieben
TIME_MIN = pd.Timestamp("1900-01-01").date()
TIME_MAX = pd.Timestamp("2100-01-01").date()
