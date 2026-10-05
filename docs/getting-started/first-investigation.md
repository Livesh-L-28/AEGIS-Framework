# First Investigation Walkthrough

Follow this guide to run an automated investigation step-by-step.

```python
import asyncio
from datetime import UTC, datetime, timedelta
from aegis import Aegis, IncidentSeverity
from aegis.providers.memory import InMemoryMetricsProvider, InMemoryLogProvider

async def main():
    now = datetime.now(UTC)
    metrics = InMemoryMetricsProvider()
    metrics.record_metric("http_request_duration_seconds", 1.8, now, "order-service")

    logs = InMemoryLogProvider()
    logs.record_log("order-service", "ERROR", "database query timeout", now)

    aegis = Aegis(metrics_provider=metrics, log_provider=logs)
    incident = aegis.create_incident(
        title="Order DB timeout spike",
        severity=IncidentSeverity.HIGH,
        service_name="order-service",
    )

    result = await aegis.investigate(incident)
    print(f"Diagnosed cause: {result.summary}")

if __name__ == "__main__":
    asyncio.run(main())
```
