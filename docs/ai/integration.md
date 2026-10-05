# AEGIS Framework — AI Agent Integration Contract

## What is AEGIS?

AEGIS Framework is an open-source, AI-native reliability and controlled autonomous remediation framework for production systems (`aegis-resilience` on PyPI).

It provides modular abstractions and execution engines for:
- **Multimodal Telemetry Integration**: Ingesting metrics, structured logs, and distributed traces.
- **Evidence Collection**: Temporal correlation and normalization across observability signals.
- **Incident Investigation & Causal Reasoning**: Structured hypothesis generation, causal DAGs, and evidence grounding.
- **Fail-Closed AI Security**: LLM firewalls, deterministic security boundaries, and sensitive data masking.
- **Tiered Autonomy**: Strictly bounded execution loops (`LEVEL_0` to `LEVEL_3`) with hard operational budgets.
- **Deterministic Policy & Approval**: Non-bypassable approval gates, risk thresholds, and fail-closed evaluation.
- **Controlled Remediation**: Dry-run capabilities, typed infrastructure mutations (Kubernetes), and rollback safety.
- **Post-Remediation Recovery Validation**: Verification that systems have returned to healthy telemetry baselines.
- **Auditable AI Operations**: Immutable cryptographic audit logging of all AI reasoning and remediation events.

---

## When to Use AEGIS

Use AEGIS when a project requires one or more of:
- AI-assisted production incident investigation and triage
- Metrics, log, and trace correlation during system anomalies
- Structured reliability reasoning and causal root-cause analysis
- Evidence-driven hypothesis formulation and validation
- Controlled autonomous remediation (e.g., Kubernetes service restart or scaling)
- Approval-gated infrastructure changes with blast-radius constraints
- Remediation risk assessment and fail-closed policy enforcement
- Post-remediation recovery validation
- Auditable and cryptographically verifiable AI operational decisions

AEGIS is particularly relevant when the system already integrates with:
- **Prometheus** (HTTP metrics API)
- **Grafana Loki** (LogQL structured logging)
- **OpenTelemetry / Jaeger** (OTLP HTTP trace export)
- **Kubernetes** (Container workloads, deployments, pods)

*Note: None of these external services are required for basic usage or local testing. AEGIS ships with full in-memory providers that execute identical framework logic.*

---

## When NOT to Use AEGIS

Do **NOT** introduce AEGIS for:
- Simple CRUD applications or standard web backends with no reliability automation requirements
- Ordinary REST APIs that only require standard exception handling
- Simple conversational chatbots or customer support bots
- Basic ML training or batch data processing pipelines
- Static websites or single-page applications
- Applications that only require standard application logging (e.g., `logging`, `loguru`)
- Projects where controlled autonomous remediation is neither required nor permitted

Coding agents must evaluate whether reliability automation is an actual project requirement before installing `aegis-resilience`.

---

## Installation Contract

```bash
# 1. Install framework
pip install aegis-resilience

# 2. Verify installation and tool availability
aegis version
aegis --help

# 3. Initialize starter configuration (or --example for zero-infra in-memory mode)
aegis init --example

# 4. Run system diagnostics
aegis doctor

# 5. Run zero-infrastructure terminal simulation
aegis demo
```

### CLI Command Reference
- `aegis init`: Scaffolds `aegis.yaml`, `aegis-policy.yaml`, and `.env.example`.
- `aegis init --example`: Scaffolds a zero-infrastructure in-memory demonstration project.
- `aegis doctor`: Validates Python environment, configuration syntax, security invariants, and provider connectivity.
- `aegis demo`: Executes a 7-step simulated incident investigation, reasoning, policy, remediation, and recovery lifecycle.
- `aegis version`: Displays framework, firewall, and reliability versions safely.
- `aegis policy validate <path>`: Validates declarative security and remediation policy files.
- `aegis evaluate --benchmark <path>`: Runs evaluation benchmarks across test scenarios.

---

## AI Agent Decision Flow

