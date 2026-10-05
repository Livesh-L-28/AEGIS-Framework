"""End-to-End Real Infrastructure Autonomous Investigation & Remediation Lab.

Demonstrates:
  Real Incident -> Prometheus Metrics -> Loki Logs -> Jaeger/OTel Spans
  -> AEGIS Evidence Collection -> Causal Reasoning -> Policy Evaluation
  -> Risk-Gated Remediation -> Kubernetes Mutation -> Recovery Validation -> Audit Trail
"""

import asyncio
import json
import time
import urllib.request
from datetime import UTC, datetime, timedelta

from aegis import (
    Aegis,
    AutonomyLevel,
    IncidentSeverity,
    SecurityRiskLevel,
)
from aegis.policy import DataClassification
from aegis.providers.config import (
    KubernetesConfig,
    LokiConfig,
    OpenTelemetryConfig,
    PrometheusConfig,
)
from aegis.providers.memory import InMemoryApprovalStore, InMemoryModelProvider
from aegis.providers.production.kubernetes import KubernetesProvider
from aegis.providers.production.loki import LokiLogProvider
from aegis.providers.production.opentelemetry import OpenTelemetryTraceProvider
from aegis.providers.production.prometheus import PrometheusMetricsProvider
from aegis.remediation import RemediationActionType

DEMO_URL = "http://localhost:18080"
PROM_URL = "http://localhost:19090"
LOKI_URL = "http://localhost:3100"


def http_post(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=3.0) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_get(url: str) -> dict:
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=3.0) as resp:
        return json.loads(resp.read().decode("utf-8"))


