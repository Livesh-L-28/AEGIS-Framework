# Prometheus Metrics Provider

```python
from aegis.providers import PrometheusConfig
from aegis.providers.production import PrometheusMetricsProvider

config = PrometheusConfig(base_url="http://prometheus:9090")
provider = PrometheusMetricsProvider(config)
```
