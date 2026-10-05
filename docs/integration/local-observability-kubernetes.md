# Real Local Observability & Kubernetes Integration Lab Guide

**Target Version**: AEGIS Framework `v0.1.0`  
**Lab Purpose**: Validate AEGIS production providers against real local Prometheus, Loki, OpenTelemetry/Jaeger, and Kubernetes infrastructure.

---

## 1. Prerequisites

- **Docker**: Docker Desktop (or engine) running locally.
- **Python**: 3.12+ with AEGIS Framework virtual environment (`.venv`).
- **Ports**: 18080 (demo service), 19090 (Prometheus), 3100 (Loki). Isolated from default development ports to prevent host conflicts.

---

## 2. Lab Architecture

```text
                    ┌──────────────────────────────────────────────┐
                    │               AEGIS Framework                │
                    │               Investigation Lab              │
                    └──────────────────────┬───────────────────────┘
                                           │
                    ┌──────────────────────┼───────────────────────┐
                    │                      │                       │
                    ▼                      ▼                       ▼
            Prometheus (v2.54.1)      Loki (v3.0.0)       Jaeger/OTel Spans
                 :19090                   :3100                 :18080
                    │                      │                       │
                    └──────────────────────┼───────────────────────┘
                                           │
                                           ▼
                                 Kubernetes Workload
                               (demo-service in namespace
                                  'aegis-integration')
```

---

## 3. Quickstart: Automated Execution

Execute the full lab lifecycle with automated container startup, readiness polling, integration test verification, autonomous incident remediation, and clean teardown:

```bash
./scripts/run_integration_lab.sh
```

---

## 4. Manual Step-by-Step Execution

### Step 1: Start Local Observability Infrastructure
```bash
docker compose -f integration/docker-compose.yml up -d
```

Verify service readiness:
- Demo service: `curl http://localhost:18080/health`
- Prometheus: `curl http://localhost:19090/-/ready`
- Loki: `curl http://localhost:3100/ready`

### Step 2: Run Pytest Real Infrastructure Suite
```bash
pytest -m integration -v
```

### Step 3: Trigger Incident Mode on Demo Application
```bash
curl -X POST -H "Content-Type: application/json" -d '{"enabled": true}' http://localhost:18080/api/incident
```

Generate degradation traffic:
```bash
for i in {1..5}; do curl http://localhost:18080/api/request; done
```

### Step 4: Run AEGIS Autonomous Investigation
```bash
python integration/run_lab.py
```

The script will:
1. Connect `PrometheusMetricsProvider`, `LokiLogProvider`, `OpenTelemetryTraceProvider`, and `KubernetesProvider`.
2. Collect real metrics from Prometheus (`http_requests_total`).
3. Query real error logs from Loki (`database_timeout`).
4. Query real distributed spans from the trace endpoint (`database_query`).
5. Normalize evidence in `aegis.evidence_engine`.
6. Formulate causal hypotheses via `aegis.investigate()`.
7. Evaluate fail-closed security and policy guardrails via `aegis.policy_engine`.
8. Generate a typed remediation plan (`scaling` to 2 replicas) with computed risk, blast radius, and SHA-256 integrity hash.
9. Verify autonomy decision under `LEVEL_2`.
10. Execute typed mutation on `KubernetesProvider` for target `aegis-integration/demo-service`.
11. Confirm post-mutation recovery via Prometheus metrics.
12. Inspect the immutable cryptographic audit log.

### Step 5: Teardown
```bash
docker compose -f integration/docker-compose.yml down --remove-orphans
```

---

## 5. Troubleshooting & FAQ

| Issue | Cause | Resolution |
|---|---|---|
| `Port 19090 or 18080 already in use` | Another local service is bound to the port. | Run `lsof -i :19090` and stop conflicting process or update `integration/docker-compose.yml`. |
| `Loki returns Ingester not ready` | Loki tsdb ring initialization takes ~15 seconds on cold boot. | The runner script automatically retries until `/ready` returns HTTP 200. |
| `Prometheus 400 timeout error` | Formatting timeout parameter with decimal point (e.g. `15.0s`). | Fixed in `PrometheusMetricsProvider` by casting to integer seconds `f"{int(timeout)}s"`. |
| `Arbitrary shell execution blocked` | KubernetesProvider design invariant. | AEGIS strictly rejects untyped shell/kubectl subprocesses; only typed actions (`scaling`, `service_restart`) are permitted. |
