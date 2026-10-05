# AEGIS Framework — Open-Source License, Dependency & Compliance Audit Report

**Date**: 2026-10-04  
**Project**: AEGIS Framework (`aegis-ai`)  
**Repository**: `Livesh-L-28/AEGIS-Framework`  
**Target Release**: Version `0.1.0`  
**License**: Apache License, Version 2.0 (Apache-2.0)  
**Distribution Targets**: GitHub (Public Repository) & PyPI (`aegis-ai` wheel and sdist)  

---

## 1. Executive Summary

This comprehensive audit was performed prior to the public open-source publication of the **AEGIS Framework** on GitHub and PyPI. The audit evaluated all direct source files, dependency trees (direct and transitive), packaging specifications, container base images, CI workflows, security boundaries, and external infrastructure integrations (Prometheus, Loki, Jaeger/OpenTelemetry, Kubernetes, `llmfirewall-core`, and `aireliability`).

The framework's primary license is **Apache License, Version 2.0**. All runtime Python dependencies are governed by permissive open-source licenses (Apache-2.0, MIT, BSD-3-Clause) or file-level copyleft licenses (MPL-2.0 via `certifi`) utilized strictly through dynamic linking without source modification. All infrastructure integrations (Prometheus, Loki, Jaeger, Kubernetes) are architected as decoupled, network-only HTTP/REST client providers; zero third-party backend source code, vendored Go binaries, or proprietary assets are bundled into AEGIS packages.

---

## 2. Final Verdict

| Evaluation Dimension | Status | Classification |
|---|---|---|
| **AEGIS Framework License** | Verified Apache-2.0, standard notice retained | **GREEN** |
| **Direct Runtime Dependencies** | MIT, BSD-3-Clause, Apache-2.0 | **GREEN** |
| **Transitive Runtime Dependencies** | MIT, BSD, PSF-2.0, MPL-2.0 (dynamically linked) | **GREEN** |
| **Prometheus Integration** | Apache-2.0, decoupled HTTP API client | **GREEN** |
| **Loki Integration** | AGPLv3 external service, decoupled HTTP REST client | **YELLOW (Documented & Compliant)** |
| **Jaeger / OpenTelemetry Integration** | Apache-2.0, HTTP/JSON decoupled client | **GREEN** |
| **Kubernetes Integration** | Apache-2.0 client primitives, `read_only=True` default | **GREEN** |
| **`llmfirewall-core` Integration** | Apache-2.0, clean PyPI dependency | **GREEN** |
| **`aireliability` Integration** | Apache-2.0, clean PyPI dependency | **GREEN** |
| **Docker Distribution** | `python:3.12-slim` (DFSG compliant, no root) | **GREEN** |
| **GitHub Actions / CI** | Official actions (`checkout@v4`, `setup-python@v5`) | **GREEN** |
| **Secrets and PII Scan** | Zero active keys, zero personal paths (`/Users/` clean) | **GREEN** |
| **Third-Party Notices** | Fully documented in `THIRD_PARTY_NOTICES.md` | **GREEN** |
| **Software Bill of Materials (SBOM)** | Valid SPDX 2.3 standard SBOM generated (`sbom.spdx.json`) | **GREEN** |

### Overall Readiness: **SAFE TO PUBLISH** (Production-Grade, Fully Compliant)

---

## 3. AEGIS License

- **License File**: Located at [LICENSE](LICENSE), containing the full text of the Apache License, Version 2.0.
- **Copyright Declaration**: `Copyright 2026 AEGIS Framework Contributors`.
- **Packaging Declaration**: `license = "Apache-2.0"` and classifier `License :: OSI Approved :: Apache Software License` in [pyproject.toml](pyproject.toml).
- **README Alignment**: README explicitly specifies Apache-2.0 licensing.
- **Source Code Files**: All modules under `aegis/` are original works. No conflicting proprietary or GPL headers are present.

---

## 4. Direct Dependencies

AEGIS declares 5 direct runtime dependencies in `pyproject.toml`:

