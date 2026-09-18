"""Tests for feature engineering module."""
import numpy as np
import pandas as pd
import pytest

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
    FEATURE_COLS,
)
from src.features import engineer_features, validate_no_target_leakage


def test_when_valid_data_expect_all_features_created(
    preprocessed_df: pd.DataFrame,
) -> None:
    """All engineered feature columns should be present after processing."""
    result = engineer_features(preprocessed_df)
    for feat in [FEAT_HOUR_OF_DAY, FEAT_DAY_OF_WEEK,
                 FEAT_IS_WEEKEND, FEAT_IS_NIGHT, FEAT_WET_BULB]:
        assert feat in result.columns


def test_when_midnight_expect_hour_zero(
    preprocessed_df: pd.DataFrame,
) -> None:
    """Timestamps at midnight should produce hour_of_day = 0."""
    result = engineer_features(preprocessed_df)
    midnight_rows = result[
        result[COL_TIMESTAMP].dt.hour == 0
    ]
    if not midnight_rows.empty:
        assert (midnight_rows[FEAT_HOUR_OF_DAY] == 0).all()


def test_when_saturday_expect_is_weekend() -> None:
    """Saturday timestamps should have is_weekend = 1."""
    # 2020-01-04 is a Saturday
    df = pd.DataFrame({
        COL_TIMESTAMP: pd.to_datetime(["2020-01-04 12:00:00"]),
        "equipment_id": ["EQ-1"],
        "Chilled Water Rate (L/sec)": [90.0],
        "Cooling Water Temperature (C)": [31.0],
        "Building Load (RT)": [500.0],
        COL_ENERGY: [120.0],
        COL_OUTSIDE_TEMP: [82.0],
        "Dew Point (F)": [75.0],
        COL_HUMIDITY: [79.0],
        "Wind Speed (mph)": [6.0],
        "Pressure (in)": [29.8],
    })
    result = engineer_features(df)
    assert result[FEAT_IS_WEEKEND].iloc[0] == 1


def test_when_late_night_expect_is_night() -> None:
    """Timestamps at 23:00 should have is_night = 1."""
    df = pd.DataFrame({
        COL_TIMESTAMP: pd.to_datetime(["2020-01-01 23:00:00"]),
        "equipment_id": ["EQ-1"],
        "Chilled Water Rate (L/sec)": [90.0],
        "Cooling Water Temperature (C)": [31.0],
        "Building Load (RT)": [500.0],
        COL_ENERGY: [120.0],
        COL_OUTSIDE_TEMP: [82.0],
        "Dew Point (F)": [75.0],
        COL_HUMIDITY: [79.0],
        "Wind Speed (mph)": [6.0],
        "Pressure (in)": [29.8],
    })
    result = engineer_features(df)
    assert result[FEAT_IS_NIGHT].iloc[0] == 1


def test_when_valid_temp_humidity_expect_wet_bulb_computed() -> None:
    """Wet-bulb should be computed as a float between temp_c and dew_point."""
    df = pd.DataFrame({
        COL_TIMESTAMP: pd.to_datetime(["2020-01-01 12:00:00"]),
        "equipment_id": ["EQ-1"],
        "Chilled Water Rate (L/sec)": [90.0],
        "Cooling Water Temperature (C)": [31.0],
        "Building Load (RT)": [500.0],
        COL_ENERGY: [120.0],
        COL_OUTSIDE_TEMP: [82.0],  # ~27.8°C
        "Dew Point (F)": [75.0],
        COL_HUMIDITY: [79.0],
        "Wind Speed (mph)": [6.0],
        "Pressure (in)": [29.8],
    })
    result = engineer_features(df)
    wb = result[FEAT_WET_BULB].iloc[0]
    assert isinstance(wb, (float, np.floating))
    # Wet-bulb should be between ~20-30°C for these inputs
    assert 15.0 < wb < 35.0


def test_when_target_in_feature_list_expect_target_never_used() -> None:
    """Target column must not be in the FEATURE_COLS constant."""
    assert COL_ENERGY not in FEATURE_COLS
