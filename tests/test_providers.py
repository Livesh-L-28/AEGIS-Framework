"""Unit tests for Provider interfaces and custom mock injection."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest

from aegis.providers import (
    ApprovalStore,
    MetricsProvider,
)


class MockMetricsProvider:
    async def query_metric(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        service_name: str | None = None,
        labels: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        return [{"signal": metric_name, "value": 42.0, "timestamp": datetime.now(UTC)}]


class MockApprovalStore:
    def __init__(self) -> None:
        self.approvals: dict[UUID, dict[str, Any]] = {}

    async def get_approval(self, remediation_id: UUID) -> dict[str, Any] | None:
        return self.approvals.get(remediation_id)

    async def store_approval(self, approval: dict[str, Any]) -> None:
        self.approvals[approval["remediation_id"]] = approval


def test_provider_protocol_conformance() -> None:
    """Ensure mock implementations conform to runtime protocols."""
    metrics_p = MockMetricsProvider()
    assert isinstance(metrics_p, MetricsProvider)

    approval_store = MockApprovalStore()
    assert isinstance(approval_store, ApprovalStore)


@pytest.mark.asyncio
async def test_provider_execution() -> None:
    """Verify provider methods function asynchronously."""
    metrics_p = MockMetricsProvider()
    now = datetime.now(UTC)
    result = await metrics_p.query_metric("cpu_usage", now, now, service_name="cart-service")
    assert len(result) == 1
    assert result[0]["value"] == 42.0

    approval_store = MockApprovalStore()
    rem_id = uuid4()
    await approval_store.store_approval({"remediation_id": rem_id, "approved": True})
    fetched = await approval_store.get_approval(rem_id)
    assert fetched is not None
    assert fetched["approved"] is True
