"""Load and validate the Zomato dataset from Hugging Face."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from .config import HF_DATASET_ID, HF_SPLIT, OPTIONAL_RAW_COLUMNS, REQUIRED_RAW_COLUMNS
from .exceptions import DatasetLoadError, EmptyDatasetError, SchemaValidationError

logger = logging.getLogger(__name__)


def validate_schema(columns: list[str] | pd.Index) -> None:
    """Reject load when required columns are missing (DI-03, DI-13)."""
    column_set = set(columns)
    missing = [col for col in REQUIRED_RAW_COLUMNS if col not in column_set]
    if missing:
        raise SchemaValidationError(
            "Dataset schema validation failed. Missing required columns: "
            + ", ".join(missing)
        )


def load_raw_dataset(
    dataset_id: str = HF_DATASET_ID,
    split: str = HF_SPLIT,
) -> pd.DataFrame:
    """
    Load the raw Hugging Face dataset into a DataFrame.

    Raises:
        DatasetLoadError: network / download / library failures (DI-01)
        EmptyDatasetError: zero rows (DI-02)
        SchemaValidationError: missing required fields (DI-03, DI-13)
    """
    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise DatasetLoadError(
            "Missing dependency 'datasets'. Install phase1 requirements first."
        ) from exc

    try:
        logger.info("Loading dataset '%s' (split=%s)...", dataset_id, split)
        dataset = load_dataset(dataset_id, split=split)
    except Exception as exc:  # noqa: BLE001 - surface any HF/network failure
        raise DatasetLoadError(
            f"Failed to load dataset '{dataset_id}'. "
            "Check network access and the Hugging Face dataset ID."
        ) from exc

    if dataset is None or len(dataset) == 0:
        raise EmptyDatasetError("No restaurant data available (dataset is empty).")

    validate_schema(dataset.column_names)

    keep_columns = [
        col
        for col in (*REQUIRED_RAW_COLUMNS, *OPTIONAL_RAW_COLUMNS)
        if col in dataset.column_names
    ]
    frame = dataset.select_columns(keep_columns).to_pandas()

    if frame.empty:
        raise EmptyDatasetError("No restaurant data available (dataset is empty).")

    logger.info("Loaded %s raw rows with columns: %s", len(frame), list(frame.columns))
    return frame


def summarize_raw(frame: pd.DataFrame) -> dict[str, Any]:
    """Small diagnostic summary for CLI / logging."""
    return {
        "rows": int(len(frame)),
        "columns": list(frame.columns),
        "null_name": int(frame["name"].isna().sum()) if "name" in frame else None,
        "null_location": int(frame["location"].isna().sum()) if "location" in frame else None,
        "null_rate": int(frame["rate"].isna().sum()) if "rate" in frame else None,
    }
