"""SHAP-based model explainability for expected energy predictions.

Uses CatBoost's native exact SHAP values (not approximate TreeExplainer)
for fast, accurate feature contribution analysis.

SHAP explains WHY the model predicted a given expected energy value.
It does NOT prove physical causality.
"""
import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor, Pool

from src.constants import CAT_FEATURES, COL_EQUIPMENT_ID

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FeatureContribution:
    """A single feature's SHAP contribution to a prediction."""

    feature_name: str
    shap_value: float
    feature_value: object  # can be str (equipment_id) or float

    @property
    def direction(self) -> str:
        """Human-readable direction of contribution."""
        if self.shap_value > 0:
            return "increased"
        elif self.shap_value < 0:
            return "decreased"
        return "neutral"


@dataclass(frozen=True)
class ExplanationResult:
    """Complete SHAP explanation for a single prediction."""

    contributions: tuple[FeatureContribution, ...]
    base_value: float
    predicted_value: float

    @property
    def top_contributors(self) -> tuple[FeatureContribution, ...]:
        """Return top 5 contributors sorted by absolute SHAP value."""
        sorted_contribs = sorted(
            self.contributions,
            key=lambda c: abs(c.shap_value),
            reverse=True,
        )
        return tuple(sorted_contribs[:5])


def explain_prediction(
    model: CatBoostRegressor,
    observation: pd.DataFrame,
    feature_cols: list[str],
) -> ExplanationResult:
    """Generate SHAP explanation for a single observation.

    Uses CatBoost's native SHAP (exact, fast) rather than the
    general-purpose SHAP library for performance.

    Args:
        model: Trained CatBoostRegressor
        observation: Single-row DataFrame with feature columns
        feature_cols: List of feature column names

    Returns:
        ExplanationResult with per-feature contributions
    """
    cat_indices = [
        i for i, col in enumerate(feature_cols) if col in CAT_FEATURES
    ]

    pool = Pool(
        observation[feature_cols],
        cat_features=cat_indices,
    )

    shap_matrix = model.get_feature_importance(
        data=pool,
        type="ShapValues",
    )

    # CatBoost SHAP: last column is the base value
    shap_values = shap_matrix[0][:-1]
    base_value = float(shap_matrix[0][-1])

    contributions = tuple(
        FeatureContribution(
            feature_name=col,
            shap_value=float(sv),
            feature_value=observation[col].iloc[0],
        )
        for col, sv in zip(feature_cols, shap_values)
    )

    predicted = float(model.predict(observation[feature_cols])[0])

    return ExplanationResult(
        contributions=contributions,
        base_value=base_value,
        predicted_value=predicted,
    )


def explain_batch(
    model: CatBoostRegressor,
    df: pd.DataFrame,
    feature_cols: list[str],
) -> list[ExplanationResult]:
    """Generate SHAP explanations for multiple observations."""
    cat_indices = [
        i for i, col in enumerate(feature_cols) if col in CAT_FEATURES
    ]

    pool = Pool(df[feature_cols], cat_features=cat_indices)
    shap_matrix = model.get_feature_importance(
        data=pool,
        type="ShapValues",
    )
    predictions = model.predict(df[feature_cols])

    results: list[ExplanationResult] = []
    for row_idx in range(len(df)):
        shap_values = shap_matrix[row_idx][:-1]
        base_value = float(shap_matrix[row_idx][-1])

        contributions = tuple(
            FeatureContribution(
                feature_name=col,
                shap_value=float(sv),
                feature_value=df[col].iloc[row_idx],
            )
            for col, sv in zip(feature_cols, shap_values)
        )

        results.append(
            ExplanationResult(
                contributions=contributions,
                base_value=base_value,
                predicted_value=float(predictions[row_idx]),
            )
        )

    logger.info("Generated SHAP explanations for %d observations", len(df))
    return results


def generate_narrative(explanation: ExplanationResult) -> str:
    """Convert SHAP explanation into a human-readable narrative.

    Returns a 1-2 sentence summary highlighting the top contributing
    features and their directional effects on expected energy.
    """
    top = explanation.top_contributors
    if not top:
        return "Insufficient data for explanation."

    increasing = [
        c for c in top if c.shap_value > 0.5
    ]
    decreasing = [
        c for c in top if c.shap_value < -0.5
    ]

    parts: list[str] = []

    if increasing:
        names = ", ".join(
            f"{c.feature_name} ({c.shap_value:+.1f} kWh)"
            for c in increasing[:3]
        )
        parts.append(f"Factors increasing expected energy: {names}.")

    if decreasing:
        names = ", ".join(
            f"{c.feature_name} ({c.shap_value:+.1f} kWh)"
            for c in decreasing[:3]
        )
        parts.append(f"Factors decreasing expected energy: {names}.")

    if not parts:
        return (
            "All feature contributions are within normal range "
            f"(predicted: {explanation.predicted_value:.1f} kWh)."
        )

    return " ".join(parts)
