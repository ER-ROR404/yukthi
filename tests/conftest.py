"""Shared pytest fixtures for the chiller intelligence test suite."""
import numpy as np
import pandas as pd
import pytest
from pathlib import Path

from src.constants import (
    COL_BUILDING_LOAD,
    COL_CHILLED_WATER_RATE,
    COL_COOLING_WATER_TEMP,
    COL_DEW_POINT,
    COL_ENERGY,
    COL_EQUIPMENT_ID,
    COL_HUMIDITY,
    COL_OUTSIDE_TEMP,
    COL_PRESSURE,
    COL_TIMESTAMP,
    COL_WIND_SPEED,
)


def _build_timestamps(
    start: str, periods: int, freq: str = "30min",
) -> pd.DatetimeIndex:
    """Generate a DatetimeIndex for test data."""
    return pd.date_range(start=start, periods=periods, freq=freq)


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Create a small valid DataFrame matching the chiller data schema.

    20 rows: 10 for CHILLER-TEST-A, 10 for CHILLER-TEST-B.
    30-minute intervals. A few NaN values in non-target columns.
    """
    rng = np.random.default_rng(42)

    timestamps_a = _build_timestamps("2020-01-01 00:00:00", 10)
    timestamps_b = _build_timestamps("2020-01-01 00:00:00", 10)

    n_per_equip = 10

    data_a = {
        COL_TIMESTAMP: timestamps_a,
        COL_EQUIPMENT_ID: ["CHILLER-TEST-A"] * n_per_equip,
        COL_CHILLED_WATER_RATE: rng.uniform(80, 110, n_per_equip),
        COL_COOLING_WATER_TEMP: rng.uniform(29, 34, n_per_equip),
        COL_BUILDING_LOAD: rng.uniform(400, 600, n_per_equip),
        COL_ENERGY: rng.uniform(100, 180, n_per_equip),
        COL_OUTSIDE_TEMP: rng.uniform(78, 90, n_per_equip),
        COL_DEW_POINT: rng.uniform(70, 78, n_per_equip),
        COL_HUMIDITY: rng.uniform(65, 90, n_per_equip),
        COL_WIND_SPEED: rng.uniform(2, 12, n_per_equip),
        COL_PRESSURE: rng.uniform(29.7, 29.9, n_per_equip),
    }
    data_b = {
        COL_TIMESTAMP: timestamps_b,
        COL_EQUIPMENT_ID: ["CHILLER-TEST-B"] * n_per_equip,
        COL_CHILLED_WATER_RATE: rng.uniform(80, 110, n_per_equip),
        COL_COOLING_WATER_TEMP: rng.uniform(29, 34, n_per_equip),
        COL_BUILDING_LOAD: rng.uniform(400, 600, n_per_equip),
        COL_ENERGY: rng.uniform(100, 180, n_per_equip),
        COL_OUTSIDE_TEMP: rng.uniform(78, 90, n_per_equip),
        COL_DEW_POINT: rng.uniform(70, 78, n_per_equip),
        COL_HUMIDITY: rng.uniform(65, 90, n_per_equip),
        COL_WIND_SPEED: rng.uniform(2, 12, n_per_equip),
        COL_PRESSURE: rng.uniform(29.7, 29.9, n_per_equip),
    }

    df_a = pd.DataFrame(data_a)
    df_b = pd.DataFrame(data_b)

    # Scatter a few NaN values (NOT in target)
    df_a.loc[2, COL_CHILLED_WATER_RATE] = np.nan
    df_a.loc[7, COL_HUMIDITY] = np.nan
    df_b.loc[4, COL_WIND_SPEED] = np.nan

    df = pd.concat([df_a, df_b], ignore_index=True)
    return df


@pytest.fixture
def sample_csv(tmp_path: Path, sample_df: pd.DataFrame) -> Path:
    """Write sample_df to a CSV file and return the path."""
    csv_path = tmp_path / "test_chiller_data.csv"
    sample_df.to_csv(csv_path, index=False)
    return csv_path


@pytest.fixture
def preprocessed_df(sample_df: pd.DataFrame) -> pd.DataFrame:
    """Return sample_df with timestamps parsed and sorted."""
    df = sample_df.copy()
    df[COL_TIMESTAMP] = pd.to_datetime(df[COL_TIMESTAMP])
    df = df.sort_values(
        [COL_EQUIPMENT_ID, COL_TIMESTAMP],
    ).reset_index(drop=True)
    return df
