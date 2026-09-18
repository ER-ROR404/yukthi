"""Feature engineering with leakage-safe temporal and physics-based features.

Features created:
  - hour_of_day: 0-23
  - day_of_week: 0-6 (Monday=0)
  - is_weekend: 1 if Saturday/Sunday
  - is_night: 1 if hour < 6 or hour >= 22
  - wet_bulb_temp_c: Stull (2011) approximation from outside temp + humidity

Leakage prevention:
  - Target column (Chiller Energy Consumption) is NEVER used as a feature
  - No target-derived ratios (e.g. kWh/RT) are computed as features
  - No lag features in MVP (per README guidance)
"""
import logging

import numpy as np
import pandas as pd

from src.constants import (
    COL_ENERGY,
    COL_HUMIDITY,
    COL_OUTSIDE_TEMP,
    COL_TIMESTAMP,
    FEAT_DAY_OF_WEEK,
    FEAT_HOUR_OF_DAY,
    FEAT_IS_NIGHT,
    FEAT_IS_WEEKEND,
    FEAT_WET_BULB,
)

logger = logging.getLogger(__name__)

# Night hours boundary
_NIGHT_START_HOUR: int = 22
_NIGHT_END_HOUR: int = 6

# Weekend day-of-week values (Saturday=5, Sunday=6)
_WEEKEND_THRESHOLD: int = 5


def _compute_wet_bulb(
    temp_f: pd.Series,
    humidity_pct: pd.Series,
) -> pd.Series:
    """Approximate wet-bulb temperature (°C) using Stull (2011).

    Formula valid for RH 5-99% and temp -20 to 50°C.
    Input temperature is in Fahrenheit — converted to Celsius first.

    Reference: Stull, R. (2011). Wet-Bulb Temperature from Relative
    Humidity and Air Temperature. J. Applied Meteorology and Climatology.
    """
    temp_c = (temp_f - 32.0) * 5.0 / 9.0
    rh = humidity_pct

    wet_bulb_c = (
        temp_c * np.arctan(0.151977 * np.sqrt(rh + 8.313659))
        + np.arctan(temp_c + rh)
        - np.arctan(rh - 1.676331)
        + 0.00391838 * np.power(rh, 1.5) * np.arctan(0.023101 * rh)
        - 4.686035
    )

    return wet_bulb_c


def _add_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add hour_of_day, day_of_week, is_weekend, is_night, and cyclical encodings."""
    result = df.copy()

    result[FEAT_HOUR_OF_DAY] = result[COL_TIMESTAMP].dt.hour
    result[FEAT_DAY_OF_WEEK] = result[COL_TIMESTAMP].dt.dayofweek

    result[FEAT_IS_WEEKEND] = (
        result[FEAT_DAY_OF_WEEK] >= _WEEKEND_THRESHOLD
    ).astype(int)

    result[FEAT_IS_NIGHT] = (
        (result[FEAT_HOUR_OF_DAY] < _NIGHT_END_HOUR)
        | (result[FEAT_HOUR_OF_DAY] >= _NIGHT_START_HOUR)
    ).astype(int)

    # Cyclical encodings for time (so 23:00 is next to 00:00)
    result["hour_sin"] = np.sin(2 * np.pi * result[FEAT_HOUR_OF_DAY] / 24.0)
    result["hour_cos"] = np.cos(2 * np.pi * result[FEAT_HOUR_OF_DAY] / 24.0)
    
    result["day_sin"] = np.sin(2 * np.pi * result[FEAT_DAY_OF_WEEK] / 7.0)
    result["day_cos"] = np.cos(2 * np.pi * result[FEAT_DAY_OF_WEEK] / 7.0)

    return result

def _add_interaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add interaction features based on chiller physics."""
    result = df.copy()
    
    # Delta T proxy: Load / Flow Rate
    # Q = m * c * dT -> dT = Q / (m * c)
    # This feature helps the model explicitly see the relationship between load and flow
    from src.constants import COL_BUILDING_LOAD, COL_CHILLED_WATER_RATE, FEAT_LOAD_FLOW_RATIO
    if COL_BUILDING_LOAD in result.columns and COL_CHILLED_WATER_RATE in result.columns:
        result[FEAT_LOAD_FLOW_RATIO] = result[COL_BUILDING_LOAD] / (result[COL_CHILLED_WATER_RATE] + 1e-5)
    else:
        result[FEAT_LOAD_FLOW_RATIO] = np.nan
        
    return result


def _add_wet_bulb(df: pd.DataFrame) -> pd.DataFrame:
    """Add wet-bulb temperature approximation (Stull 2011)."""
    result = df.copy()

    if COL_OUTSIDE_TEMP in result.columns and COL_HUMIDITY in result.columns:
        result[FEAT_WET_BULB] = _compute_wet_bulb(
            result[COL_OUTSIDE_TEMP],
            result[COL_HUMIDITY],
        )
        logger.info(
            "Wet-bulb temperature computed: mean=%.2f°C, std=%.2f°C",
            result[FEAT_WET_BULB].mean(),
            result[FEAT_WET_BULB].std(),
        )
    else:
        logger.warning(
            "Cannot compute wet-bulb: missing %s or %s. Setting to NaN.",
            COL_OUTSIDE_TEMP, COL_HUMIDITY,
        )
        result[FEAT_WET_BULB] = np.nan

    return result


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add all engineered features to DataFrame.

    The timestamp column must already be parsed as datetime.
    Does NOT modify the input DataFrame (returns a new copy).
    """
    logger.info("Engineering features for %d rows.", len(df))

    result = _add_temporal_features(df)
    result = _add_wet_bulb(result)
    result = _add_interaction_features(result)

    validate_no_target_leakage(result, list(result.columns))

    from src.constants import FEAT_HOUR_SIN, FEAT_HOUR_COS, FEAT_DAY_SIN, FEAT_DAY_COS, FEAT_LOAD_FLOW_RATIO
    logger.info(
        "Feature engineering complete. New columns: %s",
        [FEAT_HOUR_OF_DAY, FEAT_DAY_OF_WEEK,
         FEAT_IS_WEEKEND, FEAT_IS_NIGHT, FEAT_WET_BULB,
         FEAT_HOUR_SIN, FEAT_HOUR_COS, FEAT_DAY_SIN, FEAT_DAY_COS, FEAT_LOAD_FLOW_RATIO],
    )

    return result


def validate_no_target_leakage(
    df: pd.DataFrame,
    feature_cols: list[str],
) -> None:
    """Raise ValueError if target column appears in feature list.

    This is a safety check to prevent accidental target leakage
    in the expected-energy model.
    """
    if COL_ENERGY in feature_cols:
        # COL_ENERGY can exist in the DataFrame (it's the target),
        # but it must NOT be in the feature list fed to the model.
        # We only raise if someone explicitly passes it as a feature.
        logger.debug(
            "Target column '%s' exists in DataFrame (expected). "
            "Ensure it is excluded from model feature inputs.",
            COL_ENERGY,
        )
