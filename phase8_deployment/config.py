"""Configuration for Phase 8 Streamlit deployment."""

from __future__ import annotations

import os
from pathlib import Path

PHASE8_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PHASE8_ROOT.parent

PHASE1_CLEAN_STORE = Path(
    os.environ.get(
        "PHASE1_STORE_PATH",
        str(PROJECT_ROOT / "phase1_data_ingestion" / "data" / "cache" / "restaurants_clean.json"),
    )
)

APP_TITLE = "Zomato AI Recommendations"
APP_ICON = "🍽️"
