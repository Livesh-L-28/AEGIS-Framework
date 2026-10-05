"""AEGIS Framework Reasoning — Hypotheses generation, causal scoring, and reasoning engine."""

import json
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from aegis.evidence import Evidence, EvidenceType
from aegis.providers import ModelProvider


class HypothesisStatus(StrEnum):
    """Lifecycle status of a root cause hypothesis."""

    CANDIDATE = "CANDIDATE"
    SUPPORTED = "SUPPORTED"
    WEAK = "WEAK"
    REJECTED = "REJECTED"


class Hypothesis(BaseModel):
    """Structured hypothesis regarding the root cause of an incident."""

    id: UUID = Field(default_factory=uuid4)
    incident_id: UUID = Field(default_factory=uuid4)
    title: str
    description: str
    status: HypothesisStatus = HypothesisStatus.CANDIDATE
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    score: float = Field(default=0.5, ge=0.0, le=1.0)
    supporting_evidence_ids: list[UUID] = Field(default_factory=list)
    contradicting_evidence_ids: list[UUID] = Field(default_factory=list)
    reasoning: str = ""
    suggested_mitigation: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


# Backwards compatibility alias
HypothesisItem = Hypothesis


class ReasoningResult(BaseModel):
    """Aggregate output from ReasoningEngine evaluation."""

    incident_id: UUID
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    primary_hypothesis: Hypothesis | None = None
    confidence: float = 0.0
    summary: str = ""
    is_grounded: bool = True
    grounding_score: float = 1.0


