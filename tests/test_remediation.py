"""Unit tests for Remediation planning, risk scoring, and hashing."""

from uuid import uuid4

from aegis.remediation import (
    BlastRadius,
    RemediationAction,
    RemediationActionType,
    RemediationPlanner,
)
from aegis.security import SecurityRiskLevel


def test_remediation_risk_calculation() -> None:
    """RemediationPlanner calculates deterministic risk levels."""
    planner = RemediationPlanner()

    action_restart = RemediationAction(
        action_type=RemediationActionType.SERVICE_RESTART,
        target="cart-service",
    )
    blast_small = BlastRadius(affected_services=["cart-service"])
    risk = planner.calculate_risk([action_restart], blast_small)
    assert risk == SecurityRiskLevel.LOW

    action_patch = RemediationAction(
        action_type=RemediationActionType.CODE_PATCH,
        target="cart-service",
    )
    risk_patch = planner.calculate_risk([action_patch], blast_small)
    assert risk_patch == SecurityRiskLevel.HIGH


def test_remediation_plan_generation_and_hash() -> None:
    """Remediation plan generates deterministic verification hash."""
    planner = RemediationPlanner()
    incident_id = uuid4()
    plan = planner.plan_restart(
        incident_id=incident_id,
        service_name="payment-service",
        reason="Recover from thread starvation",
    )
    assert plan.risk_level == SecurityRiskLevel.LOW
    assert len(plan.actions) == 1
    assert plan.actions[0].action_type == RemediationActionType.SERVICE_RESTART

    plan_hash = plan.compute_plan_hash()
    assert len(plan_hash) == 64
    assert plan.compute_plan_hash() == plan_hash
