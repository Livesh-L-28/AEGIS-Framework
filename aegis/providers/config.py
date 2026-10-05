"""Production-grade typed configuration schemas for AEGIS external providers."""

from pydantic import BaseModel, Field


class HTTPClientConfig(BaseModel):
    """Shared HTTP client configuration for external network providers."""

    base_url: str = Field(..., description="Base URL of the external service endpoint")
    timeout_seconds: float = Field(default=10.0, ge=0.5, le=120.0)
    max_retries: int = Field(default=3, ge=0, le=5)
    backoff_factor: float = Field(default=0.5, ge=0.1, le=5.0)
    verify_ssl: bool = Field(default=True, description="Enforce TLS certificate verification by default")
    api_token: str | None = Field(default=None, repr=False, description="Bearer token or secret")
    basic_auth_user: str | None = Field(default=None, description="Basic authentication username")
    basic_auth_password: str | None = Field(default=None, repr=False, description="Basic authentication password")
    custom_headers: dict[str, str] = Field(default_factory=dict, description="Custom HTTP headers")


class PrometheusConfig(HTTPClientConfig):
    """Configuration for Prometheus / Mimir metrics provider."""

    query_timeout_seconds: float = Field(default=15.0)
    default_step: str = Field(default="15s")


class LokiConfig(HTTPClientConfig):
    """Configuration for Grafana Loki log provider."""

    default_limit: int = Field(default=100, ge=1, le=5000)


class OpenTelemetryConfig(HTTPClientConfig):
    """Configuration for OpenTelemetry / Jaeger trace provider."""

    service_name_override: str | None = None


class GitHubConfig(BaseModel):
    """Configuration for GitHub provider & webhook verification."""

    api_base_url: str = Field(default="https://api.github.com")
    token: str | None = Field(default=None, repr=False)
    webhook_secret: str | None = Field(default=None, repr=False)
    timeout_seconds: float = Field(default=10.0)


class KubernetesConfig(BaseModel):
    """Configuration for Kubernetes API provider."""

    kubeconfig_path: str | None = None
    context: str | None = None
    in_cluster: bool = False
    default_namespace: str = "default"
    read_only: bool = True


__all__ = [
    "GitHubConfig",
    "HTTPClientConfig",
    "KubernetesConfig",
    "LokiConfig",
    "OpenTelemetryConfig",
    "PrometheusConfig",
]
