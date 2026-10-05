"""AEGIS Framework Core — High-level Aegis client, configuration, and runtime utilities."""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from aegis.autonomy import AutonomyBudget, AutonomyEngine, AutonomyLevel
from aegis.core.audit import AuditCategory, InMemoryAuditLogger
from aegis.core.observability import TelemetrySink, telemetry_sink
from aegis.evidence import EvidenceEngine
from aegis.incidents import Incident, IncidentSeverity
from aegis.policy import PolicyEngine
from aegis.providers import (
    ApprovalStore,
    DeploymentProvider,
    LogProvider,
    MetricsProvider,
    ModelProvider,
    TraceProvider,
)
from aegis.reasoning import ReasoningEngine, ReasoningResult
from aegis.reliability import AIReliabilityAdapter
from aegis.remediation import RemediationPlan, RemediationPlanner
from aegis.security import GovernedToolGateway, LLMFirewallAdapter


class AegisConfig(BaseModel):
    """Declarative runtime configuration for Aegis instance."""

    autonomy_level: AutonomyLevel = AutonomyLevel.LEVEL_1
    organization_id: UUID | None = None
    telemetry_enabled: bool = True
    audit_enabled: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class Aegis:
    """Unified entrypoint for the AEGIS Framework.

    Allows applications to configure and run incident investigations,
    evidence engineering, reasoning, security policies, and remediation
    planning with pure dependency injection and zero database lock-in.
    """

    def __init__(
        self,
        metrics_provider: MetricsProvider | None = None,
        log_provider: LogProvider | None = None,
        trace_provider: TraceProvider | None = None,
        deployment_provider: DeploymentProvider | None = None,
        model_provider: ModelProvider | None = None,
        approval_store: ApprovalStore | None = None,
        autonomy_level: AutonomyLevel = AutonomyLevel.LEVEL_1,
        autonomy_budget: AutonomyBudget | None = None,
        config: AegisConfig | None = None,
        telemetry: TelemetrySink | None = None,
        audit_logger: InMemoryAuditLogger | None = None,
    ) -> None:
        self.config = config or AegisConfig(autonomy_level=autonomy_level)
        effective_autonomy = self.config.autonomy_level or autonomy_level

        self.evidence_engine = EvidenceEngine(
            metrics_provider=metrics_provider,
            log_provider=log_provider,
            trace_provider=trace_provider,
            deployment_provider=deployment_provider,
        )
        self.reasoning_engine = ReasoningEngine(model_provider=model_provider)
        self.firewall = LLMFirewallAdapter()
        self.tool_gateway = GovernedToolGateway(firewall=self.firewall)
        self.policy_engine = PolicyEngine()
        self.reliability_engine = AIReliabilityAdapter()
        self.remediation_planner = RemediationPlanner()
        self.autonomy_engine = AutonomyEngine(level=effective_autonomy, budget=autonomy_budget)
        self.approval_store = approval_store
        self.telemetry = telemetry or telemetry_sink
        self.audit = audit_logger or InMemoryAuditLogger()
        self.kubernetes_provider: Any | None = None
        self.project_config: Any | None = None

    def __repr__(self) -> str:
        return f"<Aegis (Autonomy: {self.autonomy_engine.level.value})>"

    def create_incident(
        self,
        title: str,
        severity: IncidentSeverity = IncidentSeverity.MEDIUM,
        service_name: str | None = None,
        description: str = "",
        **kwargs: Any,
    ) -> Incident:
        """Create and track a framework Incident."""
        inc = Incident(
            title=title,
            severity=severity,
            service_name=service_name,
            description=description,
            metadata=kwargs,
        )
        self.telemetry.emit(
            "incident.created",
            service_name=service_name,
            incident_id=str(inc.id),
            title=title,
            severity=severity.value,
        )
        self.audit.record(
            category=AuditCategory.REASONING,
            action="incident.created",
            target=service_name,
            details={"incident_id": str(inc.id), "title": title},
        )
        return inc

    async def investigate(
        self,
        incident: Incident,
    ) -> ReasoningResult:
        """Investigate an incident by collecting evidence and inferring root causes."""
        incident.mark_investigating()
        self.telemetry.emit(
            "evidence.collection.started",
            service_name=incident.service_name,
            incident_id=str(incident.id),
        )

        evidence = await self.evidence_engine.collect_all(
            organization_id=incident.organization_id,
            incident_id=incident.id,
            service_name=incident.service_name,
            incident_time=incident.detected_at,
        )

        self.telemetry.emit(
            "evidence.collection.completed",
            service_name=incident.service_name,
            incident_id=str(incident.id),
            evidence_count=len(evidence),
        )

        self.telemetry.emit(
            "reasoning.started",
            service_name=incident.service_name,
            incident_id=str(incident.id),
        )

        result = await self.reasoning_engine.analyze(
            incident_id=incident.id,
            evidence=evidence,
            service_name=incident.service_name,
        )

        self.telemetry.emit(
            "reasoning.completed",
            service_name=incident.service_name,
            incident_id=str(incident.id),
            hypotheses_count=len(result.hypotheses),
            primary_hypothesis=result.primary_hypothesis.title if result.primary_hypothesis else None,
        )
        self.audit.record(
            category=AuditCategory.REASONING,
            action="reasoning.completed",
            target=incident.service_name,
            details={
                "incident_id": str(incident.id),
                "hypotheses_count": len(result.hypotheses),
                "primary": result.primary_hypothesis.title if result.primary_hypothesis else None,
            },
        )
        return result

    def plan_remediation(
        self,
        incident_id: UUID,
        service_name: str,
        reason: str,
    ) -> RemediationPlan:
        """Plan a remediation action."""
        plan = self.remediation_planner.plan_restart(
            incident_id=incident_id,
            service_name=service_name,
            reason=reason,
        )
        self.telemetry.emit(
            "remediation.proposed",
            service_name=service_name,
            incident_id=str(incident_id),
            plan_id=str(plan.id),
            risk=plan.risk_level.value,
        )
        self.audit.record(
            category=AuditCategory.REMEDIATION,
            action="remediation.proposed",
            target=service_name,
            details={"plan_id": str(plan.id), "risk": plan.risk_level.value},
        )
        return plan

    @classmethod
    def from_config(cls, config_path_or_obj: Any) -> "Aegis":
        """Construct an Aegis instance from a configuration file (aegis.yaml) or AegisProjectConfig object."""
        from pathlib import Path

        from aegis.config import AegisProjectConfig
        from aegis.providers.config import (
            KubernetesConfig,
            LokiConfig,
            OpenTelemetryConfig,
            PrometheusConfig,
        )
        from aegis.providers.memory import (
            InMemoryApprovalStore,
            InMemoryLogProvider,
            InMemoryMetricsProvider,
            InMemoryModelProvider,
            InMemoryTraceProvider,
        )
        from aegis.providers.production.kubernetes import KubernetesProvider
        from aegis.providers.production.loki import LokiLogProvider
        from aegis.providers.production.opentelemetry import OpenTelemetryTraceProvider
        from aegis.providers.production.prometheus import PrometheusMetricsProvider

        if isinstance(config_path_or_obj, (str, Path)):
            cfg = AegisProjectConfig.from_file(config_path_or_obj)
        elif isinstance(config_path_or_obj, AegisProjectConfig):
            cfg = config_path_or_obj
        else:
            raise TypeError(f"Expected file path or AegisProjectConfig, got {type(config_path_or_obj)}")

        # 1. Resolve Metrics Provider
        metrics_prov: MetricsProvider
        m_cfg = cfg.providers.metrics
        if m_cfg.type == "prometheus" and m_cfg.endpoint:
            metrics_prov = PrometheusMetricsProvider(
                PrometheusConfig(
                    base_url=m_cfg.endpoint,
                    default_step=m_cfg.step,
                    timeout_seconds=m_cfg.timeout_seconds,
                )
            )
        else:
            metrics_prov = InMemoryMetricsProvider()

        # 2. Resolve Log Provider
        log_prov: LogProvider
        l_cfg = cfg.providers.logs
        if l_cfg.type == "loki" and l_cfg.endpoint:
            log_prov = LokiLogProvider(
                LokiConfig(
                    base_url=l_cfg.endpoint,
                    default_limit=l_cfg.limit,
                    timeout_seconds=l_cfg.timeout_seconds,
                )
            )
        else:
            log_prov = InMemoryLogProvider()

        # 3. Resolve Trace Provider
        trace_prov: TraceProvider
        t_cfg = cfg.providers.traces
        if t_cfg.type == "opentelemetry" and t_cfg.endpoint:
            trace_prov = OpenTelemetryTraceProvider(
                OpenTelemetryConfig(
                    base_url=t_cfg.endpoint,
                    timeout_seconds=t_cfg.timeout_seconds,
                )
            )
        else:
            trace_prov = InMemoryTraceProvider()

        autonomy_lvl = cfg.to_autonomy_level()

        instance = cls(
            metrics_provider=metrics_prov,
            log_provider=log_prov,
            trace_provider=trace_prov,
            model_provider=InMemoryModelProvider(),
            approval_store=InMemoryApprovalStore(),
            autonomy_level=autonomy_lvl,
        )

        # Attach optional kubernetes provider if configured
        if cfg.providers.kubernetes:
            k_cfg = cfg.providers.kubernetes
            k8s_provider = KubernetesProvider(
                KubernetesConfig(
                    default_namespace=k_cfg.default_namespace,
                    read_only=k_cfg.read_only,
                    kubeconfig_path=k_cfg.kubeconfig_path,
                )
            )
            instance.kubernetes_provider = k8s_provider

        instance.project_config = cfg
        return instance


__all__ = ["Aegis", "AegisConfig"]
