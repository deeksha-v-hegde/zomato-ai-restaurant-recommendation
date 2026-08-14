"""Pydantic schemas for health endpoints."""

from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class ReadyResponse(BaseModel):
    ready: bool
    store_loaded: bool
    restaurant_count: int
    groq_configured: bool
    message: str | None = None
