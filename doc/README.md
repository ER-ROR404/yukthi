# Intelligent Chiller Energy & Equipment Monitoring

YUKTHI 2026 hackathon implementation guide.

## 1. What this project does

The project learns expected chiller energy consumption from historical operating and environmental data.

Instead of asking:

> Is energy above a fixed threshold?

it asks:

> Given the current operating conditions, how much energy should this chiller be expected to consume, and how far did the measured value deviate?

Pipeline:

```text
Data
  ↓
Validation & preprocessing
  ↓
Feature engineering
  ↓
CatBoost expected-energy model
  ↓
Expected energy
  ↓
Actual − Expected
  ↓
Residual / anomaly scoring
  ↓
SHAP explanation
  ↓
Dashboard / chronological replay
```

## 2. Data facts

The project documentation specifies a full dataset of 25,003 rows, three chillers, and nominal 30-minute sampling.

The supplied development CSV is an 8,969-row subset with 11 columns and currently contains `CHILLER-01` and `CHILLER-02`. Do not hard-code those IDs.

The target is:

```text
Chiller Energy Consumption (kWh)
```

This is the measured/actual energy value in the supplied dataset. The prototype does not derive actual energy from the other sensor columns. In deployment, actual energy would normally come from an energy meter/BMS/IoT stream.

## 3. Project structure

```text
chiller-intelligence/
├── data/
│   ├── raw/chiller_data.csv
│   └── processed/
├── models/
│   └── catboost_expected_energy.cbm
├── src/
│   ├── data_loader.py
│   ├── preprocessing.py
│   ├── features.py
│   ├── train.py
│   ├── predict.py
│   ├── anomaly.py
│   └── explain.py
├── app/
│   └── dashboard.py
├── notebooks/
├── tests/
├── requirements.txt
├── PRD.md
└── README.md
```

## 4. Setup

Create an environment:

```bash
python -m venv .venv
```

Activate it.

Linux/macOS:

```bash
source .venv/bin/activate
```

Windows:

```powershell
.venv\Scripts\activate
```

Install:

```bash
pip install -r requirements.txt
```

Suggested MVP dependencies:

```text
pandas
numpy
scikit-learn
catboost
shap
joblib
matplotlib
streamlit
```

## 5. Data placement

Put the CSV at:

```text
data/raw/chiller_data.csv
```

Required columns:

```text
timestamp
equipment_id
Chilled Water Rate (L/sec)
Cooling Water Temperature (C)
Building Load (RT)
Chiller Energy Consumption (kWh)
Outside Temperature (F)
Dew Point (F)
Humidity (%)
Wind Speed (mph)
Pressure (in)
```

## 6. Preprocessing

### 6.1 Timestamp

```python
df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
df = df.dropna(subset=["timestamp"])
df = df.sort_values(["equipment_id", "timestamp"])
```

Perform time operations within each equipment group.

### 6.2 Duplicates

Check uniqueness of:

```text
equipment_id + timestamp
```

```python
duplicates = df.duplicated(
    subset=["equipment_id", "timestamp"]
).sum()
```

Resolve duplicates before training.

### 6.3 Missing values

Do not use one blanket imputation rule.

**Operational sensor gaps:** time-aware interpolation for short isolated gaps.

**Weather gaps:** time-series interpolation for short gaps; forward/backward fill can be a fallback for slowly changing variables such as pressure.

**Building Load:** interpolate when possible; use equipment-group median only as an isolated fallback.

**Target energy:** never fabricate missing supervised targets.

At inference, expected energy can be predicted without actual energy, but anomaly residual cannot be calculated until actual energy arrives.

## 7. Temporal gaps

A missing value and a missing time interval are different.

Detect gaps:

```python
df["time_diff"] = (
    df.groupby("equipment_id")["timestamp"].diff()
)
```

Do not fill multi-day gaps automatically and do not call them faults.

Because sampling can be irregular, prefer:

```python
rolling("2h")
```

over:

```python
rolling(4)
```

when calculating time-window features.

## 8. Feature engineering

Useful contextual features:

- `hour_of_day`
- `day_of_week`
- chilled-water rate
- cooling-water temperature
- building load
- outside temperature
- dew point
- humidity
- wind speed
- pressure
- `equipment_id`
- optional approximate wet-bulb temperature

### Leakage warning

Do not use:

```text
actual energy / building load
```

as an input to the expected-energy model because it contains the target.

It can be calculated after prediction as a diagnostic efficiency measure.

Target-energy lag features should only be used when the lag is genuinely available at inference and the train/test construction is leakage-safe. For the first MVP, omit them.

## 9. Train/test strategy

Use chronological validation:

```python
from sklearn.model_selection import TimeSeriesSplit

tscv = TimeSeriesSplit(n_splits=5)
```

Conceptually:

```text
Past → Train
Later → Validation/Test
```

Do not randomly shuffle the primary time-series evaluation.

## 10. CatBoost model

CatBoost predicts expected energy from context.

```python
from catboost import CatBoostRegressor

features = [
    "equipment_id",
    "Chilled Water Rate (L/sec)",
    "Cooling Water Temperature (C)",
    "Building Load (RT)",
    "Outside Temperature (F)",
    "Dew Point (F)",
    "Humidity (%)",
    "Wind Speed (mph)",
    "Pressure (in)",
    "hour_of_day",
    "day_of_week",
]

target = "Chiller Energy Consumption (kWh)"

model = CatBoostRegressor(
    iterations=500,
    depth=7,
    learning_rate=0.05,
    loss_function="RMSE",
    verbose=False
)

model.fit(
    X_train,
    y_train,
    cat_features=["equipment_id"]
)
```

