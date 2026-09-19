"""Parameter-level anomaly scoring for multi-sensor chiller telemetry.

Computes parameter-specific expected reference baselines, deviation values
(Actual - Expected), and statistical anomaly scores (z-scores via Median & MAD)
for each measured physical and environmental parameter.

Retains CatBoost contextual predictions and robust residual scores for energy.
"""
from dataclasses import dataclass
from typing import Final
import numpy as np
import pandas as pd

from src.constants import (
    COL_TIMESTAMP,
    COL_EQUIPMENT_ID,
    COL_ENERGY,
    COL_EXPECTED_ENERGY,
    COL_RESIDUAL,
    COL_ROBUST_SCORE,
    COL_COOLING_WATER_TEMP,
    COL_CHILLED_WATER_RATE,
    COL_BUILDING_LOAD,
    COL_OUTSIDE_TEMP,
    COL_HUMIDITY,
    COL_DEW_POINT,
    COL_WIND_SPEED,
    COL_PRESSURE,
)

_MIN_MAD: float = 1e-4


@dataclass(frozen=True)
class ParameterSpec:
    """Metadata specification for a measured telemetry parameter."""
    raw_col: str
    display_name: str
    unit: str
    decimals: int
    is_model_target: bool = False


# All measured telemetry parameters in the chiller system
MEASURED_PARAMETERS: Final[list[ParameterSpec]] = [
    ParameterSpec(
        raw_col=COL_ENERGY,
        display_name="Energy Consumption",
        unit="kWh",
        decimals=1,
        is_model_target=True,
    ),
    ParameterSpec(
        raw_col=COL_COOLING_WATER_TEMP,
        display_name="Cooling Water Temperature",
        unit="°C",
        decimals=1,
    ),
    ParameterSpec(
        raw_col=COL_CHILLED_WATER_RATE,
        display_name="Chilled Water Rate",
        unit="L/s",
        decimals=1,
    ),
    ParameterSpec(
        raw_col=COL_BUILDING_LOAD,
        display_name="Building Load",
        unit="RT",
        decimals=1,
    ),
    ParameterSpec(
        raw_col=COL_OUTSIDE_TEMP,
        display_name="Outside Temperature",
        unit="°F",
        decimals=1,
    ),
    ParameterSpec(
        raw_col=COL_HUMIDITY,
        display_name="Relative Humidity",
        unit="%",
        decimals=0,
    ),
    ParameterSpec(
        raw_col=COL_DEW_POINT,
        display_name="Dew Point",
        unit="°F",
        decimals=1,
    ),
    ParameterSpec(
        raw_col=COL_WIND_SPEED,
        display_name="Wind Speed",
        unit="mph",
        decimals=1,
    ),
    ParameterSpec(
        raw_col=COL_PRESSURE,
        display_name="Barometric Pressure",
        unit="in",
        decimals=2,
    ),
]


