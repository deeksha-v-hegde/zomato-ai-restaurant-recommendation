"""Configuration for Phase 2: User Input."""

from pathlib import Path

PHASE2_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PHASE2_ROOT.parent
PHASE1_CLEAN_STORE = (
    PROJECT_ROOT / "phase1_data_ingestion" / "data" / "cache" / "restaurants_clean.json"
)

VALID_BUDGETS = frozenset({"low", "medium", "high"})
MIN_RATING = 0.0
MAX_RATING = 5.0

# UI-11: truncate free-text additional preferences
MAX_ADDITIONAL_PREFERENCES_LENGTH = 500

# UI-09: how comma-separated cuisines are combined for Phase 3
DEFAULT_CUISINE_MATCH_MODE = "or"  # "or" | "and"

# UI-15: ignore duplicate submits within this window (seconds)
SUBMIT_DEBOUNCE_SECONDS = 1.5

# Reuse Phase 1 style location aliases for UI-04
LOCATION_ALIASES = {
    "bengaluru": "bangalore",
    "bangaluru": "bangalore",
    "blr": "bangalore",
    "new delhi": "delhi",
    "ncr": "delhi",
    "delhi ncr": "delhi",
    "mumbai suburban": "mumbai",
    "navi mumbai": "mumbai",
}

# Patterns that look like prompt-injection attempts (UI-14)
INJECTION_PATTERNS = (
    r"ignore\s+(all\s+)?(previous|above|prior)\s+instructions",
    r"disregard\s+(all\s+)?(previous|above|prior)\s+instructions",
    r"system\s*prompt",
    r"you\s+are\s+now\s+",
    r"<\s*/?\s*script\s*>",
)
