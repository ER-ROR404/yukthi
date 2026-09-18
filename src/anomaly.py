"""Anomaly detection via robust residual scoring and Isolation Forest.

Three-stage architecture:
  Stage 1: Robust Residual Score (Median + MAD)
  Stage 2: Context/equipment-aware scoring using Isolation Forest
  Stage 3: Persistence grouping — consecutive anomaly flags become single events

Output is described as abnormal behaviour requiring investigation,
NOT a confirmed mechanical fault.
"""
import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from src.constants import (
    COL_ANOMALY_FLAG,
    COL_ANOMALY_SCORE,
    COL_EQUIPMENT_ID,
    COL_EVENT_ID,
    COL_EXPECTED_ENERGY,
    COL_RESIDUAL,
    COL_ROBUST_SCORE,
    COL_ROLLING_MAD_RESIDUAL,
    COL_ROLLING_MEDIAN_RESIDUAL,
    COL_TIMESTAMP,
    ISOLATION_FOREST_CONTAMINATION,
    ISOLATION_FOREST_RANDOM_STATE,
    MIN_ROLLING_PERIODS,
    ROLLING_WINDOW,
)

logger = logging.getLogger(__name__)

# Minimum MAD to prevent division by zero in robust score
_MIN_MAD: float = 1e-6


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
    max_robust_score: float
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
            f"Max |robust|: {self.max_robust_score:.2f}\n"
            f"  Status: INVESTIGATE — "
            f"Repeated contextual energy deviation"
        )


def _compute_robust_residual_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Compute rolling median and MAD of residuals per equipment.

    Uses time-based rolling window to handle irregular sampling correctly.
    """
    result = df.copy()
    result[COL_ROLLING_MEDIAN_RESIDUAL] = np.nan
    result[COL_ROLLING_MAD_RESIDUAL] = np.nan
    result[COL_ROBUST_SCORE] = np.nan

    for _, group in result.groupby(COL_EQUIPMENT_ID):
        indexed = group.set_index(COL_TIMESTAMP)
        
        # Calculate rolling median
        rolling_median = indexed[COL_RESIDUAL].rolling(
            ROLLING_WINDOW, min_periods=MIN_ROLLING_PERIODS
        ).median()
        
        # Calculate absolute deviations from the rolling median
        abs_deviation = (indexed[COL_RESIDUAL] - rolling_median).abs()
        
        # Calculate rolling MAD
        rolling_mad = abs_deviation.rolling(
            ROLLING_WINDOW, min_periods=MIN_ROLLING_PERIODS
        ).median()

        # Shift to exclude current observation from its own baseline
        shifted_median = rolling_median.shift(1).values
        shifted_mad = rolling_mad.shift(1).values

        result.loc[group.index, COL_ROLLING_MEDIAN_RESIDUAL] = shifted_median
        result.loc[group.index, COL_ROLLING_MAD_RESIDUAL] = shifted_mad
        
        mad_safe = np.clip(shifted_mad, a_min=_MIN_MAD, a_max=None)
        
        # Calculate Robust Score: (x - median) / (1.4826 * mad)
        robust_score = (group[COL_RESIDUAL] - shifted_median) / (1.4826 * mad_safe)
        result.loc[group.index, COL_ROBUST_SCORE] = robust_score

    return result


def _flag_anomalies_isolation_forest(df: pd.DataFrame) -> pd.DataFrame:
    """Flag anomalies using Isolation Forest on contextual features."""
    result = df.copy()
    
    # Select features for Isolation Forest
    features = [
        COL_ROBUST_SCORE,
        COL_RESIDUAL,
        COL_EXPECTED_ENERGY,
        COL_ROLLING_MEDIAN_RESIDUAL
    ]
    
    # Drop rows with NaNs (from rolling windows)
    valid_mask = result[features].notna().all(axis=1)
    
    # Default to non-anomalous
    result[COL_ANOMALY_FLAG] = 0
    result[COL_ANOMALY_SCORE] = 0.0
    
    if not valid_mask.any():
        return result

    X = result.loc[valid_mask, features].copy()
    
    # Add equipment ID as one-hot for context awareness
    equip_dummies = pd.get_dummies(result.loc[valid_mask, COL_EQUIPMENT_ID], prefix='equip')
    X = pd.concat([X, equip_dummies], axis=1)

    # Scale numerical features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train Isolation Forest
    clf = IsolationForest(
        contamination=ISOLATION_FOREST_CONTAMINATION,
        random_state=ISOLATION_FOREST_RANDOM_STATE,
        n_jobs=-1
    )
    
    preds = clf.fit_predict(X_scaled)
    scores = clf.decision_function(X_scaled)
    
    # IsolationForest returns -1 for outliers and 1 for inliers
    is_outlier = (preds == -1)
    
    # Enforce a minimum robust score to prevent IF from flagging minor variance
    # A robust score of 3.0 means the residual is 3 MADs away from median
    is_significant = X[COL_ROBUST_SCORE].abs() > 3.0
    
    result.loc[valid_mask, COL_ANOMALY_FLAG] = (is_outlier & is_significant).astype(int)
    # Convert scores to a positive anomaly score where higher = more anomalous
    result.loc[valid_mask, COL_ANOMALY_SCORE] = -scores

    anomaly_count = result[COL_ANOMALY_FLAG].sum()
    total_count = len(result)
    logger.info(
        "Isolation Forest Anomaly flags: %d / %d (%.2f%%)",
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
        max_robust_score=float(event_rows[COL_ROBUST_SCORE].abs().max()),
        observation_count=len(event_rows),
    )


def score_anomalies(df: pd.DataFrame) -> tuple[pd.DataFrame, list[AnomalyEvent]]:
    """Full anomaly scoring pipeline.

    1. Compute robust rolling residual statistics (Median + MAD)
    2. Score anomalies contextually using Isolation Forest
    3. Group persistent anomalies into events

    Returns:
        Tuple of (DataFrame with anomaly columns, list of AnomalyEvents)
    """
    if COL_RESIDUAL not in df.columns:
        raise ValueError(
            f"Column '{COL_RESIDUAL}' required. "
            "Run predict_expected_energy first."
        )

    result = _compute_robust_residual_stats(df)
    result = _flag_anomalies_isolation_forest(result)
    result, events = _group_persistent_events(result)

    return result, events
