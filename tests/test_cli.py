"""Tests for framework CLI commands: init, doctor, policy validate, evaluate, version."""

import json
from pathlib import Path

from aegis.cli import main


def test_cli_version(capsys) -> None:
    """Verify aegis version prints versions without error."""
    code = main(["version"])
    assert code == 0
    captured = capsys.readouterr()
    assert "AEGIS Framework version: 0.1.0" in captured.out
    assert "llmfirewall-core:      available (1.0.0)" in captured.out
    assert "aireliability:         available (0.1.0)" in captured.out


def test_cli_doctor(capsys) -> None:
    """Verify aegis doctor passes all diagnostic checks."""
    code = main(["doctor"])
    assert code == 0
    captured = capsys.readouterr()
    assert "Doctor diagnostics PASSED" in captured.out
    assert "Autonomy Level 4 Omission: SECURE" in captured.out


def test_cli_init_and_policy_validate(tmp_path: Path, capsys) -> None:
    """Verify aegis init scaffolds policy and aegis policy validate checks it."""
    # 1. aegis init
    init_code = main(["init", "--dir", str(tmp_path)])
    assert init_code == 0
    policy_file = tmp_path / "aegis-policy.yaml"
    assert policy_file.exists()
    assert (tmp_path / ".env.example").exists()

    # 2. aegis policy validate
    val_code = main(["policy", "validate", str(policy_file)])
    assert val_code == 0
    captured = capsys.readouterr()
    assert "[VALID] Policy" in captured.out


def test_cli_evaluate(tmp_path: Path, capsys) -> None:
    """Verify aegis evaluate runs a benchmark YAML suite."""
    bm_file = tmp_path / "sample-benchmark.yaml"
    bm_content = """name: "sample-golden-suite"
version: "1.0"
cases:
  - name: "database-timeout-case"
    expected_root_cause: "database latency"
    expected_risk_level: "LOW"
"""
    bm_file.write_text(bm_content, encoding="utf-8")

    code = main(["evaluate", "--benchmark", str(bm_file), "--format", "json"])
    assert code == 0
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert report["total_cases"] == 1
    assert report["passed_cases"] == 1
    assert report["overall_score"] == 1.0
