"""In-memory metrics provider for deterministic testing and local execution."""

from datetime import datetime
from typing import Any


class InMemoryMetricsProvider:
    """Stores and queries deterministic metric samples in memory."""

    def __init__(self, initial_metrics: list[dict[str, Any]] | None = None) -> None:
        self.metrics: list[dict[str, Any]] = list(initial_metrics or [])

    def record_metric(
        self,
        metric_name: str,
        value: float,
        timestamp: datetime,
        service_name: str | None = None,
        labels: dict[str, str] | None = None,
        signal: str | None = None,
        provenance: str = "memory:metrics",
    ) -> None:
        """Record a metric point into memory."""
        self.metrics.append(
            {
                "metric_name": metric_name,
                "value": value,
                "timestamp": timestamp,
                "service_name": service_name,
                "labels": labels or {},
                "signal": signal or metric_name,
                "provenance": provenance,
            }
        )

    async def query_metric(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        service_name: str | None = None,
        labels: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        """Query time series data points matching criteria."""
        results: list[dict[str, Any]] = []
        for m in self.metrics:
            # Check metric_name match (or wildcard "*")
            if metric_name != "*" and m.get("metric_name") != metric_name:
                continue

            # Check timestamp bounds if available
            ts = m.get("timestamp")
            if isinstance(ts, datetime):
                # Ensure comparable timezone-awareness
                if ts.tzinfo is not None and start_time.tzinfo is None:
                    # Compare if naive/aware mismatch
                    ts_cmp = ts.replace(tzinfo=None)
                elif ts.tzinfo is None and start_time.tzinfo is not None:
                    ts_cmp = ts.replace(tzinfo=start_time.tzinfo)
                else:
                    ts_cmp = ts
                if ts_cmp < start_time or ts_cmp > end_time:
                    continue

            # Check service_name if specified
            if service_name is not None and m.get("service_name") is not None and m.get("service_name") != service_name:
                continue

            # Check labels if specified
            if labels:
                item_labels = m.get("labels", {})
                if not all(item_labels.get(k) == v for k, v in labels.items()):
                    continue

            results.append(dict(m))

        return results


__all__ = ["InMemoryMetricsProvider"]
