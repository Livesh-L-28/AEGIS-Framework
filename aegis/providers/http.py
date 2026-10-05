"""HTTP transport and client utilities with bounded retry and backoff."""

import asyncio
from typing import Any

import httpx

from aegis.providers.config import HTTPClientConfig
from aegis.providers.errors import (
    ProviderAuthenticationError,
    ProviderInvalidResponseError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)


class ResilientHTTPClient:
    """Manages HTTP requests with timeouts, bounded exponential backoff, and safe error mapping."""

    def __init__(self, config: HTTPClientConfig, provider_name: str = "http_provider") -> None:
        self.config = config
        self.provider_name = provider_name

    def _build_headers(self) -> dict[str, str]:
        headers = dict(self.config.custom_headers)
        if self.config.api_token:
            headers["Authorization"] = f"Bearer {self.config.api_token}"
        return headers

    def _build_auth(self) -> tuple[str, str] | None:
        if self.config.basic_auth_user and self.config.basic_auth_password:
            return (self.config.basic_auth_user, self.config.basic_auth_password)
        return None

    async def get_json(
        self,
        endpoint_path: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Perform resilient GET request and return parsed JSON."""
        url = self.config.base_url.rstrip("/") + "/" + endpoint_path.lstrip("/")
        headers = self._build_headers()
        auth = self._build_auth()

        last_error: Exception | None = None
        for attempt in range(self.config.max_retries + 1):
            try:
                async with httpx.AsyncClient(
                    verify=self.config.verify_ssl,
                    timeout=self.config.timeout_seconds,
                ) as client:
                    resp = await client.get(url, params=params, headers=headers, auth=auth)

                # HTTP status code mapping
                if resp.status_code in (401, 403):
                    raise ProviderAuthenticationError(
                        f"Authentication failed: HTTP {resp.status_code}",
                        provider_name=self.provider_name,
                    )
                if resp.status_code == 429:
                    retry_after = resp.headers.get("Retry-After")
                    sec = float(retry_after) if retry_after and retry_after.isdigit() else 2.0
                    raise ProviderRateLimitError(
                        f"Rate limit exceeded (HTTP 429), retry after {sec}s",
                        provider_name=self.provider_name,
                        retry_after_seconds=sec,
                    )
                if resp.status_code in (502, 503, 504):
                    raise ProviderUnavailableError(
                        f"Service unavailable: HTTP {resp.status_code}",
                        provider_name=self.provider_name,
                    )
                resp.raise_for_status()

                try:
                    return resp.json()
                except Exception as json_err:
                    raise ProviderInvalidResponseError(
                        f"Failed to parse JSON response: {json_err}",
                        provider_name=self.provider_name,
                    ) from json_err

            except (ProviderAuthenticationError, ProviderInvalidResponseError):
                # Non-retryable
                raise

            except httpx.TimeoutException:
                last_error = ProviderTimeoutError(
                    f"Request timed out after {self.config.timeout_seconds}s",
                    provider_name=self.provider_name,
                )
            except (httpx.ConnectError, httpx.NetworkError, ProviderUnavailableError, ProviderRateLimitError) as ne:
                last_error = ProviderUnavailableError(
                    f"Network / availability error: {ne}",
                    provider_name=self.provider_name,
                )
            except Exception as exc:
                last_error = ProviderUnavailableError(
                    f"Unexpected transport failure: {exc}",
                    provider_name=self.provider_name,
                )

            # Backoff before retry
            if attempt < self.config.max_retries:
                delay = self.config.backoff_factor * (2**attempt)
                await asyncio.sleep(delay)

        if last_error:
            raise last_error
        raise ProviderUnavailableError("Request failed after retries", provider_name=self.provider_name)


__all__ = ["ResilientHTTPClient"]
