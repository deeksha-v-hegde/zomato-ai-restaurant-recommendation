"""Persist and reload the clean restaurant store (DI-11)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from .config import CACHE_DIR, CLEAN_STORE_CSV_PATH, CLEAN_STORE_PATH
from .models import RestaurantRecord
from .preprocessor import records_to_dataframe

logger = logging.getLogger(__name__)


def ensure_cache_dir(cache_dir: Path = CACHE_DIR) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def save_clean_store(
    records: list[RestaurantRecord],
    json_path: Path = CLEAN_STORE_PATH,
    csv_path: Path = CLEAN_STORE_CSV_PATH,
) -> dict[str, Path]:
    """Write cleaned restaurants to JSON + CSV cache."""
    ensure_cache_dir(json_path.parent)

    payload: dict[str, Any] = {
        "count": len(records),
        "restaurants": [record.to_dict() for record in records],
    }
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    frame = records_to_dataframe(records)
    frame.to_csv(csv_path, index=False, encoding="utf-8")

    logger.info("Saved clean store: %s (%s restaurants)", json_path, len(records))
    logger.info("Saved CSV preview store: %s", csv_path)
    return {"json": json_path, "csv": csv_path}


def load_clean_store(json_path: Path = CLEAN_STORE_PATH) -> list[RestaurantRecord]:
    """Load previously cleaned restaurants from cache."""
    if not json_path.exists():
        raise FileNotFoundError(
            f"Clean restaurant store not found at '{json_path}'. Run Phase 1 pipeline first."
        )

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    restaurants = payload.get("restaurants", [])
    records = [RestaurantRecord(**item) for item in restaurants]
    logger.info("Loaded %s restaurants from clean store", len(records))
    return records


def store_exists(json_path: Path = CLEAN_STORE_PATH) -> bool:
    return json_path.exists()
