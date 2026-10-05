"""AEGIS Framework Incidents — Domain models, severities, sources, and state machines."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class IncidentSeverity(StrEnum):
    """Incident severity classification."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IncidentStatus(StrEnum):
    """Incident lifecycle states."""

    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    IDENTIFIED = "IDENTIFIED"
    MITIGATING = "MITIGATING"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class IncidentSource(StrEnum):
    """Source that initiated or reported the incident."""

    MANUAL = "MANUAL"
    ALERT = "ALERT"
    ANOMALY_DETECTOR = "ANOMALY_DETECTOR"
    TELEMETRY = "TELEMETRY"
    SIMULATION = "SIMULATION"
    SLO_BREACH = "SLO_BREACH"


class Incident(BaseModel):
    """Framework-native Incident domain entity.

    Pure in-memory domain model independent of SQLAlchemy, PostgreSQL, or FastAPI.
    """

    id: UUID = Field(default_factory=uuid4)
    organization_id: UUID = Field(default_factory=uuid4)
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default="")
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    status: IncidentStatus = IncidentStatus.OPEN
    source: IncidentSource = IncidentSource.MANUAL
    service_name: str | None = None
    detected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    resolved_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def mark_investigating(self) -> None:
        """Transition incident state to INVESTIGATING."""
        self.status = IncidentStatus.INVESTIGATING

    def mark_resolved(self, resolved_at: datetime | None = None) -> None:
        """Transition incident state to RESOLVED."""
        self.status = IncidentStatus.RESOLVED
        self.resolved_at = resolved_at or datetime.now(UTC)


__all__ = [
    "Incident",
    "IncidentSeverity",
    "IncidentSource",
    "IncidentStatus",
]
