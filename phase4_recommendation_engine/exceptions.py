"""Phase 4 recommendation engine errors."""


class RecommendationEngineError(Exception):
    """Base error for Phase 4 recommendation engine."""


class GroqConfigurationError(RecommendationEngineError):
    """Raised when Groq API key or model configuration is missing."""


class GroqAPIError(RecommendationEngineError):
    """Raised when Groq API calls fail after retries (RE-01, RE-12)."""

    def __init__(
        self,
        message: str,
        *,
        retryable: bool = True,
        status_code: int | None = None,
    ) -> None:
        self.retryable = retryable
        self.status_code = status_code
        super().__init__(message)


class LLMResponseError(RecommendationEngineError):
    """Raised when LLM output is empty or unusable (RE-02, RE-03)."""


class UnsafeLLMOutputError(RecommendationEngineError):
    """Raised when LLM output contains unsafe content (RE-14)."""
