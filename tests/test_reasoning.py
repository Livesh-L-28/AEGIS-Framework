"""Unit tests for Reasoning domain and ReasoningEngine."""

from uuid import uuid4

import pytest

from aegis.evidence import Evidence, EvidenceType
from aegis.reasoning import HypothesisStatus, ReasoningEngine


class MockModelProvider:
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        system_instruction: str | None = None,
        context: dict | None = None,
    ) -> str:
        return '{"title": "Database Connection Pool Starvation", "reasoning": "High latency detected on DB connections"}'


@pytest.mark.asyncio
async def test_reasoning_deterministic_database_analysis() -> None:
    """Reasoning engine detects database regression patterns deterministically."""
    engine = ReasoningEngine()
    incident_id = uuid4()

    ev = Evidence(
        evidence_type=EvidenceType.METRIC,
        source="prometheus",
        service_name="payment-service",
        signal="postgres_query_duration_seconds",
        content="Postgres database latency spike exceeding 5.0 seconds",
        provenance="metric:postgres_query_duration_seconds",
    )

    result = await engine.analyze(incident_id=incident_id, evidence=[ev], service_name="payment-service")

    assert result.is_grounded is True
    assert len(result.hypotheses) >= 1
    top = result.primary_hypothesis
    assert top is not None
    assert "Database" in top.title
    assert top.score >= 0.4
    assert top.status in (HypothesisStatus.CANDIDATE, HypothesisStatus.SUPPORTED)


@pytest.mark.asyncio
async def test_reasoning_with_mock_model_provider() -> None:
    """Reasoning engine incorporates structured output from model provider."""
    engine = ReasoningEngine(model_provider=MockModelProvider())
    incident_id = uuid4()

    ev = Evidence(
        evidence_type=EvidenceType.LOG,
        source="loki",
        service_name="auth-service",
        signal="auth_error",
        content="Unclassified authentication anomaly",
        provenance="log:auth_error",
    )

    result = await engine.analyze(incident_id=incident_id, evidence=[ev], service_name="auth-service")
    assert any("Database Connection Pool Starvation" in h.title for h in result.hypotheses)


@pytest.mark.asyncio
async def test_reasoning_insufficient_evidence() -> None:
    """Empty evidence yields ungrounded result."""
    engine = ReasoningEngine()
    incident_id = uuid4()
    result = await engine.analyze(incident_id=incident_id, evidence=[])
    assert result.is_grounded is False
    assert result.confidence == 0.0
    assert "Insufficient evidence" in result.summary
