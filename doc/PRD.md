# PRD — Intelligent Chiller Energy & Equipment Monitoring
## YUKTHI 2026 Hackathon

**Stage:** Hackathon MVP / prototype  
**Core flow:** Detect → Understand → Assess → Act

## 1. Product Overview

The system learns normal chiller energy behaviour under operating and environmental conditions, predicts expected energy consumption, compares it with measured energy, and identifies significant contextual deviations for investigation.

The prototype is a contextual monitoring system rather than a fixed-threshold alerting system.

## 2. Problem

Chiller energy varies with building load, chilled-water flow, cooling-water temperature, weather, equipment identity, and time. A single static energy threshold cannot reliably distinguish normal high consumption from unusual consumption under comparable conditions.

The solution therefore models:

`Expected Energy = f(operating + environmental + equipment + temporal context)`

and monitors:

`Residual = Actual Energy − Expected Energy`

## 3. Objectives

### Primary
- Build robust time-series preprocessing.
- Predict expected chiller energy.
- Quantify measured-versus-expected deviation.
- Detect contextual abnormal behaviour without requiring fault labels.
- Explain model predictions with SHAP.
- Handle equipment IDs dynamically.
- Demonstrate chronological real-time-style inference.

### Secondary
- Prevent temporal leakage.
- Handle small missing-value problems appropriately.
- Detect temporal gaps without treating them as faults.
- Present actual energy, expected energy, deviation, anomaly status, and explanation.

## 4. Dataset Scope

The project documentation specifies a full dataset of 25,003 rows, three chillers, and nominal 30-minute sampling. The supplied development CSV is an 8,969-row subset with 11 columns and currently contains `CHILLER-01` and `CHILLER-02`. The implementation must not hard-code those IDs because evaluation data may contain other equipment IDs.

### Schema

| Column | Role |
|---|---|
| `timestamp` | Time index |
| `equipment_id` | Chiller identity / categorical feature |
| `Chilled Water Rate (L/sec)` | Operating feature |
| `Cooling Water Temperature (C)` | Operating feature |
| `Building Load (RT)` | Demand/load feature |
| `Chiller Energy Consumption (kWh)` | Measured energy / ML target |
| `Outside Temperature (F)` | Environmental feature |
| `Dew Point (F)` | Environmental feature |
| `Humidity (%)` | Environmental feature |
| `Wind Speed (mph)` | Environmental feature |
| `Pressure (in)` | Environmental feature |

**Actual energy:** `Chiller Energy Consumption (kWh)` is the measured value in the supplied dataset. The ML model predicts expected energy; it does not calculate actual energy from the other fields. In deployment, actual energy would come from an energy meter/BMS/IoT stream.

## 5. Users / Stakeholders

**Users:** facility/energy managers, chiller operators, maintenance teams, technical evaluators.

**Stakeholders:** building/facility management, energy-management teams, maintenance personnel, hackathon evaluators.

## 6. Functional Requirements

### FR-01 Data ingestion
Load the supplied dataset and validate the expected schema.

### FR-02 Timestamp processing
Parse timestamps, sort chronologically, and perform time-series operations independently by `equipment_id`.

### FR-03 Missing-value handling
- Short isolated operational-sensor gaps → time-aware linear interpolation.
- Suitable weather gaps → time-series interpolation.
- Slowly changing weather fields such as pressure → forward/backward fill as fallback.
- Isolated feature gaps that cannot be locally interpolated → equipment-group median fallback where appropriate.
- Missing target energy → do not fabricate it for supervised training.

### FR-04 Temporal gaps
Detect timestamp gaps. Preserve large gaps; do not automatically label them as anomalies or faults. Use time-based rolling windows such as `2h`, not fixed row counts, when sampling is irregular.

### FR-05 Feature engineering
Create hour of day, day of week, approximate wet-bulb temperature where implemented, and other non-leaking contextual features.

Target-derived quantities such as `actual energy / load` are diagnostics after prediction, not inputs to the expected-energy model.

### FR-06 Expected-energy model
Use CatBoost Regression as the primary prototype model to predict expected energy from contextual inputs.

### FR-07 Residual
Calculate `Actual − Expected`.