def compute_all_parameter_anomalies(
    df: pd.DataFrame,
    window_periods: int = 336,  # 7 days at 30-min intervals
    min_periods: int = 12,
) -> pd.DataFrame:
    """Compute expected values, deviations, and anomaly scores for every parameter.

    For Energy:
      - Expected = CatBoost prediction
      - Deviation = Actual - Expected
      - Anomaly Score = abs(Robust MAD residual score)

    For Other Sensors:
      - Expected = Shifted 7-day rolling median per equipment
      - Deviation = Actual - Expected
      - Anomaly Score = abs(Deviation) / (1.4826 * Shifted 7-day rolling MAD)

    Returns:
      Augmented DataFrame with columns:
        <raw_col>__expected
        <raw_col>__deviation
        <raw_col>__score
        <raw_col>__status ('CRITICAL', 'WARNING', 'NORMAL')
    """
    result = df.copy()
    result = result.sort_values(by=[COL_EQUIPMENT_ID, COL_TIMESTAMP])

    for spec in MEASURED_PARAMETERS:
        col = spec.raw_col
        if col not in result.columns:
            continue

        exp_col = f"{col}__expected"
        dev_col = f"{col}__deviation"
        score_col = f"{col}__score"
        status_col = f"{col}__status"

        if spec.is_model_target:
            # Energy consumption uses contextual CatBoost model predictions
            if COL_EXPECTED_ENERGY in result.columns:
                result[exp_col] = result[COL_EXPECTED_ENERGY]
            else:
                result[exp_col] = result[col]

            result[dev_col] = result[col] - result[exp_col]

            if COL_ROBUST_SCORE in result.columns:
                result[score_col] = result[COL_ROBUST_SCORE].abs().fillna(0.0)
            else:
                result[score_col] = 0.0

        else:
            # Sensor parameters use shifted rolling baseline statistics
            expected_series = pd.Series(index=result.index, dtype=float)
            score_series = pd.Series(index=result.index, dtype=float)

            for _, group in result.groupby(COL_EQUIPMENT_ID):
                # Calculate rolling median shifted by 1 (no self-observation leakage)
                rolling_med = group[col].rolling(
                    window=window_periods, min_periods=min_periods
                ).median().shift(1)

                # Safe fallback for initial window: use early median
                early_med = group[col].iloc[:window_periods].median()
                rolling_med = rolling_med.fillna(early_med)

                # Calculate absolute deviation from rolling median
                abs_dev = (group[col] - rolling_med).abs()

                # Calculate rolling MAD shifted by 1
                rolling_mad = abs_dev.rolling(
                    window=window_periods, min_periods=min_periods
                ).median().shift(1)

                early_mad = abs_dev.iloc[:window_periods].median()
                rolling_mad = rolling_mad.fillna(early_mad)
                mad_safe = np.clip(rolling_mad.values, a_min=_MIN_MAD, a_max=None)

                deviation = group[col].values - rolling_med.values
                z_score = np.abs(deviation) / (1.4826 * mad_safe)

                expected_series.loc[group.index] = rolling_med.values
                score_series.loc[group.index] = z_score

            result[exp_col] = expected_series
            result[dev_col] = result[col] - result[exp_col]
            result[score_col] = score_series.fillna(0.0)

        # Classify status based on statistical significance
        # Score >= 3.0 -> CRITICAL (🔴)
        # 2.0 <= Score < 3.0 -> WARNING (🟠)
        # Score < 2.0 -> NORMAL (🟢)
        result[status_col] = "NORMAL"
        result.loc[result[score_col] >= 2.0, status_col] = "WARNING"
        result.loc[result[score_col] >= 3.0, status_col] = "CRITICAL"

    return result


def extract_parameter_breakdown_for_row(row: pd.Series | dict) -> list[dict]:
    """Extract full parameter breakdown list for an individual observation.

    Used by the Investigation & Evidence Workbench to display:
    Parameter | Value (Deviation) | Anomaly Score | Status
    """
    breakdown = []
    for spec in MEASURED_PARAMETERS:
        col = spec.raw_col
        if col not in row:
            continue

        act_val = row.get(col)
        exp_val = row.get(f"{col}__expected")
        dev_val = row.get(f"{col}__deviation")
        score_val = row.get(f"{col}__score", 0.0)
        status_val = row.get(f"{col}__status", "NORMAL")

        if pd.isna(act_val):
            continue

        act_f = float(act_val)
        exp_f = float(exp_val) if not pd.isna(exp_val) else act_f
        dev_f = float(dev_val) if not pd.isna(dev_val) else (act_f - exp_f)
        score_f = float(score_val) if not pd.isna(score_val) else 0.0

        breakdown.append({
            "raw_col": col,
            "parameter": spec.display_name,
            "unit": spec.unit,
            "actual": round(act_f, spec.decimals),
            "expected": round(exp_f, spec.decimals),
            "deviation": round(dev_f, spec.decimals),
            "anomaly_score": round(score_f, 2),
            "status": status_val,
            "is_target": spec.is_model_target,
        })

    # Sort so most anomalous parameters appear at the top
    breakdown.sort(key=lambda item: item["anomaly_score"], reverse=True)
    return breakdown


def generate_parameter_anomaly_table(
    df: pd.DataFrame,
    min_score: float = 2.0,
    max_rows: int = 1500,
) -> list[dict]:
    """Generate consolidated parameter-level anomaly rows for the UI table.

    Produces rows formatted as:
      Equipment ID | Timestamp | Parameter | Actual Value | Expected/Normal | Deviation Value | Anomaly Score | Status
    """
    records = []

    # Sort chronologically
    df_sorted = df.sort_values(by=[COL_TIMESTAMP, COL_EQUIPMENT_ID])

    for _, row in df_sorted.iterrows():
        ts_str = str(row[COL_TIMESTAMP])
        eq_id = str(row[COL_EQUIPMENT_ID])

        for spec in MEASURED_PARAMETERS:
            col = spec.raw_col
            score = row.get(f"{col}__score", 0.0)
            if pd.isna(score) or score < min_score:
                continue

            act = row.get(col)
            exp = row.get(f"{col}__expected")
            dev = row.get(f"{col}__deviation")
            status = row.get(f"{col}__status", "NORMAL")

            if pd.isna(act) or pd.isna(exp):
                continue

            records.append({
                "equipment_id": eq_id,
                "timestamp": ts_str,
                "parameter": spec.display_name,
                "unit": spec.unit,
                "actual": round(float(act), spec.decimals),
                "expected": round(float(exp), spec.decimals),
                "deviation": round(float(dev), spec.decimals),
                "anomaly_score": round(float(score), 2),
                "status": status,
            })

            if len(records) >= max_rows:
                break
        if len(records) >= max_rows:
            break

    # Sort descending by anomaly score so the most critical anomalies appear first
    records.sort(key=lambda r: (r["status"] != "CRITICAL", -r["anomaly_score"]))
    return records


