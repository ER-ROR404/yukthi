"""Data loader with schema validation and audit reporting.

Loads the chiller CSV, validates all 11 expected columns,
parses timestamps, and logs a data quality audit summary.
"""
import logging
from pathlib import Path

import pandas as pd

from src.constants import COL_EQUIPMENT_ID, COL_TIMESTAMP, EXPECTED_COLUMNS
from src.exceptions import DataQualityError, SchemaValidationError

logger = logging.getLogger(__name__)


def load_and_validate(filepath: Path) -> pd.DataFrame:
    """Load CSV, validate schema, parse timestamps, return sorted DataFrame."""
    logger.info("Loading data from %s", filepath)
    df = pd.read_csv(filepath)

    _validate_schema(df)
    df = _parse_timestamps(df)

    df = df.sort_values(
        by=[COL_EQUIPMENT_ID, COL_TIMESTAMP],
    ).reset_index(drop=True)

    duplicates = _check_duplicates(df)
    if duplicates > 0:
        logger.warning(
            "Found %d duplicate (equipment_id, timestamp) pairs.",
            duplicates,
        )

    _log_audit_summary(df)
    return df


def _validate_schema(df: pd.DataFrame) -> None:
    """Raise SchemaValidationError if required columns are missing."""
    if df.empty:
        raise SchemaValidationError("CSV file is empty or has no columns.")

    missing = [col for col in EXPECTED_COLUMNS if col not in df.columns]
    if missing:
        raise SchemaValidationError(
            f"Missing required columns: {missing}"
        )


def _parse_timestamps(df: pd.DataFrame) -> pd.DataFrame:
    """Parse timestamp column, drop rows with unparseable timestamps."""
    result = df.copy()
    result[COL_TIMESTAMP] = pd.to_datetime(
        result[COL_TIMESTAMP], errors="coerce",
    )

    unparseable = int(result[COL_TIMESTAMP].isna().sum())
    if unparseable > 0:
        logger.warning(
            "Dropping %d rows with unparseable timestamps.", unparseable,
        )
        result = result.dropna(subset=[COL_TIMESTAMP])

    if result.empty:
        raise DataQualityError(
            "All timestamps were unparseable. DataFrame is empty."
        )

    return result


def _check_duplicates(df: pd.DataFrame) -> int:
    """Return count of duplicate (equipment_id, timestamp) pairs."""
    return int(
        df.duplicated(subset=[COL_EQUIPMENT_ID, COL_TIMESTAMP]).sum()
    )


def _log_audit_summary(df: pd.DataFrame) -> None:
    """Log dataset shape, equipment IDs, date range, missing values."""
    logger.info("Dataset shape: %s", df.shape)

    equipment_ids = df[COL_EQUIPMENT_ID].unique().tolist()
    logger.info("Equipment IDs found: %s", equipment_ids)

    if not df.empty:
        min_date = df[COL_TIMESTAMP].min()
        max_date = df[COL_TIMESTAMP].max()
        logger.info("Date range: %s to %s", min_date, max_date)

    missing_counts = {
        col: int(count)
        for col, count in df.isna().sum().items()
        if count > 0
    }
    if missing_counts:
        logger.info("Missing values: %s", missing_counts)
    else:
        logger.info("No missing values detected.")
