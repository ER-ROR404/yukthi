"""Unit tests for parameter-level anomaly scoring and breakdown."""
import numpy as np
import pandas as pd
import pytest

from src.constants import (
    COL_TIMESTAMP,
    COL_EQUIPMENT_ID,
    COL_ENERGY,
    COL_EXPECTED_ENERGY,
    COL_RESIDUAL,
    COL_ROBUST_SCORE,
    COL_COOLING_WATER_TEMP,
    COL_CHILLED_WATER_RATE,
    COL_BUILDING_LOAD,
)
from src.parameter_anomaly import (
    MEASURED_PARAMETERS,
    compute_all_parameter_anomalies,
    extract_parameter_breakdown_for_row,
    generate_parameter_anomaly_table,
)


@pytest.fixture
def synthetic_chiller_df():
    """Create synthetic multi-equipment dataset with injected parameter anomalies."""
    n = 100
    dates = pd.date_range("2020-01-01 00:00:00", periods=n, freq="30min")

    dfs = []
    for eq in ["CHILLER-01", "CHILLER-02"]:
        energy = 120.0 + np.random.normal(0, 2, n)
        expected = np.full(n, 120.0)
        residual = energy - expected
        df = pd.DataFrame({
            COL_TIMESTAMP: dates,
            COL_EQUIPMENT_ID: eq,
            COL_ENERGY: energy,
            COL_EXPECTED_ENERGY: expected,
            COL_RESIDUAL: residual,
            COL_ROBUST_SCORE: np.random.normal(0, 1, n),
            COL_COOLING_WATER_TEMP: 30.0 + np.random.normal(0, 0.5, n),
            COL_CHILLED_WATER_RATE: 85.0 + np.random.normal(0, 1, n),
            COL_BUILDING_LOAD: 450.0 + np.random.normal(0, 5, n),
        })
        # Inject energy anomaly at index 50
        df.loc[50, COL_ENERGY] = 165.0
        df.loc[50, COL_RESIDUAL] = 45.0
        df.loc[50, COL_ROBUST_SCORE] = 6.5

        # Inject cooling water temp anomaly at index 60
        df.loc[60, COL_COOLING_WATER_TEMP] = 38.0  # +8 deg deviation

        # Inject chilled water rate anomaly at index 70
        df.loc[70, COL_CHILLED_WATER_RATE] = 50.0  # -35 L/s drop

        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)


def test_compute_all_parameter_anomalies(synthetic_chiller_df):
    """Test that all parameters are given expected values, deviations, and scores."""
    result = compute_all_parameter_anomalies(synthetic_chiller_df, window_periods=20, min_periods=5)

    # Check that expected, deviation, score, and status columns exist for each parameter
    for spec in MEASURED_PARAMETERS:
        col = spec.raw_col
        if col in synthetic_chiller_df.columns:
            assert f"{col}__expected" in result.columns
            assert f"{col}__deviation" in result.columns
            assert f"{col}__score" in result.columns
            assert f"{col}__status" in result.columns

            # Deviation must equal actual - expected
            np.testing.assert_allclose(
                result[f"{col}__deviation"].values,
                (result[col] - result[f"{col}__expected"]).values,
                rtol=1e-4,
                atol=1e-4,
            )

            # Scores must be non-negative
            assert (result[f"{col}__score"] >= 0).all()

    # Verify injected anomalies receive CRITICAL status
    row_energy_anom = result[(result[COL_EQUIPMENT_ID] == "CHILLER-01") & (result[COL_ENERGY] == 165.0)].iloc[0]
    assert row_energy_anom[f"{COL_ENERGY}__status"] == "CRITICAL"
    assert row_energy_anom[f"{COL_ENERGY}__score"] > 3.0

    row_temp_anom = result[(result[COL_EQUIPMENT_ID] == "CHILLER-01") & (result[COL_COOLING_WATER_TEMP] == 38.0)].iloc[0]
    assert row_temp_anom[f"{COL_COOLING_WATER_TEMP}__status"] == "CRITICAL"
    assert row_temp_anom[f"{COL_COOLING_WATER_TEMP}__deviation"] > 5.0
    assert row_temp_anom[f"{COL_COOLING_WATER_TEMP}__score"] > 3.0


def test_extract_parameter_breakdown_for_row(synthetic_chiller_df):
    """Test extracting structured breakdown for an individual observation."""
    scored_df = compute_all_parameter_anomalies(synthetic_chiller_df, window_periods=20, min_periods=5)
    row = scored_df[(scored_df[COL_EQUIPMENT_ID] == "CHILLER-01") & (scored_df[COL_ENERGY] == 165.0)].iloc[0]

    breakdown = extract_parameter_breakdown_for_row(row)
    assert isinstance(breakdown, list)
    assert len(breakdown) > 0

    # The top parameter must be Energy Consumption because of the injected +45 kWh spike
    assert breakdown[0]["parameter"] == "Energy Consumption"
    assert breakdown[0]["status"] == "CRITICAL"
    assert breakdown[0]["actual"] == 165.0
    assert breakdown[0]["deviation"] == pytest.approx(45.0, abs=1.0)
    assert breakdown[0]["anomaly_score"] > 3.0


def test_generate_parameter_anomaly_table(synthetic_chiller_df):
    """Test generating the tabular parameter anomaly records."""
    scored_df = compute_all_parameter_anomalies(synthetic_chiller_df, window_periods=20, min_periods=5)
    table = generate_parameter_anomaly_table(scored_df, min_score=2.0)

    assert isinstance(table, list)
    assert len(table) > 0

    # Ensure required columns are present in each row
    required_keys = {"equipment_id", "timestamp", "parameter", "actual", "expected", "deviation", "unit", "anomaly_score", "status"}
    for item in table:
        assert required_keys.issubset(item.keys())
