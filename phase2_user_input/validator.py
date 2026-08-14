"""Validate and convert raw preferences into Phase 2 output."""

from __future__ import annotations

from pathlib import Path

from .catalog import cuisine_exists_in_catalog, location_exists_in_catalog
from .config import (
    DEFAULT_CUISINE_MATCH_MODE,
    MAX_RATING,
    MIN_RATING,
    PHASE1_CLEAN_STORE,
    VALID_BUDGETS,
)
from .exceptions import PreferenceValidationError
from .models import RawUserPreferences, ValidatedPreferences
from .normalizer import (
    normalize_budget,
    normalize_cuisine_match_mode,
    normalize_location,
    sanitize_additional_preferences,
    sanitize_text,
    split_cuisines,
)


def _is_missing(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def _parse_min_rating(value: object) -> tuple[float | None, str | None]:
    """Return (rating, error_message)."""
    if _is_missing(value):
        return None, "Minimum rating is required (0 to 5)."
    try:
        rating = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None, f"Minimum rating '{value}' is not a number."
    if rating < MIN_RATING or rating > MAX_RATING:
        return None, f"Minimum rating must be between {MIN_RATING} and {MAX_RATING}."
    return rating, None


def validate_preferences(
    raw: RawUserPreferences,
    *,
    store_path: Path = PHASE1_CLEAN_STORE,
    check_catalog: bool = True,
) -> ValidatedPreferences:
    """
    Validate user preferences before Phase 3.

    Covers UI-01, UI-02, UI-04..UI-11, UI-14 and soft catalog checks for UI-03/UI-08.
    """
    errors: list[str] = []
    warnings: list[str] = []

    location_display, location_key = normalize_location(raw.location)
    if not location_key:
        errors.append("Location is required.")

    if _is_missing(raw.budget):
        errors.append("Budget is required (low, medium, or high).")
        budget = None
    else:
        budget = normalize_budget(raw.budget)
        if budget is None:
            errors.append(
                f"Invalid budget '{raw.budget}'. "
                f"Allowed values: {', '.join(sorted(VALID_BUDGETS))}."
            )

    cuisines = split_cuisines(raw.cuisine)
    if not cuisines:
        errors.append("Cuisine is required (e.g. Italian or Italian, Chinese).")

    min_rating, rating_error = _parse_min_rating(raw.min_rating)
    if rating_error:
        errors.append(rating_error)

    if errors:
        raise PreferenceValidationError(
            "Preference validation failed: " + " ".join(errors),
            errors=errors,
        )

    assert location_display is not None
    assert location_key is not None
    assert budget is not None
    assert min_rating is not None

    match_mode = normalize_cuisine_match_mode(
        raw.cuisine_match_mode,
        default=DEFAULT_CUISINE_MATCH_MODE,
    )
    additional, truncated, extra_warnings = sanitize_additional_preferences(
        raw.additional_preferences
    )
    warnings.extend(extra_warnings)

    if check_catalog:
        loc_ok = location_exists_in_catalog(location_key, store_path=store_path)
        if loc_ok is False:
            warnings.append(
                f"Location '{location_display}' was not found in the Phase 1 restaurant "
                "catalog (UI-03). Phase 3 may return no matches."
            )

        missing_cuisines = [
            cuisine
            for cuisine in cuisines
            if cuisine_exists_in_catalog(cuisine, store_path=store_path) is False
        ]
        if missing_cuisines:
            warnings.append(
                "Cuisine(s) not found in catalog: "
                + ", ".join(missing_cuisines)
                + " (UI-08). Phase 3 may return no matches."
            )

    return ValidatedPreferences(
        location=location_display,
        location_key=location_key,
        budget=budget,  # type: ignore[arg-type]
        cuisines=cuisines,
        cuisine_text=", ".join(cuisines),
        cuisine_match_mode=match_mode,  # type: ignore[arg-type]
        min_rating=float(min_rating),
        additional_preferences=additional,
        additional_preferences_truncated=truncated,
        warnings=warnings,
    )