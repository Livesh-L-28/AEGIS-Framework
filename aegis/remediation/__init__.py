"""AEGIS Framework Remediation — Planning, risk assessment, and validation definitions."""

import hashlib
import json
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from aegis.security import SecurityRiskLevel


class RemediationActionType(StrEnum):
    """Categorization of infrastructure remediation action."""

    SERVICE_RESTART = "SERVICE_RESTART"
    CONFIG_CHANGE = "CONFIG_CHANGE"
    CACHE_INVALIDATION = "CACHE_INVALIDATION"
    SCALING = "SCALING"
    CODE_PATCH = "CODE_PATCH"
    DEPLOYMENT = "DEPLOYMENT"
    ROLLBACK = "ROLLBACK"


class BlastRadius(BaseModel):
    """Report on affected blast radius."""

    affected_services: list[str] = Field(default_factory=list)
    affected_dependencies: list[str] = Field(default_factory=list)
    estimated_impact: str = ""


class ValidationPlan(BaseModel):
    """Declarative criteria for verifying action success."""

    metric_checks: list[dict[str, Any]] = Field(default_factory=list)
    health_endpoint: str | None = None
    window_seconds: int = 30
    success_criteria: str = ""


class RollbackPlan(BaseModel):
    """Declarative rollback definition in case of validation failure."""

    action_type: RemediationActionType
    target: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int = 60


class RemediationAction(BaseModel):
    """Atomic step in a remediation plan."""

    id: UUID = Field(default_factory=uuid4)
    action_type: RemediationActionType
    target: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    risk_level: SecurityRiskLevel = SecurityRiskLevel.LOW
    timeout_seconds: int = 60
    preconditions: list[str] = Field(default_factory=list)


class RemediationPlan(BaseModel):
    """Complete remediation plan with risk assessment, blast radius, validation, and rollback."""

    id: UUID = Field(default_factory=uuid4)
    incident_id: UUID = Field(default_factory=uuid4)
    service_name: str
    title: str
    description: str
    risk_level: SecurityRiskLevel = SecurityRiskLevel.MEDIUM
    actions: list[RemediationAction] = Field(default_factory=list)
    blast_radius: BlastRadius = Field(default_factory=BlastRadius)
    preconditions: list[str] = Field(default_factory=list)
    validation_plan: ValidationPlan = Field(default_factory=ValidationPlan)
    rollback_plan: RollbackPlan = Field(
        default_factory=lambda: RollbackPlan(
            action_type=RemediationActionType.ROLLBACK,
            target="",
        )
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def compute_plan_hash(self) -> str:
        """Deterministic fingerprint of actions and rollback strategy."""
        payload = {
            "incident_id": str(self.incident_id),
            "service_name": self.service_name,
            "actions": [
                {
                    "type": a.action_type.value,
                    "target": a.target,
                    "params": a.parameters,
                    "risk": a.risk_level.value,
                }
                for a in self.actions
            ],
            "rollback": self.rollback_plan.model_dump(),
        }
        encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


class RemediationPlanner:
    """Plans remediation proposals and determines objective risk."""

    def calculate_risk(
        self,
        actions: list[RemediationAction],
        blast_radius: BlastRadius,
    ) -> SecurityRiskLevel:
        """Calculates deterministic composite risk for proposed actions."""
        if any(a.action_type == RemediationActionType.CODE_PATCH for a in actions):
            return SecurityRiskLevel.HIGH

        if len(blast_radius.affected_services) > 3:
            return SecurityRiskLevel.HIGH

        if any(a.action_type in (RemediationActionType.ROLLBACK, RemediationActionType.DEPLOYMENT) for a in actions):
            return SecurityRiskLevel.MEDIUM

        if any(a.action_type == RemediationActionType.SERVICE_RESTART for a in actions):
            return SecurityRiskLevel.LOW

        return SecurityRiskLevel.LOW

    def plan_restart(
        self,
        incident_id: UUID,
        service_name: str,
        reason: str,
    ) -> RemediationPlan:
        """Construct safe service restart plan."""
        action = RemediationAction(
            action_type=RemediationActionType.SERVICE_RESTART,
            target=service_name,
            parameters={"graceful": True},
            risk_level=SecurityRiskLevel.LOW,
        )
        blast = BlastRadius(
            affected_services=[service_name],
            estimated_impact=f"Brief availability restart dip on {service_name}",
        )
        validation = ValidationPlan(
            health_endpoint=f"http://{service_name}/healthz",
            success_criteria="HTTP 200 within 30 seconds",
        )
        rollback = RollbackPlan(
            action_type=RemediationActionType.ROLLBACK,
            target=service_name,
        )

        plan = RemediationPlan(
            incident_id=incident_id,
            service_name=service_name,
            title=f"Graceful restart of {service_name}",
            description=reason,
            risk_level=SecurityRiskLevel.LOW,
            actions=[action],
            blast_radius=blast,
            validation_plan=validation,
            rollback_plan=rollback,
        )
        return plan


__all__ = [
    "BlastRadius",
    "RemediationAction",
    "RemediationActionType",
    "RemediationPlan",
    "RemediationPlanner",
    "RollbackPlan",
    "ValidationPlan",
]
