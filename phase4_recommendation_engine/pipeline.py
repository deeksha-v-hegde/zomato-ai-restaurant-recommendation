"""Phase 4 orchestration: LLM Prompt --> Groq --> Ranked Results."""

from __future__ import annotations

import logging

from phase2_user_input.models import ValidatedPreferences
from phase3_integration_layer.models import LLMPrompt, Phase3Result

from .config import MAX_REPAIR_ATTEMPTS, TOP_N_RECOMMENDATIONS
from .exceptions import (
    GroqAPIError,
    GroqConfigurationError,
    LLMResponseError,
    RecommendationEngineError,
    UnsafeLLMOutputError,
)
from .fallback import build_fallback_recommendations
from .groq_client import GroqLLMClient
from .models import Phase4Result
from .parser import build_repair_prompt, parse_llm_payload
from .validator import validate_recommendations

logger = logging.getLogger(__name__)


def _empty_result(message: str) -> Phase4Result:
    return Phase4Result(
        recommendations=[],
        summary=None,
        used_fallback=False,
        skip_llm=True,
        no_match_message=message,
    )


def _run_llm_with_repair(
    client: GroqLLMClient,
    prompt: LLMPrompt,
) -> tuple[dict[str, object], list[str]]:
    """Call Groq and optionally repair malformed JSON once (RE-03)."""
    warnings: list[str] = []
    user_message = prompt.user_message
    raw = client.complete(
        system_message=prompt.system_message,
        user_message=user_message,
    )

    for attempt in range(MAX_REPAIR_ATTEMPTS + 1):
        try:
            payload = parse_llm_payload(raw)
            return payload, warnings
        except (LLMResponseError, UnsafeLLMOutputError) as exc:
            if attempt >= MAX_REPAIR_ATTEMPTS:
                raise
            warnings.append(f"Repair attempt {attempt + 1}: {exc}")
            repair_message = build_repair_prompt(user_message, raw)
            raw = client.complete(
                system_message=prompt.system_message,
                user_message=repair_message,
            )

    raise LLMResponseError("Unable to parse LLM response after repair attempts.")


def run_phase4(
    phase3_result: Phase3Result,
    preferences: ValidatedPreferences,
    *,
    client: GroqLLMClient | None = None,
    top_n: int = TOP_N_RECOMMENDATIONS,
    allow_fallback: bool = True,
) -> Phase4Result:
    """
    Execute Phase 4 recommendation engine with Groq.

    Architecture flow:
        LLM Prompt --> Groq LLM Service --> Ranked Results + Explanations
    """
    if phase3_result.skip_llm or not phase3_result.prompt:
        message = phase3_result.no_match_message or "No candidates available for ranking."
        logger.warning("Phase 4 skipped: %s", message)
        return _empty_result(message)

    if not phase3_result.candidates:
        return _empty_result(phase3_result.no_match_message or "No candidates to rank.")

    prompt = phase3_result.prompt
    llm_client = client

    try:
        if llm_client is None:
            llm_client = GroqLLMClient()

        payload, parse_warnings = _run_llm_with_repair(llm_client, prompt)
        raw_items = payload.get("recommendations", [])
        if not isinstance(raw_items, list):
            raise LLMResponseError("'recommendations' must be a list.")

        recommendations, validation_warnings = validate_recommendations(
            raw_items,
            phase3_result.candidates,
            preferences,
            top_n=top_n,
        )
        warnings = parse_warnings + validation_warnings

        if not recommendations:
            raise LLMResponseError(
                "LLM returned no valid recommendations after validation (RE-04/RE-05)."
            )

        summary = payload.get("summary")
        if isinstance(summary, str) and summary.strip():
            summary_text: str | None = summary.strip()
        else:
            summary_text = None
            if summary is not None:
                warnings.append("Ignored non-string summary from LLM (RE-11).")

        logger.info(
            "Phase 4 LLM ranking complete: recommendations=%s model=%s",
            len(recommendations),
            llm_client.model,
        )
        return Phase4Result(
            recommendations=recommendations,
            summary=summary_text,
            used_fallback=False,
            llm_model=llm_client.model,
            warnings=warnings,
        )

    except (GroqConfigurationError, GroqAPIError, LLMResponseError, UnsafeLLMOutputError) as exc:
        logger.error("Phase 4 LLM path failed: %s", exc)
        if not allow_fallback:
            raise

        reason = str(exc)
        if isinstance(exc, GroqAPIError) and exc.status_code == 429:
            reason = "Groq rate limit exceeded — try again shortly (RE-12)."

        recommendations, summary = build_fallback_recommendations(
            phase3_result.candidates,
            preferences,
            top_n=top_n,
            reason=reason,
        )
        return Phase4Result(
            recommendations=recommendations,
            summary=summary,
            used_fallback=True,
            fallback_reason=reason,
            llm_model=getattr(llm_client, "model", None),
            warnings=[f"Fallback ranking used: {reason}"],
        )


def recommend(
    phase3_result: Phase3Result,
    preferences: ValidatedPreferences,
    *,
    api_key: str | None = None,
    model: str | None = None,
    top_n: int = TOP_N_RECOMMENDATIONS,
    allow_fallback: bool = True,
) -> Phase4Result:
    """Convenience API for later phases."""
    client = None
    if api_key is not None or model is not None:
        from .config import DEFAULT_GROQ_MODEL

        client = GroqLLMClient(
            api_key=api_key,
            model=model or DEFAULT_GROQ_MODEL,
        )
    return run_phase4(
        phase3_result,
        preferences,
        client=client,
        top_n=top_n,
        allow_fallback=allow_fallback,
    )
