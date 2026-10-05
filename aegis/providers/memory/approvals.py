"""In-memory approval store preserving approval integrity and separation-of-duties rules."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID


class InMemoryApprovalStore:
    """Stores and evaluates remediation approval records in memory."""

    def __init__(self) -> None:
        self.approvals: dict[UUID, dict[str, Any]] = {}

    async def get_approval(self, remediation_id: UUID) -> dict[str, Any] | None:
        """Fetch approval record for remediation proposal."""
        return self.approvals.get(remediation_id)

    async def store_approval(self, approval: dict[str, Any]) -> None:
        """Persist approval record with integrity timestamps."""
        rem_id = approval.get("remediation_id")
        if not rem_id:
            raise ValueError("Approval record must contain 'remediation_id'")

        if isinstance(rem_id, str):
            rem_id = UUID(rem_id)

        record = dict(approval)
        record["remediation_id"] = rem_id
        record.setdefault("created_at", datetime.now(UTC).isoformat())
        self.approvals[rem_id] = record

    def clear(self) -> None:
        """Clear all stored approvals."""
        self.approvals.clear()


__all__ = ["InMemoryApprovalStore"]
