"""In-memory concrete providers for testing, local execution, and standalone development."""

from aegis.providers.memory.approvals import InMemoryApprovalStore
from aegis.providers.memory.deployments import InMemoryDeploymentProvider
from aegis.providers.memory.logs import InMemoryLogProvider
from aegis.providers.memory.metrics import InMemoryMetricsProvider
from aegis.providers.memory.models import InMemoryModelProvider
from aegis.providers.memory.remediation import InMemoryRemediationProvider
from aegis.providers.memory.storage import InMemoryStorageProvider
from aegis.providers.memory.telemetry import InMemoryTelemetryProvider
from aegis.providers.memory.traces import InMemoryTraceProvider
from aegis.providers.memory.vectors import (
    InMemoryEmbeddingProvider,
    InMemoryVectorIndexProvider,
)

__all__ = [
    "InMemoryApprovalStore",
    "InMemoryDeploymentProvider",
    "InMemoryEmbeddingProvider",
    "InMemoryLogProvider",
    "InMemoryMetricsProvider",
    "InMemoryModelProvider",
    "InMemoryRemediationProvider",
    "InMemoryStorageProvider",
    "InMemoryTelemetryProvider",
    "InMemoryTraceProvider",
    "InMemoryVectorIndexProvider",
]
