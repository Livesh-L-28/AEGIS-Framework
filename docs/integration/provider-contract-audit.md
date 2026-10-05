# AEGIS Framework Provider Contract Audit

**Document**: Provider Contract Audit & Technical Specifications  
**Release**: `v0.1.0`  
**Purpose**: Pre-lab verification of existing provider implementations to ensure local integration uses exact existing methods, configuration schemas, safety boundaries, and endpoint semantics.

---

## 1. Provider Contract Inventory

### A. `PrometheusMetricsProvider`
- **Module**: `aegis.providers.production.prometheus`
- **Protocol Conformance**: Implements `MetricsProvider` (`query_metric`).
- **Configuration Schema**: `PrometheusConfig` (inherits `HTTPClientConfig`):
  - `base_url`: str (e.g. `http://localhost:9090`)
  - `timeout_seconds`: float (default: `10.0`)
  - `query_timeout_seconds`: float (default: `15.0`)
  - `default_step`: str (default: `"15s"`)
  - `max_retries`: int (default: `3`)
  - `backoff_factor`: float (default: `0.5`)
  - `api_token`: str | None (optional bearer token)
- **Read Operations**:
  - `query_metric(metric_name, start_time, end_time, service_name=None, labels=None) -> list[dict[str, Any]]`
  - Targets endpoint: `GET api/v1/query_range`
  - Normalizes Prometheus Matrix results into standardized dicts containing `metric_name`, `value` (float), `timestamp` (datetime), `service_name`, `labels`, `signal`, `provenance`.
- **Mutation Operations**: None. (Read-only metrics provider).
- **Authentication**: Optional Bearer token or HTTP Basic Auth via `HTTPClientConfig`.
- **Timeout & Retry**: Handled via `ResilientHTTPClient` with bounded exponential backoff (`max_retries=3`).
- **Safety Restrictions**: Validates response structure; raises typed `ProviderInvalidResponseError` on non-dict or failed query status.

---

### B. `LokiLogProvider`
- **Module**: `aegis.providers.production.loki`
- **Protocol Conformance**: Implements `LogProvider` (`query_logs`).
- **Configuration Schema**: `LokiConfig` (inherits `HTTPClientConfig`):
  - `base_url`: str (e.g. `http://localhost:3100`)
  - `default_limit`: int (default: `100`, max: `5000`)
- **Read Operations**:
  - `query_logs(query, start_time, end_time, service_name=None, limit=100) -> list[dict[str, Any]]`
  - Targets endpoint: `GET loki/api/v1/query_range`
  - Query formatting: Generates LogQL stream selector `{service="<service_name>"}` or `{job=~".+"}` and appends regex/filter matcher `|= "<query>"`.
  - Timestamp formatting: Converts standard Python `datetime` timestamps to nanoseconds (`start_ns`, `end_ns`).
  - Normalizes results into standardized dicts containing `service`, `level`, `message`, `timestamp`, `signal`, `provenance`, `metadata`.
- **Mutation Operations**: None.
- **Authentication**: Optional Bearer token / Basic Auth.
- **Safety & Boundary Restrictions**: Decoupled HTTP REST client only. Zero Loki Go code or binaries are vendored. Network client interaction does not trigger AGPLv3 copyleft.

---

### C. `OpenTelemetryTraceProvider`
- **Module**: `aegis.providers.production.opentelemetry`
- **Protocol Conformance**: Implements `TraceProvider` (`query_spans`).
- **Configuration Schema**: `OpenTelemetryConfig` (inherits `HTTPClientConfig`):
  - `base_url`: str (e.g. `http://localhost:16686` for Jaeger HTTP query API or collector)
  - `service_name_override`: str | None
- **Read Operations**:
  - `query_spans(service_name, start_time, end_time, min_duration_ms=None, only_errors=False) -> list[dict[str, Any]]`
  - Targets endpoint: `GET api/traces`
  - Parameter mapping: `start` & `end` in microseconds (`start_us`, `end_us`).
  - Normalizes Jaeger JSON spans into standardized dicts containing `trace_id`, `span_id`, `parent_span_id`, `service`, `span_name`, `duration_ms`, `timestamp`, `is_error`, `error_message`, `attributes`.
- **Mutation Operations**: None.
- **Safety Restrictions**: Pure typed JSON parsing over HTTP; no OTel C++ or Go binaries bundled.

---

### D. `KubernetesProvider`
- **Module**: `aegis.providers.production.kubernetes`
- **Protocol Conformance**: Implements workload status inspection and `execute_action` for `RemediationProvider`.
- **Configuration Schema**: `KubernetesConfig`:
  - `kubeconfig_path`: str | None
  - `context`: str | None
  - `in_cluster`: bool = False
  - `default_namespace`: str = `"default"`
  - `read_only`: bool = True (CRITICAL INVARIANT)
- **Read Operations**:
  - `get_deployment_status(service_name, namespace=None) -> dict[str, Any] | None`
- **Mutation Operations**:
  - `execute_action(action_type, target, parameters, timeout_seconds=60) -> dict[str, Any]`
  - Supported action types:
    - `RemediationActionType.SERVICE_RESTART.value` (`"service_restart"`): Triggers deployment rollout restart.
    - `RemediationActionType.SCALING.value` (`"scaling"`): Adjusts replica count.
- **Safety Invariants**:
  - Rejects mutation immediately if `config.read_only` is `True`.
  - Rejects arbitrary shell execution, `kubectl` subprocesses, or raw string commands.
  - Requires typed action targets and parameters.
