"""Phase 1 orchestration: Loader -> Preprocessor -> Clean Restaurant Store."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import CLEAN_STORE_CSV_PATH, CLEAN_STORE_PATH, HF_DATASET_ID, HF_SPLIT
from .exceptions import DataIngestionError, EmptyDatasetError
from .loader import load_raw_dataset, summarize_raw
from .models import RestaurantRecord
from .preprocessor import preprocess
from .store import load_clean_store, save_clean_store, store_exists

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class Phase1Result:
    records: list[RestaurantRecord]
    raw_rows: int
    clean_rows: int
    store_paths: dict[str, Path]
    raw_summary: dict[str, Any]
    from_cache: bool = False


def run_phase1(
    *,
    dataset_id: str = HF_DATASET_ID,
    split: str = HF_SPLIT,
    use_cache: bool = True,
    force_refresh: bool = False,
    json_path: Path = CLEAN_STORE_PATH,
    csv_path: Path = CLEAN_STORE_CSV_PATH,
) -> Phase1Result:
    """
    Execute Phase 1 data ingestion.

    Architecture flow:
        Hugging Face Dataset --> Loader --> Preprocessor --> Clean Restaurant Store
    """
    if use_cache and not force_refresh and store_exists(json_path):
        logger.info("Using cached clean store at %s", json_path)
        records = load_clean_store(json_path)
        if not records:
            raise EmptyDatasetError("Cached clean store is empty.")
        return Phase1Result(
            records=records,
            raw_rows=len(records),
            clean_rows=len(records),
            store_paths={"json": json_path, "csv": csv_path},
            raw_summary={"source": "cache"},
            from_cache=True,
        )

    raw = load_raw_dataset(dataset_id=dataset_id, split=split)
    raw_summary = summarize_raw(raw)
    records = preprocess(raw)

    if not records:
        raise EmptyDatasetError(
            "No restaurant data available after preprocessing "
            "(all rows invalid or blank names)."
        )

    paths = save_clean_store(records, json_path=json_path, csv_path=csv_path)
    return Phase1Result(
        records=records,
        raw_rows=int(len(raw)),
        clean_rows=len(records),
        store_paths=paths,
        raw_summary=raw_summary,
        from_cache=False,
    )


def get_restaurants(
    *,
    use_cache: bool = True,
    force_refresh: bool = False,
) -> list[RestaurantRecord]:
    """Convenience API for later phases to fetch clean restaurants."""
    try:
        result = run_phase1(use_cache=use_cache, force_refresh=force_refresh)
    except DataIngestionError:
        raise
    return result.records
