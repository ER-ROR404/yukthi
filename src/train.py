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
    CATBOOST_L2_LEAF_REG,
    CATBOOST_BAGGING_TEMPERATURE,
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
    accuracy: float
    train_size: int
    val_size: int


@dataclass(frozen=True)
class EquipmentMetrics:
    """Validation metrics for a specific equipment unit."""

    equipment_id: str
    mae: float
    rmse: float
    r2: float
    accuracy: float
    sample_count: int


@dataclass(frozen=True)
class TrainResult:
    """Complete training result with model and diagnostics."""

    model: CatBoostRegressor
    fold_metrics: tuple[FoldMetrics, ...]
    equipment_metrics: tuple[EquipmentMetrics, ...]
    mean_mae: float
    mean_rmse: float
    mean_r2: float
    mean_accuracy: float
    train_mae: float
    train_rmse: float
    train_r2: float
    train_accuracy: float
    feature_importances: dict[str, float]
    best_iteration: int

    def summary(self) -> str:
        """Return human-readable training summary with explicit accuracy."""
        lines = [
            "=== Training Summary ===",
            f"CV Folds: {len(self.fold_metrics)}",
            f"Training Accuracy:   {self.train_accuracy:.2f}% (100 - WAPE) | R²: {self.train_r2:.4f} | MAE: {self.train_mae:.2f} kWh",
            f"Validation Accuracy: {self.mean_accuracy:.2f}% (100 - WAPE) | R²: {self.mean_r2:.4f} | MAE: {self.mean_mae:.2f} kWh",
            f"Mean RMSE: {self.mean_rmse:.4f} kWh",
            f"Best Iteration: {self.best_iteration}",
            "",
            "Per-Fold Metrics (Chronological Validation):",
        ]
        for fm in self.fold_metrics:
            lines.append(
                f"  Fold {fm.fold}: Accuracy={fm.accuracy:.2f}%, MAE={fm.mae:.4f} kWh, RMSE={fm.rmse:.4f} kWh, R²={fm.r2:.4f} (train={fm.train_size}, val={fm.val_size})"
            )
        lines.append("")
        lines.append("Per-Equipment OOF Validation:")
        for em in self.equipment_metrics:
            lines.append(
                f"  {em.equipment_id}: Accuracy={em.accuracy:.2f}%, MAE={em.mae:.4f} kWh, RMSE={em.rmse:.4f} kWh, R²={em.r2:.4f} (n={em.sample_count})"
            )
        lines.append("")
        lines.append("Top 5 Feature Importances:")
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
        l2_leaf_reg=CATBOOST_L2_LEAF_REG,
        bagging_temperature=CATBOOST_BAGGING_TEMPERATURE,
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
    """Compute MAE, RMSE, R², Accuracy (100 - WAPE) for a single fold."""
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2 = float(r2_score(y_true, y_pred))
    sum_y = float(np.sum(y_true))
    wape = (float(np.sum(np.abs(y_true - y_pred))) / (sum_y if sum_y > 0 else 1.0)) * 100.0
    accuracy = round(max(0.0, 100.0 - wape), 2)
    return FoldMetrics(
        fold=fold_idx,
        mae=mae,
        rmse=rmse,
        r2=r2,
        accuracy=accuracy,
        train_size=train_size,
        val_size=val_size,
    )


