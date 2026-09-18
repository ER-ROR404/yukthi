"""CatBoost training with chronological time-series validation.

Trains a CatBoostRegressor to predict expected chiller energy consumption
from operational and environmental context. Uses TimeSeriesSplit for
leakage-free chronological validation.
"""
import logging
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor, Pool
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit

from src.constants import (
    CAT_FEATURES,
    CATBOOST_DEPTH,
    CATBOOST_EARLY_STOPPING,
    CATBOOST_ITERATIONS,
    CATBOOST_LEARNING_RATE,
    CATBOOST_RANDOM_SEED,
    COL_EQUIPMENT_ID,
    COL_TIMESTAMP,
    CV_SPLITS,
    FEATURE_COLS,
)
from src.exceptions import TrainingError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FoldMetrics:
    """Metrics for a single cross-validation fold."""

    fold: int
    mae: float
    rmse: float
    r2: float
    train_size: int
    val_size: int


@dataclass(frozen=True)
class TrainResult:
    """Complete training result with model and diagnostics."""

    model: CatBoostRegressor
    fold_metrics: tuple[FoldMetrics, ...]
    mean_mae: float
    mean_rmse: float
    mean_r2: float
    feature_importances: dict[str, float]
    best_iteration: int

    def summary(self) -> str:
        """Return human-readable training summary."""
        lines = [
            "=== Training Summary ===",
            f"CV Folds: {len(self.fold_metrics)}",
            f"Mean MAE:  {self.mean_mae:.4f} kWh",
            f"Mean RMSE: {self.mean_rmse:.4f} kWh",
            f"Mean R²:   {self.mean_r2:.4f}",
            f"Best Iteration: {self.best_iteration}",
            "",
            "Top 5 Feature Importances:",
        ]
        sorted_fi = sorted(
            self.feature_importances.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        for name, importance in sorted_fi[:5]:
            lines.append(f"  {name}: {importance:.4f}")
        return "\n".join(lines)


def _build_catboost_model(
    task_type: str = "CPU",
) -> CatBoostRegressor:
    """Create a CatBoostRegressor with project defaults."""
    return CatBoostRegressor(
        iterations=CATBOOST_ITERATIONS,
        depth=CATBOOST_DEPTH,
        learning_rate=CATBOOST_LEARNING_RATE,
        loss_function="RMSE",
        eval_metric="MAE",
        early_stopping_rounds=CATBOOST_EARLY_STOPPING,
        verbose=100,
        random_seed=CATBOOST_RANDOM_SEED,
        task_type=task_type,
    )


def _get_cat_feature_indices(feature_cols: list[str]) -> list[int]:
    """Return indices of categorical features within the feature list."""
    return [
        i for i, col in enumerate(feature_cols) if col in CAT_FEATURES
    ]


def _evaluate_fold(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    fold_idx: int,
    train_size: int,
    val_size: int,
) -> FoldMetrics:
    """Compute MAE, RMSE, R² for a single fold."""
    mae = mean_absolute_error(y_true, y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2 = r2_score(y_true, y_pred)
    return FoldMetrics(
        fold=fold_idx,
        mae=mae,
        rmse=rmse,
        r2=r2,
        train_size=train_size,
        val_size=val_size,
    )


def cross_validate(
    df: pd.DataFrame,
    feature_cols: list[str],
    target_col: str,
    n_splits: int = CV_SPLITS,
) -> list[FoldMetrics]:
    """Run chronological cross-validation and return per-fold metrics."""
    tscv = TimeSeriesSplit(n_splits=n_splits)
    cat_indices = _get_cat_feature_indices(feature_cols)
    fold_results: list[FoldMetrics] = []

    x_data = df[feature_cols]
    y_data = df[target_col]

    for fold_idx, (train_idx, val_idx) in enumerate(tscv.split(x_data)):
        logger.info(
            "Fold %d: train=%d rows, val=%d rows",
            fold_idx + 1,
            len(train_idx),
            len(val_idx),
        )

        x_train, x_val = x_data.iloc[train_idx], x_data.iloc[val_idx]
        y_train, y_val = y_data.iloc[train_idx], y_data.iloc[val_idx]

        model = _build_catboost_model()
        train_pool = Pool(x_train, y_train, cat_features=cat_indices)
        val_pool = Pool(x_val, y_val, cat_features=cat_indices)

        model.fit(train_pool, eval_set=val_pool, verbose=False)

        y_pred = model.predict(x_val)
        metrics = _evaluate_fold(
            y_val.values, y_pred, fold_idx + 1,
            len(train_idx), len(val_idx),
        )
        fold_results.append(metrics)

        logger.info(
            "Fold %d — MAE=%.4f, RMSE=%.4f, R²=%.4f",
            fold_idx + 1, metrics.mae, metrics.rmse, metrics.r2,
        )

    return fold_results


def train_model(
    df: pd.DataFrame,
    feature_cols: list[str],
    target_col: str,
    model_output_path: Path,
    task_type: str = "CPU",
) -> TrainResult:
    """Train CatBoost with chronological CV, save model, return results.

    The final model is trained on the FULL dataset after CV evaluation.
    """
    if df.empty:
        raise TrainingError("Cannot train on an empty DataFrame.")

    missing_cols = [c for c in feature_cols if c not in df.columns]
    if missing_cols:
        raise TrainingError(
            f"Missing feature columns: {missing_cols}"
        )
    if target_col not in df.columns:
        raise TrainingError(f"Missing target column: {target_col}")

    logger.info(
        "Starting training: %d rows, %d features, target=%s",
        len(df), len(feature_cols), target_col,
    )

    # Phase 1: Cross-validation
    fold_metrics = cross_validate(df, feature_cols, target_col)
    fold_metrics_tuple = tuple(fold_metrics)

    mean_mae = float(np.mean([fm.mae for fm in fold_metrics]))
    mean_rmse = float(np.mean([fm.rmse for fm in fold_metrics]))
    mean_r2 = float(np.mean([fm.r2 for fm in fold_metrics]))

    logger.info(
        "CV Summary — Mean MAE=%.4f, RMSE=%.4f, R²=%.4f",
        mean_mae, mean_rmse, mean_r2,
    )

    # Phase 2: Final model on full data
    cat_indices = _get_cat_feature_indices(feature_cols)
    final_model = _build_catboost_model(task_type=task_type)

    x_full = df[feature_cols]
    y_full = df[target_col]
    full_pool = Pool(x_full, y_full, cat_features=cat_indices)

    final_model.fit(full_pool, verbose=100)

    best_iteration = final_model.get_best_iteration() or CATBOOST_ITERATIONS

    # Feature importances
    importance_values = final_model.get_feature_importance()
    feature_importances = dict(zip(feature_cols, importance_values.tolist()))

    # Save model
    model_output_path.parent.mkdir(parents=True, exist_ok=True)
    final_model.save_model(str(model_output_path))
    logger.info("Model saved to %s", model_output_path)

    result = TrainResult(
        model=final_model,
        fold_metrics=fold_metrics_tuple,
        mean_mae=mean_mae,
        mean_rmse=mean_rmse,
        mean_r2=mean_r2,
        feature_importances=feature_importances,
        best_iteration=best_iteration,
    )

    logger.info(result.summary())
    return result
