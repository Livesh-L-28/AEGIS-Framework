"""Unit and integration tests for production providers using local mock HTTP test server."""

from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import pytest

from aegis.providers.config import (
    GitHubConfig,
    KubernetesConfig,
    LokiConfig,
    OpenTelemetryConfig,
    PrometheusConfig,
)
from aegis.providers.errors import (
    ProviderError,
)
from aegis.providers.production import (
    GitHubDeploymentProvider,
    GitHubWebhookHandler,
    KubernetesProvider,
    LokiLogProvider,
    OpenTelemetryTraceProvider,
    PrometheusMetricsProvider,
)


@pytest.mark.asyncio
async def test_prometheus_metrics_provider_success() -> None:
    """Test PrometheusMetricsProvider parsing standard query_range response."""
    now = datetime.now(UTC)
    t0 = now - timedelta(minutes=5)

    def handler(request: httpx.Request) -> httpx.Response:
        assert "/api/v1/query_range" in request.url.path
        return httpx.Response(
            200,
            json={
                "status": "success",
                "data": {
                    "resultType": "matrix",
                    "result": [
                        {
                            "metric": {"__name__": "http_requests_total", "service": "cart-service"},
                            "values": [
                                [str(t0.timestamp()), "150.0"],
                                [str(now.timestamp()), "250.0"],
                            ],
                        }
                    ],
                },
            },
        )

    transport = httpx.MockTransport(handler)
    config = PrometheusConfig(base_url="http://mock-prometheus:9090")
    provider = PrometheusMetricsProvider(config)
    # Inject transport for testing
    provider.client.config.max_retries = 0

    # Overwrite async client creation via mock transport
    async def mock_get_json(endpoint_path: str, params: dict[str, Any] | None = None) -> Any:
        async with httpx.AsyncClient(transport=transport) as client:
            resp = await client.get(f"http://mock-prometheus:9090/{endpoint_path}", params=params)
            return resp.json()

    provider.client.get_json = mock_get_json  # type: ignore

    results = await provider.query_metric("http_requests_total", t0, now, service_name="cart-service")
    assert len(results) == 2
    assert results[0]["value"] == 150.0
    assert results[1]["value"] == 250.0
    assert results[0]["service_name"] == "cart-service"


@pytest.mark.asyncio
async def test_opentelemetry_trace_provider_success() -> None:
    """Test OpenTelemetryTraceProvider parsing spans from traces endpoint."""
    now = datetime.now(UTC)
    t0 = now - timedelta(minutes=5)
    start_us = int(t0.timestamp() * 1_000_000)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "traceID": "trace-abc-123",
                        "spans": [
                            {
                                "traceID": "trace-abc-123",
                                "spanID": "span-root",
                                "operationName": "GET /cart",
                                "startTime": start_us,
                                "duration": 50000,
                                "tags": [{"key": "error", "value": True}, {"key": "message", "value": "Redis timeout"}],
                                "references": [],
                            }
                        ],
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    config = OpenTelemetryConfig(base_url="http://mock-otel:4318")
    provider = OpenTelemetryTraceProvider(config)

    async def mock_get_json(endpoint_path: str, params: dict[str, Any] | None = None) -> Any:
        async with httpx.AsyncClient(transport=transport) as client:
            resp = await client.get(f"http://mock-otel:4318/{endpoint_path}", params=params)
            return resp.json()

    provider.client.get_json = mock_get_json  # type: ignore

    spans = await provider.query_spans("cart-service", t0, now, only_errors=True)
    assert len(spans) == 1
    assert spans[0]["trace_id"] == "trace-abc-123"
    assert spans[0]["is_error"] is True
    assert spans[0]["duration_ms"] == 50.0
    assert spans[0]["error_message"] == "Redis timeout"


