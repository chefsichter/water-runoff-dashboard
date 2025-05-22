import datetime
import pandas as pd

# Anfangsvariablen für Dashboard
INIT_VAR = "P"

# Date Range Widget
START_DATE = datetime.date(2020, 1, 1)
END_DATE = datetime.date(2020, 1, 30)
INIT_DAY_STRIDE = (END_DATE - START_DATE).days + 1
MIN_DAY_STRIDE = 1
MAX_DAY_STRIDE = 25000

# Year Range Widget
YEAR_START_DATE = datetime.date(2020, 1, 1)
YEAR_END_DATE = datetime.date(2023, 12, 31)

# Default variablen für Dashboard, werden überschrieben
TIME_MIN = pd.Timestamp("1900-01-01").date()
TIME_MAX = pd.Timestamp("2100-01-01").date()

# Speed
INIT_SPEED_MS = 4000

# Aggregation
INIT_AGG_METHOD = 'mean'