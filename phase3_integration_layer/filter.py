"""Filter restaurant records and build a deterministic shortlist."""

from __future__ import annotations

import hashlib
import logging

from phase1_data_ingestion.models import RestaurantRecord
from phase2_user_input.models import ValidatedPreferences

from .config import MAX_CANDIDATES
from .models import CandidateRestaurant, FilterDiagnostics

logger = logging.getLogger(__name__)


def candidate_id_for(record: RestaurantRecord) -> str:
    """Stable identifier for Phase 4 hallucination checks (RE-04)."""
    key = f"{record.name.casefold()}|{record.location_key}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]


def _format_cost(cost: int | None) -> str:
    if cost is None:
        return "unknown"
    return f"₹{cost} for two"


def _format_rating(record: RestaurantRecord) -> str:
    if record.rating is None or not record.rating_valid_for_filter:
        return "unknown"
    return f"{record.rating:.1f}/5"


def _format_votes(votes: int | None) -> str:
    if votes is None:
        return "unknown"
    return str(votes)


def record_to_candidate(record: RestaurantRecord) -> CandidateRestaurant:
    """Convert a restaurant record into prompt-safe candidate fields (IL-07)."""
    return CandidateRestaurant(
        candidate_id=candidate_id_for(record),
        name=record.name,
        location=record.location,
        cuisines=record.cuisine_text or "unknown",
        cost=_format_cost(record.cost),
        budget_band=record.budget_band or "unknown",
        rating=_format_rating(record),
        votes=_format_votes(record.votes),
        rest_type=record.rest_type,
        dish_liked=record.dish_liked,
        online_order=record.online_order,
        book_table=record.book_table,
    )


def _cuisine_keys(record: RestaurantRecord) -> set[str]:
    return {cuisine.casefold().strip() for cuisine in record.cuisines if cuisine.strip()}


def _matches_cuisine(record: RestaurantRecord, preferences: ValidatedPreferences) -> bool:
    """Match multi-cuisine restaurants per OR/AND mode (IL-12)."""
    record_cuisines = _cuisine_keys(record)
    if not record_cuisines:
        return False

    user_cuisines = {cuisine.casefold().strip() for cuisine in preferences.cuisines}
    if preferences.cuisine_match_mode == "and":
        return user_cuisines.issubset(record_cuisines)
    return bool(user_cuisines & record_cuisines)


def _matches_budget(record: RestaurantRecord, preferences: ValidatedPreferences) -> bool:
    if record.budget_band is None:
        return False
    return record.budget_band == preferences.budget


def _matches_rating(record: RestaurantRecord, preferences: ValidatedPreferences) -> bool:
    if not record.rating_valid_for_filter or record.rating is None:
        return False
    return record.rating >= preferences.min_rating


def _sort_key(record: RestaurantRecord) -> tuple[float, int, str, str]:
    """Deterministic ordering: rating desc, votes desc, name asc (IL-11)."""
    rating = record.rating if record.rating is not None else -1.0
    votes = record.votes if record.votes is not None else -1
    return (-rating, -votes, record.name.casefold(), record.location_key)


def filter_by_location(
    records: list[RestaurantRecord],
    preferences: ValidatedPreferences,
) -> list[RestaurantRecord]:
    return [record for record in records if record.location_key == preferences.location_key]


def filter_by_budget(
    records: list[RestaurantRecord],
    preferences: ValidatedPreferences,
) -> list[RestaurantRecord]:
    return [record for record in records if _matches_budget(record, preferences)]


def filter_by_cuisine(
    records: list[RestaurantRecord],
    preferences: ValidatedPreferences,
) -> list[RestaurantRecord]:
    return [record for record in records if _matches_cuisine(record, preferences)]


def filter_by_rating(
    records: list[RestaurantRecord],
    preferences: ValidatedPreferences,
) -> list[RestaurantRecord]:
    return [record for record in records if _matches_rating(record, preferences)]


def build_refine_hints(
    preferences: ValidatedPreferences,
    diagnostics: FilterDiagnostics,
) -> list[str]:
    """Actionable hints when filters return no or few matches (IL-01, IL-06)."""
    hints: list[str] = []

    if diagnostics.after_location == 0:
        hints.append(
            f"No restaurants found in '{preferences.location}'. "
            "Try another area from the dataset."
        )
        return hints

    if diagnostics.after_budget == 0:
        hints.append(
            f"No restaurants in '{preferences.location}' match budget '{preferences.budget}'. "
            "Try a different budget band."
        )

    if diagnostics.after_cuisine == 0:
        mode = preferences.cuisine_match_mode.upper()
        hints.append(
            f"No restaurants in '{preferences.location}' serve "
            f"{preferences.cuisine_text} (match mode: {mode}). "
            "Try a different cuisine or switch OR/AND mode."
        )

    if diagnostics.strict_rating_removed_all:
        hints.append(
            f"Minimum rating {preferences.min_rating} removed all otherwise matching options. "
            "Try lowering the rating threshold."
        )
    elif diagnostics.after_rating == 0 and diagnostics.before_rating > 0:
        hints.append(
            f"No restaurants meet the {preferences.min_rating}+ rating filter. "
            "Try a lower minimum rating."
        )

    if not hints:
        hints.append(
            "Try relaxing one filter at a time: location, budget, cuisine, or minimum rating."
        )

    return hints


def filter_and_shortlist(
    records: list[RestaurantRecord],
    preferences: ValidatedPreferences,
    *,
    max_candidates: int = MAX_CANDIDATES,
) -> tuple[list[CandidateRestaurant], FilterDiagnostics, list[str]]:
    """
    Apply structured filters and cap the shortlist (IL-01..IL-06, IL-11, IL-12).

    Architecture flow:
        Preferences + Restaurant Store --> Filter & Shortlist --> Candidate list
    """
    after_location = filter_by_location(records, preferences)
    after_budget = filter_by_budget(after_location, preferences)
    after_cuisine = filter_by_cuisine(after_budget, preferences)
    before_rating = len(after_cuisine)
    after_rating_records = filter_by_rating(after_cuisine, preferences)

    strict_rating_removed_all = before_rating > 0 and len(after_rating_records) == 0

    sorted_records = sorted(after_rating_records, key=_sort_key)
    capped = len(sorted_records) > max_candidates
    shortlisted = sorted_records[:max_candidates]

    diagnostics = FilterDiagnostics(
        total_records=len(records),
        after_location=len(after_location),
        after_budget=len(after_budget),
        after_cuisine=len(after_cuisine),
        before_rating=before_rating,
        after_rating=len(after_rating_records),
        shortlist_count=len(shortlisted),
        capped=capped,
        strict_rating_removed_all=strict_rating_removed_all,
    )

    candidates = [record_to_candidate(record) for record in shortlisted]
    refine_hints = (
        build_refine_hints(preferences, diagnostics)
        if len(candidates) == 0
        else []
    )

    logger.info(
        "Filter pipeline: total=%s location=%s budget=%s cuisine=%s rating=%s shortlist=%s capped=%s",
        diagnostics.total_records,
        diagnostics.after_location,
        diagnostics.after_budget,
        diagnostics.after_cuisine,
        diagnostics.after_rating,
        diagnostics.shortlist_count,
        diagnostics.capped,
    )

    return candidates, diagnostics, refine_hints
