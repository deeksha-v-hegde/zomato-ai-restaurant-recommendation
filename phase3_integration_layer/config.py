"""Configuration for Phase 3: Integration Layer."""

from pathlib import Path

PHASE3_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PHASE3_ROOT.parent
PHASE1_CLEAN_STORE = (
    PROJECT_ROOT / "phase1_data_ingestion" / "data" / "cache" / "restaurants_clean.json"
)

# IL-03: cap shortlist before prompting to stay well within Groq rate limits
MAX_CANDIDATES = 10

# IL-08: keep prompts within a safe size for downstream LLM context
MAX_PROMPT_CHARS = 6000
MAX_CANDIDATES_AFTER_TRUNCATION = 10


# Budget band thresholds (aligned with Phase 1 — IL-04)
BUDGET_LOW_MAX = 300
BUDGET_MEDIUM_MAX = 700

# How many top recommendations Phase 4 should return
TOP_N_RECOMMENDATIONS = 5
