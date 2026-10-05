"""Framework-neutral append-only audit logger interface and in-memory store."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class AuditCategory(StrEnum):
    """Categorization of audit events."""

    SECURITY = "SECURITY"
    POLICY = "POLICY"
    REASONING = "REASONING"
    AUTONOMY = "AUTONOMY"
    REMEDIATION = "REMEDIATION"
    PROVIDER = "PROVIDER"
    EVALUATION = "EVALUATION"


class AuditEvent(BaseModel):
    """Structured immutable audit record."""

    id: UUID = Field(default_factory=uuid4)
    category: AuditCategory
    action: str
    actor: str = "system"
    target: str | None = None
    outcome: str = "SUCCESS"  # "SUCCESS" | "DENIED" | "BLOCKED" | "FAILED"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    details: dict[str, Any] = Field(default_factory=dict)


class InMemoryAuditLogger:
    """In-memory append-only audit event log."""

    def __init__(self) -> None:
        self._records: list[AuditEvent] = []

    def record(
        self,
        category: AuditCategory,
        action: str,
        actor: str = "system",
        target: str | None = None,
        outcome: str = "SUCCESS",
        details: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """Record an immutable audit event."""
        # Sanitize details for security
        safe_details: dict[str, Any] = {}
        if details:
            for k, v in details.items():
                if any(sec in k.lower() for sec in ("token", "password", "secret", "key")):
                    safe_details[k] = "[REDACTED]"
                else:
                    safe_details[k] = v

        event = AuditEvent(
            category=category,
            action=action,
            actor=actor,
            target=target,
            outcome=outcome,
            details=safe_details,
        )
        self._records.append(event)
        return event

    def get_events(
        self,
        category: AuditCategory | None = None,
        outcome: str | None = None,
    ) -> list[AuditEvent]:
        """Query audit records."""
        results = self._records
        if category:
            results = [e for e in results if e.category == category]
        if outcome:
            results = [e for e in results if e.outcome == outcome]
        return list(results)

    def count(self) -> int:
        """Count recorded audit entries."""
        return len(self._records)


__all__ = ["AuditCategory", "AuditEvent", "InMemoryAuditLogger"]
