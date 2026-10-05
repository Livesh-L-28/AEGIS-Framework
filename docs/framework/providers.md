# Provider Architecture & Custom Adapters

AEGIS Framework is designed around **pure protocol abstraction** and **dependency injection**. The core reasoning and safety engines never communicate directly with specific databases or external services. Instead, they depend strictly on Python protocols.

---

## 1. Provider Protocols

All provider protocols are defined in `aegis.providers` (and `aegis.providers.protocols`):

| Protocol | Purpose | Key Method |
|---|---|---|
| `MetricsProvider` | Time series metric queries | `query_metric(...)` |
| `LogProvider` | Structured and unstructured log searches | `query_logs(...)` |
| `TraceProvider` | Distributed trace span graphs | `query_spans(...)` |
| `TelemetryProvider` | Unified bundle of metrics, logs, and spans | `collect_telemetry(...)` |
| `DeploymentProvider` | Rollouts, releases, and CI/CD events | `list_recent_deployments(...)` |
| `ModelProvider` | LLM reasoning & structured analysis | `generate(...)` |
| `EmbeddingProvider` | Vector embedding generation | `embed_texts(...)` |
| `VectorIndexProvider` | Vector similarity indexing and search | `search(...)` |
| `ApprovalStore` | Remediation proposal approval storage | `store_approval(...)`, `get_approval(...)` |
| `StorageProvider` | Artifact and report blob persistence | `save(...)`, `get(...)` |
| `RemediationProvider`| Infrastructure action execution | `execute_action(...)` |

---

## 2. In-Memory Providers (`aegis.providers.memory`)

The framework ships with complete in-memory implementations of all 11 providers:

- `InMemoryMetricsProvider` — Deterministic metric series storage with label and timestamp filtering.
- `InMemoryLogProvider` — Structured log storage with level parsing (`level:error`) and text matching.
- `InMemoryTraceProvider` — Parent/child trace tree graph support with latency and error tracking.
- `InMemoryTelemetryProvider` — Composite telemetry aggregator without data duplication.
- `InMemoryDeploymentProvider` — Deployment and release event correlation.
- `InMemoryModelProvider` — Deterministic structured model output for testing reasoning engines.
- `InMemoryEmbeddingProvider` & `InMemoryVectorIndexProvider` — In-memory cosine similarity search without Postgres/pgvector.
- `InMemoryApprovalStore` — Persistent approval store enforcing separation-of-duties invariants.
- `InMemoryStorageProvider` — Byte payload storage returning `memory://` URIs.
- `InMemoryRemediationProvider` — Safe typed remediation runner that never executes subprocesses or arbitrary shell commands.

---

## 3. Implementing a Custom Provider

To connect AEGIS to your organization's observability or deployment infrastructure (such as Prometheus, Datadog, New Relic, OpenTelemetry, or custom APIs), implement the matching protocol.

### Example: Custom Prometheus Metrics Provider

```python
from datetime import datetime
from typing import Any
import httpx
from aegis.providers import MetricsProvider

class PrometheusMetricsProvider:
    """Custom MetricsProvider querying an internal Prometheus instance."""

    def __init__(self, prometheus_url: str):
        self.prometheus_url = prometheus_url

    async def query_metric(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        service_name: str | None = None,
        labels: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        query = metric_name
        if service_name:
            query = f'{metric_name}{{service="{service_name}"}}'

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.prometheus_url}/api/v1/query_range",
                params={
                    "query": query,
                    "start": start_time.timestamp(),
                    "end": end_time.timestamp(),
                    "step": "15s",
                },
            )
            data = resp.json()

        points = []
        for result in data.get("data", {}).get("result", []):
            for ts, val in result.get("values", []):
                points.append({
                    "metric_name": metric_name,
                    "value": float(val),
                    "timestamp": datetime.fromtimestamp(float(ts)),
                    "service_name": service_name,
                    "signal": metric_name,
                    "provenance": f"prometheus:{metric_name}",
                })
        return points

# Verify protocol conformance at runtime
assert isinstance(PrometheusMetricsProvider("http://localhost:9090"), MetricsProvider)
```

### Injecting Custom Providers into Aegis

Pass your custom provider directly to the `Aegis` constructor:

```python
from aegis import Aegis

aegis = Aegis(
    metrics_provider=PrometheusMetricsProvider("http://prometheus:9090"),
    # Any other providers can remain in-memory or custom:
    log_provider=my_loki_provider,
)
```
