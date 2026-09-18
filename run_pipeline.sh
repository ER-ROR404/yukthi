#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# YUKTHI 2026: End-to-End Reproducible ML Pipeline Execution
# ==============================================================================

echo "======================================================================"
echo "YUKTHI Contextual Chiller Intelligence: Running Full Pipeline"
echo "======================================================================"

source .venv/bin/activate

echo "[1/4] Running automated test suite (Unit, Adversarial, Replay Consistency)..."
pytest tests/ -v

echo "[2/4] Executing canonical 5-fold chronological cross-validation & model training..."
python3 -m src.train

echo "[3/4] Running ablation study (Baseline vs Lag vs Rolling 2h)..."
python3 -m src.run_ablation

echo "[4/4] Scoring anomalies, computing TreeSHAP explanations, and exporting payload..."
python3 -m src.export_data

echo "======================================================================"
echo "Pipeline execution successfully finished! All artifacts generated in:"
echo "  - models/ (catboost model, operating envelope, metrics, metadata)"
echo "  - frontend/server/data/ (events, summary, telemetry, shap samples)"
echo "======================================================================"
