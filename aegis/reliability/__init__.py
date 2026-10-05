"""AEGIS Framework Reliability — Native upstream integration with aireliability 0.1.0."""

from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

# Upstream direct imports from aireliability 0.1.0
try:
    from aireliability.core import (
        ExecutionStatus as AIRelExecutionStatus,
    )
    from aireliability.core import (
        ExecutionTrace as AIRelExecutionTrace,
    )
    from aireliability.core import (
        FailureReport as AIRelFailureReport,
    )
    from aireliability.core import (
        FailureSeverity as AIRelFailureSeverity,
    )
    from aireliability.core import (
        TraceStep as AIRelTraceStep,
    )
    from aireliability.diagnosis import (
        RootCauseAnalyzer as AIRelRootCauseAnalyzer,
    )
    from aireliability.evaluation import (
        MaxLatency as AIRelMaxLatency,
    )
    from aireliability.evaluation import (
        OutputContains as AIRelOutputContains,
    )
    from aireliability.failures import (
        FailureCategory as AIRelFailureCategory,
    )
    from aireliability.failures import (
        FailureType as AIRelFailureType,
    )

    _AIRELIABILITY_AVAILABLE = True
except ImportError:
    _AIRELIABILITY_AVAILABLE = False


class ReliabilityStatus(StrEnum):
    """Reliability state of an operation."""

    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    TIMEOUT = "TIMEOUT"
    CIRCUIT_OPEN = "CIRCUIT_OPEN"


class CausalDiagnosisResult(BaseModel):
    """Result of causal root-cause analysis."""

    report_id: str = Field(default_factory=lambda: f"rep-{uuid4().hex[:8]}")
    status: str = "PASS"
    primary_cause: str | None = None
    confidence: float = 1.0
    causal_chain: list[str] = Field(default_factory=list)
    summary: str = ""


class ExpectationEvaluationResult(BaseModel):
    """Outcome of evaluating declarative reliability expectations."""

    passed: bool
    score: float = 1.0
    failures: list[str] = Field(default_factory=list)


class AIReliabilityAdapter:
    """Adapter directly integrating upstream aireliability 0.1.0.

    CRITICAL RELIABILITY INVARIANT:
    aireliability is strictly diagnostic and evaluative.
    It CANNOT authorize remediation, bypass policy, or override human approval gates.
    """

    def __init__(self) -> None:
        self._analyzer = AIRelRootCauseAnalyzer() if _AIRELIABILITY_AVAILABLE else None

    def is_available(self) -> bool:
        """Check if upstream aireliability engine is loaded."""
        return _AIRELIABILITY_AVAILABLE and self._analyzer is not None

    def diagnose_trace(
        self,
        trace_id: str,
        duration_ms: float,
        status: ReliabilityStatus,
        error_message: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> CausalDiagnosisResult:
        """Run causal root cause analysis on an execution trace using aireliability."""
        if not self.is_available():
            return CausalDiagnosisResult(
                status="FAIL" if status != ReliabilityStatus.SUCCESS else "PASS",
                primary_cause=error_message or f"Execution status: {status.value}",
                summary="aireliability unavailable; simple diagnosis returned.",
            )

        try:
            is_ok = status == ReliabilityStatus.SUCCESS
            rel_status = AIRelExecutionStatus.COMPLETED if is_ok else AIRelExecutionStatus.FAILED

            step = AIRelTraceStep(
                name="execution_step",
                duration_ms=duration_ms,
                output=error_message or "Execution step finished",
            )
            trace = AIRelExecutionTrace(
                trace_id=trace_id,
                status=rel_status,
                latency_ms=duration_ms,
                steps=[step],
                output=error_message or "Execution finished",
                metadata=metadata or {},
            )

            failures: list[Any] = []
            if not is_ok:
                fail_report = AIRelFailureReport(
                    trace_id=trace_id,
                    category=AIRelFailureCategory.TASK,
                    type=AIRelFailureType.TASK_INCOMPLETE,
                    severity=AIRelFailureSeverity.HIGH,
                    message=error_message or "Execution failure observed",
                )
                failures.append(fail_report)

            if self._analyzer is None:
                return CausalDiagnosisResult(status="FAIL", summary="Analyzer not initialized")

            report = self._analyzer.diagnose(trace=trace, failures=failures)
            primary_desc = report.primary_cause.description if report.primary_cause else None
            conf = report.primary_cause.confidence if report.primary_cause else 1.0
            chain = [
                f"{link.source} -> {link.target} ({link.relationship})"
                for link in getattr(report, "causal_chain", [])
            ]

            return CausalDiagnosisResult(
                report_id=str(report.id),
                status=str(report.status),
                primary_cause=primary_desc or error_message or "Failure diagnosed",
                confidence=float(conf),
                causal_chain=chain,
                summary=str(report.summary),
            )
        except Exception as exc:
            return CausalDiagnosisResult(
                status="FAIL",
                primary_cause=f"aireliability exception: {exc}",
                confidence=0.5,
                summary=f"Encountered error during diagnosis: {exc}",
            )

    def evaluate_expectations(
        self,
        trace_id: str,
        duration_ms: float,
        output_text: str,
        max_latency_ms: float | None = None,
        expected_substring: str | None = None,
    ) -> ExpectationEvaluationResult:
        """Evaluate declarative expectations (latency thresholds, output substring)."""
        if not self.is_available():
            passed = True
            failures = []
            if max_latency_ms and duration_ms > max_latency_ms:
                passed = False
                failures.append(f"Latency {duration_ms}ms exceeded {max_latency_ms}ms")
            if expected_substring and expected_substring not in output_text:
                passed = False
                failures.append(f"Output missing substring '{expected_substring}'")
            return ExpectationEvaluationResult(passed=passed, score=1.0 if passed else 0.0, failures=failures)

        failures = []
        passed = True
        scores: list[float] = []

        step = AIRelTraceStep(
            name="step",
            duration_ms=duration_ms,
            output=output_text,
        )
        trace = AIRelExecutionTrace(
            trace_id=trace_id,
            status=AIRelExecutionStatus.COMPLETED,
            latency_ms=duration_ms,
            steps=[step],
            output=output_text,
        )

        if max_latency_ms is not None:
            lat_exp = AIRelMaxLatency(max_latency_ms=max_latency_ms)
            res = lat_exp.evaluate(trace)
            if not res.passed:
                passed = False
                failures.append(res.message)
            scores.append(float(res.score) if res.passed and res.score is not None else 0.0)

        if expected_substring is not None:
            sub_exp = AIRelOutputContains(expected_substring=expected_substring)
            res = sub_exp.evaluate(trace)
            if not res.passed:
                passed = False
                failures.append(res.message)
            scores.append(float(res.score) if res.passed and res.score is not None else 0.0)

        avg_score = (sum(scores) / len(scores)) if scores else 1.0
        return ExpectationEvaluationResult(passed=passed, score=avg_score, failures=failures)


__all__ = [
    "AIReliabilityAdapter",
    "CausalDiagnosisResult",
    "ExpectationEvaluationResult",
    "ReliabilityStatus",
]
