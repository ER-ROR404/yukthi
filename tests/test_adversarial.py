"""Adversarial failure-injection test suite for YUKTHI ML Pipeline.

Tests if the 4-state architecture correctly handles:
1. Stuck sensors (variance = 0)
2. Sudden sensor jumps (rate of change spikes)
3. Synthetic heatwaves (out-of-envelope)
4. Simultaneous sensor + energy anomalies
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from catboost import CatBoostRegressor

from src.data_loader import load_and_validate
from src.preprocessing import preprocess
from src.features import engineer_features
from src.predict import predict_expected_energy
from src.anomaly import score_anomalies
from src.constants import FEATURE_COLS, COL_ENERGY, COL_TIMESTAMP, COL_EQUIPMENT_ID

@pytest.fixture
def base_data():
    """Load a tiny slice of real data to corrupt."""
    df = load_and_validate(Path("data/raw/chiller_data.csv"))
    # Take 5 days of one chiller
    return df[df[COL_EQUIPMENT_ID] == 'CHILLER-01'].head(240).copy()

@pytest.fixture
def trained_model():
    model = CatBoostRegressor()
    model.load_model("models/catboost_expected_energy.cbm")
    return model

def _run_pipeline(df, model):
    df, _ = preprocess(df)
    df = engineer_features(df)
    df = predict_expected_energy(model, df, FEATURE_COLS)
    df, _ = score_anomalies(df)
    return df

def test_stuck_sensor_flag(base_data, trained_model):
    """A stuck thermometer should trigger LOW CONFIDENCE, not an energy anomaly."""
    df = base_data.copy()
    # Freeze the outside temperature for 15 readings (7.5 hours)
    df.loc[100:115, "Outside Temperature (F)"] = 75.0
    
    result = _run_pipeline(df, trained_model)
    
    # Check that row 112 (after 10 readings of being stuck) is flagged
    status = result.iloc[112]["system_status"]
    assert status in ["LOW CONFIDENCE", "DATA + ENERGY ISSUE"], f"Expected data warning, got {status}"

def test_sudden_sensor_jump(base_data, trained_model):
    """A sudden 80% flow drop should trigger LOW CONFIDENCE."""
    df = base_data.copy()
    
    df.loc[100, "Chilled Water Rate (L/sec)"] = 35.0
    df.loc[101, "Chilled Water Rate (L/sec)"] = 5.0  # Massive drop
    
    result = _run_pipeline(df, trained_model)
    
    status = result.iloc[101]["system_status"]
    assert status in ["LOW CONFIDENCE", "DATA + ENERGY ISSUE"], f"Expected data warning, got {status}"

def test_synthetic_heatwave_out_of_envelope(base_data, trained_model):
    """An unprecedented 110F heatwave should trigger OUT OF ENVELOPE / LOW CONFIDENCE."""
    df = base_data.copy()
    df.loc[100, "Outside Temperature (F)"] = 110.0
    
    result = _run_pipeline(df, trained_model)
    
    status = result.iloc[100]["system_status"]
    assert status in ["LOW CONFIDENCE", "DATA + ENERGY ISSUE"], f"Expected out of envelope warning, got {status}"

def test_genuine_energy_anomaly(base_data, trained_model):
    """If energy spikes but sensors are normal, it should be ABNORMAL ENERGY."""
    df = base_data.copy()
    
    # Use iloc to safely inject exactly 5 rows regardless of the original index
    df.iloc[200:206, df.columns.get_loc(COL_ENERGY)] += 100.0
    
    result = _run_pipeline(df, trained_model)
    
    status = result.iloc[204]["system_status"]
    assert status == "ABNORMAL ENERGY", f"Expected ABNORMAL ENERGY, got {status}"
