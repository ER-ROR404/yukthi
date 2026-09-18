import json
import logging
from pathlib import Path
import pandas as pd
from catboost import CatBoostRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit

from src.data_loader import load_and_validate
from src.preprocessing import preprocess
from src.features import engineer_features
from src.constants import FEATURE_COLS, COL_ENERGY, FEAT_LOAD_LAG_30M, FEAT_LOAD_ROLLING_2H_MEAN

logging.basicConfig(level=logging.INFO, format="%(message)s")

def evaluate_features(df, features, name):
    logging.info(f"--- Running Ablation: {name} ({len(features)} features) ---")
    tscv = TimeSeriesSplit(n_splits=5)
    
    maes, rmses, r2s = [], [], []
    for train_index, test_index in tscv.split(df):
        train, test = df.iloc[train_index], df.iloc[test_index]
        X_train, y_train = train[features], train[COL_ENERGY]
        X_test, y_test = test[features], test[COL_ENERGY]
        
        model = CatBoostRegressor(iterations=500, depth=4, learning_rate=0.05, verbose=0, random_seed=42)
        model.fit(X_train, y_train, cat_features=["equipment_id"])
        
        preds = model.predict(X_test)
        maes.append(float(mean_absolute_error(y_test, preds)))
        rmses.append(float(root_mean_squared_error(y_test, preds)))
        r2s.append(float(r2_score(y_test, preds)))
        
    mean_mae = sum(maes) / len(maes)
    mean_rmse = sum(rmses) / len(rmses)
    mean_r2 = sum(r2s) / len(r2s)
    
    logging.info(f"Mean MAE:  {mean_mae:.4f}")
    logging.info(f"Mean RMSE: {mean_rmse:.4f}")
    logging.info(f"Mean R2:   {mean_r2:.4f}\n")
    
    return {
        "name": name,
        "n_features": len(features),
        "mean_mae": round(mean_mae, 4),
        "mean_rmse": round(mean_rmse, 4),
        "mean_r2": round(mean_r2, 4),
        "per_fold_r2": [round(r, 4) for r in r2s],
    }

if __name__ == "__main__":
    df = load_and_validate(Path("data/raw/chiller_data.csv"))
    df, _ = preprocess(df)
    df = engineer_features(df)
    
    results = []

    # Model A: Baseline (No temporal lags)
    feats_a = [f for f in FEATURE_COLS if f not in [FEAT_LOAD_LAG_30M, FEAT_LOAD_ROLLING_2H_MEAN]]
    res_a = evaluate_features(df.dropna(subset=feats_a), feats_a, "Model A: Baseline (No Temporal Features)")
    results.append(res_a)

    # Model B: Baseline + 30m Lag
    feats_b = [f for f in FEATURE_COLS if f != FEAT_LOAD_ROLLING_2H_MEAN]
    res_b = evaluate_features(df.dropna(subset=feats_b), feats_b, "Model B: Baseline + 30m Lag")
    results.append(res_b)

    # Model C: Baseline + 30m Lag + Rolling 2h mean (Full)
    feats_c = list(FEATURE_COLS)
    res_c = evaluate_features(df.dropna(subset=feats_c), feats_c, "Model C: Baseline + 30m Lag + 2h Rolling Mean")
    results.append(res_c)

    out_path = Path("models/ablation_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"ablation_experiments": results}, f, indent=2)
    logging.info(f"Saved ablation results to {out_path}")
