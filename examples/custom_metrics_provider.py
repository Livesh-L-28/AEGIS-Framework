"""Example: Building and injecting a custom Prometheus metrics provider."""

import asyncio
from datetime import UTC, datetime
from typing import Any

from aegis import Aegis, AutonomyLevel
from aegis.providers import MetricsProvider


class CustomDatadogStyleMetricsProvider:
    """Demonstrates how an organization implements a custom MetricsProvider."""

    def __init__(self) -> None:
        self._series: list[dict[str, Any]] = []

    def seed_metric(self, name: str, value: float, ts: datetime, service: str) -> None:
        self._series.append({
            "metric_name": name,
            "value": value,
            "timestamp": ts,
            "service_name": service,
            "signal": name,
            "provenance": "datadog:api",
        })

    async def query_metric(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        service_name: str | None = None,
        labels: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        # Protocol-compliant query method
        return [
            s for s in self._series
            if (metric_name == "*" or s["metric_name"] == metric_name)
            and (service_name is None or s["service_name"] == service_name)
        ]


# Verify Protocol conformance
assert isinstance(CustomDatadogStyleMetricsProvider(), MetricsProvider)


async def main() -> None:
    now = datetime.now(UTC)
    custom_metrics = CustomDatadogStyleMetricsProvider()
    custom_metrics.seed_metric(
        "http_request_duration_seconds",
        1.85,
        now,
        "payment-gateway",
    )

    aegis = Aegis(metrics_provider=custom_metrics, autonomy_level=AutonomyLevel.LEVEL_1)
    inc = aegis.create_incident(
        title="High payment latency",
        service_name="payment-gateway",
    )

    res = await aegis.investigate(inc)
    print(f"Investigation completed with custom metrics provider: {res.summary}")


if __name__ == "__main__":
    asyncio.run(main())
