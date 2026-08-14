"""Health and readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from ...dependencies import get_app_state
from ...schemas.health import HealthResponse, ReadyResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/ready", response_model=ReadyResponse)
def ready() -> ReadyResponse:
    state = get_app_state()
    ready_flag = state.store_loaded and state.groq_configured
    message = None
    if not state.store_loaded:
        message = state.startup_error or "Phase 1 restaurant store is not loaded."
    elif not state.groq_configured:
        message = "GROQ_API_KEY is not configured."

    return ReadyResponse(
        ready=ready_flag,
        store_loaded=state.store_loaded,
        restaurant_count=len(state.records),
        groq_configured=state.groq_configured,
        message=message,
    )
