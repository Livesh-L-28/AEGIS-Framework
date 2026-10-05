"""Unit tests for Policy engine and deterministic decision gates."""

from aegis.policy import DataClassification, PolicyEngine
from aegis.security import SecurityRiskLevel


def test_policy_data_classification() -> None:
    """Policy engine classifies data sensitivity tiers deterministically."""
    engine = PolicyEngine()
    assert engine.classify_data("Regular status update") == DataClassification.INTERNAL
    assert engine.classify_data("Contains password=secret123") == DataClassification.SECRET
    assert engine.classify_data("User email: test@example.com") == DataClassification.SENSITIVE


def test_policy_blocks_unredacted_secrets() -> None:
    """Prompt containing secrets is blocked unconditionally."""
    engine = PolicyEngine()
    res = engine.evaluate_reasoning_request(
        prompt="Execute query with Bearer abcdef123456",
        model_name="mock-reasoner-v1",
        provider_name="mock",
    )
    assert res.allowed is False
    assert res.risk_level == SecurityRiskLevel.CRITICAL
    assert "credentials or secrets" in res.reason


def test_policy_blocks_unauthorized_models() -> None:
    """Prompt using unapproved model is blocked."""
    engine = PolicyEngine()
    res = engine.evaluate_reasoning_request(
        prompt="Analyze telemetry",
        model_name="unapproved-external-model",
        provider_name="unknown",
    )
    assert res.allowed is False
    assert "not in authorized model whitelist" in res.reason


def test_policy_separation_of_duties_enforcement() -> None:
    """Author cannot approve their own high-risk remediation."""
    engine = PolicyEngine()
    res = engine.evaluate_remediation_proposal(
        risk_level=SecurityRiskLevel.HIGH,
        has_approval=True,
        approver_count=1,
        author_id="user_admin",
        approver_id="user_admin",
    )
    assert res.allowed is False
    assert "Separation of duties violation" in res.reason
