"""AEGIS Framework User-Facing Project Configuration System.

Supports parsing and schema validation of `aegis.yaml` with safe
environment-variable substitution, typed provider configurations,
and robust security defaults.
"""

import os
import re
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from aegis.autonomy import AutonomyLevel

# Regular expression matching ${ENV_VAR} or ${ENV_VAR:default}
ENV_VAR_REGEX = re.compile(r"\$\{\s*([A-Za-z_][A-Za-z0-9_]*)(?::([^}]*))?\s*\}")


def substitute_env_vars(raw: str) -> str:
    """Substitute ${VAR} or ${VAR:default} in string from environment safely."""

    def replacer(match: re.Match[str]) -> str:
        var_name = match.group(1)
        default_val = match.group(2) if match.group(2) is not None else ""
        return os.environ.get(var_name, default_val)

    return ENV_VAR_REGEX.sub(replacer, raw)


class ProjectSettings(BaseModel):
    """General project metadata."""

    name: str = Field(default="aegis-project")
    environment: str = Field(default="development")
    service_name: str | None = Field(default=None)


class MetricProviderConfig(BaseModel):
    """Metrics provider section."""

    type: str = Field(default="in_memory")  # "prometheus" | "in_memory"
    endpoint: str | None = Field(default=None)
    step: str = Field(default="15s")
    timeout_seconds: float = Field(default=10.0, ge=0.5, le=120.0)


class LogProviderConfig(BaseModel):
    """Logs provider section."""

    type: str = Field(default="in_memory")  # "loki" | "in_memory"
    endpoint: str | None = Field(default=None)
    limit: int = Field(default=100, ge=1, le=5000)
    timeout_seconds: float = Field(default=10.0, ge=0.5, le=120.0)


class TraceProviderConfig(BaseModel):
    """Traces provider section."""

    type: str = Field(default="in_memory")  # "opentelemetry" | "in_memory"
    endpoint: str | None = Field(default=None)
    timeout_seconds: float = Field(default=10.0, ge=0.5, le=120.0)


class KubernetesProviderConfig(BaseModel):
    """Kubernetes provider section."""

    type: str = Field(default="kubernetes")
    default_namespace: str = Field(default="default")
    read_only: bool = Field(default=True)  # CRITICAL INVARIANT: read_only default is True
    kubeconfig_path: str | None = Field(default=None)


class ProvidersSettings(BaseModel):
    """Configured provider subsystems."""

    metrics: MetricProviderConfig = Field(default_factory=MetricProviderConfig)
    logs: LogProviderConfig = Field(default_factory=LogProviderConfig)
    traces: TraceProviderConfig = Field(default_factory=TraceProviderConfig)
    kubernetes: KubernetesProviderConfig | None = Field(default=None)


class SecuritySettings(BaseModel):
    """Framework security controls."""

    require_approval: bool = Field(default=True)
    fail_closed: bool = Field(default=True)
    allow_unauthorized_models: bool = Field(default=False)


class AutonomySettings(BaseModel):
    """Tiered autonomy controls."""

    level: int = Field(default=1, ge=0, le=3)  # LEVEL_0 to LEVEL_3 only (never 4)


class RemediationSettings(BaseModel):
    """Remediation execution safeguards."""

    dry_run: bool = Field(default=True)
    max_risk: str = Field(default="LOW")


class AegisProjectConfig(BaseModel):
    """Root model for aegis.yaml project configuration."""

    project: ProjectSettings = Field(default_factory=ProjectSettings)
    providers: ProvidersSettings = Field(default_factory=ProvidersSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    autonomy: AutonomySettings = Field(default_factory=AutonomySettings)
    remediation: RemediationSettings = Field(default_factory=RemediationSettings)

    @classmethod
    def from_yaml(cls, content: str) -> "AegisProjectConfig":
        """Parse and validate configuration from YAML string with environment substitution."""
        # 1. Substitute environment variables safely
        substituted = substitute_env_vars(content)
        data = yaml.safe_load(substituted)
        if not isinstance(data, dict):
            raise ValueError("Configuration YAML must define a mapping/dictionary at root.")
        return cls.model_validate(data)

    @classmethod
    def from_file(cls, path: str | Path) -> "AegisProjectConfig":
        """Load and validate configuration from file path."""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Configuration file not found: {p}")
        text = p.read_text(encoding="utf-8")
        return cls.from_yaml(text)

    def to_autonomy_level(self) -> AutonomyLevel:
        """Map numeric autonomy setting to AutonomyLevel enum."""
        mapping = {
            0: AutonomyLevel.LEVEL_0,
            1: AutonomyLevel.LEVEL_1,
            2: AutonomyLevel.LEVEL_2,
            3: AutonomyLevel.LEVEL_3,
        }
        return mapping.get(self.autonomy.level, AutonomyLevel.LEVEL_1)


__all__ = [
    "AegisProjectConfig",
    "AutonomySettings",
    "KubernetesProviderConfig",
    "LogProviderConfig",
    "MetricProviderConfig",
    "ProjectSettings",
    "ProvidersSettings",
    "RemediationSettings",
    "SecuritySettings",
    "TraceProviderConfig",
    "substitute_env_vars",
]
