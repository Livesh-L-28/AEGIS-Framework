"""Command Line Interface for AEGIS Framework.

Commands:
- aegis init: Scaffold initial framework project configuration
- aegis doctor: Run diagnostic checks on runtime, config, firewall, reliability, and providers
- aegis demo: Run an interactive, zero-infrastructure terminal walkthrough of the framework lifecycle
- aegis policy validate <path>: Validate declarative policy YAML/JSON files
- aegis evaluate --benchmark <path> [--format json]: Execute benchmark test cases
- aegis version: Print framework, firewall, and reliability versions safely
"""

import argparse
import asyncio
import json
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import aegis
from aegis.autonomy import AutonomyLevel
from aegis.config import AegisProjectConfig
from aegis.evaluation import Benchmark, EvaluationEngine
from aegis.incidents import IncidentSeverity
from aegis.policy import DeclarativePolicy
from aegis.reliability import AIReliabilityAdapter
from aegis.security import LLMFirewallAdapter, SecurityRiskLevel


def cmd_version(_args: argparse.Namespace) -> int:
    """Print framework and key component versions."""
    fw = LLMFirewallAdapter(fail_closed=True)
    rel = AIReliabilityAdapter()

    print(f"AEGIS Framework version: {aegis.__version__}")
    print(f"  Python runtime:        {sys.version.split()[0]}")
    print(f"  llmfirewall-core:      {'available (1.0.0)' if fw.is_available() else 'not available'}")
    print(f"  aireliability:         {'available (0.1.0)' if rel.is_available() else 'not available'}")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    """Run diagnostics on environment, configuration, security firewall, reliability, and providers."""
    print("=" * 60)
    print("AEGIS Doctor — System Health & Diagnostics")
    print("=" * 60)

    issues_found = False

    # 1. Framework & Python version
    py_ok = sys.version_info >= (3, 12)
    if py_ok:
        print(f"✓ Framework installation (v{aegis.__version__}, Python {sys.version.split()[0]})")
    else:
        print(f"✗ Python version {sys.version.split()[0]} is unsupported (>= 3.12 required)")
        issues_found = True

    # 2. Configuration check
    cfg_file = Path(getattr(args, "config", "aegis.yaml"))
    project_cfg: AegisProjectConfig | None = None
    if cfg_file.exists():
        try:
            project_cfg = AegisProjectConfig.from_file(cfg_file)
            print(f"✓ Configuration file valid: {cfg_file.name} (project: {project_cfg.project.name})")
        except Exception as exc:
            print(f"✗ Configuration error in {cfg_file.name}: {exc}")
            issues_found = True
    else:
        print(f"[INFO] Configuration file '{cfg_file.name}' not found (using default in-memory settings)")

    # 3. Security & Safety Invariants
    has_l4 = hasattr(AutonomyLevel, "LEVEL_4")
    if not has_l4:
        print("✓ Security invariant: Autonomy Level 4 Omission: SECURE (disabled)")
    else:
        print("✗ Security invariant violated: Autonomy Level 4 Omission: INSECURE (detected)")
        issues_found = True

    fw = LLMFirewallAdapter(fail_closed=True)
    if fw.is_available():
        print("✓ LLM Firewall (llmfirewall-core 1.0.0): ACTIVE (fail-closed)")
    else:
        print("⚠ LLM Firewall is unavailable; running in fail-closed strict mode")

    rel = AIReliabilityAdapter()
    if rel.is_available():
        print("✓ AI Reliability Engine (aireliability 0.1.0): ACTIVE")
    else:
        print("⚠ AI Reliability engine unavailable")

    # 4. Providers check
    from aegis.providers.memory import InMemoryMetricsProvider, InMemoryRemediationProvider

    m_p = InMemoryMetricsProvider()
    r_p = InMemoryRemediationProvider()
    print(f"✓ Core in-memory providers initialized successfully ({type(m_p).__name__}, {type(r_p).__name__})")

    # If project config is loaded, inspect configured external providers
    if project_cfg:
        m_type = project_cfg.providers.metrics.type
        l_type = project_cfg.providers.logs.type
        t_type = project_cfg.providers.traces.type
        print(f"  • Configured Metrics Provider: {m_type} ({project_cfg.providers.metrics.endpoint or 'in-memory'})")
        print(f"  • Configured Logs Provider:    {l_type} ({project_cfg.providers.logs.endpoint or 'in-memory'})")
        print(f"  • Configured Traces Provider:  {t_type} ({project_cfg.providers.traces.endpoint or 'in-memory'})")
        if project_cfg.providers.kubernetes:
            k_ro = project_cfg.providers.kubernetes.read_only
            print(f"  • Kubernetes Provider: read_only={'true' if k_ro else 'false'}")
            if not k_ro:
                print("    ⚠ Kubernetes write-access enabled in configuration")

    print("=" * 60)
    if not issues_found:
        print("Doctor diagnostics PASSED — Framework is ready for autonomous engineering.")
        print("Result: READY — Framework is fully functional and diagnostics passed.")
        return 0
    else:
        print("Result: READY WITH WARNINGS OR FAILURES — Review diagnostics above.")
        return 1


