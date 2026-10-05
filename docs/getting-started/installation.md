# Installation

## Prerequisites
- Python 3.12 or 3.13
- pip, uv, or poetry

## Standard Installation
Install the core framework from PyPI:

```bash
pip install aegis-ai
```

## Optional Provider Extras
Install optional extras according to your infrastructure requirements:

```bash
# Observability providers (Prometheus, Loki, OpenTelemetry HTTP clients)
pip install aegis-ai[observability]

# All supported integrations
pip install aegis-ai[all]
```

## Verifying Installation
Verify your installation using the framework CLI:

```bash
aegis version
aegis doctor
```
