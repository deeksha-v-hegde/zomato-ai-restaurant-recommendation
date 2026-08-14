"""Preference models for Phase 2 output."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


BudgetBand = Literal["low", "medium", "high"]
CuisineMatchMode = Literal["or", "and"]


@dataclass(slots=True)
class RawUserPreferences:
    """Unvalidated preferences captured from the form / API."""

    location: str | None = None
    budget: str | None = None
    cuisine: str | None = None
    min_rating: str | float | int | None = None
    additional_preferences: str | None = None
    cuisine_match_mode: str | None = None


@dataclass(slots=True)
class ValidatedPreferences:
    """
    Validated preference object passed to Phase 3.

    Architecture output:
        User --> Preference Form --> Validated Preference Object
    """

    location: str
    location_key: str
    budget: BudgetBand
    cuisines: list[str]
    cuisine_text: str
    cuisine_match_mode: CuisineMatchMode
    min_rating: float
    additional_preferences: str | None = None
    additional_preferences_truncated: bool = False
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