| Package | Version Constraint | Type | Upstream License | License Source / URL | Apache-2.0 Compatibility | Risk |
|---|---|---|---|---|---|---|
| `pydantic` | `>=2.7.0` | Direct Runtime | MIT | https://github.com/pydantic/pydantic | Fully Compatible | Low |
| `pyyaml` | `>=6.0.0` | Direct Runtime | MIT | https://github.com/yaml/pyyaml | Fully Compatible | Low |
| `httpx` | `>=0.27.0` | Direct Runtime | BSD-3-Clause | https://github.com/encode/httpx | Fully Compatible | Low |
| `llmfirewall-core` | `>=1.0.0` | Direct Runtime | Apache-2.0 | https://github.com/Livesh-L-28/LLMFirewall | Identical License | Low |
| `aireliability` | `>=0.1.0` | Direct Runtime | Apache-2.0 | https://github.com/Livesh-L-28/AIReliability | Identical License | Low |

All direct runtime dependencies are permissive and grant unrestricted commercial and non-commercial sublicensing, modification, and redistribution rights.

---

## 5. Transitive Dependencies

Evaluating the full dependency closure resolved on Python 3.12:

```text
aegis-ai (Apache-2.0)
 ├── pydantic (MIT)
 │    ├── pydantic-core (MIT)
 │    ├── annotated-types (MIT)
 │    ├── typing-extensions (PSF-2.0)
 │    └── typing-inspection (MIT)
 ├── pyyaml (MIT)
 ├── httpx (BSD-3-Clause)
 │    ├── httpcore (BSD-3-Clause)
 │    │    └── h11 (MIT)
 │    ├── certifi (MPL-2.0)
 │    ├── idna (BSD-3-Clause)
 │    └── anyio (MIT)
 ├── llmfirewall-core (Apache-2.0)
 └── aireliability (Apache-2.0)
```

### Analysis of Non-Permissive or Special Licenses:
- **`certifi` (MPL-2.0)**:
  - Mozilla Public License 2.0 is a file-level copyleft license.
  - *Compliance Rule*: Section 3.2 allows distributing a Larger Work under a different license (e.g. Apache-2.0) as long as the MPL-2.0 source files themselves (if modified) remain under MPL-2.0 and recipients know where to obtain them.
  - *AEGIS Implementation*: AEGIS does not modify, vendor, or bundle `certifi`. It is consumed as an unmodified, dynamically installed package from PyPI. No copyleft obligations are imposed on AEGIS.
- **`typing-extensions` (PSF-2.0)**:
  - Python Software Foundation License version 2 is an OSI-approved permissive license compatible with Apache-2.0.

There are **zero GPL, AGPL, SSPL, or proprietary transitive runtime dependencies**.

---

## 6. Prometheus Audit

- **Provider**: `PrometheusMetricsProvider` ([aegis/providers/production/prometheus.py](aegis/providers/production/prometheus.py))
- **Prometheus Upstream License**: Apache License, Version 2.0.
- **Architectural Analysis**:
  ```text
  AEGIS (Apache-2.0)
    ↓
  PrometheusMetricsProvider (Async HTTP Client)
    ↓ [HTTP PromQL API over wire: /api/v1/query]
  Prometheus Server (External Process)
  ```
- **Code Inclusion**: AEGIS bundles no Prometheus Go code, no Go binaries, and no official client libraries requiring CGO. It uses pure Python `httpx` to send standard PromQL HTTP requests.
- **Verdict**: **GREEN**. Completely compatible with Apache-2.0.

---

## 7. Loki Audit

