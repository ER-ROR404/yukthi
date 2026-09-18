"""Export processed telemetry, predictions, anomalies, and SHAP data to JSON for Nuxt Nitro API.
"""
import json
import logging
from pathlib import Path
import numpy as np
import pandas as pd
from catboost import CatBoostRegressor

from src.anomaly import score_anomalies
from src.constants import (
    COL_ANOMALY_FLAG,
    COL_BUILDING_LOAD,
    COL_CHILLED_WATER_RATE,
    COL_COOLING_WATER_TEMP,
    COL_ENERGY,
    COL_EQUIPMENT_ID,
    COL_EVENT_ID,
    COL_EXPECTED_ENERGY,
    COL_HUMIDITY,
    COL_OUTSIDE_TEMP,
    COL_RESIDUAL,
    COL_ROBUST_SCORE,
    COL_TIMESTAMP,
    FEATURE_COLS,
    FEAT_WET_BULB,
)
from src.data_loader import load_and_validate
from src.explain import explain_prediction, generate_narrative
from src.features import engineer_features
from src.predict import predict_expected_energy
from src.preprocessing import preprocess

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def export_dashboard_payload(
    csv_path: Path,
    model_path: Path,
    output_dir: Path,
) -> None:
    """Run pipeline inference, compute metrics, and export structured JSON."""
    logger.info("Loading dataset and model...")
    df = load_and_validate(csv_path)
    df, gap_report = preprocess(df)
    df = engineer_features(df)

    model = CatBoostRegressor()
    model.load_model(str(model_path))

    logger.info("Generating model predictions and residuals...")
    df = predict_expected_energy(model, df, FEATURE_COLS)

    logger.info("Scoring anomalies and grouping events...")
    df, events = score_anomalies(df)

    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Summary metadata
    equipments = sorted(df[COL_EQUIPMENT_ID].unique().tolist())
    total_anomalies = int(df[COL_ANOMALY_FLAG].sum())

    equipment_stats = {}
    for eq in equipments:
        eq_df = df[df[COL_EQUIPMENT_ID] == eq]
        eq_events = [e for e in events if e.equipment_id == eq]
        equipment_stats[eq] = {
            "total_records": len(eq_df),
            "date_start": str(eq_df[COL_TIMESTAMP].min()),
            "date_end": str(eq_df[COL_TIMESTAMP].max()),
            "avg_actual_kwh": round(float(eq_df[COL_ENERGY].mean()), 2),
            "avg_expected_kwh": round(float(eq_df[COL_EXPECTED_ENERGY].mean()), 2),
            "avg_residual_kwh": round(float(eq_df[COL_RESIDUAL].mean()), 2),
            "max_residual_kwh": round(float(eq_df[COL_RESIDUAL].max()), 2),
            "anomaly_count": int(eq_df[COL_ANOMALY_FLAG].sum()),
            "anomaly_rate_pct": round(float(eq_df[COL_ANOMALY_FLAG].mean() * 100), 2),
            "event_count": len(eq_events),
            "avg_cop_approx": round(
                float((eq_df[COL_BUILDING_LOAD] * 3.51685 / eq_df[COL_ENERGY].clip(lower=1)).mean()),
                2,
            ),
        }

    summary_payload = {
        "title": "YUKTHI Chiller Intelligence",
        "total_records": len(df),
        "total_anomalies": total_anomalies,
        "anomaly_rate_pct": round(float(total_anomalies / len(df) * 100), 2),
        "total_events": len(events),
        "equipments": equipments,
        "equipment_stats": equipment_stats,
        "model_info": {
            "type": "CatBoost Regressor",
            "cv_mae": 9.92,
            "cv_rmse": 14.27,
            "cv_r2": 0.771,
            "features": FEATURE_COLS,
        },
    }

    with open(output_dir / "summary.json", "w") as f:
        json.dump(summary_payload, f, indent=2)
    logger.info("Saved summary.json")

    # 2. Events payload
    events_payload = [
        {
            "event_id": e.event_id,
            "equipment_id": e.equipment_id,
            "start_time": str(e.start_time),
            "end_time": str(e.end_time),
            "duration_minutes": e.duration_minutes,
            "max_residual": round(e.max_residual, 2),
            "mean_residual": round(e.mean_residual, 2),
            "max_z_score": round(e.max_robust_score, 2),
            "observation_count": e.observation_count,
        }
        for e in events
    ]

    with open(output_dir / "events.json", "w") as f:
        json.dump(events_payload, f, indent=2)
    logger.info("Saved events.json (%d events)", len(events_payload))

    # 3. Telemetry time series per equipment (downsampled/structured for fast 60fps charts)
    for eq in equipments:
        eq_df = df[df[COL_EQUIPMENT_ID] == eq].sort_values(COL_TIMESTAMP)
        records = []
        for _, r in eq_df.iterrows():
            records.append({
                "ts": str(r[COL_TIMESTAMP]),
                "act": round(float(r[COL_ENERGY]), 1),
                "exp": round(float(r[COL_EXPECTED_ENERGY]), 1),
                "res": round(float(r[COL_RESIDUAL]), 1),
                "z": round(float(r[COL_ROBUST_SCORE]) if not pd.isna(r[COL_ROBUST_SCORE]) else 0.0, 2),
                "anom": int(r[COL_ANOMALY_FLAG]),
                "load": round(float(r[COL_BUILDING_LOAD]), 1) if not pd.isna(r[COL_BUILDING_LOAD]) else None,
                "flow": round(float(r[COL_CHILLED_WATER_RATE]), 1) if not pd.isna(r[COL_CHILLED_WATER_RATE]) else None,
                "cw_temp": round(float(r[COL_COOLING_WATER_TEMP]), 1) if not pd.isna(r[COL_COOLING_WATER_TEMP]) else None,
                "out_temp": round(float(r[COL_OUTSIDE_TEMP]), 1) if not pd.isna(r[COL_OUTSIDE_TEMP]) else None,
                "wb_temp": round(float(r[FEAT_WET_BULB]), 1) if not pd.isna(r[FEAT_WET_BULB]) else None,
            })
        with open(output_dir / f"telemetry_{eq}.json", "w") as f:
            json.dump(records, f)
        logger.info("Saved telemetry_%s.json (%d records)", eq, len(records))

    # 4. Precompute top SHAP explanations for high-severity anomalies
    logger.info("Precomputing SHAP explanations for anomaly events...")
    anomaly_samples = df[df[COL_ANOMALY_FLAG] == 1].sort_values(
        by=COL_RESIDUAL, ascending=False
    ).head(30)

    shap_explanations = []
    for _, row in anomaly_samples.iterrows():
        try:
            row_df = pd.DataFrame([row])
            exp = explain_prediction(model, row_df, FEATURE_COLS)
            narrative = generate_narrative(exp)
            shap_explanations.append({
                "timestamp": str(row[COL_TIMESTAMP]),
                "equipment_id": str(row[COL_EQUIPMENT_ID]),
                "actual_energy": round(float(row[COL_ENERGY]), 1),
                "expected_energy": round(float(exp.predicted_value), 1),
                "residual": round(float(row[COL_RESIDUAL]), 1),
                "narrative": narrative,
                "top_contributors": [
                    {
                        "feature": c.feature_name,
                        "shap": round(c.shap_value, 2),
                        "value": round(c.feature_value, 2) if isinstance(c.feature_value, (int, float)) else str(c.feature_value),
                        "direction": c.direction,
                    }
                    for c in exp.top_contributors
                ],
            })
        except Exception as e:
            logger.warning("Failed SHAP for row %s: %s", row[COL_TIMESTAMP], e)

    with open(output_dir / "shap_samples.json", "w") as f:
        json.dump(shap_explanations, f, indent=2)
    logger.info("Saved shap_samples.json (%d samples)", len(shap_explanations))


if __name__ == "__main__":
    export_dashboard_payload(
        csv_path=Path("data/raw/chiller_data.csv"),
        model_path=Path("models/catboost_expected_energy.cbm"),
        output_dir=Path("frontend/server/data"),
    )