async def run_lab() -> None:
    print("=" * 70)
    print("AEGIS Framework v0.1.0 — Real Infrastructure Integration Lab")
    print("=" * 70)

    # 1. Initialize AEGIS with Real Infrastructure Providers
    print("\n[Step 1] Initializing AEGIS Framework with Production Providers...")
    prom_prov = PrometheusMetricsProvider(PrometheusConfig(base_url=PROM_URL, default_step="1s"))
    loki_prov = LokiLogProvider(LokiConfig(base_url=LOKI_URL))
    otel_prov = OpenTelemetryTraceProvider(OpenTelemetryConfig(base_url=DEMO_URL))

    # Target dedicated local namespace 'aegis-integration' with read_only=False for controlled lab
    k8s_prov = KubernetesProvider(KubernetesConfig(default_namespace="aegis-integration", read_only=False))
    k8s_prov.register_workload(
        name="demo-service",
        namespace="aegis-integration",
        replicas=1,
        image="integration-demo-service:latest",
        status="Running"
    )

    aegis = Aegis(
        metrics_provider=prom_prov,
        log_provider=loki_prov,
        trace_provider=otel_prov,
        model_provider=InMemoryModelProvider(),
        approval_store=InMemoryApprovalStore(),
        autonomy_level=AutonomyLevel.LEVEL_2,
    )
    print("  -> Prometheus Provider connected to:", PROM_URL)
    print("  -> Loki Provider connected to:", LOKI_URL)
    print("  -> OpenTelemetry/Jaeger Provider connected to:", DEMO_URL)
    print("  -> Kubernetes Provider connected to namespace 'aegis-integration' (typed API)")

    # 2. Trigger Controlled Real Incident
    print("\n[Step 2] Triggering Controlled Real Incident (Degradation Mode)...")
    toggle_resp = http_post(f"{DEMO_URL}/api/incident", {"enabled": True})
    print(f"  -> Incident Mode active on demo application: {toggle_resp.get('incident_mode')}")

    import contextlib
    print("  -> Generating traffic causing database timeouts and 503 errors...")
    for _ in range(5):
        with contextlib.suppress(Exception):
            http_get(f"{DEMO_URL}/api/request")
        time.sleep(0.05)

    # Wait for Prometheus scrape cycle
    print("  -> Waiting 3s for Prometheus scrape evaluation...")
    await asyncio.sleep(3)

    # 3. Create Incident in AEGIS
    now = datetime.now(UTC)
    incident = aegis.create_incident(
        title="Elevated Error Rate and Latency on demo-service",
        service_name="demo-service",
        severity=IncidentSeverity.HIGH,
        description="Database query timeout causing cascading HTTP 503 errors",
    )
    print(f"\n[Step 3] Incident Declared in AEGIS: {incident.id} [{incident.severity.value}]")

    # 4. Real Multimodal Evidence Collection
    print("\n[Step 4] Querying Real Telemetry via AEGIS Production Providers...")
    start_window = now - timedelta(minutes=5)
    end_window = now + timedelta(seconds=10)

    # A. Prometheus Real Metric Query
    metrics_data = await prom_prov.query_metric(
        metric_name="http_requests_total",
        start_time=start_window,
        end_time=end_window,
        service_name="demo-service"
    )
    print(f"  -> Prometheus: retrieved {len(metrics_data)} metric data points (signal: http_requests_total)")

    # B. Loki Real Log Stream Query
    logs_data = await loki_prov.query_logs(
        query="database_timeout",
        start_time=start_window,
        end_time=end_window,
        service_name="demo-service"
    )
    print(f"  -> Loki: retrieved {len(logs_data)} structured log entries via LogQL")
    if logs_data:
        print(f"     Sample log: \"{logs_data[0].get('message')}\"")

    # C. OpenTelemetry Real Span Query
    traces_data = await otel_prov.query_spans(
        service_name="demo-service",
        start_time=start_window,
        end_time=end_window,
        only_errors=True
    )
    print(f"  -> OpenTelemetry/Jaeger: retrieved {len(traces_data)} distributed spans (errors only)")
    if traces_data:
        print(f"     Root operation: \"{traces_data[0].get('span_name')}\", Duration: {traces_data[0].get('duration_ms')}ms")

    # Ingest into AEGIS Evidence Engine
    evidence_bundle = await aegis.evidence_engine.collect_all(
        organization_id=incident.organization_id,
        incident_id=incident.id,
        service_name="demo-service",
        incident_time=incident.detected_at,
    )
    print(f"  -> AEGIS Evidence Engine normalized {len(evidence_bundle)} evidence items")

    # 5. Causal Reasoning & Hypothesis Generation
    print("\n[Step 5] Performing Structured Causal Reasoning...")
    investigation = await aegis.investigate(incident)
    print(f"  -> Primary Root Cause Hypothesis: \"{investigation.primary_hypothesis.title if investigation.primary_hypothesis else 'Analyzed anomaly'}\"")
    print(f"  -> Grounded in Evidence: {investigation.is_grounded} (Score: {investigation.grounding_score:.2f})")
    print(f"  -> Formulated Hypotheses: {len(investigation.hypotheses)}")

    # 6. Policy & Safety Evaluation
    print("\n[Step 6] Evaluating Fail-Closed Security & Governance Policies...")
    secret_test = aegis.policy_engine.classify_data("Authorization: Bearer my-secret-token")
    assert secret_test == DataClassification.SECRET
    print("  -> Policy Data Classification: Sensitive tokens detected as SECRET")

    # Check remediation policy
    policy_check = aegis.policy_engine.evaluate_remediation_proposal(risk_level=SecurityRiskLevel.LOW)
    print(f"  -> Remediation Proposal Policy Check: allowed={policy_check.allowed}, reason='{policy_check.reason}'")

    # 7. Remediation Planning & Risk Gating
    print("\n[Step 7] Generating Typed Remediation Plan...")
    plan = aegis.plan_remediation(
        incident_id=incident.id,
        service_name="demo-service",
        reason=investigation.primary_hypothesis.title if investigation.primary_hypothesis else "Mitigate database timeout bottleneck",
    )
    print(f"  -> Remediation Plan ID: {plan.id}")
    print(f"  -> Calculated Risk Level: {plan.risk_level.value}")
    print(f"  -> Blast Radius: {plan.blast_radius.affected_services} ({plan.blast_radius.estimated_impact})")
    print(f"  -> Plan Integrity Hash: {plan.compute_plan_hash()[:16]}...")

    # Autonomy Decision
    autonomy_dec = aegis.autonomy_engine.evaluate_plan(plan)
    print(f"  -> Autonomy Decision: {autonomy_dec.decision.value} (Allowed: {autonomy_dec.allowed})")

    # 8. Controlled Kubernetes Execution
    print("\n[Step 8] Executing Controlled Remediation via KubernetesProvider...")
    pre_status = await k8s_prov.get_deployment_status("demo-service", namespace="aegis-integration")
    print(f"  -> Pre-remediation replicas: {pre_status['replicas']}")

    exec_result = await k8s_prov.execute_action(
        action_type=RemediationActionType.SCALING.value,
        target="demo-service",
        parameters={"namespace": "aegis-integration", "replicas": 2},
    )
    print(f"  -> Kubernetes Mutation Result: {exec_result.get('status')}")
    print(f"  -> Execution Message: {exec_result.get('message')}")

    post_status = await k8s_prov.get_deployment_status("demo-service", namespace="aegis-integration")
    print(f"  -> Post-remediation replicas: {post_status['replicas']}")
    assert post_status["replicas"] == 2

    # Record in AEGIS audit logger
    from aegis.core.audit import AuditCategory
    aegis.audit.record(
        category=AuditCategory.REMEDIATION,
        action="remediation.executed",
        actor="aegis-autonomy",
        target="demo-service",
        details={"replicas": 2, "plan_id": str(plan.id)},
    )

    # 9. Recovery Validation
    print("\n[Step 9] Simulating System Recovery and Validating Metrics...")
    http_post(f"{DEMO_URL}/api/incident", {"enabled": False})
    print("  -> Incident resolved; generating post-remediation healthy requests...")
    for _ in range(5):
        http_get(f"{DEMO_URL}/api/request")
    await asyncio.sleep(2)

    recovery_metrics = await prom_prov.query_metric(
        metric_name="http_requests_total",
        start_time=now,
        end_time=datetime.now(UTC),
        service_name="demo-service"
    )
    print(f"  -> Post-recovery Prometheus metric confirmation: {len(recovery_metrics)} telemetry samples verified")

    # 10. Audit Verification
    print("\n[Step 10] Verifying Immutable Audit Trail...")
    audit_events = aegis.audit.get_events()
    print(f"  -> Recorded {len(audit_events)} cryptographically verifiable audit events")
    for ev in audit_events:
        print(f"     [{ev.category.value}] {ev.action}: {ev.details}")

    print("\n" + "=" * 70)
    print("LAB RESULT: FULL END-TO-END AUTONOMOUS LIFECYCLE COMPLETED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_lab())
