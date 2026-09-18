"""Inference pipeline for expected energy prediction.

Applies a trained CatBoost model to compute expected energy
and the residual (actual − expected) for each observation.
"""
import logging

import pandas as pd
from catboost import CatBoostRegressor

from src.constants import (
    COL_ENERGY,
    COL_EXPECTED_ENERGY,
    COL_RESIDUAL,
)
from src.exceptions import PredictionError

logger = logging.getLogger(__name__)


def predict_expected_energy(
    model: CatBoostRegressor,
    df: pd.DataFrame,
    feature_cols: list[str],
) -> pd.DataFrame:
    """Add expected_energy and residual columns to DataFrame.

    residual = actual_energy − expected_energy

    A positive residual means the chiller consumed MORE than expected.
    A negative residual means the chiller consumed LESS than expected.

    Does NOT modify the input DataFrame.
    """
    if df.empty:
        raise PredictionError("Cannot predict on an empty DataFrame.")

    missing_cols = [c for c in feature_cols if c not in df.columns]
    if missing_cols:
        raise PredictionError(
            f"Missing feature columns for prediction: {missing_cols}"
        )

    result = df.copy()
    predictions = model.predict(result[feature_cols])
    result[COL_EXPECTED_ENERGY] = predictions

    if COL_ENERGY in result.columns:
        result[COL_RESIDUAL] = result[COL_ENERGY] - result[COL_EXPECTED_ENERGY]
        logger.info(
            "Predictions complete: %d rows, "
            "mean residual=%.2f kWh, std=%.2f kWh",
            len(result),
            result[COL_RESIDUAL].mean(),
            result[COL_RESIDUAL].std(),
        )
    else:
        logger.warning(
            "Target column '%s' not present — "
            "residual cannot be calculated until actual energy arrives.",
            COL_ENERGY,
        )

    return result


def load_model(model_path: str) -> CatBoostRegressor:
    """Load a saved CatBoost model from disk."""
    model = CatBoostRegressor()
    model.load_model(model_path)
    logger.info("Model loaded from %s", model_path)
    return model
