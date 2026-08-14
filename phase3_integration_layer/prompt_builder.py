"""Assemble the LLM prompt from preferences and shortlisted candidates."""

from __future__ import annotations

import json
import logging

from phase2_user_input.models import ValidatedPreferences

from .config import (
    MAX_CANDIDATES_AFTER_TRUNCATION,
    MAX_PROMPT_CHARS,
    TOP_N_RECOMMENDATIONS,
)
from .models import CandidateRestaurant, LLMPrompt

logger = logging.getLogger(__name__)

OUTPUT_SCHEMA: dict[str, object] = {
    "recommendations": [
        {
            "candidate_id": "string — must match a candidate_id from the list",
            "rank": "integer — 1 is best fit",
            "name": "string — restaurant name (must match candidate)",
            "explanation": "string — why this fits the user's preferences",
        }
    ],
    "summary": "string — optional brief overview of the set",
}


def _build_system_message() -> str:
    return (
        "You are a restaurant recommendation assistant for Zomato-style dining in India. "
        "Rank ONLY from the provided candidate list. Do not invent restaurants or attributes "
        "not present in the candidate data. If additional preferences conflict with the "
        "shortlist, explain the trade-off instead of fabricating a perfect match (IL-10)."
    )


def _preferences_block(preferences: ValidatedPreferences) -> str:
    lines = [
        "## User preferences",
        f"- Location: {preferences.location}",
        f"- Budget: {preferences.budget}",
        f"- Cuisine(s): {preferences.cuisine_text} (match mode: {preferences.cuisine_match_mode.upper()})",
        f"- Minimum rating: {preferences.min_rating}",
    ]
    if preferences.additional_preferences:
        lines.append(f"- Additional notes: {preferences.additional_preferences}")
    if preferences.additional_preferences_truncated:
        lines.append("- Note: additional preferences were truncated for length.")
    return "\n".join(lines)


def _instructions_block(top_n: int) -> str:
    return f"""## Task
1. Rank up to {top_n} restaurants from the candidate list by fit to the user preferences.
2. Prefer higher ratings and stronger cuisine/budget alignment when ties occur.
3. Use ONLY fields provided for each candidate — do not assume rooftop views, luxury, etc.
4. If no candidate fully matches additional notes, say so honestly in the explanation.
5. Return valid JSON matching this schema (no markdown fences):

{json.dumps(OUTPUT_SCHEMA, indent=2)}
"""


def _candidates_block(candidates: list[CandidateRestaurant]) -> str:
    payload = [candidate.to_dict() for candidate in candidates]
    return "## Candidate restaurants\n" + json.dumps(payload, ensure_ascii=False, indent=2)


def _assemble_prompt(
    preferences: ValidatedPreferences,
    candidates: list[CandidateRestaurant],
    *,
    top_n: int,
) -> str:
    sections = [
        _preferences_block(preferences),
        _candidates_block(candidates),
        _instructions_block(top_n),
    ]
    return "\n\n".join(sections)


def build_llm_prompt(
    preferences: ValidatedPreferences,
    candidates: list[CandidateRestaurant],
    *,
    top_n: int = TOP_N_RECOMMENDATIONS,
    max_prompt_chars: int = MAX_PROMPT_CHARS,
) -> LLMPrompt:
    """
    Build the final LLM prompt (IL-08, IL-09).

    Truncates the candidate list if the assembled prompt exceeds max size.
    """
    if not candidates:
        raise ValueError("Cannot build prompt without candidates.")

    working = list(candidates)
    truncated = False

    user_message = _assemble_prompt(preferences, working, top_n=top_n)
    while len(user_message) > max_prompt_chars and len(working) > 1:
        truncated = True
        working = working[: max(len(working) // 2, 1)]
        user_message = _assemble_prompt(preferences, working, top_n=top_n)
        logger.warning(
            "Prompt exceeded %s chars; reduced candidates to %s",
            max_prompt_chars,
            len(working),
        )

    if len(user_message) > max_prompt_chars and len(working) == 1:
        truncated = True
        # Last resort: keep one candidate but trim optional fields.
        slim = CandidateRestaurant(
            candidate_id=working[0].candidate_id,
            name=working[0].name,
            location=working[0].location,
            cuisines=working[0].cuisines,
            cost=working[0].cost,
            budget_band=working[0].budget_band,
            rating=working[0].rating,
            votes=working[0].votes,
        )
        working = [slim]
        user_message = _assemble_prompt(preferences, working, top_n=top_n)

    if len(user_message) > max_prompt_chars:
        user_message = user_message[:max_prompt_chars]
        truncated = True
        logger.warning("Prompt hard-truncated to %s characters.", max_prompt_chars)

    if truncated and len(working) > MAX_CANDIDATES_AFTER_TRUNCATION:
        working = working[:MAX_CANDIDATES_AFTER_TRUNCATION]

    system_message = _build_system_message()
    full_text = f"SYSTEM:\n{system_message}\n\nUSER:\n{user_message}"

    return LLMPrompt(
        system_message=system_message,
        user_message=user_message,
        full_text=full_text,
        candidate_ids=[candidate.candidate_id for candidate in working],
        truncated=truncated,
        output_schema=OUTPUT_SCHEMA,
    )
