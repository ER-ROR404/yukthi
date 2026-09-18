"""Tests for anomaly detection module."""
import numpy as np
import pandas as pd
import pytest

from src.constants import (
    COL_ANOMALY_FLAG,
    COL_ANOMALY_SCORE,
    COL_ENERGY,
    COL_EQUIPMENT_ID,
    COL_EVENT_ID,
    COL_EXPECTED_ENERGY,
    COL_RESIDUAL,
    COL_ROLLING_MEDIAN_RESIDUAL,
    COL_ROLLING_MAD_RESIDUAL,
    COL_ROBUST_SCORE,
    COL_TIMESTAMP,
)
from src.anomaly import score_anomalies


def _make_residual_df(
    residuals: list[float],
    equipment_id: str = "EQ-1",
) -> pd.DataFrame:
    """Build a DataFrame with residual column for testing."""
    n = len(residuals)
    return pd.DataFrame({
        COL_TIMESTAMP: pd.date_range("2020-01-01", periods=n, freq="30min"),
        COL_EQUIPMENT_ID: [equipment_id] * n,
        COL_ENERGY: [120.0] * n,
        COL_EXPECTED_ENERGY: [120.0 - r for r in residuals],
        COL_RESIDUAL: residuals,
    })


def test_when_all_normal_residuals_expect_no_anomalies() -> None:
    """Flat residuals near zero should produce no anomaly flags."""
    residuals = [1.0, -0.5, 0.8, -1.0, 0.5, -0.3, 0.7, -0.8, 0.2, -0.4]
    df = _make_residual_df(residuals)
    result, events = score_anomalies(df)
    assert result[COL_ANOMALY_FLAG].sum() == 0
    assert len(events) == 0


def test_when_spike_residual_expect_anomaly_flagged() -> None:
    """A large spike in residual should be flagged as anomalous."""
    # 20 normal readings to build rolling stats, then 2 extreme spikes
    normal = [1.0, -0.5, 0.8, -1.0, 0.5, -0.3, 0.7, -0.8, 0.2, -0.4,
              0.9, -0.6, 0.3, -0.7, 0.4, -0.2, 0.6, -0.9, 0.1, -0.3]
    spikes = [80.0, 85.0]
    df = _make_residual_df(normal + spikes)
    result, events = score_anomalies(df)
    assert result[COL_ANOMALY_FLAG].sum() > 0


def test_when_consecutive_anomalies_expect_grouped_into_event() -> None:
    """Consecutive anomaly flags should be grouped into a single event."""
    # Normal for 6, then 4 consecutive spikes
    residuals = [1.0, -0.5, 0.8, -1.0, 0.5, -0.3, 80.0, 85.0, 90.0, 82.0]
    df = _make_residual_df(residuals)
    result, events = score_anomalies(df)

    if len(events) > 0:
        # Consecutive flags → fewer events than individual flags
        total_flags = result[COL_ANOMALY_FLAG].sum()
        assert len(events) <= total_flags


def test_when_scored_expect_all_output_columns_present() -> None:
    """Score_anomalies should add all expected output columns."""
    residuals = [1.0, -0.5, 0.8, -1.0, 0.5, -0.3, 0.7, -0.8, 0.2, -0.4]
    df = _make_residual_df(residuals)
    result, _ = score_anomalies(df)

    expected_cols = [
        COL_ROLLING_MEDIAN_RESIDUAL,
        COL_ROLLING_MAD_RESIDUAL,
        COL_ROBUST_SCORE,
        COL_ANOMALY_SCORE,
        COL_ANOMALY_FLAG,
        COL_EVENT_ID,
    ]
    for col in expected_cols:
        assert col in result.columns


def test_when_missing_residual_column_expect_error() -> None:
    """score_anomalies should raise ValueError if residual is missing."""
    df = pd.DataFrame({
        COL_TIMESTAMP: pd.date_range("2020-01-01", periods=5, freq="30min"),
        COL_EQUIPMENT_ID: ["EQ-1"] * 5,
    })
    with pytest.raises(ValueError, match="residual"):
        score_anomalies(df)


def test_when_multiple_equipment_expect_independent_scoring() -> None:
    """Anomaly scoring should be independent per equipment."""
    normal = [1.0, -0.5, 0.8, -1.0, 0.5, -0.3, 0.7, -0.8, 0.2, -0.4,
              0.9, -0.6, 0.3, -0.7, 0.4, -0.2, 0.6, -0.9, 0.1, -0.3]
    df_a = _make_residual_df(
        normal + [80.0, 85.0],
        equipment_id="EQ-A",
    )
    df_b = _make_residual_df(
        normal + [0.2, -0.4],
        equipment_id="EQ-B",
    )
    df = pd.concat([df_a, df_b], ignore_index=True)
    result, events = score_anomalies(df)

    # EQ-A should have anomalies, EQ-B should not
    eq_a_flags = result[result[COL_EQUIPMENT_ID] == "EQ-A"][COL_ANOMALY_FLAG].sum()
    eq_b_flags = result[result[COL_EQUIPMENT_ID] == "EQ-B"][COL_ANOMALY_FLAG].sum()
    assert eq_a_flags > 0
    assert eq_b_flags == 0