- **Provider**: `LokiLogProvider` ([aegis/providers/production/loki.py](aegis/providers/production/loki.py))
- **Loki Upstream License**: Grafana Labs transitioned Loki from Apache-2.0 to the **GNU Affero General Public License v3.0 (AGPL-3.0)** effective with v2.0 (and subsequently dual-licensed source code with Grafana licensing models).
- **Audit of AEGIS Implementation**:
  - Does AEGIS copy any Loki Go source code? **No**.
  - Does AEGIS vendor Loki libraries or Go packages? **No**.
  - Does AEGIS distribute Loki binaries inside the Python package or Docker image? **No**.
  - Does AEGIS import any AGPL Python libraries? **No**.
  - How does AEGIS communicate with Loki?
    ```text
    AEGIS (Apache-2.0)
      ↓
    LokiLogProvider (HTTP Client)
      ↓ [HTTP REST API over wire: /loki/api/v1/query_range]
    External Loki Cluster (AGPLv3 Server)
    ```
- **Copyleft Boundary Analysis (Section 13 of AGPLv3)**:
  - The AGPLv3 copyleft trigger ("remote network interaction") applies to users interacting with a modified version of the AGPL-licensed program over a network.
  - AEGIS is an independent client application querying standard, open HTTP endpoints over a TCP socket. Under established open-source legal interpretation (including the Free Software Foundation's FAQ on independent client-server communication), interacting with a network service via a standard documented protocol does not constitute creating a derivative work of the server.
  - AEGIS does **not** link against Loki, does not redistribute Loki, and does not require modifying AEGIS's Apache-2.0 license.
- **Verdict**: **YELLOW (Compliant & Documented)**. The external integration is legally safe and documented in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

---

## 8. Jaeger / OpenTelemetry Audit

- **Provider**: `OpenTelemetryTraceProvider` ([aegis/providers/production/opentelemetry.py](aegis/providers/production/opentelemetry.py))
- **Upstream Licenses**:
  - OpenTelemetry: Apache-2.0
  - Jaeger: Apache-2.0
- **Architectural Analysis**:
  ```text
  AEGIS (Apache-2.0)
    ↓
  OpenTelemetryTraceProvider (Async HTTP Client)
    ↓ [HTTP REST API over wire: /api/traces]
  Jaeger Query Service / OpenTelemetry Collector
  ```
- **Code Inclusion**: AEGIS implements trace query parsing natively using Python typing and `httpx`. No OpenTelemetry Go/C++ binaries are bundled.
- **Verdict**: **GREEN**. Clean and compatible.

---

## 9. Kubernetes Audit

- **Provider**: `KubernetesProvider` ([aegis/providers/production/kubernetes.py](aegis/providers/production/kubernetes.py))
- **Kubernetes Upstream License**: Apache License, Version 2.0.
- **Security & Packaging Boundary**:
  - `read_only=True` is enforced by default on the provider.
  - All operations use typed Python primitives (`WorkloadStatus`, `PodStatus`, `AuditLevel`).
  - AEGIS **does not** execute arbitrary shell commands (`subprocess.Popen(..., shell=True)`), nor does it execute the `kubectl` binary over arbitrary CLI invocations.
  - No Kubernetes manifests, Go code, or container binaries are bundled inside AEGIS.
- **Verdict**: **GREEN**. Fully preserves the required security architecture and licensing terms.

---

## 10. llmfirewall-core Audit

- **Package**: `llmfirewall-core` (Version `1.0.0`)
- **License**: Apache License, Version 2.0 (`License :: OSI Approved :: Apache Software License`).
- **Upstream Repository**: https://github.com/Livesh-L-28/LLMFirewall
- **Distribution Model**: Standard public PyPI package dependency.
- **Source Inclusion**: Not bundled or vendored in `aegis/`. Cleanly imported as a library dependency.
- **Verdict**: **GREEN**. License is identical (Apache-2.0) and fully compatible.

---

## 11. aireliability Audit

- **Package**: `aireliability` (Version `0.1.0`)
- **License**: Apache License, Version 2.0 (`License :: OSI Approved :: Apache Software License`).
- **Upstream Repository**: https://github.com/Livesh-L-28/AIReliability
- **Distribution Model**: Standard public PyPI package dependency.
- **Source Inclusion**: Not bundled or vendored in `aegis/`. Cleanly imported as a library dependency.
- **Verdict**: **GREEN**. License is identical (Apache-2.0) and fully compatible.

---

## 12. Docker Image Audit

- **File**: [Dockerfile](Dockerfile)
- **Base Image**: `FROM python:3.12-slim`
- **Publisher**: Official Docker Community / Python Software Foundation.
- **Underlying OS**: Debian GNU/Linux (Bookworm / slim).
- **Licensing & Redistribution**:
  - Debian packages are governed by the Debian Free Software Guidelines (DFSG) (mostly GPL, MIT, BSD).
  - Redistributing application layers on top of standard official base images without bundling proprietary software complies with standard open-source distribution norms.
  - Container runs as a non-root user (`aegis`, UID 1000).
- **Verdict**: **GREEN**.

---

## 13. GitHub Actions Audit

- **Workflow**: [.github/workflows/ci.yml](.github/workflows/ci.yml)
- **Actions Used**:
  - `actions/checkout@v4` (MIT License, GitHub)
  - `actions/setup-python@v5` (MIT License, GitHub)
- **Execution vs Redistribution**: Actions execute ephemeral runner steps within GitHub's infrastructure and are never packaged or redistributed with AEGIS wheel artifacts.
- **Recommendation**: For strict immutable supply-chain pinning, hash pinning (`actions/checkout@<sha>`) may be adopted before enterprise-grade release. The current semantic version tags (`@v4`, `@v5`) are acceptable for standard public open source.
- **Verdict**: **GREEN**.

---

## 14. Third-Party Source & Vendoring Audit

A complete search of all source files in `aegis/` for foreign copyright statements, license declarations, and code snippets was executed.

- **Copied Source Code**: None detected.
- **Vendored Libraries**: Zero vendored directories or submodules exist in the repository.
- **Classification**: **SAFE**. All files in `aegis/` are original work created for the AEGIS Framework.

---

## 15. Secrets and Personal Information (PII) Audit

A recursive security scan across all repository files (excluding local temporary build artifacts) revealed:
- **Personal Filesystem Paths**: All tracked source files, documentation, workflows, and tests are completely free of hardcoded `/Users/livesh/` machine paths.
- **API Keys / Tokens / Secrets**:
  - Zero active tokens, passwords, private keys, or AWS credentials exist in tracked code.
  - All occurrences of terms like `token`, `secret`, `api_key` in the codebase are security sanitization logic (e.g. `audit.py` redacting sensitive keys), Pydantic model configurations with `repr=False`, or mock strings in tests (e.g., `"secret-12345"`).
- **Repository URLs**: All URLs point to the official public GitHub repository (`https://github.com/Livesh-L-28/AEGIS-Framework`).
- **Verdict**: **GREEN**.

---

## 16. License Compatibility Matrix

| Component | Version | License | Direct/External | Apache-2.0 Compatible? | Action Required |
|---|---|---|---|---|---|
| **AEGIS Framework** | 0.1.0 | Apache-2.0 | Core Project | Yes | Primary license |
| **pydantic** | >=2.7.0 | MIT | Direct Dependency | Yes | Permissive; include notice |
| **pyyaml** | >=6.0.0 | MIT | Direct Dependency | Yes | Permissive; include notice |
| **httpx** | >=0.27.0 | BSD-3-Clause | Direct Dependency | Yes | Permissive; retain attribution |
| **llmfirewall-core** | >=1.0.0 | Apache-2.0 | Direct Dependency | Yes | Compatible; retain attribution |
| **aireliability** | >=0.1.0 | Apache-2.0 | Direct Dependency | Yes | Compatible; retain attribution |
| **pydantic-core** | 2.46.5 | MIT | Transitive | Yes | Dynamically linked |
| **annotated-types** | 0.8.0 | MIT | Transitive | Yes | Dynamically linked |
| **typing-extensions** | 4.16.0 | PSF-2.0 | Transitive | Yes | Dynamically linked |
| **typing-inspection**| 0.4.4 | MIT | Transitive | Yes | Dynamically linked |
| **httpcore** | 1.0.9 | BSD-3-Clause | Transitive | Yes | Dynamically linked |
| **h11** | 0.16.0 | MIT | Transitive | Yes | Dynamically linked |
| **certifi** | 2026.7.22 | MPL-2.0 | Transitive | Yes | Dynamically linked without modification |
| **idna** | 3.20 | BSD-3-Clause | Transitive | Yes | Dynamically linked |
| **anyio** | 4.15.1 | MIT | Transitive | Yes | Dynamically linked |
| **Prometheus** | API | Apache-2.0 | External Network | Yes | Remote HTTP API only |
| **Grafana Loki** | API | AGPL-3.0 | External Network | Yes (Client call) | Documented; zero source bundled |
| **OpenTelemetry / Jaeger** | API | Apache-2.0 | External Network | Yes | Remote HTTP API only |
| **Kubernetes** | API | Apache-2.0 | External Network | Yes | Safe client primitives; read-only default |

---

## 17. Software Bill of Materials (SBOM) Status

- An official Software Bill of Materials has been generated and validated in the **SPDX 2.3** specification standard:
  - File: [sbom.spdx.json](sbom.spdx.json)
  - Data License: `CC0-1.0`
  - Encodes the complete dependency graph, exact package names, versions, license declarations, and download locations.
  - Can be ingested directly by automated vulnerability scanners and enterprise open-source compliance registries (e.g. Snyk, Black Duck, FOSSA, Mend).

---

## 18. Required Changes

1. **Third-Party Notices**: Completed by creating [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
2. **SBOM Artifact**: Completed by generating [sbom.spdx.json](sbom.spdx.json).
3. **External AGPL Clarification**: Completed by formally analyzing and documenting the Loki HTTP integration boundary.

All required compliance items have been implemented.

---

## 19. Optional Improvements

1. **Commit SHA Pinning for GitHub Actions**: Pin `actions/checkout@v4` and `actions/setup-python@v5` to specific 40-character commit SHAs in `.github/workflows/ci.yml` if achieving SLSA level 3 compliance is desired.
2. **Automated License Checker in CI**: Integrate a license compliance check into `.github/workflows/ci.yml` (e.g., verifying that no GPL-only packages enter the transitive dependency tree in future PRs).

---

## 20. Remaining Legal Uncertainty & Legal Disclaimer

*Notice*: This report constitutes an **engineering, architecture, and packaging compliance review** conducted by software packaging and security engineering specialists. It does not constitute formal legal counsel.

- **Loki & AGPLv3**: Grafana Labs' transition of Loki to AGPLv3 is well established. While the consensus among open-source legal scholars (and the FSF) is that communicating over standard HTTP REST APIs without linking does not make the client a derivative work or subject it to copyleft, organizations with strict internal "zero AGPL anywhere in the stack" procurement policies should note that the external Loki server runs under AGPLv3 even though AEGIS itself is Apache-2.0.
- **Trademarks**: Names such as "Kubernetes", "Prometheus", "Loki", "Grafana", and "Jaeger" are trademarks of their respective foundations (CNCF/Linux Foundation, Grafana Labs). AEGIS uses these names purely in a descriptive, interoperability sense under fair use principles.

---

## 21. Final GitHub Readiness: **GREEN (Ready)**

- Clean Git status (excluding audit artifacts).
- CI workflow passing on Python 3.12 and 3.13.
- Full documentation suite with architecture guidelines and provider guides.
- No confidential credentials, personal tokens, or local workstation paths.

---

## 22. Final PyPI Readiness: **GREEN (Ready)**

- Built with modern PEP 517/621 backend (`hatchling`).
- Wheel (`aegis_ai-0.1.0-py3-none-any.whl`) and Source Distribution (`aegis_ai-0.1.0.tar.gz`) build without warnings.
- Clean installation test in an isolated virtual environment (`/tmp/aegis-license-audit`) succeeds without errors.
- CLI entrypoint `aegis doctor` and `aegis version` execute cleanly upon installation.
