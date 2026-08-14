"""Pydantic schemas for catalog endpoints."""

from __future__ import annotations

from pydantic import BaseModel


class CatalogResponse(BaseModel):
    count: int
    items: list[str]
