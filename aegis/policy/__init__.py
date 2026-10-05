from typing import Any

from pydantic import BaseModel, Field

from aegis.policy.declarative import DataClassification, DeclarativePolicy
from aegis.security import SecurityRiskLevel


class PolicyDecisionResult(BaseModel):
    """Evaluation decision produced by PolicyEngine."""

    allowed: bool
    risk_level: SecurityRiskLevel
    data_classification: DataClassification = DataClassification.INTERNAL
    requires_approval: bool = False
    reason: str
    details: dict[str, Any] = Field(default_factory=dict)


class PolicyEngine:
    """Deterministic policy gate.

    CRITICAL INVARIANT:
    The Policy Engine is strictly deterministic and authoritative.
    LLM reasoning or self-reported claims CANNOT override policy decisions.
    For example: if LLM claims 'risk = LOW', but Policy Engine determines
    the action is HIGH/CRITICAL risk, the Policy Engine wins unconditionally.
    """

    def __init__(self, allowed_models: list[str] | None = None) -> None:
        self.allowed_models = allowed_models or [
            "mock-reasoner-v1",
            "qwen2.5-coder:7b",
            "gpt-4o-mini",
        ]

    def classify_data(self, text: str) -> DataClassification:
        """Deterministically inspects text for sensitive strings."""
        lower = text.lower()
        if any(secret in lower for secret in ("password", "secret_key", "bearer ", "private_key", "authorization:")):
            return DataClassification.SECRET
        if any(pii in lower for pii in ("ssn", "credit_card", "email", "phone_number")):
            return DataClassification.SENSITIVE
        return DataClassification.INTERNAL

    def evaluate_reasoning_request(
        self,
        prompt: str,
        model_name: str,
        provider_name: str,
    ) -> PolicyDecisionResult:
        """Verify whether an AI reasoning invocation is permitted under current policy."""
        classification = self.classify_data(prompt)

        # 1. Block SECRET unredacted credentials immediately
        if classification == DataClassification.SECRET:
            return PolicyDecisionResult(
                allowed=False,
                risk_level=SecurityRiskLevel.CRITICAL,
                data_classification=classification,
                reason="Context contains unredacted credentials or secrets; policy blocks execution.",
            )

        # 2. Model whitelist check
        if model_name not in self.allowed_models:
            return PolicyDecisionResult(
                allowed=False,
                risk_level=SecurityRiskLevel.HIGH,
                data_classification=classification,
                reason=f"Model '{model_name}' is not in authorized model whitelist.",
            )

        return PolicyDecisionResult(
            allowed=True,
            risk_level=SecurityRiskLevel.READ_ONLY,
            data_classification=classification,
            reason="Reasoning request meets read-only criteria and data boundaries.",
        )

    def evaluate_remediation_proposal(
        self,
        risk_level: SecurityRiskLevel,
        has_approval: bool = False,
        approver_count: int = 0,
        author_id: str | None = None,
        approver_id: str | None = None,
    ) -> PolicyDecisionResult:
        """Evaluate if a remediation proposal can execute.

        - CRITICAL: Blocked by default.
        - HIGH: Requires authorized human approval; separation of duties (author != approver).
        - MEDIUM: Requires at least 1 approval.
        - LOW / READ_ONLY: Permitted without prior human signature.
        """
        if risk_level == SecurityRiskLevel.CRITICAL:
            return PolicyDecisionResult(
                allowed=False,
                risk_level=risk_level,
                reason="CRITICAL risk operations are blocked unconditionally by policy.",
            )

        # Separation of duties
        if (
            risk_level in (SecurityRiskLevel.MEDIUM, SecurityRiskLevel.HIGH)
            and has_approval
            and author_id
            and approver_id
            and author_id == approver_id
        ):
            return PolicyDecisionResult(
                allowed=False,
                risk_level=risk_level,
                reason="Separation of duties violation: Remediation author cannot approve their own action.",
            )

        if risk_level in (SecurityRiskLevel.MEDIUM, SecurityRiskLevel.HIGH) and (not has_approval or approver_count < 1):
            return PolicyDecisionResult(
                allowed=False,
                risk_level=risk_level,
                requires_approval=True,
                reason=f"Remediation requires human approval before execution (Risk: {risk_level.value}).",
            )

        return PolicyDecisionResult(
            allowed=True,
            risk_level=risk_level,
            requires_approval=False,
            reason=f"Remediation policy authorized at risk level '{risk_level.value}'.",
        )


__all__ = [
    "DataClassification",
    "DeclarativePolicy",
    "PolicyDecisionResult",
    "PolicyEngine",
]
