"""Unit tests for Autonomy tiers, safety invariants, and kill switches."""


from aegis.autonomy import AutonomyDecision, AutonomyEngine, AutonomyLevel
from aegis.remediation import RemediationPlan
from aegis.security import SecurityRiskLevel


def test_autonomy_level_0_observe_only() -> None:
    """LEVEL_0 strictly enforces RECOMMEND_ONLY."""
    engine = AutonomyEngine(level=AutonomyLevel.LEVEL_0)
    plan = RemediationPlan(
        service_name="order-service",
        title="Restart order-service",
        description="Restart test",
        risk_level=SecurityRiskLevel.LOW,
    )
    result = engine.evaluate_plan(plan)
    assert result.decision == AutonomyDecision.RECOMMEND_ONLY
    assert result.allowed is False


def test_autonomy_level_1_requires_approval() -> None:
    """LEVEL_1 mandates approval even for low-risk actions."""
    engine = AutonomyEngine(level=AutonomyLevel.LEVEL_1)
    plan = RemediationPlan(
        service_name="order-service",
        title="Restart order-service",
        description="Restart test",
        risk_level=SecurityRiskLevel.LOW,
    )
    result = engine.evaluate_plan(plan)
    assert result.decision == AutonomyDecision.REQUIRE_APPROVAL
    assert result.allowed is False


def test_autonomy_level_2_executes_low_risk_only() -> None:
    """LEVEL_2 auto-executes LOW risk, but blocks MEDIUM/HIGH risk."""
    engine = AutonomyEngine(level=AutonomyLevel.LEVEL_2)
    plan_low = RemediationPlan(
        service_name="order-service",
        title="Restart order-service",
        description="Restart test",
        risk_level=SecurityRiskLevel.LOW,
    )
    res_low = engine.evaluate_plan(plan_low)
    assert res_low.decision == AutonomyDecision.EXECUTE
    assert res_low.allowed is True

    plan_high = RemediationPlan(
        service_name="order-service",
        title="Patch order-service code",
        description="Patch test",
        risk_level=SecurityRiskLevel.HIGH,
    )
    res_high = engine.evaluate_plan(plan_high)
    assert res_high.decision == AutonomyDecision.REQUIRE_APPROVAL
    assert res_high.allowed is False


def test_emergency_kill_switch_blocks_all_execution() -> None:
    """When kill switch is engaged, all autonomous execution is halted."""
    engine = AutonomyEngine(level=AutonomyLevel.LEVEL_2)
    engine.activate_kill_switch()

    plan_low = RemediationPlan(
        service_name="order-service",
        title="Restart order-service",
        description="Restart test",
        risk_level=SecurityRiskLevel.LOW,
    )
    result = engine.evaluate_plan(plan_low)
    assert result.decision == AutonomyDecision.DENY
    assert result.allowed is False
    assert "kill switch is ACTIVE" in result.reason
