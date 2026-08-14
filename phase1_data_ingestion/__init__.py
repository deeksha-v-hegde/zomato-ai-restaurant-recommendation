"""Phase 1: Data Ingestion package."""

from .exceptions import (
    DataIngestionError,
    DatasetLoadError,
    EmptyDatasetError,
    SchemaValidationError,
)
from .models import RestaurantRecord
from .pipeline import Phase1Result, get_restaurants, run_phase1

__all__ = [
    "DataIngestionError",
    "DatasetLoadError",
    "EmptyDatasetError",
    "SchemaValidationError",
    "RestaurantRecord",
    "Phase1Result",
    "run_phase1",
    "get_restaurants",
]
