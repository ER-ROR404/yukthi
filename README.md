# YUKTHI 2026 — Intelligent Chiller Energy & Equipment Monitoring

> Contextual expected-behaviour modelling for chiller energy systems.
> **Detect. Understand. Assess. Act.**

## What This Does

Learns expected chiller energy consumption from historical operating and environmental data, identifies significant contextual deviations, and explains predictions with SHAP.

Instead of asking "Is energy above 500 kWh?", the system asks:

> Given current operating conditions, how much energy *should* this chiller consume, and how far did the measured value deviate?

## Pipeline

```
CSV Data → Validation → Preprocessing → Feature Engineering → CatBoost Model
                                                                     ↓
                                                              Expected Energy
                                                                     ↓
                                                          Actual − Expected
                                                                     ↓
                                                        Residual Anomaly Score
                                                                     ↓
                                                    SHAP Explanation + Dashboard
```

## Quick Start

### 1. Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

### 2. Data Placement

Place the chiller CSV at:
```
data/raw/chiller_data.csv
```

### 3. Train the Model

```bash
python -c "
from pathlib import Path
from src.data_loader import load_and_validate
from src.preprocessing import preprocess
from src.features import engineer_features
from src.train import train_model
from src.constants import FEATURE_COLS, COL_ENERGY

df = load_and_validate(Path('data/raw/chiller_data.csv'))
df, gap_report = preprocess(df)
df = engineer_features(df)
result = train_model(df, FEATURE_COLS, COL_ENERGY, Path('models/catboost_expected_energy.cbm'))
print(result.summary())
"
```

### 4. Run Dashboard

```bash
streamlit run app/dashboard.py
```

### 5. Run Tests

```bash
pytest tests/ -v
```

## Project Structure

```
yukthi/
├── data/raw/chiller_data.csv       # Input dataset
├── models/                          # Trained model artifacts
├── src/
│   ├── constants.py                 # All config and column names
│   ├── exceptions.py                # Custom exception hierarchy
│   ├── data_loader.py               # Load + validate schema
│   ├── preprocessing.py             # Variable-specific imputation
│   ├── features.py                  # Temporal + wet-bulb features
│   ├── train.py                     # CatBoost + TimeSeriesSplit CV
│   ├── predict.py                   # Expected energy + residual
│   ├── anomaly.py                   # Z-score scoring + persistence
│   └── explain.py                   # SHAP explanations
├── app/dashboard.py                 # Streamlit dashboard
├── tests/                           # pytest test suite
└── requirements.txt
```

## ML Architecture

- **Model:** CatBoost Regressor (native categorical support, ordered boosting)
- **Validation:** Chronological `TimeSeriesSplit(n_splits=5)` — no random shuffle
- **Anomaly Detection:** Dynamic residual z-scores (2h rolling window per equipment) + persistence grouping
- **Explainability:** CatBoost native exact SHAP values

## Evaluator Explanation

> "Because the supplied data does not provide labelled anomaly or fault outcomes, we formulate the problem as contextual expected-behaviour modelling. The model learns normal energy consumption from operating and environmental context, predicts expected energy for each observation, and identifies significant deviations between measured and expected consumption. SHAP then explains the factors that influenced the model's expected-energy prediction."
