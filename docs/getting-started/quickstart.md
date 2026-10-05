# Quickstart Guide

Get up and running with the **AEGIS Framework** in under five minutes.

AEGIS Framework is a developer-facing library for building autonomous reliability engineering workflows, incident investigations, evidence correlation, root cause reasoning, policy guardrails, and safe remediation.

---

## 1. Installation

Install the framework via pip:

```bash
pip install aegis-ai
```

> **Note on Architecture Separation:**
> - **Framework Core (`aegis`)**: Pure Python library with zero database or infrastructure lock-in.
> - **Memory Providers (`aegis.providers.memory`)**: In-memory, deterministic providers for local development, CI/CD, and testing.
> - **Production Providers**: Real infrastructure adapters (e.g. Prometheus, OpenTelemetry, Loki, Datadog).
> - **Reference Platform (`AEGIS AI`)**: The complete enterprise platform and web UI.

---

## 2. Minimal Working Example

This minimal snippet demonstrates creating an incident, injecting deterministic in-memory providers, and executing an automated investigation:

```python
import asyncio
from datetime import UTC, datetime, timedelta

from aegis import Aegis, AutonomyLevel, IncidentSeverity
from aegis.providers.memory import (
    InMemoryMetricsProvider,
    InMemoryLogProvider,
    InMemoryTraceProvider,
    InMemoryRemediationProvider,
)

async def main():
    now = datetime.now(UTC)

    # 1. Initialize In-Memory Providers
    metrics = InMemoryMetricsProvider()
    metrics.record_metric(
        metric_name="http_request_duration_seconds",
        value=1.65,
        timestamp=now,
        service_name="order-service",
    )

    logs = InMemoryLogProvider()
    logs.record_log(
        service="order-service",
        level="ERROR",
        message="database query timeout after 30000ms",
        timestamp=now,
    )

    traces = InMemoryTraceProvider()
    traces.record_span(
        service="order-service",
        name="postgres.query",
        duration_ms=1650.0,
        timestamp=now,
        is_error=True,
    )

    # 2. Instantiate Aegis Client
    aegis = Aegis(
        metrics_provider=metrics,
        log_provider=logs,
        trace_provider=traces,
        autonomy_level=AutonomyLevel.LEVEL_1,
    )

    # 3. Create Incident & Investigate
    incident = aegis.create_incident(
        title="Database latency degradation",
        severity=IncidentSeverity.HIGH,
        service_name="order-service",
    )

    result = await aegis.investigate(incident)
    print(f"Incident Summary: {result.summary}")
    print(f"Top Hypothesis:  {result.primary_hypothesis.title}")
    print(f"Confidence:      {result.confidence:.2f}")

    # 4. Plan Remediation
    plan = aegis.plan_remediation(
        incident_id=incident.id,
        service_name="order-service",
        reason=result.primary_hypothesis.title,
    )
    print(f"Remediation:     {plan.title} (Risk: {plan.risk_level.value})")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 3. Running the Complete Example

Run the comprehensive runnable example included in the repository:

```bash
python examples/basic_investigation.py
```

The example exercises:
- Multimodal evidence collection and chronological timeline generation
- Causal hypothesis scoring and grounding verification
- Deterministic policy guardrail evaluation
- Remediation planning with risk score, blast radius, validation criteria, and rollback strategy
- Separation of duties and human approval verification
- Autonomy tier gates (`LEVEL_0`, `LEVEL_1`, `LEVEL_2`)
- `llmfirewall-core` prompt injection inspection
- Governed tool gateway with deny-by-default execution
- Upstream `aireliability` causal trace diagnosis and expectation verification
