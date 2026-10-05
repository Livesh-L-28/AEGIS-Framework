# Third-Party Software Notices and Information

This project, **AEGIS Framework** (`aegis-ai`), is licensed under the **Apache License, Version 2.0**.
See [LICENSE](LICENSE) for the full license text.

AEGIS integrates with and depends upon various open-source third-party software components.
This document provides notice of those dependencies, their licenses, how AEGIS interacts with them, and attribution requirements.

---

## 1. Direct Python Runtime Dependencies

The following open-source Python libraries are installed as direct dependencies of `aegis-ai`:

| Component | Version Constraint | License | Project URL | Distribution / Integration |
|---|---|---|---|---|
| **pydantic** | `>=2.7.0` | MIT License | https://github.com/pydantic/pydantic | Dynamic library link (PyPI dependency); schemas & validation. |
| **pyyaml** | `>=6.0.0` | MIT License | https://github.com/yaml/pyyaml | Dynamic library link (PyPI dependency); policy & config parsing. |
| **httpx** | `>=0.27.0` | BSD-3-Clause | https://github.com/encode/httpx | Dynamic library link (PyPI dependency); asynchronous HTTP provider client. |
| **llmfirewall-core** | `>=1.0.0` | Apache-2.0 | https://github.com/Livesh-L-28/LLMFirewall | Dynamic library link (PyPI dependency); AI prompt & output safety enforcement. |
| **aireliability** | `>=0.1.0` | Apache-2.0 | https://github.com/Livesh-L-28/AIReliability | Dynamic library link (PyPI dependency); agent reliability bounds & metrics. |

All direct runtime dependencies are distributed under permissive open-source licenses (MIT, BSD-3-Clause, Apache-2.0) that are fully compatible with distributing AEGIS under Apache-2.0.

---

## 2. Transitive Python Dependencies

When installed from PyPI, the following transitive dependencies may be resolved:

| Component | License | Origin / Role | Apache-2.0 Compatibility |
|---|---|---|---|
| **annotated-types** | MIT | Dependency of `pydantic` | Compatible |
| **pydantic_core** | MIT | Compiled core of `pydantic` | Compatible |
| **typing_extensions** | PSF-2.0 | Type hinting backport | Compatible |
| **typing-inspection** | MIT | Runtime type introspection | Compatible |
| **httpcore** | BSD-3-Clause | Dependency of `httpx` | Compatible |
| **h11** | MIT | HTTP/1.1 protocol parser for `httpcore` | Compatible |
| **certifi** | MPL-2.0 | Root CA bundle for TLS verification | Compatible (file-level copyleft; linked dynamically without modification) |
| **idna** | BSD-3-Clause | International domain name validation | Compatible |
| **anyio** | MIT | Asynchronous concurrency abstraction | Compatible |

*Note on MPL-2.0 (`certifi`):* Under Section 3.1 and 3.2 of the Mozilla Public License 2.0, unmodified library distribution or dynamic linkage with larger works under Apache-2.0 is fully permissible. AEGIS does not modify or bundle `certifi` source files.

---

## 3. External Infrastructure & Service Integrations

AEGIS features built-in production provider adapters that communicate over network protocols (HTTP/LogQL/PromQL/OTLP/gRPC/REST) with external infrastructure. **None of these external systems have their source code bundled, vendored, or distributed inside the AEGIS repository or Python wheel.**

### Prometheus
- **Software**: Prometheus Monitoring System
- **License**: Apache License, Version 2.0
- **Official Source**: https://github.com/prometheus/prometheus
- **Integration**: AEGIS communicates with external Prometheus deployments via `PrometheusMetricsProvider` over the Prometheus HTTP PromQL REST API (`/api/v1/query`, `/api/v1/query_range`).
- **Bundling**: None. AEGIS contains zero Prometheus source code or binaries.

### Grafana Loki
- **Software**: Grafana Loki (Log Aggregation System)
- **License**: GNU Affero General Public License v3.0 (AGPL-3.0) / Grafana Labs Source Code (post-v2.0)
- **Official Source**: https://github.com/grafana/loki
- **Integration**: AEGIS communicates with external Loki instances via `LokiLogProvider` over the Loki HTTP LogQL REST API (`/loki/api/v1/query_range`).
- **Bundling**: None. AEGIS contains zero Loki source code, zero Loki Go binaries, and imports no Loki client code. Communication is exclusively remote HTTP API client-to-server.
- **Legal Scope**: Network interaction with an independent AGPLv3 service via standard HTTP APIs without bundling or derivative compilation does not trigger AGPL copyleft obligations on the AEGIS Apache-2.0 client code under established open-source legal consensus.

### OpenTelemetry / Jaeger
- **Software**: OpenTelemetry Project & Jaeger Tracing
- **License**: Apache License, Version 2.0
- **Official Source**: https://github.com/open-telemetry / https://github.com/jaegertracing/jaeger
- **Integration**: AEGIS communicates with OpenTelemetry Collector or Jaeger endpoints via `OpenTelemetryTraceProvider` using HTTP/JSON query APIs.
- **Bundling**: None. AEGIS contains zero OpenTelemetry or Jaeger binaries.

### Kubernetes
- **Software**: Kubernetes Container Orchestrator
- **License**: Apache License, Version 2.0
- **Official Source**: https://github.com/kubernetes/kubernetes
- **Integration**: AEGIS interacts with Kubernetes via `KubernetesProvider` using typed REST / JSON primitives (`read_only=True` by default). AEGIS executes no arbitrary shell `kubectl` binaries.
- **Bundling**: None. Zero Kubernetes source code, manifests, or binaries are bundled into AEGIS.

### GitHub
- **Software**: GitHub REST API & Webhooks
- **License**: Proprietary Web Service / API specifications Open Source
- **Official Source**: https://docs.github.com/en/rest
- **Integration**: Handled via standard HMAC-SHA256 signature verification in `GitHubWebhookHandler` and HTTP requests in `GitHubDeploymentProvider`.

---

## 4. Container Images

The official container images for AEGIS are based on the following base image:

| Image | Publisher | License | Role |
|---|---|---|---|
| `python:3.12-slim` | Python Software Foundation / Debian GNU/Linux Project | PSF License / Debian Free Software Guidelines (DFSG) | Container runtime base |

Debian GNU/Linux redistributes packages under various DFSG-compliant licenses. Standard usage of `python:3.12-slim` complies with container distribution guidelines. AEGIS images contain only the AEGIS Python package and its declared dependencies.

---

## 5. Development and Build Tools

The following tools are used during development, testing, linting, and package building only and are **not** distributed with runtime releases:

- **hatchling**: MIT License (Build backend)
- **pytest**: MIT License (Testing framework)
- **pytest-asyncio**: Apache-2.0 (Asyncio test plugin)
- **pytest-cov**: MIT License (Test coverage reporter)
- **ruff**: MIT License / Rust (Linter and formatter)
- **mypy**: MIT License (Static type analysis)
- **build**: MIT License (PEP 517 build frontend)
- **actions/checkout**, **actions/setup-python**: MIT License (GitHub Actions workflows)

---

## 6. Notice of Original Authorship

Unless otherwise noted, all source code in the `aegis` package is original work authored by the AEGIS Framework Contributors and published under the Apache License, Version 2.0.
