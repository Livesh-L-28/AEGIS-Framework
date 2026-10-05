"""Integration test suite executing real provider communication against local infrastructure.

Marked with @pytest.mark.integration so standard CI runs remain decoupled and offline.
"""

from datetime import UTC, datetime, timedelta

import pytest

from aegis.providers.config import (
    KubernetesConfig,
    LokiConfig,
    OpenTelemetryConfig,
    PrometheusConfig,
)
from aegis.providers.errors import ProviderError
from aegis.providers.production.kubernetes import KubernetesProvider
from aegis.providers.production.loki import LokiLogProvider
from aegis.providers.production.opentelemetry import OpenTelemetryTraceProvider
from aegis.providers.production.prometheus import PrometheusMetricsProvider
from aegis.remediation import RemediationActionType


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_prometheus_provider():
    """Verify PrometheusMetricsProvider communicates with real Prometheus HTTP API."""
    config = PrometheusConfig(base_url="http://localhost:19090", default_step="1s")
    provider = PrometheusMetricsProvider(config)
    now = datetime.now(UTC)
    start = now - timedelta(minutes=5)

    # Allow up to 10 seconds for initial scrape target evaluation in real container
    results = []
    for _ in range(10):
        results = await provider.query_metric("up", start_time=start, end_time=datetime.now(UTC))
        if results:
            break
        import asyncio
        await asyncio.sleep(1)

    assert isinstance(results, list)
    assert len(results) > 0
    first = results[0]
    assert first["metric_name"] == "up"
    assert "value" in first
    assert "timestamp" in first
    assert first["provenance"].startswith("prometheus:up")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_loki_provider():
    """Verify LokiLogProvider communicates with real Grafana Loki HTTP LogQL API."""
    config = LokiConfig(base_url="http://localhost:3100")
    provider = LokiLogProvider(config)
    now = datetime.now(UTC)
    start = now - timedelta(minutes=10)

    logs = await provider.query_logs(
        query="*",
        start_time=start,
        end_time=now,
        service_name="demo-service",
        limit=50
    )
    assert isinstance(logs, list)
    for entry in logs:
        assert "message" in entry
        assert "timestamp" in entry
        assert entry["provenance"].startswith("loki:")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_opentelemetry_provider():
    """Verify OpenTelemetryTraceProvider communicates with trace endpoint and parses span DAGs."""
    config = OpenTelemetryConfig(base_url="http://localhost:18080")
    provider = OpenTelemetryTraceProvider(config)
    now = datetime.now(UTC)
    start = now - timedelta(minutes=10)

    spans = await provider.query_spans(
        service_name="demo-service",
        start_time=start,
        end_time=now,
    )
    assert isinstance(spans, list)
    if spans:
        span = spans[0]
        assert "trace_id" in span
        assert "span_id" in span
        assert "duration_ms" in span
        assert "span_name" in span


@pytest.mark.integration
@pytest.mark.asyncio
async def test_kubernetes_provider_invariants():
    """Verify KubernetesProvider adheres to read_only=True default and allows controlled typed mutation."""
    # 1. Read-only default blocks mutation
    ro_provider = KubernetesProvider(KubernetesConfig(read_only=True))
    ro_provider.register_workload(name="demo-service", namespace="aegis-integration", replicas=1)

    status = await ro_provider.get_deployment_status("demo-service", namespace="aegis-integration")
    assert status is not None
    assert status["replicas"] == 1

    with pytest.raises(ProviderError) as exc:
        await ro_provider.execute_action(
            action_type=RemediationActionType.SCALING.value,
            target="demo-service",
            parameters={"namespace": "aegis-integration", "replicas": 2}
        )
    assert "READ_ONLY mode" in str(exc.value)

    # 2. Explicit mutable config executes typed scaling without shell
    rw_provider = KubernetesProvider(KubernetesConfig(read_only=False))
    rw_provider.register_workload(name="demo-service", namespace="aegis-integration", replicas=1)

    result = await rw_provider.execute_action(
        action_type=RemediationActionType.SCALING.value,
        target="demo-service",
        parameters={"namespace": "aegis-integration", "replicas": 2}
    )
    assert result["status"] == "COMPLETED"
    assert "scaled to 2 replicas" in result["message"]

    post_status = await rw_provider.get_deployment_status("demo-service", namespace="aegis-integration")
    assert post_status is not None
    assert post_status["replicas"] == 2
