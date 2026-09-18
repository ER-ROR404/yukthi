"""Preprocessing pipeline with variable-specific imputation and gap detection.

Imputation strategy (NOT one blanket rule):
- Operational sensors: time-aware interpolation per equipment group
- Weather: time-aware interpolation (shared environment)
- Slowly changing (pressure): interpolate + ffill/bfill
- Building load: interpolate per equipment + group median fallback
- Target energy: NEVER fabricate — drop rows with missing target
"""
import logging
from dataclasses import dataclass

import pandas as pd

from src.constants import (
    COL_BUILDING_LOAD,
    COL_ENERGY,
    COL_EQUIPMENT_ID,
    COL_TIMESTAMP,
    FFILL_BFILL_LIMIT,
    GAP_THRESHOLD_MINUTES,
    MAX_INTERPOLATION_GAP,
    OPERATIONAL_SENSOR_COLS,
    WEATHER_INTERPOLATE_COLS,
    WEATHER_FFILL_COLS,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TemporalGap:
    """A detected temporal gap in equipment time series."""

    equipment_id: str
    gap_start: pd.Timestamp
    gap_end: pd.Timestamp
    duration_hours: float


@dataclass(frozen=True)
class GapReport:
    """Summary of all detected temporal gaps."""

    gaps: tuple[TemporalGap, ...]
    total_gaps_per_equipment: dict[str, int]


def preprocess(df: pd.DataFrame) -> tuple[pd.DataFrame, GapReport]:
    """Full preprocessing pipeline. Returns cleaned df and gap report."""
    logger.info("Starting preprocessing pipeline.")

    result = df.sort_values(
        by=[COL_EQUIPMENT_ID, COL_TIMESTAMP],
    ).copy()

    result = _handle_duplicates(result)
    gap_report = _detect_temporal_gaps(result)
    
    # Layer 1: Data Quality (Record what needs imputation)
    result = _flag_missing_data(result)

    # Set timestamp as index for time-based interpolation
    result = result.set_index(COL_TIMESTAMP)

    result = _impute_operational_sensors(result)
    result = _impute_weather(result)
    result = _impute_slowly_changing(result)
    result = _impute_building_load(result)

    result = result.reset_index()

    # Layer 2: Sensor Health (Range checks and rate-of-change)
    result = _check_sensor_health(result)

    result = _drop_missing_target(result)

    remaining_missing = result.drop(
        columns=[COL_ENERGY], errors="ignore",
    ).isna().sum().sum()
    logger.info(
        "Preprocessing complete. Remaining missing values in features: %d",
        remaining_missing,
    )

    return result, gap_report

def _flag_missing_data(df: pd.DataFrame) -> pd.DataFrame:
    """Flag rows where data was missing before imputation."""
    result = df.copy()
    check_cols = OPERATIONAL_SENSOR_COLS + WEATHER_INTERPOLATE_COLS + WEATHER_FFILL_COLS
    available_cols = [c for c in check_cols if c in result.columns]
    
    # Flag if any of the key features are NaN
    result['was_imputed'] = result[available_cols].isna().any(axis=1).astype(int)
    return result

def _check_sensor_health(df: pd.DataFrame) -> pd.DataFrame:
    """Flag suspicious sensor readings based on physical constraints, rate of change, and stuck sensors."""
    result = df.copy()
    suspicious = pd.Series(False, index=result.index)
    
    # 1. Range checks
    if COL_BUILDING_LOAD in result.columns:
        suspicious |= (result[COL_BUILDING_LOAD] < 0)
    if 'Humidity (%)' in result.columns:
        suspicious |= (result['Humidity (%)'] < 0) | (result['Humidity (%)'] > 100)
        
    # Process per equipment for time-series checks
    if COL_EQUIPMENT_ID in result.columns and COL_TIMESTAMP in result.columns:
        result_sorted = result.sort_values(by=[COL_EQUIPMENT_ID, COL_TIMESTAMP])
        
        for eq_id, group in result_sorted.groupby(COL_EQUIPMENT_ID):
            idx = group.index
            
            # 2. Rate of change (e.g., Flow shouldn't drop 80% in 30 mins)
            if 'Chilled Water Rate (L/sec)' in group.columns:
                flow_diff_pct = group['Chilled Water Rate (L/sec)'].pct_change(fill_method=None).abs()
                # Flag if flow changes by more than 50% in one step (and wasn't near zero to begin with)
                suspicious.loc[idx] |= (flow_diff_pct > 0.5) & (group['Chilled Water Rate (L/sec)'].shift(1) > 5)
                
            # 3. Stuck sensor (e.g., Temperature exactly the same for 10+ readings / 5 hours)
            if 'Outside Temperature (F)' in group.columns:
                rolling_std = group['Outside Temperature (F)'].rolling(window=10).std()
                suspicious.loc[idx] |= (rolling_std == 0)
                
    result['sensor_health_suspicious'] = suspicious.astype(int)
    return result


def _handle_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate (equipment_id, timestamp) pairs, keep first."""
    orig_len = len(df)
    result = df.drop_duplicates(
        subset=[COL_EQUIPMENT_ID, COL_TIMESTAMP], keep="first",
    )
    dropped = orig_len - len(result)
    if dropped > 0:
        logger.info("Dropped %d duplicate records.", dropped)
    return result


def _detect_temporal_gaps(df: pd.DataFrame) -> GapReport:
    """Detect gaps > GAP_THRESHOLD_MINUTES per equipment."""
    gaps: list[TemporalGap] = []
    total_gaps: dict[str, int] = {}
    threshold = pd.Timedelta(minutes=GAP_THRESHOLD_MINUTES)

    for eq_id, group in df.groupby(COL_EQUIPMENT_ID):
        group_sorted = group.sort_values(by=COL_TIMESTAMP)
        diffs = group_sorted[COL_TIMESTAMP].diff()
        gap_mask = diffs > threshold
        eq_gaps = 0

        for idx in gap_mask[gap_mask].index:
            gap_end = group_sorted.loc[idx, COL_TIMESTAMP]
            gap_start = gap_end - diffs.loc[idx]
            duration_hrs = diffs.loc[idx].total_seconds() / 3600.0

            gaps.append(
                TemporalGap(
                    equipment_id=str(eq_id),
                    gap_start=pd.Timestamp(gap_start),
                    gap_end=pd.Timestamp(gap_end),
                    duration_hours=duration_hrs,
                )
            )
            eq_gaps += 1

        total_gaps[str(eq_id)] = eq_gaps

    logger.info(
        "Temporal gap detection: %d gaps found across %d equipment units.",
        len(gaps), len(total_gaps),
    )
    return GapReport(gaps=tuple(gaps), total_gaps_per_equipment=total_gaps)


def _impute_operational_sensors(df: pd.DataFrame) -> pd.DataFrame:
    """Time-aware interpolation for operational sensors per equipment."""
    logger.info("Imputing operational sensors.")
    result = df.copy()
    for col in OPERATIONAL_SENSOR_COLS:
        if col in result.columns:
            result[col] = result.groupby(COL_EQUIPMENT_ID)[col].transform(
                lambda x: x.interpolate(
                    method="time", limit=MAX_INTERPOLATION_GAP,
                )
            )
    return result


def _impute_weather(df: pd.DataFrame) -> pd.DataFrame:
    """Time-aware interpolation for continuous weather columns."""
    logger.info("Imputing weather columns.")
    result = df.copy()
    for col in WEATHER_INTERPOLATE_COLS:
        if col in result.columns:
            result[col] = result[col].interpolate(
                method="time", limit=MAX_INTERPOLATION_GAP,
            )
    return result


def _impute_slowly_changing(df: pd.DataFrame) -> pd.DataFrame:
    """Forward/backward fill for slowly changing weather variables."""
    logger.info("Imputing slowly changing columns.")
    result = df.copy()
    for col in WEATHER_FFILL_COLS:
        if col in result.columns:
            result[col] = result[col].ffill(
                limit=FFILL_BFILL_LIMIT,
            ).bfill(limit=FFILL_BFILL_LIMIT)
    return result


def _impute_building_load(df: pd.DataFrame) -> pd.DataFrame:
    """Interpolate per equipment, then equipment-group median fallback."""
    logger.info("Imputing building load.")
    result = df.copy()
    if COL_BUILDING_LOAD in result.columns:
        result[COL_BUILDING_LOAD] = result.groupby(
            COL_EQUIPMENT_ID,
        )[COL_BUILDING_LOAD].transform(
            lambda x: x.interpolate(
                method="time", limit=MAX_INTERPOLATION_GAP,
            )
        )
        group_medians = result.groupby(
            COL_EQUIPMENT_ID,
        )[COL_BUILDING_LOAD].transform("median")
        result[COL_BUILDING_LOAD] = result[COL_BUILDING_LOAD].fillna(
            group_medians,
        )
    return result


def _drop_missing_target(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows where target energy is missing. NEVER fabricate."""
    result = df.copy()
    if COL_ENERGY in result.columns:
        orig_len = len(result)
        result = result.dropna(subset=[COL_ENERGY])
        dropped = orig_len - len(result)
        if dropped > 0:
            logger.info(
                "Dropped %d rows with missing target (%s). "
                "Target values are NEVER fabricated.",
                dropped, COL_ENERGY,
            )
    return result
