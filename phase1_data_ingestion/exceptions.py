"""Phase 1 ingestion errors (DI-01, DI-02, DI-03, DI-13)."""


class DataIngestionError(Exception):
    """Base error for Phase 1 data ingestion."""


class DatasetLoadError(DataIngestionError):
    """Raised when the Hugging Face dataset cannot be loaded (DI-01)."""


class EmptyDatasetError(DataIngestionError):
    """Raised when the dataset has zero rows (DI-02)."""


class SchemaValidationError(DataIngestionError):
    """Raised when required columns are missing or schema changed (DI-03, DI-13)."""
