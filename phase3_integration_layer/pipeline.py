"""Phase 3 orchestration: Filter & Shortlist --> Prompt Builder."""

from __future__ import annotations

import logging
from pathlib import Path

from phase1_data_ingestion.models import RestaurantRecord
from phase1_data_ingestion.store import load_clean_store
from phase2_user_input.models import ValidatedPreferences

from .config import MAX_CANDIDATES, PHASE1_CLEAN_STORE
from .filter import filter_and_shortlist
from .models import Phase3Result
from .prompt_builder import build_llm_prompt

logger = logging.getLogger(__name__)

NO_MATCH_MESSAGE = "No restaurants match your preferences."


def run_phase3(
    preferences: ValidatedPreferences,
    records: list[RestaurantRecord] | None = None,
    *,
    store_path: Path = PHASE1_CLEAN_STORE,
    max_candidates: int = MAX_CANDIDATES,
) -> Phase3Result:
    """
    Execute Phase 3 integration layer.

    Architecture flow:
        Preferences + Restaurant Store --> Filter & Shortlist --> Prompt Builder --> LLM Prompt
    """
    if records is None:
        records = load_clean_store(store_path)

    candidates, diagnostics, refine_hints = filter_and_shortlist(
        records,
        preferences,
        max_candidates=max_candidates,
    )

    if not candidates:
        logger.warning("No candidates after filtering (IL-01). Skipping LLM prompt.")
        return Phase3Result(
            candidates=[],
            diagnostics=diagnostics,
            refine_hints=refine_hints,
            prompt=None,
            skip_llm=True,
            no_match_message=NO_MATCH_MESSAGE,
        )

    prompt = build_llm_prompt(preferences, candidates)
    logger.info(
        "Phase 3 prompt ready: candidates=%s prompt_chars=%s truncated=%s",
        len(candidates),
        len(prompt.full_text),
        prompt.truncated,
    )

    return Phase3Result(
        candidates=candidates,
        diagnostics=diagnostics,
        refine_hints=refine_hints,
        prompt=prompt,
        skip_llm=False,
        no_match_message=None,
    )


def integrate_preferences(
    preferences: ValidatedPreferences,
    *,
    store_path: Path = PHASE1_CLEAN_STORE,
    max_candidates: int = MAX_CANDIDATES,
) -> Phase3Result:
    """Convenience API for later phases."""
    return run_phase3(
        preferences,
        store_path=store_path,
        max_candidates=max_candidates,
    )