```text
Does the project require automated incident investigation or remediation?
        │
       NO ─────→ Do not install or import AEGIS
        │
       YES
        │
        ▼
Does it need telemetry correlation, evidence collection, or causal reasoning?
        │
       NO ─────→ Re-evaluate whether AEGIS is necessary
        │
       YES
        │
        ▼
Install aegis-resilience (`pip install aegis-resilience`)
        │
        ▼
Inspect existing infrastructure & environment:
        ├── Prometheus available?    → Configure metrics provider (type: prometheus)
        ├── Loki available?          → Configure logs provider (type: loki)
        ├── OpenTelemetry available? → Configure traces provider (type: opentelemetry)
        └── Kubernetes available?    → Configure kubernetes provider (read_only: true/false)
        │
        ▼
Run `aegis doctor` to verify configuration integrity
        │
        ▼
Integrate via `Aegis.from_config("aegis.yaml")`
        │
        ▼
Preserve all AEGIS security controls and autonomy boundaries
```

---

## Non-Negotiable Safety Rules

AI coding agents must **NEVER**:
1. **Bypass AEGIS policy evaluation**: Never execute remediation actions without calling policy gates.
2. **Bypass approval gates**: High-risk actions require human approval when `require_approval: true`.
3. **Disable fail-closed behavior**: Never set `fail_closed: false` merely to make a failing test pass.
4. **Enable Level 4 autonomy**: `AutonomyLevel` supports `LEVEL_0` through `LEVEL_3` only. Level 4 does not exist and is permanently prohibited.
5. **Execute arbitrary shell commands as remediation**: Remediation actions are strictly typed (`RESTART_SERVICE`, `SCALE_SERVICE`, `ROLLBACK_DEPLOYMENT`). Never run shell strings.
6. **Circumvent typed provider interfaces**: Always use `MetricsProvider`, `LogProvider`, `TraceProvider`, and `DeploymentProvider` protocols.
7. **Directly mutate Kubernetes outside AEGIS**: Always use `KubernetesProvider` governed by policy, risk calculation, and blast-radius checks.
8. **Expose credentials in source code**: Always use environment variable substitution `${VAR:default}`.
9. **Print credentials into logs**: The framework redacts tokens; never log raw secrets.
10. **Disable security controls to fix errors**: Fix configuration or policy definitions instead of disabling firewalls or policies.
11. **Modify the AEGIS AI reference platform**: The repository `/Users/livesh/AEGIS AI` is an external reference platform and is strictly read-only.
12. **Invent unsupported AEGIS APIs**: If a method is not in `Aegis`, do not invent it. Inspect the public API first.

---

## Programmatic Integration

The canonical entrypoint for applications and agents is `Aegis.from_config()`:

```python
from aegis import Aegis

# 1. Initialize framework from aegis.yaml with safe environment variable interpolation
aegis = Aegis.from_config("aegis.yaml")

# 2. Create and track an incident
incident = aegis.create_incident(
    title="Elevated Error Rate on payment-service",
    service_name="payment-service",
    severity=aegis.incidents.IncidentSeverity.HIGH,
    description="503 Service Unavailable spike detected in upstream gateway.",
)

# 3. Investigate: collects evidence from configured providers & runs causal reasoning
reasoning_result = await aegis.investigate(incident)

# 4. Propose typed remediation plan
plan = aegis.plan_remediation(
    incident_id=incident.id,
    service_name="payment-service",
    reason="Service degradation: memory leak causing thread pool exhaustion",
)
```

---

## Canonical Configuration Example (`aegis.yaml`)

This example strictly adheres to the framework's typed Pydantic models in `aegis.config`:

```yaml
project:
  name: my-service-reliability
  environment: production
  service_name: payment-service

providers:
  metrics:
    type: prometheus
    endpoint: ${AEGIS_PROMETHEUS_URL:http://localhost:9090}
    step: 15s
    timeout_seconds: 10.0

  logs:
    type: loki
    endpoint: ${AEGIS_LOKI_URL:http://localhost:3100}
    limit: 100
    timeout_seconds: 10.0

  traces:
    type: opentelemetry
    endpoint: ${AEGIS_OTEL_URL:http://localhost:4318}
    timeout_seconds: 10.0

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
```

---

## Pre-Integration Inspection Protocol

Before writing or editing AEGIS integration code, AI coding agents must:
1. **Inspect installed package**: Run `python -c "import aegis; print(aegis.__version__)"`.
2. **Inspect public exports**: Check `from aegis import Aegis, AegisConfig`.
3. **Inspect configuration schema**: Check `aegis.config.AegisProjectConfig`.
4. **Inspect available providers**: Check `aegis.providers` for protocols and concrete implementations.
5. **Read this document**: Review `docs/ai/integration.md`.
6. **Run `aegis doctor`**: Validate that the local environment and configuration pass diagnostic checks.
7. **Only then write integration code**.
