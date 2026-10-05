"""Example: Autonomy tiers and safety gate enforcement."""

from aegis import Aegis, AutonomyLevel, SecurityRiskLevel
from aegis.remediation import BlastRadius, RemediationAction, RemediationActionType, RemediationPlan


def main() -> None:
    aegis = Aegis()

    low_risk_plan = RemediationPlan(
        service_name="frontend-cache",
        title="Flush frontend cache",
        description="Routine cache invalidation",
        risk_level=SecurityRiskLevel.LOW,
        actions=[
            RemediationAction(
                action_type=RemediationActionType.CACHE_INVALIDATION,
                target="frontend-cache",
                risk_level=SecurityRiskLevel.LOW,
            )
        ],
        blast_radius=BlastRadius(affected_services=["frontend-cache"]),
    )

    medium_risk_plan = RemediationPlan(
        service_name="payment-service",
        title="Rollback deployment",
        description="Version rollback",
        risk_level=SecurityRiskLevel.MEDIUM,
        actions=[
            RemediationAction(
                action_type=RemediationActionType.ROLLBACK,
                target="payment-service",
                risk_level=SecurityRiskLevel.MEDIUM,
            )
        ],
        blast_radius=BlastRadius(affected_services=["payment-service", "order-service"]),
    )

    # LEVEL_0: Observe only
    aegis.autonomy_engine.level = AutonomyLevel.LEVEL_0
    dec0 = aegis.autonomy_engine.evaluate_plan(low_risk_plan)
    print(f"LEVEL_0 with low-risk plan: decision={dec0.decision.value}, allowed={dec0.allowed}")

    # LEVEL_1: Recommend only
    aegis.autonomy_engine.level = AutonomyLevel.LEVEL_1
    dec1 = aegis.autonomy_engine.evaluate_plan(low_risk_plan)
    print(f"LEVEL_1 with low-risk plan: decision={dec1.decision.value}, allowed={dec1.allowed}")

    # LEVEL_2: Auto-execute LOW risk only
    aegis.autonomy_engine.level = AutonomyLevel.LEVEL_2
    dec2_low = aegis.autonomy_engine.evaluate_plan(low_risk_plan)
    dec2_med = aegis.autonomy_engine.evaluate_plan(medium_risk_plan)
    print(f"LEVEL_2 with low-risk plan: decision={dec2_low.decision.value}, allowed={dec2_low.allowed}")
    print(f"LEVEL_2 with medium-risk plan: decision={dec2_med.decision.value}, allowed={dec2_med.allowed}")

    # Emergency Kill Switch
    aegis.autonomy_engine.activate_kill_switch()
    dec_kill = aegis.autonomy_engine.evaluate_plan(low_risk_plan)
    print(f"Kill switch active: decision={dec_kill.decision.value}, allowed={dec_kill.allowed}")


if __name__ == "__main__":
    main()
