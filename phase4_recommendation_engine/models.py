"""Output models for Phase 4 ranked recommendations."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

RecommendationSource = Literal["llm", "fallback"]


@dataclass(slots=True)
class Recommendation:
    """One ranked restaurant recommendation for Phase 5 display."""

    rank: int
    candidate_id: str
    name: str
    location: str
    cuisines: str
    rating: str
    cost: str
    budget_band: str
    explanation: str
    source: RecommendationSource = "llm"
    votes: str | None = None
    rest_type: str | None = None
    dish_liked: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Phase4Result:
    """
    Phase 4 output contract:
        Ranked recommendations with explanations (+ optional summary)
    """

    recommendations: list[Recommendation]
    summary: str | None
    used_fallback: bool
    fallback_reason: str | None = None
    llm_model: str | None = None
    skip_llm: bool = False
    no_match_message: str | None = None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommendations": [item.to_dict() for item in self.recommendations],
            "summary": self.summary,
            "used_fallback": self.used_fallback,
            "fallback_reason": self.fallback_reason,
            "llm_model": self.llm_model,
            "skip_llm": self.skip_llm,
            "no_match_message": self.no_match_message,
            "warnings": self.warnings,
        }
