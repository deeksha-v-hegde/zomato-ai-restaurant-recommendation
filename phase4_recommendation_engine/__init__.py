"""Phase 4: Recommendation Engine package (Groq)."""

from .exceptions import (
    GroqAPIError,
    GroqConfigurationError,
    LLMResponseError,
    RecommendationEngineError,
    UnsafeLLMOutputError,
)
from .groq_client import GroqLLMClient, get_groq_api_key
from .models import Phase4Result, Recommendation
from .pipeline import recommend, run_phase4

__all__ = [
    "RecommendationEngineError",
    "GroqConfigurationError",
    "GroqAPIError",
    "LLMResponseError",
    "UnsafeLLMOutputError",
    "Recommendation",
    "Phase4Result",
    "GroqLLMClient",
    "get_groq_api_key",
    "run_phase4",
    "recommend",
]
