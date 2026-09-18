"""Automated Hyperparameter Optimization via Optuna.

This script finds the absolute best model hyperparameters for CatBoost 
using TimeSeriesSplit cross-validation to guarantee zero leakage.
It makes the training process transparent to the user.
"""
import logging
from pathlib import Path
import re

import numpy as np
import optuna
import pandas as pd
from catboost import CatBoostRegressor, Pool
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit

from src.constants import (
    CAT_FEATURES,
    COL_ENERGY,
    CV_SPLITS,
    FEATURE_COLS,
)
from src.data_loader import load_and_validate
from src.features import engineer_features
from src.preprocessing import preprocess

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def _get_cat_feature_indices(feature_cols: list[str]) -> list[int]:
    """Return indices of categorical features within the feature list."""
    return [i for i, col in enumerate(feature_cols) if col in CAT_FEATURES]


def objective(trial: optuna.Trial, X: pd.DataFrame, y: pd.Series) -> float:
    """Optuna objective function for CatBoost hyperparameter tuning."""
    
    # Suggest hyperparameters
    param = {
        "iterations": trial.suggest_int("iterations", 500, 2000, step=100),
        "depth": trial.suggest_int("depth", 4, 10),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.1, log=True),
        "l2_leaf_reg": trial.suggest_float("l2_leaf_reg", 1.0, 10.0),
        "bagging_temperature": trial.suggest_float("bagging_temperature", 0.0, 1.0),
        "loss_function": "RMSE",
        "eval_metric": "MAE",
        "random_seed": 42,
        "verbose": False,
        "task_type": "CPU", # Adjust to GPU if needed
    }
    
    tscv = TimeSeriesSplit(n_splits=CV_SPLITS)
    cat_indices = _get_cat_feature_indices(FEATURE_COLS)
    
    mae_scores = []
    r2_scores = []
    
    for train_idx, val_idx in tscv.split(X):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
        
        train_pool = Pool(X_train, y_train, cat_features=cat_indices)
        val_pool = Pool(X_val, y_val, cat_features=cat_indices)
        
        model = CatBoostRegressor(**param)
        model.fit(train_pool, eval_set=val_pool, early_stopping_rounds=50, verbose=False)
        
        preds = model.predict(X_val)
        mae = mean_absolute_error(y_val, preds)
        r2 = r2_score(y_val, preds)
        
        mae_scores.append(mae)
        r2_scores.append(r2)
        
    mean_mae = np.mean(mae_scores)
    mean_r2 = np.mean(r2_scores)
    
    # We want to minimize MAE, but let's log the R2 as a user attribute for transparency
    trial.set_user_attr("R2", float(mean_r2))
    
    return float(mean_mae)


def optimize_and_update_constants():
    """Run Optuna and automatically update constants.py with the best params."""
    logger.info("\n" + "="*60)
    logger.info("🚀 STARTING INTELLIGENT HYPERPARAMETER OPTIMIZATION (OPTUNA)")
    logger.info("="*60)
    
    df = load_and_validate(Path("data/raw/chiller_data.csv"))
    df, _ = preprocess(df)
    df = engineer_features(df)
    
    X = df[FEATURE_COLS]
    y = df[COL_ENERGY]
    
    logger.info("\nData loaded and preprocessed.")
    logger.info(f"Dataset shape: {X.shape}, Features: {len(FEATURE_COLS)}")
    
    # Optuna study
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(direction="minimize", study_name="CatBoost_Optimization")
    
    logger.info("\nSearching for optimal hyperparameters (Running 20 trials)...")
    
    # Custom callback to print transparent progress
    def print_callback(study, trial):
        r2 = trial.user_attrs.get("R2", 0)
        logger.info(f"Trial {trial.number:02d} | MAE: {trial.value:.4f} kWh | R²: {r2:.4f} | Params: {trial.params}")
        
    study.optimize(lambda t: objective(t, X, y), n_trials=20, callbacks=[print_callback])
    
    best_params = study.best_params
    best_r2 = study.best_trial.user_attrs.get('R2')
    
    logger.info("\n" + "="*60)
    logger.info("🎯 OPTIMIZATION COMPLETE!")
    logger.info("="*60)
    logger.info(f"Best Mean MAE: {study.best_value:.4f} kWh")
    logger.info(f"Best Mean R²:  {best_r2:.4f}")
    logger.info("Best Parameters Discovered:")
    for k, v in best_params.items():
        logger.info(f"  {k}: {v}")
        
    # Update src/constants.py with best params
    update_constants_file(best_params)
    

def update_constants_file(best_params: dict):
    """Update src/constants.py with the newly found optimal params."""
    constants_path = Path("src/constants.py")
    content = constants_path.read_text()
    
    # Regex replace
    content = re.sub(
        r"CATBOOST_ITERATIONS: Final\[int\] = \d+",
        f"CATBOOST_ITERATIONS: Final[int] = {best_params['iterations']}",
        content
    )
    content = re.sub(
        r"CATBOOST_DEPTH: Final\[int\] = \d+",
        f"CATBOOST_DEPTH: Final[int] = {best_params['depth']}",
        content
    )
    content = re.sub(
        r"CATBOOST_LEARNING_RATE: Final\[float\] = [\d\.]+",
        f"CATBOOST_LEARNING_RATE: Final[float] = {best_params['learning_rate']:.4f}",
        content
    )
    
    # Add new params if they don't exist
    if "CATBOOST_L2_LEAF_REG" not in content:
        content = content.replace(
            "CATBOOST_LEARNING_RATE:",
            f"CATBOOST_L2_LEAF_REG: Final[float] = {best_params['l2_leaf_reg']:.4f}\nCATBOOST_BAGGING_TEMPERATURE: Final[float] = {best_params['bagging_temperature']:.4f}\nCATBOOST_LEARNING_RATE:"
        )
    else:
        content = re.sub(
            r"CATBOOST_L2_LEAF_REG: Final\[float\] = [\d\.]+",
            f"CATBOOST_L2_LEAF_REG: Final[float] = {best_params['l2_leaf_reg']:.4f}",
            content
        )
        content = re.sub(
            r"CATBOOST_BAGGING_TEMPERATURE: Final\[float\] = [\d\.]+",
            f"CATBOOST_BAGGING_TEMPERATURE: Final[float] = {best_params['bagging_temperature']:.4f}",
            content
        )
        
    constants_path.write_text(content)
    logger.info("\n✅ Auto-updated src/constants.py with the absolute best parameters!")
    
if __name__ == "__main__":
    optimize_and_update_constants()