@pytest.mark.asyncio
async def test_loki_log_provider_success() -> None:
    """Test LokiLogProvider stream parsing."""
    now = datetime.now(UTC)
    t0 = now - timedelta(minutes=5)
    ts_ns = str(int(now.timestamp() * 1_000_000_000))

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "status": "success",
                "data": {
                    "resultType": "streams",
                    "result": [
                        {
                            "stream": {"service": "checkout", "level": "error"},
                            "values": [
                                [ts_ns, "connection reset by peer"],
                            ],
                        }
                    ],
                },
            },
        )

    transport = httpx.MockTransport(handler)
    config = LokiConfig(base_url="http://mock-loki:3100")
    provider = LokiLogProvider(config)

    async def mock_get_json(endpoint_path: str, params: dict[str, Any] | None = None) -> Any:
        async with httpx.AsyncClient(transport=transport) as client:
            resp = await client.get(f"http://mock-loki:3100/{endpoint_path}", params=params)
            return resp.json()

    provider.client.get_json = mock_get_json  # type: ignore

    logs = await provider.query_logs("level:error", t0, now, service_name="checkout")
    assert len(logs) == 1
    assert logs[0]["service"] == "checkout"
    assert logs[0]["level"] == "ERROR"
    assert logs[0]["message"] == "connection reset by peer"


@pytest.mark.asyncio
async def test_github_deployment_provider() -> None:
    """Test GitHubDeploymentProvider listing deployment records."""
    now = datetime.now(UTC)
    t0 = now - timedelta(hours=1)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=[
                {
                    "id": 9012,
                    "sha": "1234567890abcdef",
                    "ref": "v1.2.0",
                    "environment": "production",
                    "created_at": now.isoformat(),
                    "creator": {"login": "octocat"},
                }
            ],
        )

    transport = httpx.MockTransport(handler)
    config = GitHubConfig(token="test-token")
    provider = GitHubDeploymentProvider(config, "org", "repo")

    async def mock_get_json(endpoint_path: str, params: dict[str, Any] | None = None) -> Any:
        async with httpx.AsyncClient(transport=transport) as client:
            resp = await client.get(f"https://api.github.com/{endpoint_path}", params=params)
            return resp.json()

    provider.client.get_json = mock_get_json  # type: ignore

    deps = await provider.list_recent_deployments("production", t0, now + timedelta(minutes=1))
    assert len(deps) == 1
    assert deps[0]["version"] == "v1.2.0"
    assert deps[0]["commit_sha"] == "1234567890abcdef"
    assert deps[0]["author"] == "octocat"


def test_github_webhook_handler_hmac_verification() -> None:
    """Test webhook signature authentication and event normalization."""
    secret = "super-secret-key"
    handler = GitHubWebhookHandler(secret=secret)

    payload = b'{"action":"created","repository":{"full_name":"org/repo"},"deployment":{"id":42,"ref":"main"}}'
    import hashlib
    import hmac

    valid_sig = "sha256=" + hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()

    # Valid signature
    res = handler.process_webhook("deployment", payload, valid_sig)
    assert res.valid is True
    assert res.repository == "org/repo"
    assert res.deployment_info["deployment_id"] == "42"

    # Invalid signature
    bad_res = handler.process_webhook("deployment", payload, "sha256=invalid")
    assert bad_res.valid is False
    assert "Invalid HMAC" in str(bad_res.error)


@pytest.mark.asyncio
async def test_kubernetes_provider_typed_remediation() -> None:
    """Test typed Kubernetes provider enforces READ_ONLY and mutation controls."""
    config = KubernetesConfig(read_only=True)
    provider = KubernetesProvider(config)
    provider.register_workload("api-gw", "production", replicas=3)

    # Read status works
    status = await provider.get_deployment_status("api-gw", "production")
    assert status is not None
    assert status["replicas"] == 3

    # Mutation fails in READ_ONLY mode
    with pytest.raises(ProviderError, match="READ_ONLY mode"):
        await provider.execute_action("SERVICE_RESTART", "api-gw", {"namespace": "production"})

    # Allow mutation explicitly
    provider.config.read_only = False
    exec_res = await provider.execute_action("SERVICE_RESTART", "api-gw", {"namespace": "production"})
    assert exec_res["status"] == "COMPLETED"
    updated = await provider.get_deployment_status("api-gw", "production")
    assert updated is not None
    assert updated["restart_count"] == 1
