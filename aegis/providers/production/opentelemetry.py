"""Production-grade OpenTelemetry / Jaeger trace provider implementing TraceProvider."""

from datetime import datetime
from typing import Any

from aegis.providers.config import OpenTelemetryConfig
from aegis.providers.errors import ProviderInvalidResponseError
from aegis.providers.http import ResilientHTTPClient


class OpenTelemetryTraceProvider:
    """Production trace provider querying OpenTelemetry / Jaeger HTTP API."""

    def __init__(self, config: OpenTelemetryConfig) -> None:
        self.config = config
        self.client = ResilientHTTPClient(config, provider_name="opentelemetry")

    async def query_spans(
        self,
        service_name: str,
        start_time: datetime,
        end_time: datetime,
        min_duration_ms: float | None = None,
        only_errors: bool = False,
    ) -> list[dict[str, Any]]:
        """Query distributed trace spans and normalize to framework trace domain."""
        # Convert microseconds for Jaeger / OTel HTTP query API
        start_us = int(start_time.timestamp() * 1_000_000)
        end_us = int(end_time.timestamp() * 1_000_000)

        params: dict[str, Any] = {
            "service": service_name,
            "start": str(start_us),
            "end": str(end_us),
            "limit": "100",
        }
        if min_duration_ms is not None:
            params["minDuration"] = f"{int(min_duration_ms * 1000)}us"
        if only_errors:
            params["tags"] = '{"error":"true"}'

        data = await self.client.get_json("api/traces", params=params)

        if not isinstance(data, dict):
            raise ProviderInvalidResponseError(
                "Invalid response format from OpenTelemetry endpoint",
                provider_name="opentelemetry",
            )

        spans_out: list[dict[str, Any]] = []
        for trace in data.get("data", []):
            trace_id = trace.get("traceID", "unknown")
            for span in trace.get("spans", []):
                span_id = span.get("spanID", "")
                operation_name = span.get("operationName", "operation")
                start_time_us = span.get("startTime", start_us)
                duration_us = span.get("duration", 0)
                duration_ms = duration_us / 1000.0

                tags = {t.get("key"): t.get("value") for t in span.get("tags", [])}
                is_error = bool(tags.get("error", False))
                error_msg = tags.get("message") or tags.get("error.message")

                # References for parent relationship
                parent_id = None
                for ref in span.get("references", []):
                    if ref.get("refType") == "CHILD_OF":
                        parent_id = ref.get("spanID")
                        break

                spans_out.append(
                    {
                        "trace_id": trace_id,
                        "span_id": span_id,
                        "parent_span_id": parent_id,
                        "service": service_name,
                        "service_name": service_name,
                        "span_name": operation_name,
                        "duration_ms": duration_ms,
                        "timestamp": datetime.fromtimestamp(start_time_us / 1_000_000, tz=start_time.tzinfo),
                        "is_error": is_error,
                        "error_message": error_msg,
                        "attributes": tags,
                    }
                )

        return spans_out


__all__ = ["OpenTelemetryTraceProvider"]
