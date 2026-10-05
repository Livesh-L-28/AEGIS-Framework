"""AEGIS Framework Provider Interfaces — Neutral protocols for infrastructure decoupling.

Every component in AEGIS that interacts with external infrastructure
(metrics, logs, traces, models, vectors, approvals) depends exclusively
on these abstract protocols.
"""

from collections.abc import Sequence
from datetime import datetime
from typing import Any, Protocol, runtime_checkable
from uuid import UUID

from aegis.providers.config import (
    GitHubConfig,
    HTTPClientConfig,
    KubernetesConfig,
    LokiConfig,
    OpenTelemetryConfig,
    PrometheusConfig,
)
from aegis.providers.errors import (
    ProviderAuthenticationError,
    ProviderConfigurationError,
    ProviderError,
    ProviderInvalidResponseError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)


@runtime_checkable
class MetricsProvider(Protocol):
    """Protocol for querying infrastructure and application metrics."""

    async def query_metric(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        service_name: str | None = None,
        labels: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        """Query time series data points."""
        ...


@runtime_checkable
class LogProvider(Protocol):
    """Protocol for querying service and container logs."""

    async def query_logs(
        self,
        query: str,
        start_time: datetime,
        end_time: datetime,
        service_name: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Query log entries within a time window."""
        ...


@runtime_checkable
class TraceProvider(Protocol):
    """Protocol for querying distributed traces and span graphs."""

    async def query_spans(
        self,
        service_name: str,
        start_time: datetime,
        end_time: datetime,
        min_duration_ms: float | None = None,
        only_errors: bool = False,
    ) -> list[dict[str, Any]]:
        """Query distributed trace spans."""
        ...


@runtime_checkable
class TelemetryProvider(Protocol):
    """Unified telemetry protocol combining metrics, logs, and traces."""

    async def collect_telemetry(
        self,
        service_name: str,
        start_time: datetime,
        end_time: datetime,
    ) -> dict[str, Any]:
        """Collect unified telemetry bundle."""
        ...


@runtime_checkable
class DeploymentProvider(Protocol):
    """Protocol for querying deployment, release, and config history."""

    async def list_recent_deployments(
        self,
        service_name: str | None,
        start_time: datetime,
        end_time: datetime,
    ) -> list[dict[str, Any]]:
        """List deployment events and releases within timeframe."""
        ...


@runtime_checkable
class ModelProvider(Protocol):
    """Protocol for LLM reasoning and generation backends."""

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        system_instruction: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Generate structured or text response from model."""
        ...


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Protocol for vector embeddings generation."""

    async def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        """Compute vector embeddings for a batch of text strings."""
        ...


@runtime_checkable
class VectorIndexProvider(Protocol):
    """Protocol for similarity search over document embeddings."""

    async def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search top-k matching documents by embedding vector."""
        ...


@runtime_checkable
class ApprovalStore(Protocol):
    """Protocol for storing and evaluating remediation approval records."""

    async def get_approval(self, remediation_id: UUID) -> dict[str, Any] | None:
        """Fetch approval record for remediation proposal."""
        ...

    async def store_approval(self, approval: dict[str, Any]) -> None:
        """Persist approval record."""
        ...


@runtime_checkable
class RemediationProvider(Protocol):
    """Protocol for executing verified infrastructure remediation actions."""

    async def execute_action(
        self,
        action_type: str,
        target: str,
        parameters: dict[str, Any],
        timeout_seconds: int = 60,
    ) -> dict[str, Any]:
        """Execute remediation action on external system."""
        ...


@runtime_checkable
class StorageProvider(Protocol):
    """Protocol for persistence of artifacts, reports, and knowledge."""

    async def save(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Store binary payload and return URI."""
        ...

    async def get(self, key: str) -> bytes | None:
        """Retrieve binary payload."""
        ...


__all__ = [
    "ApprovalStore",
    "DeploymentProvider",
    "EmbeddingProvider",
    "GitHubConfig",
    "HTTPClientConfig",
    "KubernetesConfig",
    "LogProvider",
    "LokiConfig",
    "MetricsProvider",
    "ModelProvider",
    "OpenTelemetryConfig",
    "PrometheusConfig",
    "ProviderAuthenticationError",
    "ProviderConfigurationError",
    "ProviderError",
    "ProviderInvalidResponseError",
    "ProviderRateLimitError",
    "ProviderTimeoutError",
    "ProviderUnavailableError",
    "RemediationProvider",
    "StorageProvider",
    "TelemetryProvider",
    "TraceProvider",
    "VectorIndexProvider",
]
