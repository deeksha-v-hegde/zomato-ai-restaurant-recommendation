"""Preprocess and normalize raw Zomato restaurant records."""

from __future__ import annotations

import logging
import re
import unicodedata
from typing import Any

import pandas as pd

from .config import BUDGET_LOW_MAX, BUDGET_MEDIUM_MAX, LOCATION_ALIASES
from .models import RestaurantRecord

logger = logging.getLogger(__name__)

_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_RATING_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*/\s*5\s*$")
_COST_DIGITS_RE = re.compile(r"[^\d]")


def sanitize_text(value: Any) -> str | None:
    """Preserve UTF-8 text; strip only unsafe control characters (DI-12)."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null"}:
        return None
    text = unicodedata.normalize("NFC", text)
    text = _CONTROL_CHARS_RE.sub("", text).strip()
    return text or None


def normalize_location(value: Any) -> tuple[str | None, str | None]:
    """
    Normalize location display + lookup key (DI-09).

    Returns (display_location, location_key).
    """
    text = sanitize_text(value)
    if text is None:
        return None, None

    key = re.sub(r"\s+", " ", text.casefold()).strip()
    key = LOCATION_ALIASES.get(key, key)
    display = text.title() if text == text.upper() or text == text.lower() else text
    return display, key


def parse_rating(value: Any) -> tuple[float | None, bool]:
    """
    Parse Zomato rating strings like '4.1/5', 'NEW', '-', blank (DI-06).

    Returns (rating, valid_for_filter).
    """
    text = sanitize_text(value)
    if text is None:
        return None, False

    lowered = text.casefold()
    if lowered in {"new", "-", "nan"}:
        return None, False

    match = _RATING_RE.match(text)
    if match:
        rating = float(match.group(1))
    else:
        try:
            rating = float(text)
        except ValueError:
            return None, False

    if rating < 0 or rating > 5:
        return None, False
    return rating, True


def parse_cost(value: Any) -> int | None:
    """Parse approx cost text such as '1,200' or '₹800' (DI-07)."""
    text = sanitize_text(value)
    if text is None:
        return None

    digits = _COST_DIGITS_RE.sub("", text)
    if not digits:
        return None
    try:
        return int(digits)
    except ValueError:
        return None


def budget_band_from_cost(cost: int | None) -> str | None:
    """Map numeric cost to low / medium / high bands."""
    if cost is None:
        return None
    if cost <= BUDGET_LOW_MAX:
        return "low"
    if cost <= BUDGET_MEDIUM_MAX:
        return "medium"
    return "high"


def split_cuisines(value: Any) -> list[str]:
    """Split multi-cuisine strings and normalize tokens (DI-10)."""
    text = sanitize_text(value)
    if text is None:
        return []

    parts = [part.strip() for part in text.split(",")]
    cuisines: list[str] = []
    seen: set[str] = set()
    for part in parts:
        cleaned = sanitize_text(part)
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key in seen:
            continue
        seen.add(key)
        cuisines.append(cleaned)
    return cuisines


def parse_votes(value: Any) -> int | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        text = sanitize_text(value)
        if text is None:
            return None
        digits = _COST_DIGITS_RE.sub("", text)
        return int(digits) if digits else None


def row_to_record(row: pd.Series) -> RestaurantRecord | None:
    """Convert one raw row into a clean record, or None if invalid (DI-04)."""
    name = sanitize_text(row.get("name"))
    if name is None:
        return None

    location, location_key = normalize_location(row.get("location"))
    cuisines = split_cuisines(row.get("cuisines"))
    cost = parse_cost(row.get("approx_cost(for two people)"))
    rating, rating_valid = parse_rating(row.get("rate"))

    return RestaurantRecord(
        name=name,
        location=location or "Unknown",
        location_key=location_key or "unknown",
        cuisines=cuisines,
        cuisine_text=", ".join(cuisines) if cuisines else "",
        cost=cost,
        budget_band=budget_band_from_cost(cost),
        rating=rating,
        rating_valid_for_filter=rating_valid,
        votes=parse_votes(row.get("votes")),
        rest_type=sanitize_text(row.get("rest_type")),
        online_order=sanitize_text(row.get("online_order")),
        book_table=sanitize_text(row.get("book_table")),
        listed_in_type=sanitize_text(row.get("listed_in(type)")),
        listed_in_city=sanitize_text(row.get("listed_in(city)")),
        address=sanitize_text(row.get("address")),
        url=sanitize_text(row.get("url")),
        dish_liked=sanitize_text(row.get("dish_liked")),
    )


def deduplicate_records(records: list[RestaurantRecord]) -> list[RestaurantRecord]:
    """Keep one row per (name, location_key), preferring higher votes/rating (DI-08)."""

    def sort_key(record: RestaurantRecord) -> tuple[int, float]:
        votes = record.votes if record.votes is not None else -1
        rating = record.rating if record.rating is not None else -1.0
        return votes, rating

    best: dict[tuple[str, str], RestaurantRecord] = {}
    for record in records:
        key = (record.name.casefold(), record.location_key)
        current = best.get(key)
        if current is None or sort_key(record) > sort_key(current):
            best[key] = record
    return list(best.values())


def preprocess(frame: pd.DataFrame) -> list[RestaurantRecord]:
    """
    Full preprocess pipeline:
    extract fields -> normalize -> drop invalid names -> dedupe.
    """
    records: list[RestaurantRecord] = []
    dropped_blank_name = 0

    for _, row in frame.iterrows():
        record = row_to_record(row)
        if record is None:
            dropped_blank_name += 1
            continue
        records.append(record)

    before_dedupe = len(records)
    records = deduplicate_records(records)

    logger.info(
        "Preprocess complete: kept=%s, dropped_blank_name=%s, removed_duplicates=%s",
        len(records),
        dropped_blank_name,
        before_dedupe - len(records),
    )
    return records


def records_to_dataframe(records: list[RestaurantRecord]) -> pd.DataFrame:
    """Convert clean records to a flat DataFrame for CSV export / inspection."""
    rows = []
    for record in records:
        rows.append(
            {
                "name": record.name,
                "location": record.location,
                "location_key": record.location_key,
                "cuisines": record.cuisine_text,
                "cost": record.cost,
                "budget_band": record.budget_band,
                "rating": record.rating,
                "rating_valid_for_filter": record.rating_valid_for_filter,
                "votes": record.votes,
                "rest_type": record.rest_type,
                "online_order": record.online_order,
                "book_table": record.book_table,
                "listed_in_type": record.listed_in_type,
                "listed_in_city": record.listed_in_city,
                "address": record.address,
                "url": record.url,
                "dish_liked": record.dish_liked,
            }
        )
    return pd.DataFrame(rows)
