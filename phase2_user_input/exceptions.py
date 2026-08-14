"""Phase 2 user-input errors."""


class UserInputError(Exception):
    """Base error for Phase 2 user input."""


class PreferenceValidationError(UserInputError):
    """Raised when preference validation fails."""

    def __init__(self, message: str, errors: list[str] | None = None) -> None:
        self.errors = errors or [message]
        super().__init__(message)


class DuplicateSubmitError(UserInputError):
    """Raised when the same preferences are submitted too quickly (UI-15)."""
