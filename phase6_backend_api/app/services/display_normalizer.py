"""Phase 5 display normalization (embedded until phase5_output_display exists)."""

from __future__ import annotations

import html
import re

from phase4_recommendation_engine.models import Phase4Result, Recommendation

from ..config import MAX_EXPLANATION_LENGTH, MAX_NAME_LENGTH
from ..schemas.recommend import RecommendationCard

_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_SCRIPT_TAG_RE = re.compile(r"<\s*/?\s*script[^>]*>", re.IGNORECASE)


def _safe_text(value: str | None, *, fallback: str = "N/A", max_length: int | None = None) -> str:
    if value is None or not str(value).strip():
        return fallback
    text = _CONTROL_CHARS_RE.sub("", str(value).strip())
    text = _SCRIPT_TAG_RE.sub("", text)
    text = html.escape(text, quote=True)
    if max_length and len(text) > max_length:
        return text[: max_length - 1].rstrip() + "…"
    return text


def normalize_recommendation(item: Recommendation) -> RecommendationCard:
    """Map Phase 4 recommendation to Phase 5 display card (OD-02, OD-03, OD-04)."""
    return RecommendationCard(
        rank=item.rank,
        candidate_id=item.candidate_id,
        name=_safe_text(item.name, fallback="Unknown", max_length=MAX_NAME_LENGTH),
        location=_safe_text(item.location),
        cuisines=_safe_text(item.cuisines),
        rating=_safe_text(item.rating),
        cost=_safe_text(item.cost),
        budget_band=_safe_text(item.budget_band),
        explanation=_safe_text(
            item.explanation,
            fallback="Matches your selected preferences.",
            max_length=MAX_EXPLANATION_LENGTH,
        ),
        source=item.source,
    )


def normalize_recommendations(result: Phase4Result) -> list[RecommendationCard]:
    return [normalize_recommendation(item) for item in result.recommendations]
