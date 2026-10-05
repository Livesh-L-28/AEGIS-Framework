"""Example: Remediation planning with explicit human approval workflow."""

import asyncio
from datetime import UTC, datetime
from uuid import uuid4

from aegis import Aegis, SecurityRiskLevel
from aegis.providers.memory import InMemoryApprovalStore, InMemoryRemediationProvider


async def main() -> None:
    approvals = InMemoryApprovalStore()
    remediation = InMemoryRemediationProvider()
    remediation.set_service_state("order-service", {"status": "DEGRADED", "instances": 1})

    aegis = Aegis(approval_store=approvals)
    inc_id = uuid4()

    # 1. Propose remediation
    plan = aegis.plan_remediation(incident_id=inc_id, service_name="order-service", reason="Thread exhaustion")
    print(f"Proposed Plan: {plan.title} (Calculated Risk: {plan.risk_level.value})")

    # 2. Policy evaluation before approval
    policy_res = aegis.policy_engine.evaluate_remediation_proposal(
        risk_level=SecurityRiskLevel.MEDIUM,
        has_approval=False,
    )
    print(f"Policy evaluation before human sign-off: allowed={policy_res.allowed}, requires_approval={policy_res.requires_approval}")

    # 3. SRE records signed approval
    await approvals.store_approval({
        "remediation_id": plan.id,
        "author_id": "ai-engine",
        "approver_id": "sre-lead-bob",
        "decision": "APPROVED",
        "timestamp": datetime.now(UTC).isoformat(),
    })

    # 4. Policy evaluation after approval
    policy_after = aegis.policy_engine.evaluate_remediation_proposal(
        risk_level=SecurityRiskLevel.MEDIUM,
        has_approval=True,
        approver_count=1,
        author_id="ai-engine",
        approver_id="sre-lead-bob",
    )
    print(f"Policy evaluation after human sign-off: allowed={policy_after.allowed}")

    # 5. Execute verified action
    if policy_after.allowed:
        exec_res = await remediation.execute_action(
            action_type=plan.actions[0].action_type.value,
            target=plan.actions[0].target,
            parameters=plan.actions[0].parameters,
        )
        print(f"Remediation execution completed: {exec_res['output']}")


if __name__ == "__main__":
    asyncio.run(main())
