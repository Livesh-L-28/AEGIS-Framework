"""Tests for user-facing configuration system and Aegis.from_config factory."""

import os
from pathlib import Path

from aegis import Aegis, AutonomyLevel
from aegis.config import AegisProjectConfig, substitute_env_vars


def test_substitute_env_vars():
    """Verify environment variable substitution with defaults."""
    os.environ["TEST_AEGIS_HOST"] = "metrics.internal"
    raw = "endpoint: http://${TEST_AEGIS_HOST}:9090/${MISSING_PATH:v1}"
    res = substitute_env_vars(raw)
    assert res == "endpoint: http://metrics.internal:9090/v1"


def test_project_config_defaults():
    """Verify clean defaults for development and safety."""
    cfg = AegisProjectConfig()
    assert cfg.project.name == "aegis-project"
    assert cfg.providers.metrics.type == "in_memory"
    assert cfg.security.require_approval is True
    assert cfg.security.fail_closed is True
    assert cfg.remediation.dry_run is True
    assert cfg.to_autonomy_level() == AutonomyLevel.LEVEL_1


def test_project_config_from_yaml():
    """Verify parsing from YAML string."""
    yaml_text = """
project:
  name: test-app
  environment: production

providers:
  metrics:
    type: prometheus
    endpoint: http://localhost:9090
    step: 30s
  kubernetes:
    type: kubernetes
    default_namespace: prod
    read_only: true

security:
  require_approval: true

autonomy:
  level: 2
"""
    cfg = AegisProjectConfig.from_yaml(yaml_text)
    assert cfg.project.name == "test-app"
    assert cfg.providers.metrics.type == "prometheus"
    assert cfg.providers.metrics.step == "30s"
    assert cfg.providers.kubernetes is not None
    assert cfg.providers.kubernetes.read_only is True
    assert cfg.to_autonomy_level() == AutonomyLevel.LEVEL_2


def test_aegis_from_config_in_memory(tmp_path: Path):
    """Verify Aegis.from_config creates fully wired Aegis instance from file."""
    cfg_file = tmp_path / "aegis.yaml"
    cfg_file.write_text("""
project:
  name: local-test

providers:
  metrics:
    type: in_memory
  logs:
    type: in_memory
  traces:
    type: in_memory

autonomy:
  level: 1
""", encoding="utf-8")

    app = Aegis.from_config(cfg_file)
    assert isinstance(app, Aegis)
    assert app.autonomy_engine.level == AutonomyLevel.LEVEL_1
    assert app.evidence_engine is not None
    assert app.reasoning_engine is not None
    assert app.policy_engine is not None


def test_aegis_from_config_with_external_providers(tmp_path: Path):
    """Verify Aegis.from_config correctly constructs production providers with endpoints."""
    cfg_file = tmp_path / "aegis.yaml"
    cfg_file.write_text("""
project:
  name: prod-test

providers:
  metrics:
    type: prometheus
    endpoint: http://localhost:19090
  logs:
    type: loki
    endpoint: http://localhost:3100
  traces:
    type: opentelemetry
    endpoint: http://localhost:18080
  kubernetes:
    type: kubernetes
    read_only: true

autonomy:
  level: 2
""", encoding="utf-8")

    app = Aegis.from_config(cfg_file)
    assert isinstance(app, Aegis)
    assert app.autonomy_engine.level == AutonomyLevel.LEVEL_2
    assert hasattr(app, "kubernetes_provider")
    k8s_provider = app.kubernetes_provider
    assert k8s_provider.config.read_only is True
