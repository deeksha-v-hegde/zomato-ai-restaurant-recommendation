"""Configuration for Phase 4: Recommendation Engine (Groq)."""

from __future__ import annotations

import os
from pathlib import Path

PHASE4_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PHASE4_ROOT.parent

# Groq settings (RE-01, RE-12, RE-13)
GROQ_API_KEY_ENV = "GROQ_API_KEY"
GROQ_MODEL_ENV = "GROQ_MODEL"
DEFAULT_GROQ_MODEL = "groq/compound-mini"

ENV_FILE = PROJECT_ROOT / ".env"
GROQ_TEMPERATURE = 0.0
GROQ_MAX_TOKENS = 2048
GROQ_TIMEOUT_SECONDS = 60.0

# Retry with exponential backoff (RE-01, RE-12)
MAX_LLM_RETRIES = 4
RETRY_BASE_DELAY_SECONDS = 2.0
RETRY_MAX_DELAY_SECONDS = 10.0


# One schema-repair attempt before fallback (RE-03)
MAX_REPAIR_ATTEMPTS = 1

# How many recommendations to request from the LLM
TOP_N_RECOMMENDATIONS = 5

# Fallback explanation when LLM omits text (RE-08)
DEFAULT_EXPLANATION = (
    "Matches your filters for location, budget, cuisine, and minimum rating."
)

# Patterns suggesting unsafe LLM output (RE-14)
UNSAFE_OUTPUT_PATTERNS = (
    r"ignore\s+(all\s+)?(previous|above|prior)\s+instructions",
    r"<\s*/?\s*script\s*>",
)
