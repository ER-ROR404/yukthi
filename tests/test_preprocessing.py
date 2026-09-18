"""Tests for preprocessing module."""
import numpy as np
import pandas as pd
import pytest

from src.constants import (
    COL_BUILDING_LOAD,
    COL_CHILLED_WATER_RATE,
    COL_ENERGY,
    COL_EQUIPMENT_ID,
    COL_HUMIDITY,
    COL_TIMESTAMP,
    COL_WIND_SPEED,
)
from src.preprocessing import preprocess


def test_when_valid_data_expect_no_missing_in_operational_sensors(
    preprocessed_df: pd.DataFrame,
) -> None:
    """After preprocessing, operational sensors should have no NaN."""
    df, _ = preprocess(preprocessed_df)
    assert df[COL_CHILLED_WATER_RATE].isna().sum() == 0


def test_when_valid_data_expect_gap_report_returned(
    preprocessed_df: pd.DataFrame,
) -> None:
    """Preprocessing should return a GapReport object."""
    _, gap_report = preprocess(preprocessed_df)
    assert hasattr(gap_report, "gaps")
    assert hasattr(gap_report, "total_gaps_per_equipment")


def test_when_target_missing_expect_rows_dropped_not_fabricated() -> None:
    """Rows with missing target should be dropped, not filled."""
    df = pd.DataFrame({
        COL_TIMESTAMP: pd.date_range("2020-01-01", periods=5, freq="30min"),
        COL_EQUIPMENT_ID: ["EQ-1"] * 5,
        COL_CHILLED_WATER_RATE: [90.0] * 5,
        "Cooling Water Temperature (C)": [31.0] * 5,
        COL_BUILDING_LOAD: [500.0] * 5,
        COL_ENERGY: [120.0, np.nan, 130.0, np.nan, 125.0],
        "Outside Temperature (F)": [82.0] * 5,
        "Dew Point (F)": [75.0] * 5,
        COL_HUMIDITY: [79.0] * 5,
        COL_WIND_SPEED: [6.0] * 5,
        "Pressure (in)": [29.8] * 5,
    })
    result, _ = preprocess(df)
    assert result[COL_ENERGY].isna().sum() == 0
    assert len(result) == 3  # 2 rows with NaN target dropped


def test_when_temporal_gap_exists_expect_detected() -> None:
    """A 3-hour gap should be detected as a temporal gap."""
    timestamps = list(pd.date_range("2020-01-01", periods=5, freq="30min"))
    # Insert a 3-hour gap
    timestamps.append(timestamps[-1] + pd.Timedelta(hours=3))

    df = pd.DataFrame({
        COL_TIMESTAMP: timestamps,
        COL_EQUIPMENT_ID: ["EQ-1"] * 6,
        COL_CHILLED_WATER_RATE: [90.0] * 6,
        "Cooling Water Temperature (C)": [31.0] * 6,
        COL_BUILDING_LOAD: [500.0] * 6,
        COL_ENERGY: [120.0] * 6,
        "Outside Temperature (F)": [82.0] * 6,
        "Dew Point (F)": [75.0] * 6,
        COL_HUMIDITY: [79.0] * 6,
        COL_WIND_SPEED: [6.0] * 6,
        "Pressure (in)": [29.8] * 6,
    })
    _, gap_report = preprocess(df)
    assert len(gap_report.gaps) >= 1
    assert gap_report.gaps[0].duration_hours >= 2.5


def test_when_no_gaps_expect_empty_gap_report(
    preprocessed_df: pd.DataFrame,
) -> None:
    """Regular 30-min data should produce no gaps > 60min."""
    _, gap_report = preprocess(preprocessed_df)
    assert len(gap_report.gaps) == 0


def test_when_duplicates_exist_expect_removed() -> None:
    """Duplicate (equipment_id, timestamp) rows should be removed."""
    ts = pd.Timestamp("2020-01-01 00:00:00")
    df = pd.DataFrame({
        COL_TIMESTAMP: [ts, ts, ts + pd.Timedelta(minutes=30)],
        COL_EQUIPMENT_ID: ["EQ-1", "EQ-1", "EQ-1"],
        COL_CHILLED_WATER_RATE: [90.0, 91.0, 92.0],
        "Cooling Water Temperature (C)": [31.0, 31.5, 32.0],
        COL_BUILDING_LOAD: [500.0, 510.0, 520.0],
        COL_ENERGY: [120.0, 121.0, 122.0],
        "Outside Temperature (F)": [82.0, 82.0, 83.0],
        "Dew Point (F)": [75.0, 75.0, 75.0],
        COL_HUMIDITY: [79.0, 79.0, 80.0],
        COL_WIND_SPEED: [6.0, 6.0, 7.0],
        "Pressure (in)": [29.8, 29.8, 29.8],
    })
    result, _ = preprocess(df)
    assert len(result) == 2