These are a starting configuration, not a claim that these hyperparameters are optimal. Tune with chronological validation.

## 11. Expected energy and residual

```python
df["expected_energy"] = model.predict(df[features])

df["residual"] = (
    df["Chiller Energy Consumption (kWh)"]
    - df["expected_energy"]
)
```

Example:

```text
Actual energy   = 520 kWh
Expected energy = 470 kWh
Residual        = +50 kWh
```

Interpretation:

> The chiller consumed 50 kWh more than the model expected under the observed context.

This is a contextual deviation, not automatically a mechanical fault.

## 12. Anomaly detection

Start with residual analysis and dynamic residual scoring.

An optional second stage can use:

```python
from sklearn.ensemble import IsolationForest
```

Conceptual architecture:

```text
Actual Energy
      |
      +------ Expected Energy
                  |
                  v
             Residual
                  |
                  v
        Dynamic residual score
                  |
                  v
        Optional Isolation Forest
                  |
                  v
          Anomaly status
```

The output should be described as abnormal behaviour requiring investigation, not as a confirmed physical fault.

## 13. Persistence

Example:

```text
10:00 normal
10:30 abnormal
11:00 abnormal
11:30 abnormal
12:00 normal
```

Instead of three independent alerts, group them as one abnormal event:

```text
10:30–11:30
Repeated contextual energy deviation
```

This reduces alert noise.

## 14. SHAP

SHAP explains why the model produced a particular expected-energy prediction.

```text
Observation
    ↓
CatBoost
    ↓
Expected Energy
    ↓
SHAP
    ├── Building Load contribution
    ├── Cooling Water Temperature contribution
    ├── Flow contribution
    └── Weather contribution
```

Example:

> High building load and cooling-water temperature increased the model's expected-energy prediction.

SHAP does not prove that a particular physical component caused the anomaly.

## 15. Real-time-style execution

The supplied dataset is historical. Do not claim that it is a live sensor stream.

Replay records chronologically:

```python
for _, row in df.sort_values("timestamp").iterrows():
    # receive observation
    # preprocess
    # predict expected energy
    # calculate residual
    # calculate anomaly status
    # generate explanation
    # update dashboard
    pass
```

This demonstrates the inference behaviour that a future live meter/BMS stream would use.

## 16. Dashboard output

A useful demo panel:

```text
CHILLER-01                 10:30
--------------------------------
Actual Energy       520 kWh
Expected Energy     470 kWh
Deviation            +50 kWh
Status              INVESTIGATE
--------------------------------
Building Load        800 RT
Cooling Water Temp    29 C
Flow                  25 L/s
--------------------------------
Explanation
High load and cooling-water
temperature increased expected
energy; actual consumption
remained above expectation.
```

## 17. Expected outputs

### Training

```text
models/catboost_expected_energy.cbm
```

Metrics:

```text
MAE
RMSE
R²
```

Also save residual diagnostics.

### Inference

Recommended fields:

```text
timestamp
equipment_id
actual_energy
expected_energy
residual
anomaly_score
anomaly_status
```

### Dashboard

Show:

- current chiller;
- actual energy;
- expected energy;
- deviation;
- anomaly status;
- operating context;
- model explanation.

## 18. Implementation order

1. Data audit.
2. Schema/type validation.
3. Timestamp sorting and equipment grouping.
4. Missing-value preprocessing.
5. Temporal-gap detection.
6. Feature engineering.
7. CatBoost training.
8. Chronological validation.
9. Residual analysis.
10. Dynamic anomaly scoring.
11. Persistence/event grouping.
12. SHAP explanation.
13. Chronological replay.
14. Dashboard.

## 19. Common mistakes

### Fixed threshold

Avoid:

```python
if energy > 500:
    anomaly = True
```

because operating context matters.

### Random split

Avoid random shuffling for the primary time-series evaluation.

### Filling long gaps

Do not treat a multi-day data absence as ordinary missing sensor values.

### Future leakage

A live pipeline cannot use a future reading that has not arrived.

### Target leakage

Do not feed actual-energy-derived quantities into the expected-energy predictor.

### SHAP overclaim

SHAP explains model behaviour; it does not establish physical causality.

### Hard-coded equipment

Use `equipment_id` dynamically.

## 20. Definition of Done

- [ ] Dataset loads and schema validates.
- [ ] Duplicate records are handled.
- [ ] Missing values are handled appropriately.
- [ ] Temporal gaps are detected and preserved.
- [ ] Features are leakage-safe.
- [ ] CatBoost model trains.
- [ ] Chronological validation is implemented.
- [ ] MAE/RMSE/R² are reported.
- [ ] Expected energy is generated.
- [ ] Residual is calculated.
- [ ] Anomaly scoring works.
- [ ] Persistence/event grouping works or is explicitly scoped.
- [ ] SHAP works for selected predictions.
- [ ] Chronological replay works.
- [ ] Dashboard displays actual versus expected energy.
- [ ] PRD and README match the implementation.

## 21. Evaluator explanation

Use this concise explanation:

> “Because the supplied data does not provide labelled anomaly or fault outcomes, we formulate the problem as contextual expected-behaviour modelling. The model learns normal energy consumption from operating and environmental context, predicts expected energy for each observation, and identifies significant deviations between measured and expected consumption. SHAP then explains the factors that influenced the model's expected-energy prediction.”

If asked where actual energy comes from:

> “In the prototype, actual energy comes from the measured `Chiller Energy Consumption (kWh)` field. In deployment, that value would be supplied by an energy meter or BMS/IoT stream.”

If asked whether the system detects a compressor fault:

> “Not directly. The available data does not contain labelled fault outcomes. The system detects contextual abnormal energy behaviour and produces an investigation signal.”
