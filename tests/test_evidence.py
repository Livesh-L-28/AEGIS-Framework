"""Unit tests for Evidence domain and EvidenceEngine."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest

from aegis.evidence import Evidence, EvidenceEngine, EvidenceType


class MockMetricsProvider:
    async def query_metric(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        service_name: str | None = None,
        labels: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        return [
            {
                "signal": "http_errors_5xx",
                "value": 150.0,
                "timestamp": datetime.now(UTC),
                "provenance": "prometheus:http_errors_total",
            }
        ]


class MockLogProvider:
    async def query_logs(
        self,
        query: str,
        start_time: datetime,
        end_time: datetime,
        service_name: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        return [
            {
                "signal": "NullPointerException",
                "message": "FATAL: database query timeout",
                "timestamp": datetime.now(UTC),
                "provenance": "loki:order-service-logs",
            }
        ]


@pytest.mark.asyncio
async def test_evidence_collection_from_mock_providers() -> None:
    """EvidenceEngine collects, deduplicates, and ranks evidence from mock providers."""
    engine = EvidenceEngine(
        metrics_provider=MockMetricsProvider(),
        log_provider=MockLogProvider(),
    )
    incident_id = uuid4()
    org_id = uuid4()

    evidence_items = await engine.collect_all(
        organization_id=org_id,
        incident_id=incident_id,
        service_name="order-service",
    )

    assert len(evidence_items) == 2
    types = {e.evidence_type for e in evidence_items}
    assert EvidenceType.METRIC in types
    assert EvidenceType.LOG in types

    # Verify ranking
    assert evidence_items[0].relevance_score > 0.0
    assert evidence_items[0].relevance_score <= 1.0


def test_timeline_construction() -> None:
    """Timeline entries link to evidence item IDs."""
    engine = EvidenceEngine()
    item1 = Evidence(
        evidence_type=EvidenceType.METRIC,
        source="prometheus",
        signal="cpu_spike",
        content="CPU spiked above 95%",
        provenance="metric:cpu",
    )
    item2 = Evidence(
        evidence_type=EvidenceType.LOG,
        source="loki",
        signal="oom_killed",
        content="Process killed by OOM killer",
        provenance="log:oom",
    )

    timeline = engine.construct_timeline([item1, item2])
    assert len(timeline) == 2
    assert timeline[0].evidence_ids == [item1.id]
    assert timeline[1].evidence_ids == [item2.id]
