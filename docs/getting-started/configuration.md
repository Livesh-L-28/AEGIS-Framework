# Configuration Guide

AEGIS Framework is configured via explicit objects or environment variables.

## Environment Variables Template (.env.example)

```bash
# Observability Providers
PROMETHEUS_URL=http://localhost:9090
LOKI_URL=http://localhost:3100
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318

# Security & Tokens
AEGIS_API_TOKEN=
GITHUB_TOKEN=
GITHUB_WEBHOOK_SECRET=

# Autonomy Tier
AEGIS_AUTONOMY_LEVEL=LEVEL_1_RECOMMEND
```

## Typed Configuration

```python
from aegis.providers import PrometheusConfig, LokiConfig, OpenTelemetryConfig

prom_config = PrometheusConfig(
    base_url="http://prometheus:9090",
    timeout_seconds=15.0,
    verify_ssl=True,
)
```
