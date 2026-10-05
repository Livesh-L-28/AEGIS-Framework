"""AEGIS Framework Evaluation — Golden datasets, regression testing, and evaluation engine."""

from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import yaml
from pydantic import BaseModel, Field


class EvaluationMetric(StrEnum):
    """Supported evaluation dimensions."""

    GROUNDING_ACCURACY = "GROUNDING_ACCURACY"
    HYPOTHESIS_CORRECTNESS = "HYPOTHESIS_CORRECTNESS"
    REMEDIATION_VALIDITY = "REMEDIATION_VALIDITY"
    SECURITY_COMPLIANCE = "SECURITY_COMPLIANCE"
    LATENCY = "LATENCY"


class EvaluationCase(BaseModel):
    """Deterministic benchmark scenario test case."""

    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str = ""
    expected_root_cause: str
    expected_risk_level: str
    input_signals: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvaluationResult(BaseModel):
    """Evaluation outcome for a benchmark case."""

    case_id: UUID
    case_name: str
    passed: bool
    score: float = 1.0
    metric: EvaluationMetric = EvaluationMetric.HYPOTHESIS_CORRECTNESS
    details: dict[str, Any] = Field(default_factory=dict)
    failures: list[str] = Field(default_factory=list)


class Benchmark(BaseModel):
    """A collection of evaluation cases loaded from YAML or created dynamically."""

    name: str
    version: str = "1.0"
    description: str = ""
    cases: list[EvaluationCase] = Field(default_factory=list)

    @classmethod
    def from_yaml(cls, content: str) -> "Benchmark":
        """Load benchmark suite from YAML string."""
        raw = yaml.safe_load(content)
        if not isinstance(raw, dict):
            raise ValueError("Benchmark YAML must be a mapping/dict")
        return cls.model_validate(raw)

    @classmethod
    def from_file(cls, path: str | Path) -> "Benchmark":
        """Load benchmark suite from a file path."""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Benchmark file not found: {p}")
        return cls.from_yaml(p.read_text(encoding="utf-8"))


class BenchmarkReport(BaseModel):
    """Aggregate summary report for a benchmark run."""

    benchmark_name: str
    total_cases: int
    passed_cases: int
    failed_cases: int
    overall_score: float
    results: list[EvaluationResult] = Field(default_factory=list)


class EvaluationEngine:
    """Benchmark evaluation runner independent of external databases."""

    def evaluate_case(
        self,
        case: EvaluationCase,
        actual_root_cause: str,
        actual_risk_level: str,
    ) -> EvaluationResult:
        """Evaluate a benchmark case against actual system reasoning outputs."""
        failures: list[str] = []
        passed = True

        cause_match = case.expected_root_cause.lower() in actual_root_cause.lower()
        if not cause_match:
            failures.append(f"Root cause mismatch: expected '{case.expected_root_cause}', got '{actual_root_cause}'")
            passed = False

        if case.expected_risk_level != actual_risk_level:
            failures.append(f"Risk mismatch: expected '{case.expected_risk_level}', got '{actual_risk_level}'")
            passed = False

        score = 1.0 if passed else (0.5 if cause_match else 0.0)

        return EvaluationResult(
            case_id=case.id,
            case_name=case.name,
            passed=passed,
            score=score,
            failures=failures,
            details={
                "cause_match": cause_match,
                "expected_risk": case.expected_risk_level,
                "actual_risk": actual_risk_level,
            },
        )

    def run_benchmark(
        self,
        benchmark: Benchmark,
        evaluator_fn: Any = None,
    ) -> BenchmarkReport:
        """Execute all cases in a benchmark suite."""
        results: list[EvaluationResult] = []
        for case in benchmark.cases:
            if evaluator_fn:
                actual_cause, actual_risk = evaluator_fn(case)
            else:
                actual_cause, actual_risk = case.expected_root_cause, case.expected_risk_level

            res = self.evaluate_case(case, actual_cause, actual_risk)
            results.append(res)

        passed_count = sum(1 for r in results if r.passed)
        failed_count = len(results) - passed_count
        avg_score = (sum(r.score for r in results) / len(results)) if results else 1.0

        return BenchmarkReport(
            benchmark_name=benchmark.name,
            total_cases=len(results),
            passed_cases=passed_count,
            failed_cases=failed_count,
            overall_score=round(avg_score, 4),
            results=results,
        )


__all__ = [
    "Benchmark",
    "BenchmarkReport",
    "EvaluationCase",
    "EvaluationEngine",
    "EvaluationMetric",
    "EvaluationResult",
]
