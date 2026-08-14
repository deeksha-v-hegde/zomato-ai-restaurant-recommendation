"""Normalize and sanitize raw preference text."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from .config import (
    INJECTION_PATTERNS,
    LOCATION_ALIASES,
    MAX_ADDITIONAL_PREFERENCES_LENGTH,
    VALID_BUDGETS,
)

_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_INJECTION_RE = re.compile("|".join(INJECTION_PATTERNS), re.IGNORECASE)


def sanitize_text(value: Any) -> str | None:
    """Trim and strip unsafe control characters; preserve UTF-8."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    text = unicodedata.normalize("NFC", text)
    text = _CONTROL_CHARS_RE.sub("", text).strip()
    return text or None


def normalize_location(value: Any) -> tuple[str | None, str | None]:
    """Return (display_location, location_key) with alias mapping (UI-04)."""
    text = sanitize_text(value)
    if text is None:
        return None, None

    key = re.sub(r"\s+", " ", text.casefold()).strip()
    key = LOCATION_ALIASES.get(key, key)
    display = text.title() if text == text.upper() or text == text.lower() else text
    return display, key


def normalize_budget(value: Any) -> str | None:
    """Normalize budget to low|medium|high when possible (UI-05)."""
    text = sanitize_text(value)
    if text is None:
        return None

    key = text.casefold()
    aliases = {
        "l": "low",
        "lo": "low",
        "m": "medium",
        "med": "medium",
        "mid": "medium",
        "h": "high",
        "hi": "high",
    }
    key = aliases.get(key, key)
    return key if key in VALID_BUDGETS else None


def split_cuisines(value: Any) -> list[str]:
    """Split comma-separated cuisines and de-duplicate (UI-09)."""
    text = sanitize_text(value)
    if text is None:
        return []

    parts = [part.strip() for part in text.split(",")]
    cuisines: list[str] = []
    seen: set[str] = set()
    for part in parts:
        cleaned = sanitize_text(part)
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key in seen:
            continue
        seen.add(key)
        cuisines.append(cleaned)
    return cuisines


def normalize_cuisine_match_mode(value: Any, default: str = "or") -> str:
    text = sanitize_text(value)
    if text is None:
        return default
    key = text.casefold()
    return key if key in {"or", "and"} else default


def sanitize_additional_preferences(value: Any) -> tuple[str | None, bool, list[str]]:
    """
    Sanitize free-text preferences (UI-10, UI-11, UI-14).

    Returns (text, truncated, warnings).
    """
    text = sanitize_text(value)
    if text is None:
        return None, False, []

    warnings: list[str] = []
    if _INJECTION_RE.search(text):
        # Neutralize injection-like content instead of sending it raw to an LLM.
        text = _INJECTION_RE.sub("[filtered]", text)
        warnings.append(
            "Additional preferences contained instruction-like text that was filtered "
            "for safety (UI-14)."
        )

    truncated = False
    if len(text) > MAX_ADDITIONAL_PREFERENCES_LENGTH:
        text = text[:MAX_ADDITIONAL_PREFERENCES_LENGTH].rstrip()
        truncated = True
        warnings.append(
            f"Additional preferences truncated to {MAX_ADDITIONAL_PREFERENCES_LENGTH} characters."
        )

    return text, truncated, warnings
