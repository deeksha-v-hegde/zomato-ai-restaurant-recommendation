"""Structured restaurant record produced by Phase 1."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class RestaurantRecord:
    """Clean restaurant record ready for Phase 3 filtering."""

    name: str
    location: str
    location_key: str
    cuisines: list[str]
    cuisine_text: str
    cost: int | None
    budget_band: str | None
    rating: float | None
    rating_valid_for_filter: bool
    votes: int | None = None
    rest_type: str | None = None
    online_order: str | None = None
    book_table: str | None = None
    listed_in_type: str | None = None
    listed_in_city: str | None = None
    address: str | None = None
    url: str | None = None
    dish_liked: str | None = None
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
