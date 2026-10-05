"""AEGIS Framework Evidence — Multimodal evidence domain, ranking, deduplication, and engine."""

from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from aegis.providers import DeploymentProvider, LogProvider, MetricsProvider, TraceProvider


class EvidenceType(StrEnum):
    """Categorization of evidence artifacts."""

    LOG = "LOG"
    METRIC = "METRIC"
    TRACE = "TRACE"
    DEPLOYMENT = "DEPLOYMENT"
    SERVICE = "SERVICE"
    DEPENDENCY = "DEPENDENCY"
    CODE = "CODE"
    COMMIT = "COMMIT"
    KNOWLEDGE = "KNOWLEDGE"
    CONFIGURATION = "CONFIGURATION"


class EvidenceSeverity(StrEnum):
    """Severity weighting of observed evidence."""

    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Evidence(BaseModel):
    """Normalized canonical representation of an evidence item."""

    id: UUID = Field(default_factory=uuid4)
    organization_id: UUID = Field(default_factory=uuid4)
    incident_id: UUID = Field(default_factory=uuid4)
    evidence_type: EvidenceType
    source: str = Field(..., description="Provider or collector source (e.g. prometheus, loki, otel, git)")
    service_name: str | None = Field(default=None, description="Affected service or component name")
    signal: str = Field(..., description="Specific metric, log level, event, or span name")
    observed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    severity: EvidenceSeverity = EvidenceSeverity.MEDIUM
    content: str = Field(..., description="Human-readable description or observation summary")
    structured_data: dict[str, Any] = Field(default_factory=dict, description="Raw normalized data payload")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Provider/collector confidence")
    relevance_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Score computed during ranking")
    provenance: str = Field(..., description="Traceable provenance citation: query, span ID, or commit hash")
    metadata: dict[str, Any] = Field(default_factory=dict)


# Backwards compatibility alias for EvidenceItem
EvidenceItem = Evidence


class TimelineEntry(BaseModel):
    """A chronological event in an incident timeline linking to evidence."""

    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime
    title: str
    description: str
    service_name: str | None = None
    event_type: str = "TELEMETRY"
    evidence_ids: list[UUID] = Field(default_factory=list)


