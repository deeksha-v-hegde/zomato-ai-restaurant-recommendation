"""Configuration for Phase 6: Backend API."""

from __future__ import annotations

import os
from pathlib import Path

PHASE6_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = PHASE6_ROOT.parent

PHASE1_CLEAN_STORE = Path(
    os.environ.get(
        "PHASE1_STORE_PATH",
        str(PROJECT_ROOT / "phase1_data_ingestion" / "data" / "cache" / "restaurants_clean.json"),
    )
)

ENV_FILE = PROJECT_ROOT / ".env"
API_TITLE = "Zomato Recommendation API"
API_VERSION = "1.0.0"

DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
)

MAX_NAME_LENGTH = 120
MAX_EXPLANATION_LENGTH = 600