def cross_validate(
    df: pd.DataFrame,
    feature_cols: list[str],
    target_col: str,
    n_splits: int = CV_SPLITS,
) -> tuple[list[FoldMetrics], list[EquipmentMetrics]]:
    """Run chronological cross-validation and return per-fold and per-equipment metrics."""
    tscv = TimeSeriesSplit(n_splits=n_splits)
    cat_indices = _get_cat_feature_indices(feature_cols)
    fold_results: list[FoldMetrics] = []
    oof_records: list[pd.DataFrame] = []

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

        # Collect out-of-fold predictions with equipment_id
        oof_chunk = pd.DataFrame({
            COL_EQUIPMENT_ID: x_val[COL_EQUIPMENT_ID].values,
            "actual": y_val.values,
            "predicted": y_pred,
        })
        oof_records.append(oof_chunk)

        logger.info(
            "Fold %d — Accuracy=%.2f%%, MAE=%.4f, RMSE=%.4f, R²=%.4f",
            fold_idx + 1, metrics.accuracy, metrics.mae, metrics.rmse, metrics.r2,
        )

    # Per-equipment evaluation across all out-of-fold validation sets
    all_oof = pd.concat(oof_records, ignore_index=True)
    equipment_metrics: list[EquipmentMetrics] = []
    for eq_id, group in all_oof.groupby(COL_EQUIPMENT_ID):
        eq_mae = float(mean_absolute_error(group["actual"], group["predicted"]))
        eq_rmse = float(np.sqrt(mean_squared_error(group["actual"], group["predicted"])))
        eq_r2 = float(r2_score(group["actual"], group["predicted"]))
        sum_act = float(np.sum(group["actual"]))
        eq_wape = (float(np.sum(np.abs(group["actual"] - group["predicted"]))) / (sum_act if sum_act > 0 else 1.0)) * 100.0
        eq_acc = round(max(0.0, 100.0 - eq_wape), 2)
        eq_res = EquipmentMetrics(
            equipment_id=str(eq_id),
            mae=eq_mae,
            rmse=eq_rmse,
            r2=eq_r2,
            accuracy=eq_acc,
            sample_count=len(group),
        )
        equipment_metrics.append(eq_res)
        logger.info(
            "Equipment %s OOF — Accuracy=%.2f%%, MAE=%.4f, RMSE=%.4f, R²=%.4f (n=%d)",
            eq_id, eq_acc, eq_mae, eq_rmse, eq_r2, len(group),
        )

    return fold_results, equipment_metrics


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
    import json
    from datetime import datetime, timezone
    from src.envelope import compute_operating_envelope

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

    # Phase 1: Cross-validation (chronological TimeSeriesSplit)
    fold_metrics, equipment_metrics = cross_validate(df, feature_cols, target_col)
    fold_metrics_tuple = tuple(fold_metrics)
    equipment_metrics_tuple = tuple(equipment_metrics)

    mean_mae = float(np.mean([fm.mae for fm in fold_metrics]))
    mean_rmse = float(np.mean([fm.rmse for fm in fold_metrics]))
    mean_r2 = float(np.mean([fm.r2 for fm in fold_metrics]))
    mean_accuracy = round(float(np.mean([fm.accuracy for fm in fold_metrics])), 2)

    logger.info(
        "CV Summary — Validation Accuracy=%.2f%%, Mean MAE=%.4f, RMSE=%.4f, R²=%.4f",
        mean_accuracy, mean_mae, mean_rmse, mean_r2,
    )

    # Save Operating Envelope computed strictly from the first 80% chronological split (train only)
    split_idx = int(len(df) * 0.8)
    train_split_df = df.iloc[:split_idx]
    envelope_path = model_output_path.parent / "operating_envelope.json"
    compute_operating_envelope(train_split_df, save_path=envelope_path)

    # Phase 2: Final model on full data
    cat_indices = _get_cat_feature_indices(feature_cols)
    final_model = _build_catboost_model(task_type=task_type)

    x_full = df[feature_cols]
    y_full = df[target_col]
    full_pool = Pool(x_full, y_full, cat_features=cat_indices)

    final_model.fit(full_pool, verbose=100)

    best_iteration = final_model.get_best_iteration() or CATBOOST_ITERATIONS

    # Training set performance on full fit
    train_preds = final_model.predict(x_full)
    train_mae = float(mean_absolute_error(y_full, train_preds))
    train_rmse = float(np.sqrt(mean_squared_error(y_full, train_preds)))
    train_r2 = float(r2_score(y_full, train_preds))
    sum_full = float(np.sum(y_full))
    train_wape = (float(np.sum(np.abs(y_full - train_preds))) / (sum_full if sum_full > 0 else 1.0)) * 100.0
    train_accuracy = round(max(0.0, 100.0 - train_wape), 2)

    # Feature importances
    importance_values = final_model.get_feature_importance()
    feature_importances = dict(zip(feature_cols, importance_values.tolist()))

    # Save model artifact
    model_output_path.parent.mkdir(parents=True, exist_ok=True)
    final_model.save_model(str(model_output_path))
    logger.info("Model saved to %s", model_output_path)

    # Save Feature Configuration
    feature_config_path = model_output_path.parent / "feature_config.json"
    with open(feature_config_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "feature_cols": feature_cols,
                "categorical_features": CAT_FEATURES,
                "target_col": target_col,
                "n_features": len(feature_cols),
            },
            f,
            indent=2,
        )
    logger.info("Saved feature configuration to %s", feature_config_path)

    # Save Model Metrics
    metrics_path = model_output_path.parent / "model_metrics.json"
    metrics_payload = {
        "training_performance": {
            "accuracy_pct": train_accuracy,
            "mae": round(train_mae, 4),
            "rmse": round(train_rmse, 4),
            "r2": round(train_r2, 4),
        },
        "canonical_cv": {
            "n_splits": len(fold_metrics),
            "mean_accuracy_pct": mean_accuracy,
            "mean_mae": round(mean_mae, 4),
            "mean_rmse": round(mean_rmse, 4),
            "mean_r2": round(mean_r2, 4),
            "per_fold": [
                {
                    "fold": fm.fold,
                    "accuracy_pct": fm.accuracy,
                    "mae": round(fm.mae, 4),
                    "rmse": round(fm.rmse, 4),
                    "r2": round(fm.r2, 4),
                    "train_size": fm.train_size,
                    "val_size": fm.val_size,
                }
                for fm in fold_metrics
            ],
        },
        "per_equipment": {
            em.equipment_id: {
                "accuracy_pct": em.accuracy,
                "mae": round(em.mae, 4),
                "rmse": round(em.rmse, 4),
                "r2": round(em.r2, 4),
                "samples": em.sample_count,
            }
            for em in equipment_metrics
        },
    }
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_payload, f, indent=2)
    logger.info("Saved model metrics to %s", metrics_path)

    # Save Model Metadata
    metadata_path = model_output_path.parent / "model_metadata.json"
    metadata_payload = {
        "model_type": "CatBoostRegressor",
        "model_version": "1.0.0",
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
        "random_seed": CATBOOST_RANDOM_SEED,
        "iterations": CATBOOST_ITERATIONS,
        "depth": CATBOOST_DEPTH,
        "learning_rate": CATBOOST_LEARNING_RATE,
        "l2_leaf_reg": CATBOOST_L2_LEAF_REG,
        "cv_splits": CV_SPLITS,
        "training_rows": len(df),
        "target_col": target_col,
        "training_accuracy_pct": train_accuracy,
        "validation_accuracy_pct": mean_accuracy,
    }
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata_payload, f, indent=2)
    logger.info("Saved model metadata to %s", metadata_path)

    result = TrainResult(
        model=final_model,
        fold_metrics=fold_metrics_tuple,
        equipment_metrics=equipment_metrics_tuple,
        mean_mae=mean_mae,
        mean_rmse=mean_rmse,
        mean_r2=mean_r2,
        mean_accuracy=mean_accuracy,
        train_mae=train_mae,
        train_rmse=train_rmse,
        train_r2=train_r2,
        train_accuracy=train_accuracy,
        feature_importances=feature_importances,
        best_iteration=best_iteration,
    )

    logger.info(result.summary())
    return result

if __name__ == "__main__":
    import argparse
    from src.data_loader import load_and_validate
    from src.preprocessing import preprocess
    from src.features import engineer_features
    from src.constants import FEATURE_COLS, COL_ENERGY
    
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    
    parser = argparse.ArgumentParser(description="Train CatBoost model.")
    parser.add_argument("--task-type", default="CPU", choices=["CPU", "GPU"])
    args = parser.parse_args()
    
    logger.info("Starting ML pipeline: Data Loader -> Preprocessing -> Feature Engineering -> Training")
    df = load_and_validate(Path("data/raw/chiller_data.csv"))
    df, _ = preprocess(df)
    df = engineer_features(df)
    
    train_model(
        df=df,
        feature_cols=FEATURE_COLS,
        target_col=COL_ENERGY,
        model_output_path=Path("models/catboost_expected_energy.cbm"),
        task_type=args.task_type
    )
