"""Root endpoint with API usage hints."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["root"])


@router.get("/")
def root() -> JSONResponse:
    """
    Helpful landing page for developers who open the API URL in a browser.

    The web UI runs on the Phase 7 frontend (Vite), not on this port.
    """
    return JSONResponse(
        {
            "service": "Zomato Recommendation API (Phase 6)",
            "message": "This is the backend API. Open the frontend UI to use the app.",
            "frontend_dev_url": "http://localhost:5173",
            "docs_url": "/docs",
            "endpoints": {
                "health": "/health",
                "ready": "/ready",
                "locations": "/catalog/locations",
                "cuisines": "/catalog/cuisines",
                "recommend": "POST /recommend",
            },
        }
    )
