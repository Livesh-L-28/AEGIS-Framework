"""AEGIS Framework Autonomy — Tiered autonomy levels, budgets, and safety controls."""

from enum import StrEnum

from pydantic import BaseModel

from aegis.remediation import RemediationPlan
from aegis.security import SecurityRiskLevel


class AutonomyLevel(StrEnum):
    """Explicit bounded autonomy tiers."""

    LEVEL_0 = "LEVEL_0_OBSERVE_ONLY"
    LEVEL_1 = "LEVEL_1_RECOMMEND"
    LEVEL_2 = "LEVEL_2_AUTO_EXECUTE_LOW_RISK"
    LEVEL_3 = "LEVEL_3_AUTO_EXECUTE_APPROVED_CLASSES"
    # LEVEL_4 is deliberately omitted / disabled by architecture design


class AutonomyDecision(StrEnum):
    """Action decisions produced by AutonomyEngine."""

    EXECUTE = "EXECUTE"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    RECOMMEND_ONLY = "RECOMMEND_ONLY"
    DENY = "DENY"


class AutonomyBudget(BaseModel):
    """Strict execution budget constraints."""

    max_iterations: int = 10
    max_tool_calls: int = 25
    max_duration_seconds: int = 300
    max_cost_usd: float = 2.0


class AutonomyDecisionResult(BaseModel):
    """Outcome of autonomy gate evaluation."""

    decision: AutonomyDecision
    reason: str
    autonomy_level: AutonomyLevel
    allowed: bool


class AutonomyEngine:
    """Governs automated execution boundaries.

    CRITICAL ARCHITECTURAL SAFETY INVARIANTS:
    - LEVEL_4 (fully unrestricted autonomy) is PERMANENTLY DISABLED.
    - If emergency kill switch is engaged, all autonomous actions are DENIED.
    - HIGH and CRITICAL risk operations always require approval or are DENIED.
    """

    def __init__(
        self,
        level: AutonomyLevel = AutonomyLevel.LEVEL_1,
        budget: AutonomyBudget | None = None,
    ) -> None:
        self.level = level
        self.budget = budget or AutonomyBudget()
        self.kill_switch_active = False

    def activate_kill_switch(self) -> None:
        """Immediately halts all autonomous execution."""
        self.kill_switch_active = True

    def deactivate_kill_switch(self) -> None:
        """Deactivates kill switch."""
        self.kill_switch_active = False

    def evaluate_plan(
        self,
        plan: RemediationPlan,
    ) -> AutonomyDecisionResult:
        """Evaluate whether a proposed plan can be automatically executed under current tier."""
        if self.kill_switch_active:
            return AutonomyDecisionResult(
                decision=AutonomyDecision.DENY,
                reason="Emergency stop kill switch is ACTIVE. Auto-execution blocked.",
                autonomy_level=self.level,
                allowed=False,
            )

        if self.level == AutonomyLevel.LEVEL_0:
            return AutonomyDecisionResult(
                decision=AutonomyDecision.RECOMMEND_ONLY,
                reason="Autonomy is set to LEVEL_0 (Observe only). Auto-execution disabled.",
                autonomy_level=self.level,
                allowed=False,
            )

        if self.level == AutonomyLevel.LEVEL_1:
            return AutonomyDecisionResult(
                decision=AutonomyDecision.REQUIRE_APPROVAL,
                reason="LEVEL_1 (Recommend) requires human review and signoff.",
                autonomy_level=self.level,
                allowed=False,
            )

        # LEVEL_2: Only LOW risk actions may auto-execute
        if self.level == AutonomyLevel.LEVEL_2:
            if plan.risk_level in (SecurityRiskLevel.READ_ONLY, SecurityRiskLevel.LOW):
                return AutonomyDecisionResult(
                    decision=AutonomyDecision.EXECUTE,
                    reason="Plan meets LOW risk requirements for LEVEL_2 auto-execution.",
                    autonomy_level=self.level,
                    allowed=True,
                )
            return AutonomyDecisionResult(
                decision=AutonomyDecision.REQUIRE_APPROVAL,
                reason=f"Plan risk '{plan.risk_level.value}' exceeds LEVEL_2 LOW threshold; requires approval.",
                autonomy_level=self.level,
                allowed=False,
            )

        # LEVEL_3: MEDIUM risk allowed if blast radius is single service
        if self.level == AutonomyLevel.LEVEL_3:
            if plan.risk_level in (SecurityRiskLevel.READ_ONLY, SecurityRiskLevel.LOW):
                return AutonomyDecisionResult(
                    decision=AutonomyDecision.EXECUTE,
                    reason="Low risk action authorized under LEVEL_3.",
                    autonomy_level=self.level,
                    allowed=True,
                )
            if plan.risk_level == SecurityRiskLevel.MEDIUM and len(plan.blast_radius.affected_services) <= 1:
                return AutonomyDecisionResult(
                    decision=AutonomyDecision.EXECUTE,
                    reason="Medium risk bounded action approved under LEVEL_3.",
                    autonomy_level=self.level,
                    allowed=True,
                )
            return AutonomyDecisionResult(
                decision=AutonomyDecision.REQUIRE_APPROVAL,
                reason="Action risk or blast radius exceeds LEVEL_3 policy; human sign-off mandatory.",
                autonomy_level=self.level,
                allowed=False,
            )

        # Fallback deny
        return AutonomyDecisionResult(
            decision=AutonomyDecision.DENY,
            reason="Unknown or unsupported autonomy state.",
            autonomy_level=self.level,
            allowed=False,
        )


__all__ = [
    "AutonomyBudget",
    "AutonomyDecision",
    "AutonomyDecisionResult",
    "AutonomyEngine",
    "AutonomyLevel",
]
