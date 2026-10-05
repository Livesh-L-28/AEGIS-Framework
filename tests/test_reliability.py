"""Unit tests for Reliability domain and AIReliability adapter."""

from aegis.reliability import AIReliabilityAdapter, ReliabilityStatus


def test_aireliability_adapter_diagnosis() -> None:
    """AIReliabilityAdapter performs causal diagnosis on traces."""
    adapter = AIReliabilityAdapter()
    result = adapter.diagnose_trace(
        trace_id="tr-12345",
        duration_ms=120.0,
        status=ReliabilityStatus.SUCCESS,
    )
    assert result.status in ("PASS", "ok")
    assert result.confidence >= 0.0


def test_aireliability_adapter_expectations() -> None:
    """Expectation checks evaluate latency constraints and string presence."""
    adapter = AIReliabilityAdapter()
    res = adapter.evaluate_expectations(
        trace_id="tr-test-exp",
        duration_ms=50.0,
        output_text="Service recovered and operational",
        max_latency_ms=100.0,
        expected_substring="recovered",
    )
    assert res.passed is True
    assert res.score == 1.0


def test_aireliability_adapter_failing_expectations() -> None:
    """Expectation checks fail when constraints are violated."""
    adapter = AIReliabilityAdapter()
    res = adapter.evaluate_expectations(
        trace_id="tr-test-fail",
        duration_ms=250.0,
        output_text="Error internal crash",
        max_latency_ms=100.0,
        expected_substring="operational",
    )
    assert res.passed is False
    assert len(res.failures) >= 1
