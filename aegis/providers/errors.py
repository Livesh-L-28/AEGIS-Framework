"""Production-grade exceptions and error model for AEGIS providers."""

from typing import Any


class ProviderError(Exception):
    """Base exception for all AEGIS provider errors.

    Ensures safe error messages that never leak credentials or internal tokens.
    """

    def __init__(
        self,
        message: str,
        provider_name: str = "unknown",
        details: dict[str, Any] | None = None,
    ) -> None:
        self.provider_name = provider_name
        self.details = details or {}
        sanitized_msg = self._sanitize(message)
        super().__init__(f"[{provider_name}] {sanitized_msg}")

    @staticmethod
    def _sanitize(msg: str) -> str:
        """Strip possible secrets or tokens from error message strings."""
        lower = msg.lower()
        for pattern in ("bearer ", "token=", "key=", "password=", "secret="):
            if pattern in lower:
                # Redact substring
                idx = lower.find(pattern)
                return msg[: idx + len(pattern)] + "[REDACTED]"
        return msg


class ProviderTimeoutError(ProviderError):
    """Raised when a provider request times out."""


class ProviderAuthenticationError(ProviderError):
    """Raised on authentication or authorization failure (401/403). Non-retryable."""


class ProviderRateLimitError(ProviderError):
    """Raised when provider rate limit is exceeded (429)."""

    def __init__(
        self,
        message: str,
        provider_name: str = "unknown",
        retry_after_seconds: float | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, provider_name, details)
        self.retry_after_seconds = retry_after_seconds


class ProviderUnavailableError(ProviderError):
    """Raised when provider service is unreachable or 503/502/504."""


class ProviderInvalidResponseError(ProviderError):
    """Raised when provider returns an unparseable or schema-invalid response."""


class ProviderConfigurationError(ProviderError):
    """Raised when provider configuration parameters are missing or invalid."""


__all__ = [
    "ProviderAuthenticationError",
    "ProviderConfigurationError",
    "ProviderError",
    "ProviderInvalidResponseError",
    "ProviderRateLimitError",
    "ProviderTimeoutError",
    "ProviderUnavailableError",
]