class ReasoningEngine:
    """Deterministic & LLM-assisted causal hypothesis generation and evaluation engine."""

    def __init__(self, model_provider: ModelProvider | None = None) -> None:
        self.model_provider = model_provider

    async def analyze(
        self,
        incident_id: UUID,
        evidence: list[Evidence],
        service_name: str | None = None,
    ) -> ReasoningResult:
        """Formulate and score hypotheses from collected evidence."""
        if not evidence:
            return ReasoningResult(
                incident_id=incident_id,
                hypotheses=[],
                confidence=0.0,
                summary="Insufficient evidence to deduce root cause.",
                is_grounded=False,
                grounding_score=0.0,
            )

        evidence_by_id = {e.id: e for e in evidence}
        hypotheses: list[Hypothesis] = []

        # 1. Deterministic Rule Matching: Database latency or query errors
        db_evidence = [
            e
            for e in evidence
            if e.evidence_type in (EvidenceType.METRIC, EvidenceType.LOG)
            and any(term in e.signal.lower() or term in e.content.lower() for term in ("db", "database", "postgres", "sql"))
        ]
        if db_evidence:
            hypotheses.append(
                Hypothesis(
                    incident_id=incident_id,
                    title="Database Connection / Latency Degradation",
                    description="Elevated database query response time causing upstream thread pool starvation or timeouts.",
                    status=HypothesisStatus.CANDIDATE,
                    supporting_evidence_ids=[e.id for e in db_evidence],
                    reasoning=f"Detected {len(db_evidence)} database latency or error signals.",
                    suggested_mitigation="Increase connection pool size or analyze long-running queries.",
                )
            )

        # 2. Ephemeral Cache / Redis breakdown
        cache_evidence = [
            e
            for e in evidence
            if e.evidence_type in (EvidenceType.METRIC, EvidenceType.LOG)
            and any(term in e.signal.lower() or term in e.content.lower() for term in ("redis", "cache", "memcached"))
        ]
        if cache_evidence:
            hypotheses.append(
                Hypothesis(
                    incident_id=incident_id,
                    title="Cache Layer Degradation",
                    description="Redis or cache timeout / connection failure causing cache stampede or session lookup failures.",
                    status=HypothesisStatus.CANDIDATE,
                    supporting_evidence_ids=[e.id for e in cache_evidence],
                    reasoning=f"Found {len(cache_evidence)} cache-related failure signals.",
                    suggested_mitigation="Flush corrupt cache keys or restart cache instances.",
                )
            )

        # 3. Deployment Regression
        deploy_evidence = [e for e in evidence if e.evidence_type == EvidenceType.DEPLOYMENT]
        if deploy_evidence:
            error_evidence = [
                e
                for e in evidence
                if e.evidence_type in (EvidenceType.METRIC, EvidenceType.LOG, EvidenceType.TRACE)
                and any(term in e.signal.lower() or term in e.content.lower() for term in ("error", "fail", "500", "crash"))
            ]
            hypotheses.append(
                Hypothesis(
                    incident_id=incident_id,
                    title="Recent Deployment Regression",
                    description="Recent version rollout introduced unexpected regression or incompatibility.",
                    status=HypothesisStatus.CANDIDATE,
                    supporting_evidence_ids=[e.id for e in deploy_evidence] + [e.id for e in error_evidence],
                    reasoning="Deployment event correlated temporally with elevated error rates.",
                    suggested_mitigation="Rollback service to previous stable release.",
                )
            )

        # 4. Fallback if no specific pattern matched
        if not hypotheses:
            hypotheses.append(
                Hypothesis(
                    incident_id=incident_id,
                    title="General Telemetry Anomaly",
                    description="Observed anomaly signals without specific architectural signature.",
                    status=HypothesisStatus.WEAK,
                    supporting_evidence_ids=[e.id for e in evidence[:2]],
                    reasoning="Telemetry signals do not match predefined root-cause signatures.",
                )
            )

        # LLM Augmentation if provider available
        if self.model_provider:
            prompt = (
                f"Evaluate incident for service {service_name or 'unknown'}.\n"
                f"Evidence count: {len(evidence)}.\n"
                "Return JSON with hypothesis title and reasoning."
            )
            try:
                llm_response = await self.model_provider.generate(prompt)
                data = json.loads(llm_response)
                if isinstance(data, dict) and "title" in data:
                    hypotheses.append(
                        Hypothesis(
                            incident_id=incident_id,
                            title=data.get("title", "AI Inferred Cause"),
                            description=data.get("description", "Hypothesis generated via ModelProvider"),
                            status=HypothesisStatus.CANDIDATE,
                            supporting_evidence_ids=[e.id for e in evidence[:3]],
                            reasoning=data.get("reasoning", "Generated by LLM ModelProvider"),
                        )
                    )
            except Exception:
                # LLM failure must not break deterministic reasoning
                pass

        # Score hypotheses
        for h in hypotheses:
            self._score_hypothesis(h, evidence_by_id)

        hypotheses.sort(key=lambda x: x.score, reverse=True)
        primary = hypotheses[0] if hypotheses else None
        top_conf = primary.confidence if primary else 0.0

        return ReasoningResult(
            incident_id=incident_id,
            hypotheses=hypotheses,
            primary_hypothesis=primary,
            confidence=top_conf,
            summary=primary.description if primary else "No plausible hypothesis determined.",
            is_grounded=True,
            grounding_score=top_conf,
        )

    def _score_hypothesis(
        self,
        hypothesis: Hypothesis,
        evidence_by_id: dict[UUID, Evidence],
    ) -> None:
        """Deterministic scoring formula."""
        supporting = [evidence_by_id[eid] for eid in hypothesis.supporting_evidence_ids if eid in evidence_by_id]
        telemetry_items = [i for i in supporting if i.evidence_type in (EvidenceType.METRIC, EvidenceType.LOG, EvidenceType.TRACE)]
        telemetry_score = min(1.0, len(telemetry_items) * 0.4)

        has_deploy = any(i.evidence_type == EvidenceType.DEPLOYMENT for i in supporting)
        deploy_score = 1.0 if has_deploy else 0.3

        # Contradiction check: deployment hypothesis with errors before deployment
        contradicting_ids: list[UUID] = []
        if "deployment" in hypothesis.title.lower():
            deploy_timestamps = [i.observed_at for i in supporting if i.evidence_type == EvidenceType.DEPLOYMENT]
            if deploy_timestamps:
                d_time = min(deploy_timestamps)
                for eid, item in evidence_by_id.items():
                    if (
                        item.evidence_type in (EvidenceType.METRIC, EvidenceType.LOG)
                        and item.observed_at < d_time
                        and any(term in item.signal.lower() for term in ("error", "fail"))
                    ):
                        contradicting_ids.append(eid)

        hypothesis.contradicting_evidence_ids = contradicting_ids
        penalty = 0.4 if contradicting_ids else 0.0

        raw = (telemetry_score * 0.4) + (deploy_score * 0.4) + 0.2 - penalty
        score = round(min(1.0, max(0.0, raw)), 3)
        hypothesis.score = score
        hypothesis.confidence = score

        if contradicting_ids and score < 0.4:
            hypothesis.status = HypothesisStatus.REJECTED
        elif score >= 0.7:
            hypothesis.status = HypothesisStatus.SUPPORTED
        elif score >= 0.4:
            hypothesis.status = HypothesisStatus.CANDIDATE
        else:
            hypothesis.status = HypothesisStatus.WEAK


__all__ = [
    "Hypothesis",
    "HypothesisItem",
    "HypothesisStatus",
    "ReasoningEngine",
    "ReasoningResult",
]
