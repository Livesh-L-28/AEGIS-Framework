# AGENTS.md — Instructions for AI Coding Agents

## Purpose

AEGIS Framework (`aegis-ai` on PyPI) provides AI-assisted reliability engineering, multimodal evidence collection, causal reasoning, fail-closed policy enforcement, and controlled autonomous remediation.

## Canonical Instructions Before Modifying or Integrating

Before generating integration code or modifying AEGIS:
1. **Read**: [`docs/ai/integration.md`](file:///Users/livesh/AEGIS-Framework/docs/ai/integration.md)
2. **Review Quickstart**: [`docs/ai/quickstart.md`](file:///Users/livesh/AEGIS-Framework/docs/ai/quickstart.md)
3. **Inspect Capabilities**: [`docs/ai/capabilities.yaml`](file:///Users/livesh/AEGIS-Framework/docs/ai/capabilities.yaml)

## Installation

```bash
pip install aegis-ai
```

## Supported Entry Points

```python
from aegis import Aegis

# Always instantiate using configuration or explicit dependency injection
aegis = Aegis.from_config("aegis.yaml")
```

Do NOT invent non-existent APIs or methods. Inspect `aegis/__init__.py` and `aegis/core/__init__.py`.

## Safety Constraints (Non-Negotiable)

Never:
- Bypass AEGIS policy evaluation or approval gates.
- Disable fail-closed behavior to force remediations to succeed.
- Enable or implement Autonomy Level 4 (only Levels 0–3 are valid).
- Execute arbitrary shell strings for remediation (use typed actions only).
- Directly mutate Kubernetes without going through `KubernetesProvider` policies.
- Expose credentials, tokens, or plaintext secrets in configuration or logs.
- Modify the external reference platform at `/Users/livesh/AEGIS AI`.
