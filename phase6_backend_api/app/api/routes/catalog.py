"""Catalog endpoints for Phase 7 dropdowns."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from phase2_user_input.catalog import get_known_cuisines, get_known_locations

from ...dependencies import get_app_state
from ...schemas.catalog import CatalogResponse

router = APIRouter(prefix="/catalog", tags=["catalog"])


def _title_case_key(key: str) -> str:
    return " ".join(part.capitalize() for part in key.split())


@router.get("/locations", response_model=CatalogResponse)
def list_locations() -> CatalogResponse:
    state = get_app_state()
    if not state.store_loaded:
        raise HTTPException(status_code=503, detail="Restaurant catalog is not available.")

    keys = sorted(get_known_locations(state.store_path))
    items = [_title_case_key(key) for key in keys]
    return CatalogResponse(count=len(items), items=items)


@router.get("/cuisines", response_model=CatalogResponse)
def list_cuisines() -> CatalogResponse:
    state = get_app_state()
    if not state.store_loaded:
        raise HTTPException(status_code=503, detail="Restaurant catalog is not available.")

    keys = sorted(get_known_cuisines(state.store_path))
    items = [_title_case_key(key) for key in keys]
    return CatalogResponse(count=len(items), items=items)
