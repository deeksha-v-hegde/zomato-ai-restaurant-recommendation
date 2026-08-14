"""Parse JSON recommendations from Groq LLM responses."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from .exceptions import LLMResponseError, UnsafeLLMOutputError
from .config import UNSAFE_OUTPUT_PATTERNS

logger = logging.getLogger(__name__)

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)
_UNSAFE_RE = re.compile("|".join(UNSAFE_OUTPUT_PATTERNS), re.IGNORECASE)


def _check_safe_text(text: str) -> None:
    if _UNSAFE_RE.search(text):
        raise UnsafeLLMOutputError(
            "LLM output contained unsafe or instruction-like content (RE-14)."
        )


def extract_json_text(raw: str) -> str:
    """Strip markdown fences and surrounding whitespace from LLM output."""
    text = raw.strip()
    if not text:
        raise LLMResponseError("LLM returned an empty response (RE-02).")

    _check_safe_text(text)

    fence_match = _JSON_FENCE_RE.search(text)
    if fence_match:
        return fence_match.group(1).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]

    return text


def parse_llm_payload(raw: str) -> dict[str, Any]:
    """Parse the LLM JSON payload (RE-03)."""
    json_text = extract_json_text(raw)
    try:
        payload = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise LLMResponseError(f"LLM response is not valid JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise LLMResponseError("LLM JSON root must be an object.")

    recommendations = payload.get("recommendations")
    if recommendations is None:
        raise LLMResponseError("LLM JSON missing 'recommendations' array.")

    if not isinstance(recommendations, list):
        raise LLMResponseError("'recommendations' must be a list.")

    summary = payload.get("summary")
    if summary is not None and not isinstance(summary, str):
        raise LLMResponseError("'summary' must be a string when present.")

    return payload


def build_repair_prompt(original_user_message: str, malformed_response: str) -> str:
    """Ask the LLM to repair malformed JSON once (RE-03)."""
    snippet = malformed_response[:2000]
    return (
        f"{original_user_message}\n\n"
        "## Repair request\n"
        "Your previous response was not valid JSON. "
        "Return ONLY a corrected JSON object matching the required schema. "
        "Do not include markdown fences or extra commentary.\n\n"
        f"Previous response:\n{snippet}"
    )