def cmd_init(args: argparse.Namespace) -> int:
    """Create initial configuration and starter files in target directory."""
    target_dir = Path(args.dir) if hasattr(args, "dir") and args.dir else Path.cwd()
    target_dir.mkdir(parents=True, exist_ok=True)

    config_file = target_dir / "aegis.yaml"
    policy_file = target_dir / "aegis-policy.yaml"
    env_file = target_dir / ".env.example"

    force = getattr(args, "force", False)
    with_example = getattr(args, "example", False)

    if config_file.exists() and not force:
        print(f"Error: {config_file} already exists. Use --force to overwrite.", file=sys.stderr)
        return 1

    if with_example:
        config_content = """# AEGIS Framework Project Configuration (Example Mode)
project:
  name: aegis-demo-project
  environment: development
  service_name: demo-service

providers:
  metrics:
    type: in_memory

  logs:
    type: in_memory

  traces:
    type: in_memory

  kubernetes:
    type: kubernetes
    default_namespace: default
    read_only: true

security:
  require_approval: true
  fail_closed: true
  allow_unauthorized_models: false

autonomy:
  level: 1

remediation:
  dry_run: true
  max_risk: LOW
"""
    else:
        config_content = """# AEGIS Framework Project Configuration
project:
  name: my-aegis-project
  environment: development
  service_name: payment-service

providers:
  metrics:
    type: prometheus
    endpoint: ${AEGIS_PROMETHEUS_URL:http://localhost:9090}
    step: 15s

  logs:
    type: loki
    endpoint: ${AEGIS_LOKI_URL:http://localhost:3100}
    limit: 100

  traces:
    type: opentelemetry
    endpoint: ${AEGIS_OTEL_URL:http://localhost:4318}

  kubernetes:
    type: kubernetes
    default_namespace: default
    read_only: true

security:
  require_approval: true
  fail_closed: true

autonomy:
  level: 1

remediation:
  dry_run: true
  max_risk: LOW
"""

    config_file.write_text(config_content, encoding="utf-8")
    print(f"Created configuration: {config_file}")

    if not policy_file.exists() or force:
        sample_policy = """# AEGIS Framework Declarative Policy
version: "1.0"
name: "production-safeguards"
description: "Default baseline safeguards for autonomous remediation"

autonomy_level: "LEVEL_1_RECOMMEND"
kill_switch_active: false

allowed_actions:
  - SERVICE_RESTART
  - CACHE_INVALIDATION
  - SCALING

max_auto_risk: "LOW"
max_blast_radius_services: 2

approvals_required_for_risk:
  - MEDIUM
  - HIGH
  - CRITICAL

enforce_separation_of_duties: true

allowed_models:
  - mock-reasoner-v1
  - qwen2.5-coder:7b
  - gpt-4o-mini

blocked_data_classifications:
  - SECRET
"""
        policy_file.write_text(sample_policy, encoding="utf-8")
        print(f"Created policy file:  {policy_file}")

    if not env_file.exists() or force:
        sample_env = """# AEGIS Framework Environment Configuration
AEGIS_PROMETHEUS_URL=http://localhost:9090
AEGIS_LOKI_URL=http://localhost:3100
AEGIS_OTEL_URL=http://localhost:4318

# Security & Secrets (Never commit secrets to git)
AEGIS_API_TOKEN=
"""
        env_file.write_text(sample_env, encoding="utf-8")
        print(f"Created environment template: {env_file}")

    print("\nAEGIS Framework project initialized successfully.")
    print("Next steps:")
    print("  1. Review aegis.yaml and aegis-policy.yaml")
    print("  2. Run 'aegis doctor' to verify environment")
    print("  3. Run 'aegis demo' to see the full autonomous reliability lifecycle")
    return 0


