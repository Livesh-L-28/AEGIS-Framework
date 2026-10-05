# OpenTelemetry Trace Provider

```python
from aegis.providers import OpenTelemetryConfig
from aegis.providers.production import OpenTelemetryTraceProvider

config = OpenTelemetryConfig(base_url="http://jaeger:16686")
provider = OpenTelemetryTraceProvider(config)
```
