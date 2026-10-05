"""Production provider adapters for Prometheus, OpenTelemetry, Loki, GitHub, and Kubernetes."""

from aegis.providers.production.github import GitHubDeploymentProvider
from aegis.providers.production.kubernetes import KubernetesProvider
from aegis.providers.production.loki import LokiLogProvider
from aegis.providers.production.opentelemetry import OpenTelemetryTraceProvider
from aegis.providers.production.prometheus import PrometheusMetricsProvider
from aegis.providers.production.webhooks import GitHubWebhookHandler, WebhookIngestResult

__all__ = [
    "GitHubDeploymentProvider",
    "GitHubWebhookHandler",
    "KubernetesProvider",
    "LokiLogProvider",
    "OpenTelemetryTraceProvider",
    "PrometheusMetricsProvider",
    "WebhookIngestResult",
]
