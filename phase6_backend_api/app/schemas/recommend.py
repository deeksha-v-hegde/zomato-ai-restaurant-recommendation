"""Pydantic schemas for POST /recommend."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class RecommendRequest(BaseModel):
    location: str = Field(..., min_length=1, description="Location preference")
    budget: str = Field(..., min_length=1, description="Budget band: low | medium | high")
    cuisine: str = Field(..., min_length=1, description="Cuisine (comma-separated allowed)")
    min_rating: float = Field(..., ge=0.0, le=5.0, description="Minimum rating 0-5")
    additional_preferences: str | None = Field(
        default=None,
        description="Optional free-text preferences",
    )
    cuisine_match_mode: Literal["or", "and"] | None = Field(
        default=None,
        description="How multiple cuisines are matched",
    )


class PreferencesSummary(BaseModel):
    location: str
    location_key: str
    budget: str
    cuisines: list[str]
    min_rating: float


class RecommendationCard(BaseModel):
    rank: int
    candidate_id: str
    name: str
    location: str
    cuisines: str
    rating: str
    cost: str
    budget_band: str
    explanation: str
    source: str


class FilterDiagnostics(BaseModel):
    total_records: int
    after_location: int
    after_budget: int
    after_cuisine: int
    after_rating: int
    shortlist_count: int


class RecommendResponse(BaseModel):
    state: Literal["results", "no_match", "fallback"]
    preferences: PreferencesSummary | None = None
    recommendations: list[RecommendationCard] = Field(default_factory=list)
    summary: str | None = None
    used_fallback: bool = False
    fallback_reason: str | None = None
    warnings: list[str] = Field(default_factory=list)
    no_match_message: str | None = None
    refine_hints: list[str] = Field(default_factory=list)
    filter_diagnostics: FilterDiagnostics | None = None
    llm_model: str | None = None


class ValidationErrorDetail(BaseModel):
    field: str
    message: str


class ValidationErrorResponse(BaseModel):
    detail: list[ValidationErrorDetail]
