"""Example: AI Coding Agent Integration with AEGIS Framework.

Demonstrates canonical integration pattern:
1. Initialize Aegis from human-readable configuration
2. Create an incident
3. Collect evidence and perform causal reasoning
4. Plan controlled remediation with safety guardrails
"""

import asyncio
from pathlib import Path

from aegis import Aegis
from aegis.incidents import IncidentSeverity


async def main() -> None:
    # 1. Initialize AEGIS from configuration file
    # (If aegis.yaml doesn't exist, we fallback to default in-memory configuration)
    config_path = Path("aegis.yaml")
    if config_path.exists():
        aegis = Aegis.from_config(config_path)
    else:
        # Programmatic in-memory fallback
        from aegis.config import AegisProjectConfig

        aegis = Aegis.from_config(AegisProjectConfig())

    print(f"✓ AEGIS client initialized: {aegis}")

    # 2. Declare an incident
    incident = aegis.create_incident(
        title="Elevated Error Rate on payment-service",
        service_name="payment-service",
        severity=IncidentSeverity.HIGH,
        description="Downstream timeout observed in payment gateway processor.",
    )
    print(f"✓ Incident created: {incident.id} [{incident.severity.value}]")

    # 3. Investigate incident (evidence collection + reasoning)
    reasoning_result = await aegis.investigate(incident)
    print(f"✓ Reasoning complete. Generated {len(reasoning_result.hypotheses)} hypotheses.")
    if reasoning_result.primary_hypothesis:
        print(f"  Primary Hypothesis: {reasoning_result.primary_hypothesis.title}")

    # 4. Propose remediation plan (fail-closed, risk-evaluated)
    plan = aegis.plan_remediation(
        incident_id=incident.id,
        service_name="payment-service",
        reason="Restarting degraded container pool to mitigate resource exhaustion.",
    )
    print(f"✓ Remediation plan generated: {plan.id} (Risk: {plan.risk_level.value})")
    print("✓ AEGIS agent integration demonstration finished successfully.")


if __name__ == "__main__":
    asyncio.run(main())