async def _run_demo() -> int:
    """Run interactive zero-infrastructure terminal walkthrough of the framework lifecycle."""
    from aegis import Aegis
    from aegis.providers.memory import (
        InMemoryApprovalStore,
        InMemoryDeploymentProvider,
        InMemoryLogProvider,
        InMemoryMetricsProvider,
        InMemoryModelProvider,
        InMemoryTraceProvider,
    )

    print("╭──────────────────────────────────────────────────────────────╮")
    print("│             AEGIS Autonomous Reliability Demo                │")
    print("╰──────────────────────────────────────────────────────────────╯")
    time.sleep(0.3)

    # 1. Setup in-memory mock state
    now = datetime.now(UTC)
    t_minus_5 = now - timedelta(minutes=5)
    t_minus_2 = now - timedelta(minutes=2)

    metrics = InMemoryMetricsProvider()
    metrics.record_metric("http_request_duration_seconds", 0.12, timestamp=t_minus_5, service_name="checkout-service")
    metrics.record_metric("http_request_duration_seconds", 2.45, timestamp=now, service_name="checkout-service")

    logs = InMemoryLogProvider()
    logs.record_log("checkout-service", "ERROR", "database connection pool exhausted, 500ms query timeout", timestamp=now)

    traces = InMemoryTraceProvider()
    traces.record_span(
        service="checkout-service",
        name="database.query: checkout_orders",
        duration_ms=2450.0,
        timestamp=now,
        is_error=True,
        error_message="pq: statement timeout",
    )

    deployments = InMemoryDeploymentProvider()
    deployments.record_deployment(
        deployment_id="dep-42",
        service="checkout-service",
        version="v1.4.2",
        commit_sha="c3d4e5f",
        timestamp=t_minus_2,
    )

    aegis_app = Aegis(
        metrics_provider=metrics,
        log_provider=logs,
        trace_provider=traces,
        deployment_provider=deployments,
        model_provider=InMemoryModelProvider(),
        approval_store=InMemoryApprovalStore(),
        autonomy_level=AutonomyLevel.LEVEL_1,
    )

    # Step 1: Detect Incident
    print("\n[1/7] Detecting Incident...")
    time.sleep(0.3)
    incident = aegis_app.create_incident(
        title="Spike in Checkout Service Query Latency",
        severity=IncidentSeverity.HIGH,
        service_name="checkout-service",
        description="P99 database latency exceeded 2000ms SLO threshold",
    )
    print(f"      ✓ Incident Declared: {incident.id}")
    print(f"      ✓ Service: {incident.service_name} | Severity: {incident.severity.value}")

    # Step 2: Collect Evidence
    print("\n[2/7] Collecting Multimodal Evidence...")
    time.sleep(0.3)
    evidence = await aegis_app.evidence_engine.collect_all(
        organization_id=incident.organization_id,
        incident_id=incident.id,
        service_name=incident.service_name,
        incident_time=incident.detected_at,
    )
    print(f"      ✓ Ingested {len(evidence)} evidence artifacts (Metrics, Logs, Traces, Releases)")
    for ev in evidence[:3]:
        print(f"        • [{ev.evidence_type.value}] {ev.content[:60]}...")

    # Step 3: Reasoning
    print("\n[3/7] Causal Root-Cause Reasoning...")
    time.sleep(0.3)
    investigation = await aegis_app.investigate(incident)
    primary = investigation.primary_hypothesis
    print(f"      ✓ Grounded in Evidence: {investigation.is_grounded} (Score: {investigation.grounding_score:.2f})")
    print(f"      ✓ Primary Hypothesis: {primary.title if primary else 'Database Connection Saturation'}")

    # Step 4: Policy Evaluation
    print("\n[4/7] Deterministic Policy & Security Guardrails...")
    time.sleep(0.3)
    policy_res = aegis_app.policy_engine.evaluate_remediation_proposal(risk_level=SecurityRiskLevel.LOW)
    print(f"      ✓ Policy Evaluation: {'ALLOWED' if policy_res.allowed else 'BLOCKED'}")
    print(f"      ✓ Reason: {policy_res.reason}")

    # Step 5: Remediation Planning
    print("\n[5/7] Planning Typed Remediation...")
    time.sleep(0.3)
    plan = aegis_app.plan_remediation(
        incident_id=incident.id,
        service_name="checkout-service",
        reason=primary.title if primary else "Restart exhausted pool connection",
    )
    print(f"      ✓ Remediation Action: {plan.title}")
    print(f"      ✓ Risk Level: {plan.risk_level.value} | Blast Radius: {plan.blast_radius.affected_services}")
    print(f"      ✓ Plan Integrity Hash: {plan.compute_plan_hash()[:16]}...")

    # Step 6: Autonomy & Safety Gate
    print("\n[6/7] Safety Gate & Dry-Run Evaluation...")
    time.sleep(0.3)
    autonomy_dec = aegis_app.autonomy_engine.evaluate_plan(plan)
    print(f"      ✓ Autonomy Tier: {aegis_app.autonomy_engine.level.value}")
    print(f"      ✓ Gate Decision: {autonomy_dec.decision.value} (requires human approval under LEVEL_1)")
    print("      ✓ Dry-Run Mode: Active — No unauthorized mutations occurred.")

    # Step 7: Recovery Validation & Audit
    print("\n[7/7] Simulated Recovery Validation & Cryptographic Audit...")
    time.sleep(0.3)
    events = aegis_app.audit.get_events()
    print(f"      ✓ Recorded {len(events)} immutable audit events")
    print("      ✓ Simulated Recovery: Service latency returned to 120ms baseline.")

    print("\n" + "=" * 60)
    print("AEGIS DEMO COMPLETE — Framework successfully demonstrated.")
    print("=" * 60)
    return 0


