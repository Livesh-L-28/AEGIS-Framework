# Grafana Loki Log Provider

```python
from aegis.providers import LokiConfig
from aegis.providers.production import LokiLogProvider

config = LokiConfig(base_url="http://loki:3100")
provider = LokiLogProvider(config)
```
