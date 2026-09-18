YUKTHI 2026
NATIONAL-LEVEL HACKATHON
DATA SPECIFICATION
Intelligent Energy & Equipment Monitoring
Participant Reference Document

1. Purpose of this Document
   This document defines the data contract for the YUKTHI 2026 Intelligent Energy & Equipment Monitoring challenge. It describes the structure, fields, units, temporal characteristics, missing-data conventions, and interpretation of the participant dataset.
   Teams should use this specification when designing their data ingestion, preprocessing, feature engineering, and application pipelines. Solutions should be designed to operate on datasets that conform to this specification rather than relying on hand-coded observations.
2. Dataset Overview
   The participant development dataset is provided as a CSV file containing historical observations from multiple chiller units. Each record represents an observation for a specific equipment unit at a particular timestamp.

- File format: CSV
- Development dataset size: 25,003 rows
- Number of fields: 11
- Equipment units represented: 3 (CHILLER-01, CHILLER-02, CHILLER-03)
- Observation period: 2019-08-18 00:00:00 to 2020-06-01 13:00:00
- Nominal observation interval: 30 minutes (occasional larger gaps are present)
  The development dataset does not contain an anomaly/fault target column. Teams are expected to formulate their ML approach using the information available in the dataset.

3. Data Structure
   3.1 Record Identity
   Each observation is uniquely identified by the combination of timestamp and equipment_id. The same timestamp may legitimately occur for different equipment units because the units are monitored independently.
   Teams should treat each equipment_id as its own chronological equipment series when performing time-series analysis. An identical timestamp across different equipment units is not, by itself, a duplicate record. The supplied development dataset contains 0 duplicate (equipment_id, timestamp) pairs.
   3.2 Field Specification
   | Field | Data Type | Unit | Description | Participant Interpretation |
   |---|---|---|---|---|
   | timestamp | Datetime | - | Observation timestamp | Temporal reference for each observation; preserve chronological ordering within each unit. |
   | equipment_id | Categorical / Identifier | - | Chiller unit identifier | Identifies equipment (CHILLER-01, CHILLER-02, CHILLER-03). |
   | Chilled Water Rate | Numeric | L/sec | Chilled-water flow rate | Operational variable characterizing behavior and relationship with load/energy. |
   | Cooling Water Temperature | Numeric | °C | Cooling-water temperature | Thermal operating/context variable relevant to chiller behavior. |
   | Building Load | Numeric | RT | Building cooling load | Cooling demand/load associated with the observation. |
   | Chiller Energy Consumption | Numeric | kWh | Chiller energy consumption | Primary energy-related measurement for analyzing energy behavior. |
   | Outside Temperature | Numeric | °F | Outdoor/ambient temperature | Environmental variable influencing operating conditions. |
   | Dew Point | Numeric | °F | Outdoor dew-point temperature | Contextual variable related to atmospheric moisture conditions. |
   | Humidity | Numeric | % | Relative humidity | Environmental variable influencing operating conditions. |
   | Wind Speed | Numeric | mph | Outdoor wind speed | Environmental/contextual variable. |
   | Pressure | Numeric | in | Atmospheric pressure | Environmental/contextual variable. |
4. Data Types and Missing Values
   Numeric measurement fields are supplied as numeric values, while timestamp and equipment_id are non-numeric. Missing values are represented as blank/NaN values in the CSV. Teams should determine an appropriate strategy for handling missing data.
   | Field | Missing Values | Share of Dataset |
   |---|---|---|
   | Chilled Water Rate (L/sec) | 40 | 0.160% |
   | Cooling Water Temperature (C) | 5 | 0.020% |
   | Building Load (RT) | 19 | 0.076% |
   | Chiller Energy Consumption (kWh) | 9 | 0.036% |
   | Humidity (%) | 20 | 0.080% |
   | Wind Speed (mph) | 23 | 0.092% |
   | Pressure (in) | 12 | 0.048% |
   Fields with zero missing values: timestamp, equipment_id, Outside Temperature (F), and Dew Point (F).
5. Temporal Characteristics

- The dataset is time-indexed and intended for chronological analysis.
- Nominal sampling interval is 30 minutes, but gaps longer than the nominal interval exist.
- Do not automatically interpret a gap as an equipment fault or anomaly.
- Temporal features, rolling statistics, lagged variables, persistence, and trends should be considered.

6. Equipment-Level Analysis

- Equipment identifiers (equipment_id) should be retained throughout the analysis pipeline.
- Treat equipment_id as a categorical identifier rather than a continuous numeric variable.
- Analyze temporal behavior within each equipment unit where appropriate.
- Equipment-specific operating characteristics should be considered; differences between units are not automatically anomalies.

7. Contextual and Multivariate Interpretation
   Participants should consider relationships between equipment behavior and operating/environmental variables rather than isolated metrics. A measurement appearing unusual in isolation may be normal under specific operating conditions, while normal isolated values may indicate anomalies when analyzed contextually.
8. Data Quality Considerations
   Appropriate considerations for pipeline preparation include:

- Missing-value handling
- Outlier and noise handling
- Timestamp ordering and temporal gaps
- Equipment-specific behavior
- Feature scaling or transformation
- Lagged, rolling, or historical features
- Prevention of information leakage when validating time-dependent models

9. Target and Ground-Truth Information
   The participant development dataset does not expose an anomaly, fault, health, or maintenance target field. Participants must formulate an appropriate methodology for learning expected behavior and identifying deviations.
10. Reusable Data Pipeline Requirement

- Solutions must be modular and able to ingest, validate, preprocess, and analyze conforming datasets.
- Avoid hard-coded observation values, fixed row counts, or hard-coded timestamps.
- Process equipment_id and timestamp programmatically.

11. What the Data Does and Does Not Specify
    | The dataset provides | The dataset does NOT prescribe |
    |---|---|
    | Historical equipment observations | A specific ML algorithm |
    | Equipment identifiers and timestamps | A specific anomaly-detection method |
    | Energy-related measurements | A fixed feature engineering strategy |
    | Operational/chiller measurements | A fixed threshold or scoring formula |
    | Environmental/contextual measurements | A specific application architecture |
12. Participant Data Contract - Summary

- CSV input with 11 fields defined in Section 3.2.
- timestamp serves as the temporal reference; equipment_id identifies the equipment unit.
- Measurement fields are numeric with specified units.
- Missing values occur in measurement fields and must be handled programmatically.
- Nominal 30-minute sampling interval with potential temporal gaps.
- Dynamic pipeline structure with no dependency on fixed row counts or hard-coded values.
- Unlabeled dataset without explicit target/ground-truth columns.

13. Relationship to the Problem Statement
    This document defines the data contract and available data. It should be read alongside the YUKTHI 2026 Problem Statement and Evaluation Guidelines.
