"""Optional catalog helpers backed by Phase 1 clean store."""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path

from .config import PHASE1_CLEAN_STORE

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _load_catalog(store_path: str) -> tuple[set[str], set[str]]:
    path = Path(store_path)
    if not path.exists():
        logger.warning("Phase 1 clean store not found at %s; catalog checks skipped.", path)
        return set(), set()

    payload = json.loads(path.read_text(encoding="utf-8"))
    restaurants = payload.get("restaurants", [])

    locations: set[str] = set()
    cuisines: set[str] = set()
    for row in restaurants:
        location_key = str(row.get("location_key") or "").casefold().strip()
        if location_key:
            locations.add(location_key)
        for cuisine in row.get("cuisines") or []:
            key = str(cuisine).casefold().strip()
            if key:
                cuisines.add(key)
        # Also split cuisine_text if list missing
        cuisine_text = row.get("cuisine_text") or ""
        for part in str(cuisine_text).split(","):
            key = part.casefold().strip()
            if key:
                cuisines.add(key)

    logger.info(
        "Loaded catalog from Phase 1 store: %s locations, %s cuisines",
        len(locations),
        len(cuisines),
    )
    return locations, cuisines


def get_known_locations(store_path: Path = PHASE1_CLEAN_STORE) -> set[str]:
    locations, _ = _load_catalog(str(store_path))
    return locations


def get_known_cuisines(store_path: Path = PHASE1_CLEAN_STORE) -> set[str]:
    _, cuisines = _load_catalog(str(store_path))
    return cuisines


def location_exists_in_catalog(location_key: str, store_path: Path = PHASE1_CLEAN_STORE) -> bool | None:
    """
    Return True/False when catalog is available, or None when store is missing.
    """
    locations = get_known_locations(store_path)
    if not locations:
        return None
    return location_key in locations


def cuisine_exists_in_catalog(cuisine: str, store_path: Path = PHASE1_CLEAN_STORE) -> bool | None:
    cuisines = get_known_cuisines(store_path)
    if not cuisines:
        return None
    return cuisine.casefold().strip() in cuisines


def clear_catalog_cache() -> None:
    _load_catalog.cache_clear()
