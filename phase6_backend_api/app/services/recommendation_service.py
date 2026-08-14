"""Orchestrate Phases 2 → 3 → 4 → 5 for POST /recommend."""

from __future__ import annotations

import logging

from phase1_data_ingestion.models import RestaurantRecord
from phase2_user_input.exceptions import PreferenceValidationError
from phase2_user_input.models import RawUserPreferences, ValidatedPreferences
from phase2_user_input.validator import validate_preferences
from phase3_integration_layer.pipeline import run_phase3
from phase4_recommendation_engine.pipeline import run_phase4

from ..schemas.recommend import (
    FilterDiagnostics,
    PreferencesSummary,
    RecommendRequest,
    RecommendResponse,
    ValidationErrorDetail,
)
from .display_normalizer import normalize_recommendations

logger = logging.getLogger(__name__)


def _preferences_summary(preferences: ValidatedPreferences) -> PreferencesSummary:
    return PreferencesSummary(
        location=preferences.location,
        location_key=preferences.location_key,
        budget=preferences.budget,
        cuisines=preferences.cuisines,
        min_rating=preferences.min_rating,
    )


def _filter_diagnostics(phase3_result) -> FilterDiagnostics:
    diag = phase3_result.diagnostics
    return FilterDiagnostics(
        total_records=diag.total_records,
        after_location=diag.after_location,
        after_budget=diag.after_budget,
        after_cuisine=diag.after_cuisine,
        after_rating=diag.after_rating,
        shortlist_count=diag.shortlist_count,
    )


class RecommendationService:
    """Run the full recommendation pipeline for API requests."""

    def __init__(self, records: list[RestaurantRecord]) -> None:
        self.records = records

    def recommend(self, request: RecommendRequest) -> RecommendResponse:
        raw = RawUserPreferences(
            location=request.location,
            budget=request.budget,
            cuisine=request.cuisine,
            min_rating=request.min_rating,
            additional_preferences=request.additional_preferences,
            cuisine_match_mode=request.cuisine_match_mode,
        )

        try:
            preferences = validate_preferences(raw, check_catalog=False)
        except PreferenceValidationError as exc:
            raise exc

        phase3 = run_phase3(preferences, records=self.records)
        prefs_summary = _preferences_summary(preferences)
        diagnostics = _filter_diagnostics(phase3)
        warnings = list(preferences.warnings)

        if phase3.skip_llm or not phase3.candidates:
            return RecommendResponse(
                state="no_match",
                preferences=prefs_summary,
                recommendations=[],
                no_match_message=phase3.no_match_message,
                refine_hints=phase3.refine_hints,
                filter_diagnostics=diagnostics,
                warnings=warnings,
            )

        phase4 = run_phase4(phase3, preferences, allow_fallback=True)
        warnings.extend(phase4.warnings)

        if phase4.skip_llm and not phase4.recommendations:
            return RecommendResponse(
                state="no_match",
                preferences=prefs_summary,
                recommendations=[],
                no_match_message=phase4.no_match_message,
                refine_hints=phase3.refine_hints,
                filter_diagnostics=diagnostics,
                warnings=warnings,
            )

        cards = normalize_recommendations(phase4)
        state = "fallback" if phase4.used_fallback else "results"

        return RecommendResponse(
            state=state,
            preferences=prefs_summary,
            recommendations=cards,
            summary=phase4.summary,
            used_fallback=phase4.used_fallback,
            fallback_reason=phase4.fallback_reason,
            warnings=warnings,
            filter_diagnostics=diagnostics,
            llm_model=phase4.llm_model,
        )


def validation_error_details(exc: PreferenceValidationError) -> list[ValidationErrorDetail]:
    details: list[ValidationErrorDetail] = []
    for message in exc.errors:
        field = "preferences"
        lowered = message.lower()
        for candidate in ("location", "budget", "cuisine", "rating", "minimum rating"):
            if candidate in lowered:
                field = candidate.replace(" ", "_")
                if field == "minimum_rating":
                    field = "min_rating"
                break
        details.append(ValidationErrorDetail(field=field, message=message))
    return details