def classify_observation_anomaly(row: pd.Series | dict) -> dict:
    """Classify an observation into one of 6 distinct physical anomaly categories.

    Distinguishes:
      - ⚡ Excess Power Surge (P_act >> P_exp)
      - 📉 Power Meter Drop / Bypass (P_act << P_exp)
      - 🌡️ Condenser Water Overheating (Cooling tower heat rejection issue)
      - 🌊 Excess Water Pumping (Over-pumping hydraulic energy waste)
      - 💧 Hydraulic Flow Restriction (Valve throttle or pump restriction)
      - 🏢 Building Thermal Load Surge (Severe unexpected cooling demand)
    """
    z_en = float(row.get(COL_ROBUST_SCORE, 0.0) or 0.0)
    res_en = float(row.get(COL_RESIDUAL, 0.0) or 0.0)

    z_cw = float(row.get(f"{COL_COOLING_WATER_TEMP}__score", 0.0) or 0.0)
    dev_cw = float(row.get(f"{COL_COOLING_WATER_TEMP}__deviation", 0.0) or 0.0)

    z_flow = float(row.get(f"{COL_CHILLED_WATER_RATE}__score", 0.0) or 0.0)
    dev_flow = float(row.get(f"{COL_CHILLED_WATER_RATE}__deviation", 0.0) or 0.0)

    z_load = float(row.get(f"{COL_BUILDING_LOAD}__score", 0.0) or 0.0)
    dev_load = float(row.get(f"{COL_BUILDING_LOAD}__deviation", 0.0) or 0.0)

    # 1. Primary Energy Deviations (Robust Score >= 3.0)
    if abs(z_en) >= 3.0:
        if res_en > 0:
            return {
                "type": "Excess Power Surge",
                "category": "power_surge",
                "icon": "⚡",
                "parameter": "Energy Consumption",
                "unit": "kWh",
                "actual": round(float(row.get(COL_ENERGY, 0.0)), 1),
                "expected": round(float(row.get(COL_EXPECTED_ENERGY, 0.0)), 1),
                "deviation": round(res_en, 1),
                "anomaly_score": round(abs(z_en), 2),
                "severity": "CRITICAL" if abs(z_en) >= 4.0 else "WARNING",
                "diagnosis": f"Chiller drawing +{res_en:.1f} kWh excess electrical power beyond contextual baseline.",
                "recommendation": "Inspect condenser tube scaling, check refrigerant charge, and verify compressor lift."
            }
        else:
            return {
                "type": "Power Meter Drop / Bypass",
                "category": "power_drop",
                "icon": "📉",
                "parameter": "Energy Consumption",
                "unit": "kWh",
                "actual": round(float(row.get(COL_ENERGY, 0.0)), 1),
                "expected": round(float(row.get(COL_EXPECTED_ENERGY, 0.0)), 1),
                "deviation": round(res_en, 1),
                "anomaly_score": round(abs(z_en), 2),
                "severity": "CRITICAL" if abs(z_en) >= 4.0 else "WARNING",
                "diagnosis": f"Power consumption dropped {res_en:.1f} kWh below expected physical baseline.",
                "recommendation": "Verify power meter current transformer (CT) phase integrity and check unloader valve status."
            }

    # 2. Condenser Water Overheating (Cooling Tower Heat Rejection Issue)
    if z_cw >= 2.8 and dev_cw > 0:
        return {
            "type": "Condenser Water Overheating",
            "category": "condenser",
            "icon": "🌡️",
            "parameter": "Cooling Water Temperature",
            "unit": "°C",
            "actual": round(float(row.get(COL_COOLING_WATER_TEMP, 0.0)), 1),
            "expected": round(float(row.get(f"{COL_COOLING_WATER_TEMP}__expected", 0.0)), 1),
            "deviation": round(dev_cw, 1),
            "anomaly_score": round(z_cw, 2),
            "severity": "CRITICAL" if z_cw >= 3.5 else "WARNING",
            "diagnosis": f"Condenser cooling water temperature +{dev_cw:.1f}°C above seasonal equilibrium.",
            "recommendation": "Check cooling tower fan VFD staging, inspect tower fill nozzles, and test water treatment."
        }

    # 3. Chilled Water Pumping Inefficiencies
    if z_flow >= 2.8:
        if dev_flow > 0:
            return {
                "type": "Excess Water Pumping",
                "category": "pumping",
                "icon": "🌊",
                "parameter": "Chilled Water Rate",
                "unit": "L/s",
                "actual": round(float(row.get(COL_CHILLED_WATER_RATE, 0.0)), 1),
                "expected": round(float(row.get(f"{COL_CHILLED_WATER_RATE}__expected", 0.0)), 1),
                "deviation": round(dev_flow, 1),
                "anomaly_score": round(z_flow, 2),
                "severity": "WARNING",
                "diagnosis": f"Chilled water circulation rate +{dev_flow:.1f} L/s above nominal flow setpoint.",
                "recommendation": "Inspect primary-secondary decoupler bypass and check differential pressure sensor setpoint."
            }
        else:
            return {
                "type": "Hydraulic Flow Restriction",
                "category": "flow_drop",
                "icon": "💧",
                "parameter": "Chilled Water Rate",
                "unit": "L/s",
                "actual": round(float(row.get(COL_CHILLED_WATER_RATE, 0.0)), 1),
                "expected": round(float(row.get(f"{COL_CHILLED_WATER_RATE}__expected", 0.0)), 1),
                "deviation": round(dev_flow, 1),
                "anomaly_score": round(z_flow, 2),
                "severity": "CRITICAL",
                "diagnosis": f"Chilled water circulation dropped {dev_flow:.1f} L/s below normal hydraulic threshold.",
                "recommendation": "Inspect chilled water pump suction strainer, verify isolation valves, and check for air lock."
            }

    # 4. Building Thermal Load Surge
    if z_load >= 2.8 and dev_load > 0:
        return {
            "type": "Building Thermal Load Surge",
            "category": "load_surge",
            "icon": "🏢",
            "parameter": "Building Load",
            "unit": "RT",
            "actual": round(float(row.get(COL_BUILDING_LOAD, 0.0)), 1),
            "expected": round(float(row.get(f"{COL_BUILDING_LOAD}__expected", 0.0)), 1),
            "deviation": round(dev_load, 1),
            "anomaly_score": round(z_load, 2),
            "severity": "WARNING",
            "diagnosis": f"Building thermal demand spiked +{dev_load:.1f} RT above expected schedule.",
            "recommendation": "Verify air handler outside air damper positions and check building occupancy schedule."
        }

    # Default Nominal
    return {
        "type": "Nominal Operation",
        "category": "nominal",
        "icon": "✅",
        "parameter": "System Performance",
        "unit": "kWh",
        "actual": round(float(row.get(COL_ENERGY, 0.0)), 1),
        "expected": round(float(row.get(COL_EXPECTED_ENERGY, 0.0)), 1),
        "deviation": round(res_en, 1),
        "anomaly_score": round(abs(z_en), 2),
        "severity": "NOMINAL",
        "diagnosis": "All parameters operating within expected physical envelope.",
        "recommendation": "Routine monitoring only. No technician intervention required."
    }


def generate_classified_anomalies_table(
    df: pd.DataFrame,
    max_rows: int = 2500,
) -> list[dict]:
    """Generate categorized multi-type anomaly records for the UI table."""
    records = []
    df_sorted = df.sort_values(by=[COL_TIMESTAMP, COL_EQUIPMENT_ID])

    for _, row in df_sorted.iterrows():
        classification = classify_observation_anomaly(row)
        if classification["category"] == "nominal":
            continue

        records.append({
            "equipment_id": str(row[COL_EQUIPMENT_ID]),
            "timestamp": str(row[COL_TIMESTAMP]),
            "anomaly_type": classification["type"],
            "category": classification["category"],
            "icon": classification["icon"],
            "parameter": classification["parameter"],
            "unit": classification["unit"],
            "actual": classification["actual"],
            "expected": classification["expected"],
            "deviation": classification["deviation"],
            "anomaly_score": classification["anomaly_score"],
            "severity": classification["severity"],
            "diagnosis": classification["diagnosis"],
            "recommendation": classification["recommendation"],
        })

        if len(records) >= max_rows:
            break

    # Sort so CRITICAL and highest anomaly scores appear first
    records.sort(key=lambda r: (r["severity"] != "CRITICAL", -r["anomaly_score"]))
    return records

