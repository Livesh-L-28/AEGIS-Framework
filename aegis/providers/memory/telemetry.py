"""In-memory unified telemetry provider composing metrics, logs, and traces."""

from datetime import datetime
from typing import Any

from aegis.providers.memory.logs import InMemoryLogProvider
from aegis.providers.memory.metrics import InMemoryMetricsProvider
from aegis.providers.memory.traces import InMemoryTraceProvider


class InMemoryTelemetryProvider:
    """Unified in-memory telemetry provider composing metrics, logs, and traces."""

    def __init__(
        self,
        metrics_provider: InMemoryMetricsProvider | None = None,
        log_provider: InMemoryLogProvider | None = None,
        trace_provider: InMemoryTraceProvider | None = None,
    ) -> None:
        self.metrics_provider = metrics_provider or InMemoryMetricsProvider()
        self.log_provider = log_provider or InMemoryLogProvider()
        self.trace_provider = trace_provider or InMemoryTraceProvider()

    async def collect_telemetry(
        self,
        service_name: str,
        start_time: datetime,
        end_time: datetime,
    ) -> dict[str, Any]:
        """Collect unified telemetry bundle without data duplication."""
        metrics = await self.metrics_provider.query_metric(
            metric_name="*",
            start_time=start_time,
            end_time=end_time,
            service_name=service_name,
        )
        logs = await self.log_provider.query_logs(
            query="*",
            start_time=start_time,
            end_time=end_time,
            service_name=service_name,
            limit=1000,
        )
        spans = await self.trace_provider.query_spans(
            service_name=service_name,
            start_time=start_time,
            end_time=end_time,
        )
        return {
            "service_name": service_name,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "metrics": metrics,
            "logs": logs,
            "traces": spans,
        }


__all__ = ["InMemoryTelemetryProvider"]
