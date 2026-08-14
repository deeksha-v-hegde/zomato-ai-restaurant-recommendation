"""Validate and normalize LLM recommendations against candidates."""

from __future__ import annotations

import logging
import re

from phase2_user_input.models import ValidatedPreferences
from phase3_integration_layer.models import CandidateRestaurant

from .config import DEFAULT_EXPLANATION
from .models import Recommendation

logger = logging.getLogger(__name__)

_RATING_RE = re.compile(r"(\d+(?:\.\d+)?)")


def _candidate_map(
    candidates: list[CandidateRestaurant],
) -> dict[str, CandidateRestaurant]:
    return {candidate.candidate_id: candidate for candidate in candidates}


def _name_matches(candidate: CandidateRestaurant, llm_name: str) -> bool:
    return candidate.name.casefold().strip() == str(llm_name).casefold().strip()


def _rating_value(text: str) -> float | None:
    match = _RATING_RE.search(text or "")
    if not match:
        return None
    return float(match.group(1))


def _passes_preference_checks(
    candidate: CandidateRestaurant,
    preferences: ValidatedPreferences,
) -> bool:
    """Post-validate each item against user filters (RE-05)."""
    if candidate.budget_band != "unknown" and candidate.budget_band != preferences.budget:
        return False

    user_cuisines = {cuisine.casefold().strip() for cuisine in preferences.cuisines}
    record_cuisines = {
        part.casefold().strip()
        for part in candidate.cuisines.split(",")
        if part.strip()
    }
    if not record_cuisines:
        return False

    if preferences.cuisine_match_mode == "and":
        if not user_cuisines.issubset(record_cuisines):
            return False
    elif not (user_cuisines & record_cuisines):
        return False

    rating = _rating_value(candidate.rating)
    if rating is not None and rating < preferences.min_rating:
        return False

    return True


def _normalize_explanation(
    explanation: object,
    candidate: CandidateRestaurant,
    preferences: ValidatedPreferences,
) -> str:
    if isinstance(explanation, str) and explanation.strip():
        return explanation.strip()
    return (
        f"Recommended based on your {preferences.budget} budget, "
        f"{preferences.cuisine_text} cuisine preference, and "
        f"{candidate.rating} rating in {preferences.location}."
    )


def validate_recommendations(
    raw_items: list[object],
    candidates: list[CandidateRestaurant],
    preferences: ValidatedPreferences,
    *,
    top_n: int,
) -> tuple[list[Recommendation], list[str]]:
    """
    Drop hallucinations, dedupe, and enforce preference checks (RE-04..RE-08).

    Returns (recommendations, warnings).
    """
    by_id = _candidate_map(candidates)
    warnings: list[str] = []
    seen_ids: set[str] = set()
    parsed: list[tuple[int, Recommendation]] = []

    for item in raw_items:
        if not isinstance(item, dict):
            warnings.append("Skipped non-object recommendation entry.")
            continue

        candidate_id = str(item.get("candidate_id") or "").strip()
        llm_name = str(item.get("name") or "").strip()
        if not candidate_id or candidate_id not in by_id:
            warnings.append(
                f"Dropped hallucinated or unknown candidate_id '{candidate_id or '(missing)'}'."
            )
            continue

        candidate = by_id[candidate_id]
        if llm_name and not _name_matches(candidate, llm_name):
            warnings.append(
                f"Name mismatch for {candidate_id}: LLM='{llm_name}' "
                f"expected='{candidate.name}'. Using catalog name."
            )

        if not _passes_preference_checks(candidate, preferences):
            warnings.append(
                f"Dropped {candidate.name} ({candidate_id}) — failed post-validation "
                "against user preferences (RE-05)."
            )
            continue

        if candidate_id in seen_ids:
            warnings.append(f"Deduplicated duplicate candidate_id '{candidate_id}'.")
            continue
        seen_ids.add(candidate_id)

        try:
            rank = int(item.get("rank", len(parsed) + 1))
        except (TypeError, ValueError):
            rank = len(parsed) + 1

        explanation = _normalize_explanation(
            item.get("explanation"),
            candidate,
            preferences,
        )
        if not explanation:
            explanation = DEFAULT_EXPLANATION
            warnings.append(f"Used default explanation for {candidate.name} (RE-08).")

        parsed.append(
            (
                rank,
                Recommendation(
                    rank=rank,
                    candidate_id=candidate_id,
                    name=candidate.name,
                    location=candidate.location,
                    cuisines=candidate.cuisines,
                    rating=candidate.rating,
                    cost=candidate.cost,
                    budget_band=candidate.budget_band,
                    explanation=explanation,
                    source="llm",
                    votes=candidate.votes,
                    rest_type=candidate.rest_type,
                    dish_liked=candidate.dish_liked,
                ),
            )
        )

    parsed.sort(key=lambda pair: (pair[0], pair[1].name.casefold()))
    recommendations = []
    for index, (_, recommendation) in enumerate(parsed[:top_n], start=1):
        recommendation.rank = index
        recommendations.append(recommendation)

    if len(recommendations) < top_n:
        warnings.append(
            f"LLM returned {len(recommendations)} valid recommendations "
            f"(requested up to {top_n}) — not padded (RE-06)."
        )

    return recommendations, warnings
