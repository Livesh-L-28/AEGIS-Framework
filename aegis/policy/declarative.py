"""Declarative policy schema and YAML/JSON policy loader."""

from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from aegis.autonomy import AutonomyLevel
from aegis.remediation import RemediationActionType
from aegis.security import SecurityRiskLevel


class DataClassification(StrEnum):
    """Context sensitivity tier."""

    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    SENSITIVE = "SENSITIVE"
    SECRET = "SECRET"


class DeclarativePolicy(BaseModel):
    """Declarative policy file model with full schema validation."""

    version: str = Field(default="1.0")
    name: str = Field(default="default-policy")
    description: str = Field(default="")

    # Autonomy controls
    autonomy_level: AutonomyLevel = Field(default=AutonomyLevel.LEVEL_1)
    kill_switch_active: bool = Field(default=False)

    # Action boundaries
    allowed_actions: list[RemediationActionType] = Field(
        default_factory=lambda: [
            RemediationActionType.SERVICE_RESTART,
            RemediationActionType.CACHE_INVALIDATION,
            RemediationActionType.SCALING,
        ]
    )

    # Risk thresholds
    max_auto_risk: SecurityRiskLevel = Field(default=SecurityRiskLevel.LOW)
    max_blast_radius_services: int = Field(default=3, ge=1)

    # Approval requirements
    approvals_required_for_risk: list[SecurityRiskLevel] = Field(
        default_factory=lambda: [
            SecurityRiskLevel.MEDIUM,
            SecurityRiskLevel.HIGH,
            SecurityRiskLevel.CRITICAL,
        ]
    )
    enforce_separation_of_duties: bool = Field(default=True)

    # Security & AI models
    allowed_models: list[str] = Field(
        default_factory=lambda: [
            "mock-reasoner-v1",
            "qwen2.5-coder:7b",
            "gpt-4o-mini",
        ]
    )
    blocked_data_classifications: list[DataClassification] = Field(
        default_factory=lambda: [DataClassification.SECRET]
    )

    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_yaml(cls, yaml_content: str) -> "DeclarativePolicy":
        """Parse policy from YAML string."""
        data = yaml.safe_load(yaml_content)
        if not isinstance(data, dict):
            raise ValueError("YAML policy content must be a mapping/dict")
        return cls.model_validate(data)

    @classmethod
    def from_file(cls, path: str | Path) -> "DeclarativePolicy":
        """Load policy from a YAML or JSON file path."""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Policy file not found: {p}")
        text = p.read_text(encoding="utf-8")
        return cls.from_yaml(text)


__all__ = ["DeclarativePolicy"]