class EvidenceEngine:
    """Orchestrates deterministic multi-source evidence collection, correlation, deduplication, and timeline construction."""

    def __init__(
        self,
        metrics_provider: MetricsProvider | None = None,
        log_provider: LogProvider | None = None,
        trace_provider: TraceProvider | None = None,
        deployment_provider: DeploymentProvider | None = None,
    ) -> None:
        self.metrics_provider = metrics_provider
        self.log_provider = log_provider
        self.trace_provider = trace_provider
        self.deployment_provider = deployment_provider

    async def collect_all(
        self,
        organization_id: UUID,
        incident_id: UUID,
        service_name: str | None,
        incident_time: datetime | None = None,
        window_before_minutes: int = 15,
        window_after_minutes: int = 10,
    ) -> list[Evidence]:
        """Collects evidence across configured providers within the bounded window."""
        t_ref = incident_time or datetime.now(UTC)
        start_time = t_ref - timedelta(minutes=window_before_minutes)
        end_time = t_ref + timedelta(minutes=window_after_minutes)

        collected: list[Evidence] = []

        # 1. Metrics collection
        if self.metrics_provider and service_name:
            for m_name in ("http_errors_total", "http_request_duration_seconds"):
                metric_data = await self.metrics_provider.query_metric(
                    metric_name=m_name,
                    start_time=start_time,
                    end_time=end_time,
                    service_name=service_name,
                )
                for m in metric_data:
                    val = m.get("value", 0)
                    sig = m.get("signal", m.get("metric_name", "metric_anomaly"))
                    sev = EvidenceSeverity.HIGH if val > 10 else EvidenceSeverity.MEDIUM
                    collected.append(
                        Evidence(
                            organization_id=organization_id,
                            incident_id=incident_id,
                            evidence_type=EvidenceType.METRIC,
                            source="metrics_provider",
                            service_name=service_name,
                            signal=sig,
                            observed_at=m.get("timestamp", t_ref),
                            severity=sev,
                            content=f"Observed metric signal {sig} value={val}",
                            structured_data=m,
                            provenance=m.get("provenance", "metrics:query"),
                        )
                    )

        # 2. Logs collection
        if self.log_provider and service_name:
            log_entries = await self.log_provider.query_logs(
                query="level:error",
                start_time=start_time,
                end_time=end_time,
                service_name=service_name,
            )
            for l_entry in log_entries:
                collected.append(
                    Evidence(
                        organization_id=organization_id,
                        incident_id=incident_id,
                        evidence_type=EvidenceType.LOG,
                        source="log_provider",
                        service_name=service_name,
                        signal=l_entry.get("signal", "error_log"),
                        observed_at=l_entry.get("timestamp", t_ref),
                        severity=EvidenceSeverity.HIGH,
                        content=l_entry.get("message", "Error log line"),
                        structured_data=l_entry,
                        provenance=l_entry.get("provenance", "loki:query"),
                    )
                )

        # 3. Traces collection
        if self.trace_provider and service_name:
            spans = await self.trace_provider.query_spans(
                service_name=service_name,
                start_time=start_time,
                end_time=end_time,
                only_errors=True,
            )
            for sp in spans:
                collected.append(
                    Evidence(
                        organization_id=organization_id,
                        incident_id=incident_id,
                        evidence_type=EvidenceType.TRACE,
                        source="trace_provider",
                        service_name=service_name,
                        signal=sp.get("span_name", "error_span"),
                        observed_at=sp.get("timestamp", t_ref),
                        severity=EvidenceSeverity.HIGH,
                        content=f"Error span in {sp.get('span_name')} (latency: {sp.get('duration_ms')}ms)",
                        structured_data=sp,
                        provenance=f"span:{sp.get('span_id', 'unknown')}",
                    )
                )

        # 4. Deployments collection
        if self.deployment_provider:
            deploys = await self.deployment_provider.list_recent_deployments(
                service_name=service_name,
                start_time=start_time,
                end_time=end_time,
            )
            for d in deploys:
                collected.append(
                    Evidence(
                        organization_id=organization_id,
                        incident_id=incident_id,
                        evidence_type=EvidenceType.DEPLOYMENT,
                        source="deployment_provider",
                        service_name=service_name,
                        signal=f"deploy:{d.get('version', 'unknown')}",
                        observed_at=d.get("timestamp", t_ref),
                        severity=EvidenceSeverity.MEDIUM,
                        content=f"Service deployment event version={d.get('version')}",
                        structured_data=d,
                        provenance=d.get("commit_sha", "deploy:event"),
                    )
                )

        deduped = self.deduplicate_evidence(collected)
        ranked = self.rank_evidence(deduped, primary_service=service_name)
        return ranked

    def deduplicate_evidence(self, items: list[Evidence]) -> list[Evidence]:
        """Deterministic deduplication based on type, service, signal, and provenance."""
        seen: dict[str, Evidence] = {}
        for item in items:
            key = f"{item.evidence_type.value}:{item.service_name or 'any'}:{item.signal}:{item.provenance}"
            if key not in seen:
                seen[key] = item
            else:
                if item.confidence > seen[key].confidence:
                    seen[key] = item
        return list(seen.values())

    def rank_evidence(
        self,
        items: list[Evidence],
        primary_service: str | None = None,
    ) -> list[Evidence]:
        """Deterministic scoring and ranking of evidence items."""
        severity_weights = {
            EvidenceSeverity.CRITICAL: 1.0,
            EvidenceSeverity.HIGH: 0.85,
            EvidenceSeverity.MEDIUM: 0.65,
            EvidenceSeverity.LOW: 0.45,
            EvidenceSeverity.INFO: 0.35,
        }

        type_weights = {
            EvidenceType.METRIC: 1.0,
            EvidenceType.TRACE: 0.95,
            EvidenceType.LOG: 0.90,
            EvidenceType.DEPLOYMENT: 0.85,
            EvidenceType.DEPENDENCY: 0.80,
            EvidenceType.CODE: 0.75,
            EvidenceType.KNOWLEDGE: 0.60,
            EvidenceType.SERVICE: 0.70,
            EvidenceType.COMMIT: 0.70,
            EvidenceType.CONFIGURATION: 0.65,
        }

        for item in items:
            sev_w = severity_weights.get(item.severity, 0.5)
            type_w = type_weights.get(item.evidence_type, 0.5)
            svc_w = 1.0 if (primary_service and item.service_name == primary_service) else 0.8

            score = (sev_w * 0.45) + (type_w * 0.25) + (svc_w * 0.15) + (item.confidence * 0.15)
            item.relevance_score = round(min(1.0, max(0.0, score)), 4)

        items.sort(key=lambda x: (x.relevance_score, x.observed_at), reverse=True)
        return items

    def construct_timeline(
        self,
        evidence: list[Evidence],
    ) -> list[TimelineEntry]:
        """Builds a structured chronological timeline linking each entry to relevant evidence IDs."""
        sorted_evidence = sorted(evidence, key=lambda x: x.observed_at)
        timeline: list[TimelineEntry] = []

        for item in sorted_evidence:
            title = f"[{item.evidence_type.value}] {item.service_name or 'System'}: {item.signal}"
            entry = TimelineEntry(
                timestamp=item.observed_at,
                title=title,
                description=item.content,
                service_name=item.service_name,
                event_type=item.evidence_type.value,
                evidence_ids=[item.id],
            )
            timeline.append(entry)

        return timeline


__all__ = [
    "Evidence",
    "EvidenceEngine",
    "EvidenceItem",
    "EvidenceSeverity",
    "EvidenceType",
    "TimelineEntry",
]
