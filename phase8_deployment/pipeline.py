"""Run the recommendation pipeline for the Streamlit app."""

from __future__ import annotations

import html
from dataclasses import dataclass
from functools import lru_cache

from phase2_user_input.catalog import get_known_cuisines, get_known_locations
from phase4_recommendation_engine.groq_client import load_env_file
from phase6_backend_api.app.dependencies import init_app_state
from phase6_backend_api.app.schemas.recommend import RecommendRequest, RecommendResponse
from phase6_backend_api.app.services.recommendation_service import RecommendationService

from .config import PHASE1_CLEAN_STORE


@dataclass
class RuntimeStatus:
    store_loaded: bool
    restaurant_count: int
    groq_configured: bool
    startup_error: str | None = None


@dataclass
class CatalogData:
    locations: list[str]
    cuisines: list[str]


@dataclass
class SearchInput:
    location: str
    budget: str
    cuisine: str
    min_rating: float
    additional_preferences: str | None = None
    cuisine_match_mode: str | None = "or"


@dataclass
class AppContext:
    service: RecommendationService
    status: RuntimeStatus
    catalog: CatalogData


def _title_case(value: str) -> str:
    return " ".join(part.capitalize() for part in value.split())


@lru_cache(maxsize=1)
def load_runtime() -> AppContext:
    """Load Phase 1 store once per process."""
    load_env_file()
    state = init_app_state(PHASE1_CLEAN_STORE)

    locations = sorted(_title_case(key) for key in get_known_locations(state.store_path))
    cuisines = sorted(_title_case(key) for key in get_known_cuisines(state.store_path))

    status = RuntimeStatus(
        store_loaded=state.store_loaded,
        restaurant_count=len(state.records),
        groq_configured=state.groq_configured,
        startup_error=state.startup_error,
    )
    catalog = CatalogData(locations=locations, cuisines=cuisines)
    service = RecommendationService(state.records)
    return AppContext(service=service, status=status, catalog=catalog)


def resolve_location_for_search(ctx: AppContext, requested_location: str, requested_cuisine: str) -> str:
    if requested_location and requested_location not in ("All Locations", "All Areas"):
        return requested_location

    if requested_cuisine and requested_cuisine not in ("All Cuisines", "All Selected"):
        target_cui = requested_cuisine.casefold()
        matching_locs = [
            r.location for r in ctx.service.records
            if any(target_cui in c.casefold() for c in r.cuisines)
        ]
        if matching_locs:
            from collections import Counter
            counts = Counter(matching_locs)
            best_loc = counts.most_common(1)[0][0]
            return _title_case(best_loc)

    for loc in ("Koramangala 5th Block", "Indiranagar", "Jayanagar", "Bellandur"):
        if loc in ctx.catalog.locations:
            return loc
    return ctx.catalog.locations[0]


def run_search(search: SearchInput) -> RecommendResponse:
    load_env_file()
    ctx = load_runtime()

    resolved_loc = resolve_location_for_search(ctx, search.location, search.cuisine)
    request = RecommendRequest(
        location=resolved_loc,
        budget=search.budget,  # type: ignore[arg-type]
        cuisine=search.cuisine if search.cuisine not in ("All Cuisines", "All Selected") else "North Indian",
        min_rating=search.min_rating,
        additional_preferences=search.additional_preferences,
        cuisine_match_mode=search.cuisine_match_mode,  # type: ignore[arg-type]
    )
    return ctx.service.recommend(request)


def decode_display_text(value: str | None) -> str:
    if not value:
        return "N/A"
    return html.unescape(value)
