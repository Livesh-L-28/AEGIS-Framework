"""Structured framework observability and telemetry event emission without mandatory external dependencies."""

import contextlib
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class FrameworkEvent(BaseModel):
    """Normalized internal telemetry and lifecycle event."""

    event_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    payload: dict[str, Any] = Field(default_factory=dict)
    service_name: str | None = None
    incident_id: str | None = None


class TelemetrySink:
    """Dispatches framework lifecycle events to registered hooks/callbacks."""

    def __init__(self) -> None:
        self._handlers: list[Callable[[FrameworkEvent], None]] = []
        self._recorded_events: list[FrameworkEvent] = []

    def register_handler(self, handler: Callable[[FrameworkEvent], None]) -> None:
        """Register a subscriber callback for telemetry events."""
        self._handlers.append(handler)

    def emit(
        self,
        event_name: str,
        service_name: str | None = None,
        incident_id: str | None = None,
        **payload: Any,
    ) -> FrameworkEvent:
        """Emit a structured event safely stripping sensitive keys."""
        safe_payload = {}
        for k, v in payload.items():
            k_lower = k.lower()
            if any(secret in k_lower for secret in ("token", "password", "key", "secret", "auth")):
                safe_payload[k] = "[REDACTED]"
            else:
                safe_payload[k] = v

        event = FrameworkEvent(
            event_name=event_name,
            service_name=service_name,
            incident_id=incident_id,
            payload=safe_payload,
        )
        self._recorded_events.append(event)

        for handler in self._handlers:
            with contextlib.suppress(Exception):
                handler(event)

        return event

    def get_events(self, event_name: str | None = None) -> list[FrameworkEvent]:
        """Fetch recorded events, optionally filtered by event name."""
        if event_name:
            return [e for e in self._recorded_events if e.event_name == event_name]
        return list(self._recorded_events)

    def clear(self) -> None:
        """Clear recorded events."""
        self._recorded_events.clear()


# Global default telemetry sink
telemetry_sink = TelemetrySink()

__all__ = ["FrameworkEvent", "TelemetrySink", "telemetry_sink"]
