# AEGIS Framework

> Open-source autonomous reliability engineering framework for AI-powered incident investigation, reasoning, remediation, and reliability automation.

[![CI](https://github.com/Livesh-L-28/AEGIS-Framework/actions/workflows/ci.yml/badge.svg)](https://github.com/Livesh-L-28/AEGIS-Framework/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://python.org)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://img.shields.io/badge/mypy-checked-blue.svg)](https://mypy-lang.org/)

---

> 🚀 **Status: v0.1.0 Public Release**  
> AEGIS Framework is a production-grade, open-source autonomous reliability engineering framework providing modular provider interfaces, deterministic safety guardrails, AI reasoning engines, and automated remediation.

---

---

## What is AEGIS?
AEGIS is an open-source, AI-native reliability and controlled autonomous remediation framework for production systems (`aegis-ai` on PyPI). It correlates multimodal observability signals (metrics, logs, traces), performs causal failure reasoning, evaluates fail-closed safety policies, and executes approval-gated remediation.

## Why Use AEGIS?
- **Stop Reinventing SRE Bots**: Standardize incident triage, hypothesis generation, and blast-radius assessment.
- **Fail-Closed Safety**: Built-in LLM firewalls (`llmfirewall-core`), strict policy gates, and bounded autonomy budgets (`LEVEL_0` to `LEVEL_3`).
- **Production Observability**: Native support for Prometheus, Grafana Loki, OpenTelemetry, and Kubernetes.
- **Zero Hallucinated Actions**: Typed, deterministic remediation actions with pre-execution safety checks and post-remediation recovery validation.

## Installation

```bash
pip install aegis-ai
```

---

## Consumption Paths

### 🧑‍💻 Path 1: Human Developers
Initialize and test autonomous reliability locally in 60 seconds with zero external infrastructure:
```bash
aegis init --example
aegis doctor
aegis demo
```

### 🤖 Path 2: AI Coding Agents (Claude Code, Cursor, Codex, Copilot)
AI coding agents can discover, configure, and safely integrate AEGIS without inventing parallel reliability subsystems:
- **Canonical Agent Guide**: [`docs/ai/integration.md`](docs/ai/integration.md)
- **Agent Rules & Invariants**: [`AGENTS.md`](AGENTS.md)
- **Machine-Readable Manifest**: [`docs/ai/capabilities.yaml`](docs/ai/capabilities.yaml)
- **AI Agent Quickstart**: [`docs/ai/quickstart.md`](docs/ai/quickstart.md)

---

## Relationship to AEGIS AI

| Component | Role | Description |
|---|---|---|
| **AEGIS Framework** | **Reusable Library** | The modular, lightweight, open-source Python framework (`pip install aegis-ai`) providing foundational abstractions, evidence models, reasoning interfaces, security guardrails, and autonomy boundaries. |
| **AEGIS AI** | **Reference Platform** | The enterprise flagship application providing full end-to-end production deployment, databases, web UI, vector search, and integrated microservices. |

```text
AEGIS Framework
    =
Reusable framework

AEGIS AI
    =
Full reference platform built around the same reliability architecture
```

---

## Architecture Overview

```text
Application / Client Workflows
              │
              ▼
       AEGIS Framework
              │
  ┌───────────┼───────────┬───────────┐
  ▼           ▼           ▼           ▼
Incident   Evidence   AI Reasoning   AI Security
Management Engineering (Hypotheses)  (Fail-Closed)
  │           │           │           │
  └───────────┼───────────┴───────────┘
              │
  ┌───────────┼───────────┬───────────┐
  ▼           ▼           ▼           ▼
Reliability Policy     Autonomy    Remediation
(SLO/Budgets) (Gates)  (Levels 0-3)(Verified)
              │
              ▼
          Evaluation
       (Golden/Release)
              │
              ▼
          Providers
 (LLM / Telemetry / Vector)
```

---

## Core Capabilities (Roadmap)

- **Incident Lifecycle Management**: Structured representations of incidents, phases, status, and impact.
- **Multimodal Evidence Engineering**: Ingestion, temporal correlation, and normalization across metrics, logs, and distributed traces.
- **Root Cause & Causal Reasoning**: Structured hypothesis generation, causal DAGs, and validation loops.
- **Fail-Closed AI Security**: Prompt injection defense, LLM firewalls, deterministic boundary validations, and strict RBAC.
- **Tiered Autonomy**: Strictly bounded execution loops (`LEVEL_0` observation to `LEVEL_3` autonomous actions) with hard budgets.
- **Deterministic Policy & Approval**: Non-bypassable human approval gates, change freeze locks, and kill switches.
- **Verified Remediation**: Dry-run capabilities, safe action execution, rollback strategies, and deployment verification.
- **Continuous Evaluation**: Golden datasets, adversarial evaluation, and strict release gates.

---

## Installation

```bash
# Clone the repository
git clone https://github.com/Livesh-L-28/AEGIS-Framework.git
cd AEGIS-Framework

# Install in editable mode
pip install -e .
```

---

## Quickstart & Developer Experience

AEGIS provides an out-of-the-box CLI to scaffold, validate, and simulate autonomous incident engineering in seconds without requiring external infrastructure:

```bash
# 1. Initialize a new AEGIS project (or generate a standalone in-memory template)
aegis init --example

# 2. Run comprehensive framework, configuration, and security diagnostics
aegis doctor

# 3. Simulate the complete 7-step autonomous reliability lifecycle locally
aegis demo
```

### Python API Integration

```python
from aegis import Aegis

# Initialize directly from human-readable configuration with env var interpolation
aegis = Aegis.from_config("aegis.yaml")

# Run autonomous lifecycle
print(f"AEGIS Framework active: {aegis.config.project.name} (Autonomy Level {aegis.config.autonomy.level})")
```

---

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run linters and type checkers
ruff check .
mypy aegis

# Run tests
pytest
```

---

## Contributing

We welcome community contributions! Please review [CONTRIBUTING.md](CONTRIBUTING.md) and our [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before submitting pull requests.

---

## Security

Security is foundational to AEGIS. For vulnerability reporting guidelines and our fail-closed security architecture, see [SECURITY.md](SECURITY.md).

---

## License

AEGIS Framework is licensed under the [Apache License, Version 2.0](LICENSE).
