"""Anomaly detection via dynamic residual scoring and persistence grouping.

Two-stage architecture:
  Stage 1: Dynamic z-score on rolling residual (per equipment, time-based window)
  Stage 2: Persistence grouping — consecutive anomaly flags become single events

Output is described as abnormal behaviour requiring investigation,
NOT a confirmed mechanical fault.
"""
import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.constants import (
    ANOMALY_Z_THRESHOLD,
    COL_ANOMALY_FLAG,
    COL_EQUIPMENT_ID,
    COL_EVENT_ID,
    COL_EXPECTED_ENERGY,
    COL_RESIDUAL,
    COL_ROLLING_MEAN_RESIDUAL,
    COL_ROLLING_STD_RESIDUAL,
    COL_TIMESTAMP,
    COL_Z_SCORE,
    MIN_ROLLING_PERIODS,
    ROLLING_WINDOW,
)

logger = logging.getLogger(__name__)

# Minimum std to prevent division by zero in z-score
_MIN_STD: float = 1e-6


@dataclass(frozen=True)
class AnomalyEvent:
    """A grouped persistent anomaly event."""

    event_id: int
    equipment_id: str
    start_time: pd.Timestamp
    end_time: pd.Timestamp
    duration_minutes: float
    max_residual: float
    mean_residual: float
    max_z_score: float
    observation_count: int

    def describe(self) -> str:
        """Return human-readable event description."""
        return (
            f"Event #{self.event_id}: {self.equipment_id}, "
            f"{self.start_time} → {self.end_time} "
            f"({self.duration_minutes:.0f} min, "
            f"{self.observation_count} obs)\n"
            f"  Max deviation: {self.max_residual:+.1f} kWh, "
            f"Mean: {self.mean_residual:+.1f} kWh, "
            f"Max |z|: {self.max_z_score:.2f}\n"
            f"  Status: INVESTIGATE — "
            f"Repeated contextual energy deviation"
        )


def _compute_rolling_residual_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Compute rolling mean/std of residuals per equipment (2h window).

    Uses time-based rolling window to handle irregular sampling correctly.
    """
    result = df.copy()
    result[COL_ROLLING_MEAN_RESIDUAL] = np.nan
    result[COL_ROLLING_STD_RESIDUAL] = np.nan

    for _, group in result.groupby(COL_EQUIPMENT_ID):
        indexed = group.set_index(COL_TIMESTAMP)
        rolling = indexed[COL_RESIDUAL].rolling(
            ROLLING_WINDOW, min_periods=MIN_ROLLING_PERIODS,
        )
        # .shift(1) excludes current observation from its own baseline,
        # preventing a spike from inflating its own rolling std
        result.loc[group.index, COL_ROLLING_MEAN_RESIDUAL] = (
            rolling.mean().shift(1).values
        )
        result.loc[group.index, COL_ROLLING_STD_RESIDUAL] = (
            rolling.std().shift(1).values
        )

    return result


def _compute_z_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Compute z-score of residual relative to rolling statistics."""
    result = df.copy()
    std_safe = result[COL_ROLLING_STD_RESIDUAL].clip(lower=_MIN_STD)
    result[COL_Z_SCORE] = (
        (result[COL_RESIDUAL] - result[COL_ROLLING_MEAN_RESIDUAL])
        / std_safe
    )
    return result


def _flag_anomalies(
    df: pd.DataFrame,
    threshold: float = ANOMALY_Z_THRESHOLD,
) -> pd.DataFrame:
    """Flag observations where |z_score| exceeds threshold."""
    result = df.copy()
    result[COL_ANOMALY_FLAG] = (
        result[COL_Z_SCORE].abs() > threshold
    ).astype(int)

    # NaN z-scores (insufficient rolling window data) → not anomalous
    result.loc[result[COL_Z_SCORE].isna(), COL_ANOMALY_FLAG] = 0

    anomaly_count = result[COL_ANOMALY_FLAG].sum()
    total_count = len(result)
    logger.info(
        "Anomaly flags: %d / %d (%.2f%%)",
        anomaly_count, total_count,
        anomaly_count / max(total_count, 1) * 100,
    )
    return result


def _group_persistent_events(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, list[AnomalyEvent]]:
    """Group consecutive anomaly flags into persistent events per equipment.

    Reduces alert noise by consolidating e.g. three consecutive
    30-min anomaly flags into one event spanning 10:30–11:30.
    """
    result = df.copy()
    result[COL_EVENT_ID] = 0
    events: list[AnomalyEvent] = []
    event_counter = 0

    for eid, group in result.groupby(COL_EQUIPMENT_ID):
        group_sorted = group.sort_values(COL_TIMESTAMP)
        flags = group_sorted[COL_ANOMALY_FLAG].values
        indices = group_sorted.index.values
        timestamps = group_sorted[COL_TIMESTAMP].values

        in_event = False
        event_start_idx = 0

        for i, flag in enumerate(flags):
            if flag == 1 and not in_event:
                in_event = True
                event_start_idx = i
            elif flag == 0 and in_event:
                in_event = False
                event_counter += 1
                event = _build_event(
                    event_counter, str(eid),
                    group_sorted.iloc[event_start_idx:i],
                )
                events.append(event)
                result.loc[
                    indices[event_start_idx:i], COL_EVENT_ID
                ] = event_counter

        # Handle event that extends to end of series
        if in_event:
            event_counter += 1
            event = _build_event(
                event_counter, str(eid),
                group_sorted.iloc[event_start_idx:],
            )
            events.append(event)
            result.loc[
                indices[event_start_idx:], COL_EVENT_ID
            ] = event_counter

    logger.info(
        "Persistence grouping: %d anomaly flags → %d events",
        int(result[COL_ANOMALY_FLAG].sum()), len(events),
    )
    return result, events


def _build_event(
    event_id: int,
    equipment_id: str,
    event_rows: pd.DataFrame,
) -> AnomalyEvent:
    """Construct an AnomalyEvent from a slice of flagged rows."""
    start = pd.Timestamp(event_rows[COL_TIMESTAMP].iloc[0])
    end = pd.Timestamp(event_rows[COL_TIMESTAMP].iloc[-1])
    duration = (end - start).total_seconds() / 60.0

    return AnomalyEvent(
        event_id=event_id,
        equipment_id=equipment_id,
        start_time=start,
        end_time=end,
        duration_minutes=duration,
        max_residual=float(event_rows[COL_RESIDUAL].max()),
        mean_residual=float(event_rows[COL_RESIDUAL].mean()),
        max_z_score=float(event_rows[COL_Z_SCORE].abs().max()),
        observation_count=len(event_rows),
    )


def score_anomalies(
    df: pd.DataFrame,
    threshold: float = ANOMALY_Z_THRESHOLD,
) -> tuple[pd.DataFrame, list[AnomalyEvent]]:
    """Full anomaly scoring pipeline.

    1. Compute rolling residual statistics per equipment
    2. Compute z-scores
    3. Flag anomalies above threshold
    4. Group persistent anomalies into events

    Returns:
        Tuple of (DataFrame with anomaly columns, list of AnomalyEvents)
    """
    if COL_RESIDUAL not in df.columns:
        raise ValueError(
            f"Column '{COL_RESIDUAL}' required. "
            "Run predict_expected_energy first."
        )

    result = _compute_rolling_residual_stats(df)
    result = _compute_z_scores(result)
    result = _flag_anomalies(result, threshold=threshold)
    result, events = _group_persistent_events(result)

    return result, events
