"""Centralized constants for the chiller intelligence pipeline.

All column names, thresholds, and configuration live here.
Zero magic strings or numbers in the rest of the codebase.
"""
from typing import Final


# ---------------------------------------------------------------------------
# Column names (exact match to CSV schema)
# ---------------------------------------------------------------------------
COL_TIMESTAMP: Final[str] = "timestamp"
COL_EQUIPMENT_ID: Final[str] = "equipment_id"
COL_CHILLED_WATER_RATE: Final[str] = "Chilled Water Rate (L/sec)"
COL_COOLING_WATER_TEMP: Final[str] = "Cooling Water Temperature (C)"
COL_BUILDING_LOAD: Final[str] = "Building Load (RT)"
COL_ENERGY: Final[str] = "Chiller Energy Consumption (kWh)"
COL_OUTSIDE_TEMP: Final[str] = "Outside Temperature (F)"
COL_DEW_POINT: Final[str] = "Dew Point (F)"
COL_HUMIDITY: Final[str] = "Humidity (%)"
COL_WIND_SPEED: Final[str] = "Wind Speed (mph)"
COL_PRESSURE: Final[str] = "Pressure (in)"

# ---------------------------------------------------------------------------
# Schema: all expected CSV columns in order
# ---------------------------------------------------------------------------
EXPECTED_COLUMNS: Final[list[str]] = [
    COL_TIMESTAMP,
    COL_EQUIPMENT_ID,
    COL_CHILLED_WATER_RATE,
    COL_COOLING_WATER_TEMP,
    COL_BUILDING_LOAD,
    COL_ENERGY,
    COL_OUTSIDE_TEMP,
    COL_DEW_POINT,
    COL_HUMIDITY,
    COL_WIND_SPEED,
    COL_PRESSURE,
]

# ---------------------------------------------------------------------------
# Engineered feature names
# ---------------------------------------------------------------------------
FEAT_HOUR_OF_DAY: Final[str] = "hour_of_day"
FEAT_DAY_OF_WEEK: Final[str] = "day_of_week"
FEAT_IS_WEEKEND: Final[str] = "is_weekend"
FEAT_IS_NIGHT: Final[str] = "is_night"
FEAT_WET_BULB: Final[str] = "wet_bulb_temp_c"

# ---------------------------------------------------------------------------
# Feature columns (input to CatBoost — NO target-derived quantities)
# ---------------------------------------------------------------------------
FEATURE_COLS: Final[list[str]] = [
    COL_EQUIPMENT_ID,
    COL_CHILLED_WATER_RATE,
    COL_COOLING_WATER_TEMP,
    COL_BUILDING_LOAD,
    COL_OUTSIDE_TEMP,
    COL_DEW_POINT,
    COL_HUMIDITY,
    COL_WIND_SPEED,
    COL_PRESSURE,
    FEAT_HOUR_OF_DAY,
    FEAT_DAY_OF_WEEK,
    FEAT_IS_WEEKEND,
    FEAT_IS_NIGHT,
    FEAT_WET_BULB,
]

CAT_FEATURES: Final[list[str]] = [COL_EQUIPMENT_ID]

# ---------------------------------------------------------------------------
# Operational sensor columns (for targeted imputation)
# ---------------------------------------------------------------------------
OPERATIONAL_SENSOR_COLS: Final[list[str]] = [
    COL_CHILLED_WATER_RATE,
    COL_COOLING_WATER_TEMP,
]

WEATHER_COLS: Final[list[str]] = [
    COL_OUTSIDE_TEMP,
    COL_DEW_POINT,
    COL_HUMIDITY,
    COL_WIND_SPEED,
]

SLOWLY_CHANGING_COLS: Final[list[str]] = [
    COL_PRESSURE,
]

# ---------------------------------------------------------------------------
# Preprocessing thresholds
# ---------------------------------------------------------------------------
NOMINAL_INTERVAL_MINUTES: Final[int] = 30
GAP_THRESHOLD_MINUTES: Final[int] = 60
ROLLING_WINDOW: Final[str] = "2h"
MAX_INTERPOLATION_GAP: Final[int] = 3  # max consecutive NaNs to interpolate
FFILL_BFILL_LIMIT: Final[int] = 6  # for slowly changing vars like pressure

# ---------------------------------------------------------------------------
# Anomaly detection
# ---------------------------------------------------------------------------
MIN_ROLLING_PERIODS: Final[int] = 4
ISOLATION_FOREST_CONTAMINATION = "auto"
ISOLATION_FOREST_RANDOM_STATE: Final[int] = 42

# ---------------------------------------------------------------------------
# CatBoost training defaults
# ---------------------------------------------------------------------------
CATBOOST_ITERATIONS: Final[int] = 1000
CATBOOST_DEPTH: Final[int] = 7
CATBOOST_LEARNING_RATE: Final[float] = 0.05
CATBOOST_EARLY_STOPPING: Final[int] = 50
CATBOOST_RANDOM_SEED: Final[int] = 42
CV_SPLITS: Final[int] = 5

# ---------------------------------------------------------------------------
# Output column names
# ---------------------------------------------------------------------------
COL_EXPECTED_ENERGY: Final[str] = "expected_energy"
COL_RESIDUAL: Final[str] = "residual"
COL_ROLLING_MEDIAN_RESIDUAL: Final[str] = "rolling_median_residual"
COL_ROLLING_MAD_RESIDUAL: Final[str] = "rolling_mad_residual"
COL_ROBUST_SCORE: Final[str] = "robust_score"
COL_ANOMALY_SCORE: Final[str] = "anomaly_score"
COL_ANOMALY_FLAG: Final[str] = "anomaly_flag"
COL_EVENT_ID: Final[str] = "event_id"
COL_TIME_DIFF: Final[str] = "time_diff_minutes"
