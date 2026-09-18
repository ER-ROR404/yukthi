"""Operating envelope computation and persistence.

Computes 1st and 99th percentile bounds ONLY from training data (no future leakage).
Saves to models/operating_envelope.json for production inference.
"""
import json
import logging
from pathlib import Path
from typing import Final

import pandas as pd

from src.constants import (
    COL_BUILDING_LOAD,
    COL_CHILLED_WATER_RATE,
    COL_COOLING_WATER_TEMP,
    COL_OUTSIDE_TEMP,
)

logger = logging.getLogger(__name__)

DEFAULT_ENVELOPE_PATH: Final[Path] = Path("models/operating_envelope.json")

ENVELOPE_COLUMNS: Final[list[str]] = [
    COL_OUTSIDE_TEMP,
    COL_BUILDING_LOAD,
    COL_CHILLED_WATER_RATE,
    COL_COOLING_WATER_TEMP,
]

# Calibrated fallback bounds from training dataset (1st - 99th percentiles)
FALLBACK_ENVELOPE_BOUNDS: Final[dict[str, tuple[float, float]]] = {
    COL_OUTSIDE_TEMP: (77.0, 91.0),
    COL_BUILDING_LOAD: (370.0, 745.0),
    COL_CHILLED_WATER_RATE: (75.0, 131.0),
    COL_COOLING_WATER_TEMP: (28.0, 34.0),
}


def compute_operating_envelope(
    train_df: pd.DataFrame,
    columns: list[str] = ENVELOPE_COLUMNS,
    lower_quantile: float = 0.01,
    upper_quantile: float = 0.99,
    save_path: Path | None = DEFAULT_ENVELOPE_PATH,
) -> dict[str, tuple[float, float]]:
    """Compute operating envelope percentiles strictly on training data."""
    envelope = {}
    for col in columns:
        if col in train_df.columns:
            valid_vals = train_df[col].dropna()
            q_low = float(valid_vals.quantile(lower_quantile))
            q_high = float(valid_vals.quantile(upper_quantile))
            envelope[col] = (round(q_low, 2), round(q_high, 2))

    if save_path:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "metadata": {
                "lower_quantile": lower_quantile,
                "upper_quantile": upper_quantile,
                "train_rows": len(train_df),
                "generated_from": "training_data_only",
            },
            "bounds": {k: {"lower": v[0], "upper": v[1]} for k, v in envelope.items()},
        }
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        logger.info("Saved operating envelope artifact to %s", save_path)

    return envelope


def load_operating_envelope(
    path: Path = DEFAULT_ENVELOPE_PATH,
) -> dict[str, tuple[float, float]]:
    """Load operating envelope from JSON artifact; fallback to constants if missing."""
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            bounds = data.get("bounds", {})
            return {
                k: (float(v["lower"]), float(v["upper"]))
                for k, v in bounds.items()
            }
        except Exception as e:
            logger.warning("Could not read envelope from %s (%s). Using fallbacks.", path, e)
    return FALLBACK_ENVELOPE_BOUNDS
