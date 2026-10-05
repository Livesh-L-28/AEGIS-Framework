"""In-memory structured log provider for deterministic testing and local execution."""

from datetime import datetime
from typing import Any


class InMemoryLogProvider:
    """Stores and queries structured log records in memory."""

    def __init__(self, initial_logs: list[dict[str, Any]] | None = None) -> None:
        self.logs: list[dict[str, Any]] = list(initial_logs or [])

    def record_log(
        self,
        service: str,
        level: str,
        message: str,
        timestamp: datetime,
        request_id: str | None = None,
        signal: str | None = None,
        provenance: str = "memory:logs",
        **metadata: Any,
    ) -> None:
        """Record a structured log entry into memory."""
        self.logs.append(
            {
                "service": service,
                "service_name": service,
                "level": level.upper(),
                "message": message,
                "timestamp": timestamp,
                "request_id": request_id,
                "signal": signal or f"log:{level.lower()}",
                "provenance": provenance,
                "metadata": metadata,
            }
        )

    async def query_logs(
        self,
        query: str,
        start_time: datetime,
        end_time: datetime,
        service_name: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Query log entries within a time window."""
        results: list[dict[str, Any]] = []
        q_lower = query.lower()

        # Parse simple query terms like 'level:error'
        target_level = None
        if "level:" in q_lower:
            parts = q_lower.split("level:")
            target_level = parts[1].split()[0].upper()

        for entry in self.logs:
            # Service filter
            entry_service = entry.get("service") or entry.get("service_name")
            if service_name is not None and entry_service is not None and entry_service != service_name:
                continue

            # Time filter
            ts = entry.get("timestamp")
            if isinstance(ts, datetime):
                if ts.tzinfo is not None and start_time.tzinfo is None:
                    ts_cmp = ts.replace(tzinfo=None)
                elif ts.tzinfo is None and start_time.tzinfo is not None:
                    ts_cmp = ts.replace(tzinfo=start_time.tzinfo)
                else:
                    ts_cmp = ts
                if ts_cmp < start_time or ts_cmp > end_time:
                    continue

            # Query filter
            if target_level and entry.get("level") != target_level:
                continue
            elif not target_level and query != "*":
                msg = str(entry.get("message", "")).lower()
                sig = str(entry.get("signal", "")).lower()
                if q_lower not in msg and q_lower not in sig:
                    continue

            results.append(dict(entry))
            if len(results) >= limit:
                break

        return results


__all__ = ["InMemoryLogProvider"]
