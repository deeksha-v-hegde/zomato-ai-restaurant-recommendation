"""Phase 3 integration layer errors."""


class IntegrationLayerError(Exception):
    """Base error for Phase 3 integration layer."""


class NoCandidatesError(IntegrationLayerError):
    """Raised when filters return zero candidates (IL-01)."""

    def __init__(self, message: str, refine_hints: list[str] | None = None) -> None:
        self.refine_hints = refine_hints or [message]
        super().__init__(message)


class PromptTooLargeError(IntegrationLayerError):
    """Raised when a prompt cannot be reduced below context limits (IL-08)."""
