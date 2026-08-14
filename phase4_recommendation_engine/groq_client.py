"""Groq LLM client for Phase 4."""

from __future__ import annotations

import logging
import os
import time
from typing import Any

from .config import (
    DEFAULT_GROQ_MODEL,
    ENV_FILE,
    GROQ_API_KEY_ENV,
    GROQ_MAX_TOKENS,
    GROQ_MODEL_ENV,
    GROQ_TEMPERATURE,
    GROQ_TIMEOUT_SECONDS,
    MAX_LLM_RETRIES,
    RETRY_BASE_DELAY_SECONDS,
    RETRY_MAX_DELAY_SECONDS,
)
from .exceptions import GroqAPIError, GroqConfigurationError

logger = logging.getLogger(__name__)

_dotenv_loaded = False


def load_env_file() -> None:
    """Load project-root .env into os.environ when present."""
    global _dotenv_loaded
    if _dotenv_loaded:
        return
    _dotenv_loaded = True

    if not ENV_FILE.exists():
        return

    try:
        from dotenv import load_dotenv
    except ImportError:
        logger.debug("python-dotenv not installed; skipping .env load.")
        return

    load_dotenv(ENV_FILE)
    logger.debug("Loaded environment from %s", ENV_FILE)


def get_groq_api_key() -> str:
    load_env_file()
    api_key = os.environ.get(GROQ_API_KEY_ENV, "").strip()
    if not api_key:
        raise GroqConfigurationError(
            f"Missing Groq API key. Set the {GROQ_API_KEY_ENV} environment variable."
        )
    return api_key


def _is_retryable_error(exc: Exception) -> bool:
    status_code = getattr(exc, "status_code", None)
    if status_code in {408, 429, 500, 502, 503, 504}:
        return True
    message = str(exc).casefold()
    retry_markers = ("timeout", "timed out", "connection", "rate limit", "overloaded")
    return any(marker in message for marker in retry_markers)


def _retry_delay(attempt: int) -> float:
    delay = RETRY_BASE_DELAY_SECONDS * (2 ** attempt)
    return min(delay, RETRY_MAX_DELAY_SECONDS)


class GroqLLMClient:
    """Thin wrapper around the Groq chat completions API."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        temperature: float = GROQ_TEMPERATURE,
        max_tokens: int = GROQ_MAX_TOKENS,
        timeout: float = GROQ_TIMEOUT_SECONDS,
    ) -> None:
        load_env_file()
        self.api_key = api_key or get_groq_api_key()
        self.model = model or os.environ.get(GROQ_MODEL_ENV, DEFAULT_GROQ_MODEL).strip() or DEFAULT_GROQ_MODEL
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self._client: Any | None = None

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                from groq import Groq
            except ImportError as exc:
                raise GroqConfigurationError(
                    "Groq SDK not installed. Run: pip install groq"
                ) from exc
            self._client = Groq(api_key=self.api_key, timeout=self.timeout)
        return self._client

    def complete(
        self,
        *,
        system_message: str,
        user_message: str,
        json_mode: bool = True,
    ) -> str:
        """
        Send a chat completion request with retries (RE-01, RE-12).

        Returns the assistant message content.
        """
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ]
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        last_error: Exception | None = None
        for attempt in range(MAX_LLM_RETRIES):
            try:
                client = self._get_client()
                response = client.chat.completions.create(**kwargs)
                content = response.choices[0].message.content
                if content is None or not str(content).strip():
                    raise GroqAPIError(
                        "Groq returned an empty completion (RE-02).",
                        retryable=True,
                    )
                return str(content).strip()
            except GroqConfigurationError:
                raise
            except Exception as exc:
                last_error = exc
                retryable = _is_retryable_error(exc)
                if attempt >= MAX_LLM_RETRIES - 1 or not retryable:
                    status_code = getattr(exc, "status_code", None)
                    raise GroqAPIError(
                        f"Groq API call failed: {exc}",
                        retryable=retryable,
                        status_code=status_code,
                    ) from exc

                delay = _retry_delay(attempt)
                logger.warning(
                    "Groq call failed (attempt %s/%s): %s — retrying in %.1fs",
                    attempt + 1,
                    MAX_LLM_RETRIES,
                    exc,
                    delay,
                )
                time.sleep(delay)

        raise GroqAPIError(f"Groq API call failed: {last_error}")