### FR-08 Anomaly scoring
Use contextual residual behaviour rather than a single raw-energy threshold. A dynamic residual score and optional Isolation Forest stage may be used.

### FR-09 Persistence
Consolidate repeated abnormal observations into meaningful events where appropriate.

### FR-10 Explainability
Use SHAP to explain how features contributed to the model's expected-energy prediction. SHAP is not proof of physical causality.

### FR-11 Monitoring
Show chiller ID, timestamp, actual energy, expected energy, deviation, anomaly status/score, context, and explanation.

## 7. Non-Functional Requirements

- **Temporal integrity:** chronological validation.
- **Leakage prevention:** no future information in training features or preprocessing statistics.
- **Scalability:** dynamic equipment handling.
- **Interpretability:** operator/evaluator-friendly explanations.
- **Reproducibility:** deterministic preprocessing and training configuration.
- **MVP performance:** interactive inference/replay without unnecessary infrastructure.

## 8. Technical Architecture

```text
Historical CSV / Future Meter-BMS Stream
                 |
                 v
        Schema + Data Validation
                 |
                 v
      Timestamp + Equipment Grouping
                 |
        +--------+--------+
        |                 |
        v                 v
 Missing-value       Temporal-gap
 preprocessing       detection
        |                 |
        +--------+--------+
                 v
          Feature Engineering
                 |
                 v
       Chronological Validation
                 |
                 v
       CatBoost Regression
                 |
                 v
          Expected Energy
                 |
                 v
       Actual − Expected
                 |
                 v
   Dynamic Residual Scoring
        + optional Isolation Forest
                 |
                 v
        SHAP + Dashboard
```

## 9. ML Design

### Stage A — Expected behaviour
**Model:** CatBoost Regression  
**Input:** operating, environmental, equipment, and temporal context.  
**Output:** expected energy in kWh.

### Stage B — Contextual deviation
`Residual = Actual Energy − Expected Energy`

### Stage C — Anomaly detection
Analyse residual behaviour dynamically. An optional Isolation Forest can detect unusual residual patterns.

The output represents abnormal behaviour requiring investigation, not a confirmed mechanical fault.

### Stage D — Explainability
SHAP explains the contribution of input features to the expected-energy prediction.

## 10. Validation

Use chronological/time-series validation such as `TimeSeriesSplit`.

Report:
- MAE
- RMSE
- R²

Also inspect residual distributions, alert persistence, false-alert behaviour, and behaviour across equipment groups.

## 11. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Missing sensor values | Variable-specific time-aware preprocessing |
| Irregular timestamps | Detect gaps and use time-based windows |
| Target leakage | Exclude target-derived predictors |
| Temporal leakage | Chronological validation |
| False alerts | Contextual residual scoring + persistence |
| Unseen equipment | Dynamic `equipment_id` handling |
| Overclaiming faults | Describe output as abnormal behaviour/investigation signal |
| MVP complexity | Keep the pipeline focused |

## 12. Out of Scope

- Direct mechanical diagnosis of a specific failed component.
- Automatic maintenance execution.
- Fabricating missing target energy.
- Treating every time gap as a fault.
- Fixed thresholds as the primary anomaly logic.
- Assuming only the development chiller IDs exist.
- Full industrial BMS/SCADA integration.

## 13. Success Criteria

A judge should be able to follow one record through:

**Measured actual energy → expected energy → residual → anomaly score/status → model explanation**

and understand why contextual modelling is used instead of a raw fixed threshold.

## 14. Demo

Replay historical records chronologically:
1. Show incoming timestamp and chiller ID.
2. Read measured actual energy.
3. Predict expected energy.
4. Calculate residual.
5. Update anomaly score/status.
6. Display SHAP explanation.
7. Group repeated abnormal observations into an event when appropriate.

## 15. Evaluator Positioning

> “Because the supplied data does not provide labelled anomaly or fault outcomes, we formulate the problem as contextual expected-behaviour modelling. The model learns normal energy consumption from operating and environmental context, predicts expected energy for each observation, and identifies significant deviations between measured and expected consumption. SHAP then explains the factors that influenced the model's expected-energy prediction.”

