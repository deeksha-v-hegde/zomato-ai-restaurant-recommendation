"""Phase 2 orchestration: User -> Preference Form -> Validated Preference Object."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path

from .config import PHASE1_CLEAN_STORE, SUBMIT_DEBOUNCE_SECONDS
from .exceptions import DuplicateSubmitError, PreferenceValidationError
from .form import collect_preferences, collect_preferences_interactive
from .models import RawUserPreferences, ValidatedPreferences
from .validator import validate_preferences

logger = logging.getLogger(__name__)

_last_submit_fingerprint: str | None = None
_last_submit_at: float = 0.0


@dataclass(slots=True)
class Phase2Result:
    preferences: ValidatedPreferences
    raw: RawUserPreferences
    source: str  # "interactive" | "api" | "args"


def _fingerprint(raw: RawUserPreferences) -> str:
    payload = {
        "location": raw.location,
        "budget": raw.budget,
        "cuisine": raw.cuisine,
        "min_rating": str(raw.min_rating),
        "additional_preferences": raw.additional_preferences,
        "cuisine_match_mode": raw.cuisine_match_mode,
    }
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _guard_duplicate_submit(raw: RawUserPreferences) -> None:
    """UI-15: block identical rapid resubmits."""
    global _last_submit_fingerprint, _last_submit_at

    fingerprint = _fingerprint(raw)
    now = time.monotonic()
    if (
        _last_submit_fingerprint == fingerprint
        and (now - _last_submit_at) < SUBMIT_DEBOUNCE_SECONDS
    ):
        raise DuplicateSubmitError(
            f"Duplicate submit ignored (wait {SUBMIT_DEBOUNCE_SECONDS}s)."
        )
    _last_submit_fingerprint = fingerprint
    _last_submit_at = now


def reset_submit_guard() -> None:
    """Test helper to clear debounce state."""
    global _last_submit_fingerprint, _last_submit_at
    _last_submit_fingerprint = None
    _last_submit_at = 0.0


def run_phase2(
    raw: RawUserPreferences | None = None,
    *,
    interactive: bool = False,
    check_catalog: bool = True,
    store_path: Path = PHASE1_CLEAN_STORE,
    enforce_debounce: bool = True,
    source: str | None = None,
) -> Phase2Result:
    """
    Execute Phase 2 user input collection + validation.

    Architecture flow:
        User --> Preference Form --> Validated Preference Object
    """
    if raw is None and interactive:
        raw = collect_preferences_interactive()
        resolved_source = source or "interactive"
    elif raw is None:
        raise PreferenceValidationError(
            "No preferences provided. Pass raw preferences or use interactive=True."
        )
    else:
        resolved_source = source or "api"

    if enforce_debounce:
        _guard_duplicate_submit(raw)

    preferences = validate_preferences(
        raw,
        store_path=store_path,
        check_catalog=check_catalog,
    )
    logger.info(
        "Phase 2 validated preferences: location=%s budget=%s cuisines=%s min_rating=%s",
        preferences.location_key,
        preferences.budget,
        preferences.cuisines,
        preferences.min_rating,
    )
    for warning in preferences.warnings:
        logger.warning("%s", warning)

    return Phase2Result(preferences=preferences, raw=raw, source=resolved_source)


def get_validated_preferences(
    *,
    location: str,
    budget: str,
    cuisine: str,
    min_rating: float | int | str,
    additional_preferences: str | None = None,
    cuisine_match_mode: str | None = None,
    check_catalog: bool = True,
) -> ValidatedPreferences:
    """Convenience API for later phases."""
    raw = collect_preferences(
        location=location,
        budget=budget,
        cuisine=cuisine,
        min_rating=min_rating,
        additional_preferences=additional_preferences,
        cuisine_match_mode=cuisine_match_mode,
    )
    return run_phase2(
        raw,
        check_catalog=check_catalog,
        enforce_debounce=False,
        source="api",
    ).preferences
