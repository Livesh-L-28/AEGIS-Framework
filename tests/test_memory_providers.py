"""Unit tests for all In-Memory Concrete Providers in AEGIS Framework."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from aegis.providers import (
    ApprovalStore,
    DeploymentProvider,
    EmbeddingProvider,
    LogProvider,
    MetricsProvider,
    ModelProvider,
    RemediationProvider,
    StorageProvider,
    TelemetryProvider,
    TraceProvider,
    VectorIndexProvider,
)
from aegis.providers.memory import (
    InMemoryApprovalStore,
    InMemoryDeploymentProvider,
    InMemoryEmbeddingProvider,
    InMemoryLogProvider,
    InMemoryMetricsProvider,
    InMemoryModelProvider,
    InMemoryRemediationProvider,
    InMemoryStorageProvider,
    InMemoryTelemetryProvider,
    InMemoryTraceProvider,
    InMemoryVectorIndexProvider,
)


def test_in_memory_provider_protocol_conformance() -> None:
    """Verify that every in-memory provider satisfies its respective Protocol."""
    assert isinstance(InMemoryMetricsProvider(), MetricsProvider)
    assert isinstance(InMemoryLogProvider(), LogProvider)
    assert isinstance(InMemoryTraceProvider(), TraceProvider)
    assert isinstance(InMemoryTelemetryProvider(), TelemetryProvider)
    assert isinstance(InMemoryDeploymentProvider(), DeploymentProvider)
    assert isinstance(InMemoryModelProvider(), ModelProvider)
    assert isinstance(InMemoryEmbeddingProvider(), EmbeddingProvider)
    assert isinstance(InMemoryVectorIndexProvider(), VectorIndexProvider)
    assert isinstance(InMemoryApprovalStore(), ApprovalStore)
    assert isinstance(InMemoryStorageProvider(), StorageProvider)
    assert isinstance(InMemoryRemediationProvider(), RemediationProvider)


@pytest.mark.asyncio
async def test_in_memory_metrics_provider() -> None:
    """Test InMemoryMetricsProvider queries and filtering."""
    provider = InMemoryMetricsProvider()
    t0 = datetime(2026, 10, 4, 12, 0, 0, tzinfo=UTC)
    t1 = t0 + timedelta(minutes=5)
    t2 = t0 + timedelta(minutes=10)

    provider.record_metric("http_request_duration_seconds", 0.12, t0, service_name="order-service")
    provider.record_metric("http_request_duration_seconds", 1.60, t1, service_name="order-service")
    provider.record_metric("http_request_duration_seconds", 0.05, t1, service_name="user-service")

    # Filter by service_name
    res = await provider.query_metric("http_request_duration_seconds", t0, t2, service_name="order-service")
    assert len(res) == 2
    assert res[0]["value"] == 0.12
    assert res[1]["value"] == 1.60

    # Wildcard metric query
    all_res = await provider.query_metric("*", t0, t2)
    assert len(all_res) == 3


@pytest.mark.asyncio
async def test_in_memory_log_provider() -> None:
    """Test InMemoryLogProvider structured logs and level parsing."""
    provider = InMemoryLogProvider()
    t0 = datetime(2026, 10, 4, 12, 0, 0, tzinfo=UTC)

    provider.record_log("order-service", "INFO", "Server started", t0)
    provider.record_log("order-service", "ERROR", "database query timeout", t0 + timedelta(seconds=10), request_id="req-1")

    # Query level:error
    err_logs = await provider.query_logs("level:error", t0, t0 + timedelta(minutes=1), service_name="order-service")
    assert len(err_logs) == 1
    assert err_logs[0]["message"] == "database query timeout"
    assert err_logs[0]["request_id"] == "req-1"

    # Query text search
    txt_logs = await provider.query_logs("timeout", t0, t0 + timedelta(minutes=1))
    assert len(txt_logs) == 1


@pytest.mark.asyncio
async def test_in_memory_trace_provider() -> None:
    """Test InMemoryTraceProvider span tree recording and query."""
    provider = InMemoryTraceProvider()
    t0 = datetime(2026, 10, 4, 12, 0, 0, tzinfo=UTC)

    span1 = provider.record_span(service="gateway", name="POST /orders", duration_ms=1600.0, timestamp=t0, is_error=True)
    provider.record_span(
        service="order-service",
        name="OrderService.process",
        duration_ms=1550.0,
        timestamp=t0,
        parent_span_id=span1["span_id"],
        is_error=True,
    )

    err_spans = await provider.query_spans("order-service", t0 - timedelta(minutes=1), t0 + timedelta(minutes=1), only_errors=True)
    assert len(err_spans) == 1
    assert err_spans[0]["parent_span_id"] == span1["span_id"]
    assert err_spans[0]["duration_ms"] == 1550.0


@pytest.mark.asyncio
async def test_in_memory_telemetry_provider() -> None:
    """Test InMemoryTelemetryProvider unified collection."""
    metrics = InMemoryMetricsProvider()
    logs = InMemoryLogProvider()
    traces = InMemoryTraceProvider()

    t0 = datetime(2026, 10, 4, 12, 0, 0, tzinfo=UTC)
    metrics.record_metric("cpu_utilization", 85.0, t0, service_name="auth-service")
    logs.record_log("auth-service", "WARN", "High memory usage", t0)
    traces.record_span("auth-service", "authenticate", 20.0, t0)

    unified = InMemoryTelemetryProvider(metrics, logs, traces)
    bundle = await unified.collect_telemetry("auth-service", t0 - timedelta(minutes=1), t0 + timedelta(minutes=1))

    assert bundle["service_name"] == "auth-service"
    assert len(bundle["metrics"]) == 1
    assert len(bundle["logs"]) == 1
    assert len(bundle["traces"]) == 1


@pytest.mark.asyncio
async def test_in_memory_deployment_provider() -> None:
    """Test InMemoryDeploymentProvider deployment history."""
    provider = InMemoryDeploymentProvider()
    t0 = datetime(2026, 10, 4, 12, 0, 0, tzinfo=UTC)

    provider.record_deployment("dep-1", "order-service", "v1.0.0", "abc1234", t0 - timedelta(hours=1))
    provider.record_deployment("dep-2", "order-service", "v1.1.0", "def5678", t0)

    recent = await provider.list_recent_deployments("order-service", t0 - timedelta(minutes=10), t0 + timedelta(minutes=10))
    assert len(recent) == 1
    assert recent[0]["version"] == "v1.1.0"
    assert recent[0]["commit_sha"] == "def5678"


@pytest.mark.asyncio
async def test_in_memory_model_provider() -> None:
    """Test InMemoryModelProvider deterministic reasoning responses."""
    provider = InMemoryModelProvider(default_response={"title": "Default RCA", "reasoning": "Standard pattern"})
    provider.set_response_for_prompt_substring("database", {"title": "PostgreSQL Saturation", "reasoning": "Connection timeout"})

    resp1 = await provider.generate("Analyze database queries")
    assert "PostgreSQL Saturation" in resp1

    resp2 = await provider.generate("Analyze general health")
    assert "Default RCA" in resp2
    assert len(provider.call_history) == 2


@pytest.mark.asyncio
async def test_in_memory_vector_index_provider() -> None:
    """Test InMemoryEmbeddingProvider and InMemoryVectorIndexProvider."""
    embedder = InMemoryEmbeddingProvider(dimensions=4)
    vectors = await embedder.embed_texts(["database error", "network latency"])
    assert len(vectors) == 2
    assert len(vectors[0]) == 4

    index = InMemoryVectorIndexProvider()
    index.add_document("doc-1", "Fix database connection pooling", [1.0, 0.0, 0.0, 0.0], {"category": "db"})
    index.add_document("doc-2", "Restart ingress routing", [0.0, 1.0, 0.0, 0.0], {"category": "network"})

    # Query matching doc-1
    results = await index.search([1.0, 0.0, 0.0, 0.0], top_k=1)
    assert len(results) == 1
    assert results[0]["id"] == "doc-1"
    assert results[0]["score"] == 1.0


@pytest.mark.asyncio
async def test_in_memory_approval_store() -> None:
    """Test InMemoryApprovalStore persistence and retrieval."""
    store = InMemoryApprovalStore()
    rem_id = uuid4()

    assert await store.get_approval(rem_id) is None

    await store.store_approval({
        "remediation_id": rem_id,
        "author_id": "ai-engine",
        "approver_id": "operator-bob",
        "decision": "APPROVED",
    })

    record = await store.get_approval(rem_id)
    assert record is not None
    assert record["approver_id"] == "operator-bob"
    assert record["decision"] == "APPROVED"
    assert "created_at" in record


@pytest.mark.asyncio
async def test_in_memory_storage_provider() -> None:
    """Test InMemoryStorageProvider save and get."""
    store = InMemoryStorageProvider()
    uri = await store.save("reports/incident-01.json", b'{"incident": "db-spike"}', "application/json")
    assert uri == "memory://reports/incident-01.json"

    data = await store.get("reports/incident-01.json")
    assert data == b'{"incident": "db-spike"}'

    assert await store.get("non-existent") is None
    assert "reports/incident-01.json" in store.list_keys()


@pytest.mark.asyncio
async def test_in_memory_remediation_provider_safe_typed_actions() -> None:
    """Test InMemoryRemediationProvider enforces typed actions and refuses arbitrary commands."""
    provider = InMemoryRemediationProvider()
    provider.set_service_state("order-service", {"status": "DEGRADED", "instances": 2})

    # 1. Execute safe typed service restart
    res = await provider.execute_action("SERVICE_RESTART", "order-service", {"graceful": True})
    assert res["status"] == "COMPLETED"
    state = provider.get_service_state("order-service")
    assert state["status"] == "RESTARTED"
    assert "restarted_at" in state

    # 2. Execute safe scaling
    res_scale = await provider.execute_action("SCALING", "order-service", {"replicas": 5})
    assert res_scale["status"] == "COMPLETED"
    assert provider.get_service_state("order-service")["instances"] == 5

    # 3. Deny untyped or dangerous shell commands
    with pytest.raises(ValueError, match="not supported by InMemoryRemediationProvider"):
        await provider.execute_action("SHELL_EXEC", "order-service", {"cmd": "rm -rf /"})
