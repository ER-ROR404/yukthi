"""Test Batch vs Streaming Replay Consistency.

Proves that processing records one-at-a-time via ChillerStateStore produces
identical engineered features and predictions as the full batch pipeline.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from catboost import CatBoostRegressor

from src.constants import FEATURE_COLS, COL_EQUIPMENT_ID, COL_TIMESTAMP
from src.data_loader import load_and_validate
from src.preprocessing import preprocess
from src.features import engineer_features
from src.predict import predict_expected_energy
from src.state_store import ChillerStateStore


@pytest.fixture
def sample_data():
    df = load_and_validate(Path("data/raw/chiller_data.csv"))
    # Take first 50 chronological observations for CHILLER-01
    sample = df[df[COL_EQUIPMENT_ID] == "CHILLER-01"].head(50).copy()
    preprocessed, _ = preprocess(sample)
    return preprocessed


def test_batch_vs_streaming_consistency(sample_data):
    """Verify batch features and streaming features match within floating-point tolerance."""
    # 1. Batch calculation
    batch_df = engineer_features(sample_data)
    
    # Load trained model if available
    model_path = Path("models/catboost_expected_energy.cbm")
    model = CatBoostRegressor()
    if model_path.exists():
        model.load_model(str(model_path))
        batch_df = predict_expected_energy(model, batch_df, FEATURE_COLS)
    else:
        model = None

    # 2. Streaming calculation with ChillerStateStore
    store = ChillerStateStore(model=model)
    streaming_records = []
    for _, row in sample_data.iterrows():
        record = row.to_dict()
        res = store.process_record(record)
        streaming_records.append(res)
        
    stream_df = pd.DataFrame(streaming_records)

    # 3. Compare key features between batch and stream
    compare_cols = [
        "hour_of_day",
        "is_weekend",
        "wet_bulb_temp_c",
        "load_flow_ratio",
        "out_of_envelope",
        "load_lag_30m",
        "load_rolling_2h_mean",
    ]

    for col in compare_cols:
        batch_vals = batch_df[col].values
        stream_vals = stream_df[col].values
        # Handle NaNs
        np.testing.assert_allclose(
            np.nan_to_num(batch_vals, nan=-999.0),
            np.nan_to_num(stream_vals, nan=-999.0),
            rtol=1e-4,
            atol=1e-4,
            err_msg=f"Discrepancy found in feature: {col}",
        )

    # 4. If model is available, compare predicted expected energy
    if model is not None and "expected_energy" in batch_df.columns:
        np.testing.assert_allclose(
            batch_df["expected_energy"].values,
            stream_df["expected_energy"].values,
            rtol=1e-4,
            atol=1e-4,
            err_msg="Discrepancy found in expected_energy predictions!",
        )
