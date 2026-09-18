"""Streaming ChillerStateStore for one-record-at-a-time replay.

Maintains chronological equipment buffer in memory to calculate
gap-safe lag, rolling 2h mean, and envelope flags without requiring
the full historical dataset during inference.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Final, Any
import numpy as np
import pandas as pd
from catboost import CatBoostRegressor

from src.constants import (
    COL_TIMESTAMP,
    COL_EQUIPMENT_ID,
    COL_BUILDING_LOAD,
    COL_CHILLED_WATER_RATE,
    COL_COOLING_WATER_TEMP,
    COL_OUTSIDE_TEMP,
    COL_DEW_POINT,
    COL_HUMIDITY,
    COL_WIND_SPEED,
    COL_PRESSURE,
    FEAT_HOUR_OF_DAY,
    FEAT_DAY_OF_WEEK,
    FEAT_IS_WEEKEND,
    FEAT_IS_NIGHT,
    FEAT_WET_BULB,
    FEAT_HOUR_SIN,
    FEAT_HOUR_COS,
    FEAT_DAY_SIN,
    FEAT_DAY_COS,
    FEAT_LOAD_FLOW_RATIO,
    FEAT_OUT_OF_ENVELOPE,
    FEAT_LOAD_LAG_30M,
    FEAT_LOAD_ROLLING_2H_MEAN,
    FEAT_WAS_IMPUTED,
    FEAT_SENSOR_SUSPICIOUS,
    FEATURE_COLS,
)
from src.envelope import load_operating_envelope


@dataclass
class EquipmentBuffer:
    """Rolling state for a single equipment unit."""
    last_timestamp: datetime | None = None
    last_load: float | None = None
    recent_loads: list[float] = field(default_factory=list)  # up to 4 previous loads


class ChillerStateStore:
    """Stateful stream processor for online / replay inference."""

    def __init__(self, model: CatBoostRegressor | None = None) -> None:
        self.model = model
        self.buffers: dict[str, EquipmentBuffer] = {}
        self.envelope_bounds = load_operating_envelope()

    def process_record(self, record: dict[str, Any]) -> dict[str, Any]:
        """Process a single observation dictionary and return features + prediction."""
        rec = dict(record)
        eq_id = str(rec[COL_EQUIPMENT_ID])
        ts = pd.to_datetime(rec[COL_TIMESTAMP])

        if eq_id not in self.buffers:
            self.buffers[eq_id] = EquipmentBuffer()
        buf = self.buffers[eq_id]

        # 1. Elapsed time & temporal lag features
        if buf.last_timestamp is not None:
            elapsed_minutes = (ts - buf.last_timestamp).total_seconds() / 60.0
        else:
            elapsed_minutes = np.nan

        rec["elapsed_minutes"] = elapsed_minutes
        valid_lag = (
            not np.isnan(elapsed_minutes)
            and (0.0 <= elapsed_minutes <= 90.0)
        )

        if valid_lag and buf.last_load is not None:
            rec[FEAT_LOAD_LAG_30M] = float(buf.last_load)
            # Rolling 2h mean over up to 4 prior observations
            rec[FEAT_LOAD_ROLLING_2H_MEAN] = float(np.mean(buf.recent_loads))
        else:
            rec[FEAT_LOAD_LAG_30M] = np.nan
            rec[FEAT_LOAD_ROLLING_2H_MEAN] = np.nan

        # 2. Time/Calendar features
        rec[FEAT_HOUR_OF_DAY] = int(ts.hour)
        rec[FEAT_DAY_OF_WEEK] = int(ts.dayofweek)
        rec[FEAT_IS_WEEKEND] = int(ts.dayofweek in [5, 6])
        rec[FEAT_IS_NIGHT] = int(ts.hour < 6 or ts.hour >= 22)

        hour_rad = 2.0 * np.pi * ts.hour / 24.0
        rec[FEAT_HOUR_SIN] = float(np.sin(hour_rad))
        rec[FEAT_HOUR_COS] = float(np.cos(hour_rad))

        day_rad = 2.0 * np.pi * ts.dayofweek / 7.0
        rec[FEAT_DAY_SIN] = float(np.sin(day_rad))
        rec[FEAT_DAY_COS] = float(np.cos(day_rad))

        # 3. Wet-bulb (Stull 2011)
        temp_f = float(rec[COL_OUTSIDE_TEMP])
        hum = float(rec[COL_HUMIDITY])
        temp_c = (temp_f - 32.0) * (5.0 / 9.0)
        rec[FEAT_WET_BULB] = float(
            temp_c * np.arctan(0.151977 * np.sqrt(hum + 8.313659))
            + np.arctan(temp_c + hum)
            - np.arctan(hum - 1.676331)
            + 0.00391838 * (hum ** 1.5) * np.arctan(0.023101 * hum)
            - 4.686035
        )

        # 4. Interaction
        load = float(rec[COL_BUILDING_LOAD])
        flow = float(rec[COL_CHILLED_WATER_RATE])
        rec[FEAT_LOAD_FLOW_RATIO] = float(load / (flow + 1e-5))

        # 5. Operating Envelope
        out_of_envelope = 0
        for col, (q_low, q_high) in self.envelope_bounds.items():
            val = rec.get(col)
            if val is not None and not np.isnan(val):
                if val < q_low or val > q_high:
                    out_of_envelope = 1
                    break
        rec[FEAT_OUT_OF_ENVELOPE] = out_of_envelope

        # Flags (defaults if not provided)
        if FEAT_WAS_IMPUTED not in rec:
            rec[FEAT_WAS_IMPUTED] = 0
        if FEAT_SENSOR_SUSPICIOUS not in rec:
            rec[FEAT_SENSOR_SUSPICIOUS] = 0

        # 6. Model Prediction
        if self.model is not None:
            # Build 1-row DataFrame strictly ordered by FEATURE_COLS
            feature_row = pd.DataFrame([{col: rec.get(col, np.nan) for col in FEATURE_COLS}])
            expected_energy = float(self.model.predict(feature_row)[0])
            rec["expected_energy"] = expected_energy
            if "Chiller Energy Consumption (kWh)" in rec:
                rec["residual"] = float(rec["Chiller Energy Consumption (kWh)"]) - expected_energy

        # 7. Update state buffer for this equipment
        buf.last_timestamp = ts
        buf.last_load = load
        buf.recent_loads.append(load)
        if len(buf.recent_loads) > 4:
            buf.recent_loads.pop(0)

        return rec
