"""FastAPI application entrypoint."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import catalog, health, recommend, root
from .config import API_TITLE, API_VERSION, DEFAULT_CORS_ORIGINS
from .dependencies import AppState, init_app_state, set_app_state

logger = logging.getLogger(__name__)

app_state: AppState = AppState()


def _parse_cors_origins() -> list[str]:
    raw = os.environ.get("CORS_ORIGINS", "").strip()
    if not raw:
        return list(DEFAULT_CORS_ORIGINS)
    parsed = [origin.strip() for origin in raw.split(",") if origin.strip()]
    if any("*" in origin for origin in parsed):
        return ["*"]
    return parsed


@asynccontextmanager
async def lifespan(app: FastAPI):
    global app_state
    app_state = init_app_state()
    set_app_state(app_state)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title=API_TITLE, version=API_VERSION, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_parse_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(root.router)
    app.include_router(health.router)
    app.include_router(catalog.router)
    app.include_router(recommend.router)

    return app


app = create_app()
