# Changelog

All notable changes to the AEGIS Framework project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-10-05

### Added
- **Production Provider Adapters**:
  - `PrometheusMetricsProvider`: Resilient PromQL metric queries with retry, bounded exponential backoff, and safe error parsing.
  - `OpenTelemetryTraceProvider`: Distributed trace queries and span tree normalization for OpenTelemetry / Jaeger.
  - `LokiLogProvider`: LogQL stream queries with time-window filtering and structured log parsing.
  - `GitHubDeploymentProvider` & `GitHubWebhookHandler`: Release correlation and HMAC SHA-256 signature verification.
  - `KubernetesProvider`: Typed workload status inspection and controlled mutations (no arbitrary shell).
- **In-Memory Concrete Providers**: Complete suite of 11 in-memory providers (`InMemoryMetricsProvider`, `InMemoryLogProvider`, `InMemoryTraceProvider`, `InMemoryTelemetryProvider`, `InMemoryDeploymentProvider`, `InMemoryModelProvider`, `InMemoryVectorIndexProvider`, `InMemoryApprovalStore`, `InMemoryStorageProvider`, `InMemoryRemediationProvider`).
- **Framework CLI (`aegis`)**:
  - `aegis version`: Reports framework, llmfirewall-core, and aireliability versions.
  - `aegis doctor`: Comprehensive diagnostics for runtime, firewall, reliability, and security invariants.
  - `aegis init`: Scaffolds project policies and `.env.example`.
  - `aegis policy validate`: Validates declarative YAML/JSON policies.
  - `aegis evaluate`: Runs benchmark suites with JSON output support.
- **Declarative Policy Engine**: Pydantic-backed declarative YAML/JSON policy format with strict validation.
- **Framework Observability & Audit**: Lightweight in-memory `TelemetrySink` and append-only `InMemoryAuditLogger`.
- **Benchmark Suite**: Golden dataset benchmark runner (`aegis.evaluation.Benchmark`).
- **Production Examples**: Comprehensive examples for Prometheus, OpenTelemetry, Kubernetes, custom providers, and autonomy policies.
- **Developer Experience & Onboarding Layer**:
  - `aegis init --example`: Zero-infrastructure starter scaffolding and runnable standalone demo.
  - `aegis demo`: Full 7-step simulated terminal walkthrough of incident investigation, reasoning, policy, remediation, and recovery.
  - `Aegis.from_config("aegis.yaml")`: Human-readable configuration system supporting typed provider mapping and safe environment-variable interpolation (`${VAR:default}`).
  - `aegis doctor`: Comprehensive diagnostics inspecting configuration schema, runtime, fail-closed security invariants, and provider connectivity.
- **AI-Agent Native Discoverability Layer**:
  - Canonical agent integration contract (`docs/ai/integration.md`) with explicit "When to Use", "When NOT to Use", and non-negotiable safety rules.
  - Machine-readable capability manifest (`docs/ai/capabilities.yaml`) declaring supported providers and security bounds.
  - Root agent instructions (`AGENTS.md`), Claude Code (`CLAUDE.md`), and Cursor (`.cursorrules`) integration pointers.
  - Vibe-coding scenario (`docs/ai/vibe-coding-integration.md`) demonstrating framework reuse over custom SRE bot implementation.

### Changed
- Integrated native upstream `aireliability 0.1.0` and `llmfirewall-core 1.0.0` with fail-closed invariants.
- Expanded `pyproject.toml` with optional dependency extras (`[observability]`, `[all]`, `[dev]`) and CLI console script.
- Hardened Prometheus, Loki, OpenTelemetry, and Kubernetes production providers with live local infrastructure validation.
