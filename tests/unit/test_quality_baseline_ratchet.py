import json
from decimal import Decimal
from pathlib import Path

import pytest

from scripts.check_quality_baseline_ratchet import evaluate_metrics, main


def _baseline() -> dict:
    return {
        "schema_version": 1,
        "metrics": [
            {
                "name": "findings",
                "log": "findings.txt",
                "kind": "count",
                "pattern": "^finding$",
                "comparison": "not_above",
                "baseline": 2,
                "threshold": 2,
                "remediation": "remove the finding",
            },
            {
                "name": "coverage",
                "log": "coverage.txt",
                "kind": "number",
                "pattern": "coverage=([0-9.]+)%",
                "comparison": "not_below",
                "baseline": 90,
                "threshold": 90,
                "remediation": "add behavioural tests",
            },
        ],
    }


def _write_fixture(tmp_path: Path, *, findings: int = 2, coverage: float = 90) -> tuple[Path, Path]:
    baseline_path = tmp_path / "baseline.json"
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    (artifact_dir / "findings.txt").write_text("finding\n" * findings, encoding="utf-8")
    (artifact_dir / "coverage.txt").write_text(f"coverage={coverage}%\n", encoding="utf-8")
    baseline_path.write_text(json.dumps(_baseline()), encoding="utf-8")
    return baseline_path, artifact_dir


def test_ratchet_accepts_metrics_at_threshold(tmp_path: Path) -> None:
    baseline_path, artifact_dir = _write_fixture(tmp_path)

    results = evaluate_metrics(json.loads(baseline_path.read_text()), artifact_dir)

    assert all(result.passed for result in results)
    assert results[0].delta == 0


def test_ratchet_rejects_new_finding_and_coverage_drop(tmp_path: Path) -> None:
    baseline_path, artifact_dir = _write_fixture(tmp_path, findings=3, coverage=89.99)

    results = evaluate_metrics(json.loads(baseline_path.read_text()), artifact_dir)

    assert [result.name for result in results if not result.passed] == ["findings", "coverage"]
    assert results[0].delta == 1
    assert results[1].delta == Decimal("-0.01")


def test_number_metric_accepts_explicit_zero_success_output(tmp_path: Path) -> None:
    baseline = {
        "schema_version": 1,
        "metrics": [
            {
                "name": "dependency_findings",
                "log": "deptry.txt",
                "kind": "number",
                "pattern": r"Found (\d+) dependency issues\.",
                "zero_pattern": r"Success! No dependency issues found\.",
                "comparison": "not_above",
                "baseline": 1,
                "threshold": 1,
                "remediation": "remove dependency findings",
            }
        ],
    }
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    (artifact_dir / "deptry.txt").write_text(
        "Success! No dependency issues found.\n",
        encoding="utf-8",
    )

    results = evaluate_metrics(baseline, artifact_dir)

    assert results[0].current == Decimal(0)
    assert results[0].passed


def test_count_metric_rejects_malformed_zero_finding_output(tmp_path: Path) -> None:
    baseline = {
        "schema_version": 1,
        "metrics": [
            {
                "name": "findings",
                "log": "findings.txt",
                "kind": "count",
                "pattern": r"^finding$",
                "zero_pattern": r"QUALITY_COMMAND_STATUS=0",
                "comparison": "not_above",
                "baseline": 0,
                "threshold": 0,
                "remediation": "fix the tool failure",
            }
        ],
    }
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    (artifact_dir / "findings.txt").write_text(
        "tool failed before producing a report\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Missing zero-success marker"):
        evaluate_metrics(baseline, artifact_dir)


def test_security_ratchet_does_not_trade_low_findings_for_high_findings(
    tmp_path: Path,
) -> None:
    baseline = {
        "schema_version": 1,
        "metrics": [
            {
                "name": "security_low_findings",
                "log": "security.txt",
                "kind": "number",
                "pattern": r"Total issues \(by severity\):.*?Low:[ \t]*(\d+)",
                "comparison": "not_above",
                "baseline": 3,
                "threshold": 3,
                "remediation": "fix low findings",
            },
            {
                "name": "security_high_findings",
                "log": "security.txt",
                "kind": "number",
                "pattern": r"Total issues \(by severity\):.*?High:[ \t]*(\d+)",
                "comparison": "not_above",
                "baseline": 0,
                "threshold": 0,
                "remediation": "fix high findings",
            },
        ],
    }
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    (artifact_dir / "security.txt").write_text(
        "Total issues (by severity):\n\tUndefined: 0\n\tLow: 2\n\tMedium: 0\n\tHigh: 1\n",
        encoding="utf-8",
    )

    results = evaluate_metrics(baseline, artifact_dir)

    assert [result.name for result in results if not result.passed] == ["security_high_findings"]


def test_explicit_baseline_update_records_current_values(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    baseline_path, artifact_dir = _write_fixture(tmp_path, findings=1, coverage=91.25)
    monkeypatch.setattr(
        "sys.argv",
        [
            "check_quality_baseline_ratchet.py",
            "--baseline",
            str(baseline_path),
            "--artifact-dir",
            str(artifact_dir),
            "--update-baseline",
        ],
    )

    assert main() == 0
    updated = json.loads(baseline_path.read_text())
    assert updated["metrics"][0]["baseline"] == 1
    assert updated["metrics"][0]["threshold"] == 1
    assert updated["metrics"][1]["baseline"] == 91.25
    assert updated["metrics"][1]["threshold"] == 91.25
