"""Models for Phase 3 output: filtered candidates and LLM prompt."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class FilterDiagnostics:
    """Counts at each filtering stage for refine hints and logging."""

    total_records: int
    after_location: int
    after_budget: int
    after_cuisine: int
    before_rating: int
    after_rating: int
    shortlist_count: int
    capped: bool = False
    strict_rating_removed_all: bool = False


@dataclass(slots=True)
class CandidateRestaurant:
    """Restaurant row prepared for the LLM prompt (IL-07)."""

    candidate_id: str
    name: str
    location: str
    cuisines: str
    cost: str
    budget_band: str
    rating: str
    votes: str
    rest_type: str | None = None
    dish_liked: str | None = None
    online_order: str | None = None
    book_table: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return {key: value for key, value in payload.items() if value is not None}


@dataclass(slots=True)
class LLMPrompt:
    """Final prompt payload for Phase 4 (IL-09)."""

    system_message: str
    user_message: str
    full_text: str
    candidate_ids: list[str]
    truncated: bool = False
    output_schema: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Phase3Result:
    """
    Phase 3 output contract:
        Filtered candidate list + Final LLM prompt
    """

    candidates: list[CandidateRestaurant]
    diagnostics: FilterDiagnostics
    refine_hints: list[str]
    prompt: LLMPrompt | None
    skip_llm: bool
    no_match_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "diagnostics": asdict(self.diagnostics),
            "refine_hints": self.refine_hints,
            "prompt": self.prompt.to_dict() if self.prompt else None,
            "skip_llm": self.skip_llm,
            "no_match_message": self.no_match_message,
        }
