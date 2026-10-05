"""In-memory distributed trace provider for deterministic testing and local execution."""

from datetime import datetime
from typing import Any
from uuid import uuid4


class InMemoryTraceProvider:
    """Stores and queries distributed trace spans in memory."""

    def __init__(self, initial_spans: list[dict[str, Any]] | None = None) -> None:
        self.spans: list[dict[str, Any]] = list(initial_spans or [])

    def record_span(
        self,
        service: str,
        name: str,
        duration_ms: float,
        timestamp: datetime,
        trace_id: str | None = None,
        span_id: str | None = None,
        parent_span_id: str | None = None,
        is_error: bool = False,
        error_message: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Record a span with parent/child relationship and timing."""
        span_data = {
            "trace_id": trace_id or f"trace-{uuid4().hex[:8]}",
            "span_id": span_id or f"span-{uuid4().hex[:8]}",
            "parent_span_id": parent_span_id,
            "service": service,
            "service_name": service,
            "span_name": name,
            "duration_ms": duration_ms,
            "timestamp": timestamp,
            "is_error": is_error,
            "error_message": error_message,
            "attributes": attributes or {},
        }
        self.spans.append(span_data)
        return span_data

    async def query_spans(
        self,
        service_name: str,
        start_time: datetime,
        end_time: datetime,
        min_duration_ms: float | None = None,
        only_errors: bool = False,
    ) -> list[dict[str, Any]]:
        """Query distributed trace spans."""
        results: list[dict[str, Any]] = []

        for span in self.spans:
            # Service filter
            svc = span.get("service") or span.get("service_name")
            if service_name != "*" and svc != service_name:
                continue

            # Time filter
            ts = span.get("timestamp")
            if isinstance(ts, datetime):
                if ts.tzinfo is not None and start_time.tzinfo is None:
                    ts_cmp = ts.replace(tzinfo=None)
                elif ts.tzinfo is None and start_time.tzinfo is not None:
                    ts_cmp = ts.replace(tzinfo=start_time.tzinfo)
                else:
                    ts_cmp = ts
                if ts_cmp < start_time or ts_cmp > end_time:
                    continue

            # Duration filter
            if min_duration_ms is not None and span.get("duration_ms", 0.0) < min_duration_ms:
                continue

            # Error filter
            if only_errors and not span.get("is_error", False):
                continue

            results.append(dict(span))

        return results


__all__ = ["InMemoryTraceProvider"]
