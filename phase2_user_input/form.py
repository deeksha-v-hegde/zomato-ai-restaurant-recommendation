"""Preference form collectors (interactive CLI + programmatic)."""

from __future__ import annotations

from .models import RawUserPreferences


def collect_preferences(
    *,
    location: str | None = None,
    budget: str | None = None,
    cuisine: str | None = None,
    min_rating: str | float | int | None = None,
    additional_preferences: str | None = None,
    cuisine_match_mode: str | None = None,
) -> RawUserPreferences:
    """Programmatic preference capture (API / non-interactive form)."""
    return RawUserPreferences(
        location=location,
        budget=budget,
        cuisine=cuisine,
        min_rating=min_rating,
        additional_preferences=additional_preferences,
        cuisine_match_mode=cuisine_match_mode,
    )


def _prompt(label: str, required: bool = True) -> str | None:
    suffix = "" if required else " (optional)"
    value = input(f"{label}{suffix}: ").strip()
    return value or None


def collect_preferences_interactive() -> RawUserPreferences:
    """
    Interactive preference form.

    Architecture:
        User --> Preference Form --> Validated Preference Object
    """
    print("Zomato AI Recommender — Preference Form")
    print("Enter your preferences (required fields marked).\n")

    location = _prompt("Location (e.g. Banashankari, BTM, Bangalore)", required=True)
    budget = _prompt("Budget [low | medium | high]", required=True)
    cuisine = _prompt("Cuisine (comma-separated ok, e.g. Italian, Chinese)", required=True)
    min_rating = _prompt("Minimum rating (0-5, e.g. 4.0)", required=True)
    additional = _prompt(
        "Additional preferences (e.g. family-friendly, quick service)",
        required=False,
    )
    match_mode = _prompt("Cuisine match mode [or|and] (default: or)", required=False)

    return RawUserPreferences(
        location=location,
        budget=budget,
        cuisine=cuisine,
        min_rating=min_rating,
        additional_preferences=additional,
        cuisine_match_mode=match_mode,
    )
