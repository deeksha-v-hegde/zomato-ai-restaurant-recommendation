"""Recommendation endpoint."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from phase2_user_input.exceptions import PreferenceValidationError

from ...dependencies import get_app_state
from ...schemas.recommend import RecommendRequest, RecommendResponse, ValidationErrorResponse
from ...services.recommendation_service import RecommendationService, validation_error_details

router = APIRouter(tags=["recommend"])


@router.post(
    "/recommend",
    response_model=RecommendResponse,
    responses={422: {"model": ValidationErrorResponse}},
)
def recommend(request: RecommendRequest) -> RecommendResponse:
    state = get_app_state()
    if not state.store_loaded:
        raise HTTPException(
            status_code=503,
            detail=state.startup_error or "Restaurant store is not loaded. Run Phase 1 first.",
        )

    service = RecommendationService(state.records)
    try:
        return service.recommend(request)
    except PreferenceValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=[item.model_dump() for item in validation_error_details(exc)],
        ) from exc
