"""Application state and startup dependencies."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

from phase1_data_ingestion.models import RestaurantRecord
from phase1_data_ingestion.store import load_clean_store
from phase4_recommendation_engine.groq_client import load_env_file

from .config import ENV_FILE, PHASE1_CLEAN_STORE

logger = logging.getLogger(__name__)

_app_state: "AppState | None" = None


@dataclass
class AppState:
    """Shared runtime state loaded on startup."""

    store_path: Path = PHASE1_CLEAN_STORE
    records: list[RestaurantRecord] = field(default_factory=list)
    store_loaded: bool = False
    groq_configured: bool = False
    startup_error: str | None = None


def _check_groq_configured() -> bool:
    load_env_file()
    return bool(os.environ.get("GROQ_API_KEY", "").strip())


def init_app_state(store_path: Path = PHASE1_CLEAN_STORE) -> AppState:
    """Load Phase 1 store and verify Groq configuration."""
    state = AppState(store_path=store_path)
    state.groq_configured = _check_groq_configured()

    if ENV_FILE.exists():
        logger.info("Environment file found at %s", ENV_FILE)

    try:
        state.records = load_clean_store(store_path)
        state.store_loaded = bool(state.records)
        logger.info(
            "Phase 6 startup: loaded %s restaurants from %s",
            len(state.records),
            store_path,
        )
    except FileNotFoundError as exc:
        state.startup_error = str(exc)
        logger.error("Phase 1 store not found: %s", exc)
    except Exception as exc:
        state.startup_error = str(exc)
        logger.exception("Failed to load Phase 1 store")

    return state


def set_app_state(state: AppState) -> None:
    global _app_state
    _app_state = state


def get_app_state() -> AppState:
    if _app_state is None:
        return init_app_state()
    return _app_state
