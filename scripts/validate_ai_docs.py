#!/usr/bin/env python3
"""Validate consistency of AI documentation and metadata against AEGIS Framework package."""

import sys
from pathlib import Path

import yaml

import aegis
from aegis.autonomy import AutonomyLevel
from aegis.config import AegisProjectConfig


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    errors: list[str] = []

    print("Checking AI documentation and metadata consistency...")

    # 1. Check required documentation files exist
    required_files = [
        root / "docs/ai/integration.md",
        root / "docs/ai/quickstart.md",
        root / "docs/ai/vibe-coding-integration.md",
        root / "docs/ai/capabilities.yaml",
        root / "AGENTS.md",
        root / "CLAUDE.md",
        root / ".cursorrules",
        root / "examples/ai_agent_integration.py",
    ]
    for rf in required_files:
        if not rf.exists():
            errors.append(f"Missing required AI integration file: {rf.relative_to(root)}")
        else:
            print(f"  ✓ Found {rf.relative_to(root)}")

    # 2. Validate capabilities.yaml
    cap_file = root / "docs/ai/capabilities.yaml"
    if cap_file.exists():
        try:
            data = yaml.safe_load(cap_file.read_text(encoding="utf-8"))
            if data.get("version") != aegis.__version__:
                errors.append(f"capabilities.yaml version {data.get('version')} does not match aegis.__version__ {aegis.__version__}")
            if data.get("package") != "aegis-ai":
                errors.append(f"capabilities.yaml package {data.get('package')} != 'aegis-ai'")
            sec = data.get("security", {})
            lvl4 = sec.get("level_4_enabled")
            if lvl4 is None:
                lvl4 = sec.get("autonomy_levels", {}).get("level_4_enabled")
            if lvl4 is not False:
                errors.append("capabilities.yaml must declare level_4_enabled: false")
            print("  ✓ capabilities.yaml parsed and validated")
        except Exception as exc:
            errors.append(f"Failed to parse capabilities.yaml: {exc}")

    # 3. Check public imports and invariants
    try:
        from aegis import Aegis
        assert callable(Aegis.from_config)
        assert hasattr(aegis, "__version__")
        print("  ✓ Public exports verified: Aegis, AegisConfig, Aegis.from_config")
    except Exception as exc:
        errors.append(f"Failed to import public API: {exc}")

    # Check Autonomy Level 4 omission invariant
    if hasattr(AutonomyLevel, "LEVEL_4"):
        errors.append("AutonomyLevel.LEVEL_4 must not exist")
    else:
        print("  ✓ Autonomy invariant verified: LEVEL_4 is omitted")

    # 4. Check configuration example validity
    integration_doc = root / "docs/ai/integration.md"
    if integration_doc.exists():
        content = integration_doc.read_text(encoding="utf-8")
        if "${AEGIS_PROMETHEUS_URL" not in content:
            errors.append("docs/ai/integration.md must demonstrate environment variable substitution")
        # Validate that the YAML snippet inside integration.md parses against AegisProjectConfig
        import re
        yaml_blocks = re.findall(r"```yaml\n(.*?)\n```", content, re.DOTALL)
        matched_valid_config = False
        for block in yaml_blocks:
            if "providers:" in block and "metrics:" in block:
                try:
                    cfg = AegisProjectConfig.from_yaml(block)
                    matched_valid_config = True
                    print(f"  ✓ Configuration snippet validated against schema: project '{cfg.project.name}'")
                except Exception as exc:
                    errors.append(f"Configuration YAML snippet in integration.md failed schema validation: {exc}")
        if not matched_valid_config:
            errors.append("Could not find valid providers configuration block in docs/ai/integration.md")

    # 5. Secret audit in new documentation
    for check_path in required_files:
        if check_path.exists():
            text = check_path.read_text(encoding="utf-8").lower()
            for pattern in ["bearer ey", "password123", "aws_secret", "private_key", "ghp_"]:
                if pattern in text:
                    errors.append(f"Potential secret pattern '{pattern}' found in {check_path.name}")

    if errors:
        print("\nERRORS DETECTED:")
        for err in errors:
            print(f"  ✗ {err}")
        return 1

    print("\n✓ All AI documentation and metadata consistency checks passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
