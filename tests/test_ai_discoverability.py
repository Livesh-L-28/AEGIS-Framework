"""Test AI discoverability, metadata consistency, and agent contracts."""

from pathlib import Path

import yaml

import aegis
from aegis import Aegis, AegisConfig
from aegis.autonomy import AutonomyLevel
from aegis.config import AegisProjectConfig

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_ai_agent_contract_files_exist() -> None:
    """Verify all canonical AI integration documentation files exist."""
    required = [
        REPO_ROOT / "docs/ai/integration.md",
        REPO_ROOT / "docs/ai/quickstart.md",
        REPO_ROOT / "docs/ai/vibe-coding-integration.md",
        REPO_ROOT / "docs/ai/capabilities.yaml",
        REPO_ROOT / "AGENTS.md",
        REPO_ROOT / "CLAUDE.md",
        REPO_ROOT / ".cursorrules",
        REPO_ROOT / "examples/ai_agent_integration.py",
    ]
    for p in required:
        assert p.exists(), f"Required AI file missing: {p.name}"


def test_capabilities_manifest_consistency() -> None:
    """Verify capabilities.yaml matches actual framework version, package name, and security invariants."""
    cap_path = REPO_ROOT / "docs/ai/capabilities.yaml"
    data = yaml.safe_load(cap_path.read_text(encoding="utf-8"))

    assert data["version"] == aegis.__version__
    assert data["package"] == "aegis-resilience"
    assert data["security"]["fail_closed"] is True
    assert data["security"]["approval_gates"] is True
    assert data["security"]["arbitrary_shell_remediation"] is False

    # Invariant: Level 4 autonomy must be explicitly disabled
    sec = data["security"]
    lvl4 = sec.get("level_4_enabled")
    if lvl4 is None:
        lvl4 = sec.get("autonomy_levels", {}).get("level_4_enabled")
    assert lvl4 is False


def test_ai_integration_contract_safety_invariants() -> None:
    """Verify docs/ai/integration.md contains all critical safety rules and no secrets."""
    doc = (REPO_ROOT / "docs/ai/integration.md").read_text(encoding="utf-8")

    assert "Non-Negotiable Safety Rules" in doc
    assert "Level 4" in doc
    assert "arbitrary shell" in doc.lower()
    assert "fail-closed" in doc.lower()
    assert "Aegis.from_config" in doc
    assert "${AEGIS_PROMETHEUS_URL" in doc

    # Secret check
    for forbidden in ["password123", "bearer ey", "private_key", "ghp_"]:
        assert forbidden not in doc.lower()


def test_agents_md_contract() -> None:
    """Verify AGENTS.md points to canonical documentation and specifies safety invariants."""
    agents_doc = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")

    assert "docs/ai/integration.md" in agents_doc
    assert "pip install aegis-resilience" in agents_doc
    assert "Aegis.from_config" in agents_doc
    assert "Level 4" in agents_doc


def test_documented_config_schema_validation() -> None:
    """Verify YAML configuration snippet in docs/ai/integration.md parses with AegisProjectConfig."""
    doc = (REPO_ROOT / "docs/ai/integration.md").read_text(encoding="utf-8")
    import re

    snippets = re.findall(r"```yaml\n(.*?)\n```", doc, re.DOTALL)
    valid_blocks = 0
    for snippet in snippets:
        if "providers:" in snippet and "metrics:" in snippet:
            cfg = AegisProjectConfig.from_yaml(snippet)
            assert cfg.project.name == "my-service-reliability"
            assert cfg.providers.metrics.type == "prometheus"
            assert cfg.providers.kubernetes is not None
            assert cfg.providers.kubernetes.read_only is True
            assert cfg.security.fail_closed is True
            assert cfg.autonomy.level == 1
            valid_blocks += 1

    assert valid_blocks >= 1, "Failed to find and validate YAML configuration snippet in integration.md"


def test_public_api_availability() -> None:
    """Verify Aegis.from_config() factory exists and AutonomyLevel 4 is omitted."""
    assert callable(Aegis.from_config)
    assert hasattr(AegisConfig, "model_validate")
    assert not hasattr(AutonomyLevel, "LEVEL_4")
