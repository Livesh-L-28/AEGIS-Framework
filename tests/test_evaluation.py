"""Unit tests for Evaluation engine and benchmark cases."""

from aegis.evaluation import EvaluationCase, EvaluationEngine


def test_evaluation_engine_benchmark_execution() -> None:
    """EvaluationEngine verifies benchmark case outcomes in memory."""
    engine = EvaluationEngine()
    case = EvaluationCase(
        name="DB Query Degradation Benchmark",
        description="Verifies detection of Postgres query thread pool exhaustion",
        expected_root_cause="Database",
        expected_risk_level="LOW",
    )

    res = engine.evaluate_case(
        case=case,
        actual_root_cause="Database Connection / Latency Degradation",
        actual_risk_level="LOW",
    )
    assert res.passed is True
    assert res.score == 1.0
    assert len(res.failures) == 0


def test_evaluation_engine_catches_regression() -> None:
    """EvaluationEngine flags regressions in root cause or risk determination."""
    engine = EvaluationEngine()
    case = EvaluationCase(
        name="Cache Regression Benchmark",
        description="Verifies detection of cache layer failure",
        expected_root_cause="Cache",
        expected_risk_level="LOW",
    )

    res = engine.evaluate_case(
        case=case,
        actual_root_cause="Network packet loss",
        actual_risk_level="HIGH",
    )
    assert res.passed is False
    assert res.score == 0.0
    assert len(res.failures) == 2