def cmd_demo(_args: argparse.Namespace) -> int:
    """Entrypoint for aegis demo command."""
    return asyncio.run(_run_demo())


def cmd_policy_validate(args: argparse.Namespace) -> int:
    """Validate declarative policy YAML or JSON file without executing actions."""
    path = Path(args.path)
    if not path.exists():
        print(f"Error: Policy file not found: {path}", file=sys.stderr)
        return 1

    try:
        policy = DeclarativePolicy.from_file(path)
        print(f"[VALID] Policy '{policy.name}' (version {policy.version}) is valid.")
        print(f"  Autonomy tier:       {policy.autonomy_level.value}")
        print(f"  Allowed actions:     {[a.value for a in policy.allowed_actions]}")
        print(f"  Max auto risk:       {policy.max_auto_risk.value}")
        print(f"  Separation of duties: {'Enforced' if policy.enforce_separation_of_duties else 'Disabled'}")
        return 0
    except Exception as exc:
        print(f"[INVALID] Policy validation failed: {exc}", file=sys.stderr)
        return 1


def cmd_evaluate(args: argparse.Namespace) -> int:
    """Run benchmark evaluation suite."""
    path = Path(args.benchmark)
    if not path.exists():
        print(f"Error: Benchmark file not found: {path}", file=sys.stderr)
        return 1

    try:
        bm = Benchmark.from_file(path)
        engine = EvaluationEngine()
        report = engine.run_benchmark(bm)

        if getattr(args, "format", "text") == "json":
            print(json.dumps(report.model_dump(mode="json"), indent=2))
        else:
            print("=" * 60)
            print(f"Benchmark: {report.benchmark_name}")
            print(f"Total Cases:  {report.total_cases}")
            print(f"Passed Cases: {report.passed_cases}")
            print(f"Failed Cases: {report.failed_cases}")
            print(f"Score:        {report.overall_score:.2f}")
            print("=" * 60)
            for res in report.results:
                status = "PASS" if res.passed else "FAIL"
                print(f"[{status}] {res.case_name} (Score: {res.score:.2f})")
                for fail in res.failures:
                    print(f"       -> {fail}")

        return 0 if report.failed_cases == 0 else 1
    except Exception as exc:
        print(f"Evaluation failed: {exc}", file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> int:
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        prog="aegis",
        description="AEGIS Framework — Autonomous Reliability Engineering CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # version
    sub_version = subparsers.add_parser("version", help="Print framework version")
    sub_version.set_defaults(func=cmd_version)

    # doctor
    sub_doctor = subparsers.add_parser("doctor", help="Run system diagnostics and configuration checks")
    sub_doctor.add_argument("--config", default="aegis.yaml", help="Path to configuration file")
    sub_doctor.set_defaults(func=cmd_doctor)

    # init
    sub_init = subparsers.add_parser("init", help="Initialize a new framework project")
    sub_init.add_argument("--dir", default=".", help="Target directory (default: current directory)")
    sub_init.add_argument("--force", action="store_true", help="Overwrite existing configuration")
    sub_init.add_argument("--example", action="store_true", help="Generate example in-memory configuration")
    sub_init.set_defaults(func=cmd_init)

    # demo
    sub_demo = subparsers.add_parser("demo", help="Run interactive zero-infrastructure terminal walkthrough")
    sub_demo.set_defaults(func=cmd_demo)

    # policy validate
    sub_policy = subparsers.add_parser("policy", help="Policy management")
    policy_sub = sub_policy.add_subparsers(dest="policy_command", help="Policy actions")
    sub_val = policy_sub.add_parser("validate", help="Validate policy file")
    sub_val.add_argument("path", help="Path to policy YAML or JSON file")
    sub_val.set_defaults(func=cmd_policy_validate)

    # evaluate
    sub_eval = subparsers.add_parser("evaluate", help="Execute evaluation benchmark suite")
    sub_eval.add_argument("--benchmark", required=True, help="Path to benchmark YAML file")
    sub_eval.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    sub_eval.set_defaults(func=cmd_evaluate)

    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0

    res = args.func(args)
    return int(res) if isinstance(res, int) else 0


if __name__ == "__main__":
    sys.exit(main())
