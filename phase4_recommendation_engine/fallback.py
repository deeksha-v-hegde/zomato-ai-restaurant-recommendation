"""Deterministic fallback ranking when Groq/LLM is unavailable."""

from __future__ import annotations

import logging
import re

from phase2_user_input.models import ValidatedPreferences
from phase3_integration_layer.models import CandidateRestaurant

from .config import DEFAULT_EXPLANATION, TOP_N_RECOMMENDATIONS
from .models import Recommendation

logger = logging.getLogger(__name__)

_RATING_RE = re.compile(r"(\d+(?:\.\d+)?)")


def _parse_rating_value(rating: str) -> float:
    match = _RATING_RE.search(rating or "")
    if not match:
        return -1.0
    return float(match.group(1))


def _parse_votes_value(votes: str) -> int:
    text = (votes or "").strip()
    if not text or text.lower() == "unknown":
        return -1
    try:
        return int(text)
    except ValueError:
        return -1


def _sort_key(candidate: CandidateRestaurant) -> tuple[float, int, str]:
    return (
        -_parse_rating_value(candidate.rating),
        -_parse_votes_value(candidate.votes),
        candidate.name.casefold(),
    )


def _template_explanation(
    candidate: CandidateRestaurant,
    preferences: ValidatedPreferences,
) -> str:
    """Preference-tied fallback explanation (RE-08, RE-09, RE-15)."""
    parts = [
        f"Located in {preferences.location}",
        f"within your {preferences.budget} budget band",
        f"serving {candidate.cuisines}",
    ]
    if candidate.rating and candidate.rating != "unknown":
        parts.append(f"with rating {candidate.rating}")
    else:
        parts.append("rating not available in dataset")

    explanation = ", ".join(parts) + "."
    if preferences.additional_preferences:
        explanation += (
            f" Note: additional preference '{preferences.additional_preferences[:80]}' "
            "was considered via structured filters only."
        )
    return explanation


def build_fallback_recommendations(
    candidates: list[CandidateRestaurant],
    preferences: ValidatedPreferences,
    *,
    top_n: int = TOP_N_RECOMMENDATIONS,
    reason: str | None = None,
) -> tuple[list[Recommendation], str | None]:
    """
    Rank filtered candidates without the LLM (RE-01, RE-02, RE-03, RE-12).

    Returns (recommendations, summary).
    """
    sorted_candidates = sorted(candidates, key=_sort_key)[:top_n]
    recommendations: list[Recommendation] = []

    for index, candidate in enumerate(sorted_candidates, start=1):
        explanation = _template_explanation(candidate, preferences)
        if reason:
            explanation = f"{explanation} (AI explanation unavailable: {reason})"
        elif not explanation.strip():
            explanation = DEFAULT_EXPLANATION

        recommendations.append(
            Recommendation(
                rank=index,
                candidate_id=candidate.candidate_id,
                name=candidate.name,
                location=candidate.location,
                cuisines=candidate.cuisines,
                rating=candidate.rating,
                cost=candidate.cost,
                budget_band=candidate.budget_band,
                explanation=explanation,
                source="fallback",
                votes=candidate.votes,
                rest_type=candidate.rest_type,
                dish_liked=candidate.dish_liked,
            )
        )

    summary = None
    if recommendations:
        summary = (
            f"Showing {len(recommendations)} top matches ranked by rating and popularity "
            f"for {preferences.location} ({preferences.budget} budget, "
            f"{preferences.cuisine_text})."
        )
        if reason:
            summary += f" Fallback ranking used: {reason}"

    logger.info("Built %s fallback recommendations", len(recommendations))
    return recommendations, summary
