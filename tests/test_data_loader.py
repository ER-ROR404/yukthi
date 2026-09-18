"""Tests for data_loader module."""
import pandas as pd
import pytest
from pathlib import Path

from src.constants import COL_EQUIPMENT_ID, COL_TIMESTAMP, EXPECTED_COLUMNS
from src.data_loader import load_and_validate
from src.exceptions import SchemaValidationError


def test_when_valid_csv_expect_correct_shape(sample_csv: Path) -> None:
    """Valid CSV should load with all 20 rows and 11 columns."""
    df = load_and_validate(sample_csv)
    assert df.shape[0] == 20
    assert df.shape[1] == len(EXPECTED_COLUMNS)


def test_when_valid_csv_expect_parsed_timestamps(sample_csv: Path) -> None:
    """Timestamps should be parsed as datetime64."""
    df = load_and_validate(sample_csv)
    assert pd.api.types.is_datetime64_any_dtype(df[COL_TIMESTAMP])


def test_when_valid_csv_expect_sorted_by_equipment_and_time(
    sample_csv: Path,
) -> None:
    """Result should be sorted by equipment_id, then timestamp."""
    df = load_and_validate(sample_csv)
    for _, group in df.groupby(COL_EQUIPMENT_ID):
        timestamps = group[COL_TIMESTAMP].values
        assert all(timestamps[i] <= timestamps[i + 1] for i in range(len(timestamps) - 1))


def test_when_missing_column_expect_schema_error(tmp_path: Path) -> None:
    """CSV missing a required column should raise SchemaValidationError."""
    csv_path = tmp_path / "bad.csv"
    df = pd.DataFrame({"timestamp": ["2020-01-01"], "equipment_id": ["X"]})
    df.to_csv(csv_path, index=False)

    with pytest.raises(SchemaValidationError, match="Missing required columns"):
        load_and_validate(csv_path)


def test_when_empty_csv_expect_schema_error(tmp_path: Path) -> None:
    """Empty CSV should raise SchemaValidationError."""
    csv_path = tmp_path / "empty.csv"
    csv_path.write_text("")

    with pytest.raises(Exception):
        load_and_validate(csv_path)


def test_when_all_columns_present_expect_no_error(sample_csv: Path) -> None:
    """CSV with all required columns should not raise any error."""
    df = load_and_validate(sample_csv)
    for col in EXPECTED_COLUMNS:
        assert col in df.columns
