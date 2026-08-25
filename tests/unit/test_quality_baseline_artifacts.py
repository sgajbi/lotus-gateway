import json
from pathlib import Path

from scripts.check_quality_baseline_artifacts import (
    EXPECTED_BASELINE_LOGS,
    QUALITY_TOOL_LOGS,
    validate_quality_baseline_artifacts,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_complete_artifacts(tmp_path: Path) -> tuple[Path, Path]:
    artifact_dir = tmp_path / "quality-baseline"
    artifact_dir.mkdir()
    for log_name in EXPECTED_BASELINE_LOGS:
        evidence = f"{log_name} evidence\n"
        if log_name in QUALITY_TOOL_LOGS:
            evidence += "QUALITY_COMMAND_STATUS=0\n"
        (artifact_dir / log_name).write_text(evidence, encoding="utf-8")

    openapi_path = tmp_path / "openapi.json"
    openapi_path.write_text(
        json.dumps({"openapi": "3.1.0", "paths": {"/health": {"get": {}}}}),
        encoding="utf-8",
    )
    return artifact_dir, openapi_path


def test_validate_quality_baseline_artifacts_accepts_complete_evidence(tmp_path: Path) -> None:
    artifact_dir, openapi_path = _write_complete_artifacts(tmp_path)

    findings = validate_quality_baseline_artifacts(
        artifact_dir=artifact_dir,
        openapi_path=openapi_path,
    )

    assert findings == []


def test_quality_tool_logs_are_expected_baseline_artifacts() -> None:
    assert set(QUALITY_TOOL_LOGS) <= set(EXPECTED_BASELINE_LOGS)


def test_validate_quality_baseline_artifacts_reports_missing_log(tmp_path: Path) -> None:
    artifact_dir, openapi_path = _write_complete_artifacts(tmp_path)
    missing_log = artifact_dir / EXPECTED_BASELINE_LOGS[0]
    missing_log.unlink()

    findings = validate_quality_baseline_artifacts(
        artifact_dir=artifact_dir,
        openapi_path=openapi_path,
    )

    assert findings == [f"Missing quality baseline log: {missing_log}"]


def test_validate_quality_baseline_artifacts_reports_missing_command_status(
    tmp_path: Path,
) -> None:
    artifact_dir, openapi_path = _write_complete_artifacts(tmp_path)
    status_log = artifact_dir / QUALITY_TOOL_LOGS[0]
    status_log.write_text("ruff evidence\n", encoding="utf-8")

    findings = validate_quality_baseline_artifacts(
        artifact_dir=artifact_dir,
        openapi_path=openapi_path,
    )

    assert findings == [
        f"Expected exactly one QUALITY_COMMAND_STATUS marker in {status_log}, found 0"
    ]


def test_validate_quality_baseline_artifacts_rejects_ambiguous_or_invalid_status(
    tmp_path: Path,
) -> None:
    artifact_dir, openapi_path = _write_complete_artifacts(tmp_path)
    duplicate_log = artifact_dir / QUALITY_TOOL_LOGS[0]
    duplicate_log.write_text(
        "QUALITY_COMMAND_STATUS=0\nQUALITY_COMMAND_STATUS=1\n",
        encoding="utf-8",
    )
    invalid_log = artifact_dir / QUALITY_TOOL_LOGS[1]
    invalid_log.write_text("QUALITY_COMMAND_STATUS=failed\n", encoding="utf-8")

    findings = validate_quality_baseline_artifacts(
        artifact_dir=artifact_dir,
        openapi_path=openapi_path,
    )

    assert findings == [
        f"Expected exactly one QUALITY_COMMAND_STATUS marker in {duplicate_log}, found 2",
        (
            "Invalid QUALITY_COMMAND_STATUS marker in "
            f"{invalid_log}: expected a non-negative integer, received 'failed'"
        ),
    ]


def test_validate_quality_baseline_artifacts_reports_invalid_openapi(tmp_path: Path) -> None:
    artifact_dir, openapi_path = _write_complete_artifacts(tmp_path)
    openapi_path.write_text(json.dumps({"openapi": "3.1.0", "paths": {}}), encoding="utf-8")

    findings = validate_quality_baseline_artifacts(
        artifact_dir=artifact_dir,
        openapi_path=openapi_path,
    )

    assert findings == [f"Generated OpenAPI artifact is missing non-empty 'paths': {openapi_path}"]


def test_quality_baseline_workflow_enforces_artifact_set_before_upload() -> None:
    workflow = (REPO_ROOT / ".github" / "workflows" / "quality-baseline.yml").read_text(
        encoding="utf-8"
    )

    assert "Enforce Refactored Source Thresholds" in workflow
    assert "python scripts/check_refactor_quality_thresholds.py \\" in workflow
    assert "--max-source-file-lines 316" in workflow
    assert "--max-function-lines 49" in workflow
    assert "output/quality-baseline/refactor-thresholds.txt" in workflow
    assert "Enforce Workflow Governance" in workflow
    assert "python scripts/check_workflow_action_runtime.py \\" in workflow
    assert "output/quality-baseline/workflow-governance.txt" in workflow
    assert "Enforce Agent Quality Evidence" in workflow
    assert "python scripts/check_agent_quality_evidence.py \\" in workflow
    assert "output/quality-baseline/agent-quality-evidence.txt" in workflow
    assert "Validate Quality Baseline Artifact Set" in workflow
    assert "Demo Certification Baseline" in workflow
    assert "make demo-certification" in workflow
    assert "output/quality-baseline/demo-certification.txt" in workflow
    assert "Install Duplicate-Code Quality Tooling" in workflow
    assert "npm ci --ignore-scripts" in workflow
    assert "Duplicate Code Baseline" in workflow
    assert "--min-lines 15" in workflow
    assert "--min-tokens 50" in workflow
    assert "--pattern 'src/app/**/*.py'" in workflow
    assert "output/quality-baseline/duplicate-code.txt" in workflow
    assert "Enforce Duplicate Code Ratchet" in workflow
    assert "scripts/check_duplicate_code_ratchet.py" in workflow
    assert "quality/duplicate_code_baseline.json" in workflow
    assert "output/quality-baseline/duplicate-code-ratchet.txt" in workflow
    assert "output/quality-baseline/quality-ratchet.txt" in workflow
    assert "Quality Baseline / Ratcheted Trend Gate" in workflow
    assert "set -o pipefail" in workflow
    assert "python scripts/check_quality_baseline_ratchet.py" in workflow
    assert "QUALITY_COMMAND_STATUS" in workflow
    assert "output/demo-certification/" in workflow
    assert "python scripts/check_quality_baseline_artifacts.py" in workflow
    assert "if-no-files-found: error" in workflow


def test_complexity_baseline_aggregates_all_producer_statuses() -> None:
    workflow = (REPO_ROOT / ".github" / "workflows" / "quality-baseline.yml").read_text(
        encoding="utf-8"
    )

    complexity_step = workflow.split("      - name: Complexity Baseline", 1)[1].split(
        "      - name: Dead Code Baseline", 1
    )[0]

    assert "radon cc src/app -s -a || radon_cc_status=$?" in complexity_step
    assert "radon mi src/app -s || radon_mi_status=$?" in complexity_step
    assert (
        "xenon --max-absolute C --max-modules B --max-average A src/app || xenon_status=$?"
        in complexity_step
    )
    assert (
        'if [ "${radon_cc_status}" -ne 0 ] || [ "${radon_mi_status}" -ne 0 ] || '
        '[ "${xenon_status}" -ne 0 ]; then' in complexity_step
    )
    assert "printf 'QUALITY_COMMAND_STATUS=%s\\n' \"${status}\"" in complexity_step


def test_quality_baseline_workflow_has_one_authoritative_automated_event() -> None:
    workflow = (REPO_ROOT / ".github" / "workflows" / "quality-baseline.yml").read_text(
        encoding="utf-8"
    )

    assert "  pull_request:\n    branches: [ main ]" in workflow
    assert "  workflow_dispatch:\n" in workflow
    assert "  push:\n" not in workflow
    assert (
        "group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.run_id }}"
        in workflow
    )
    assert "cancel-in-progress: true" in workflow
    assert "name: Quality Baseline / Ratcheted Trend Gate" in workflow


def test_duplicate_detector_is_pinned_and_uses_the_repo_quality_package() -> None:
    package = json.loads((REPO_ROOT / "quality" / "package.json").read_text(encoding="utf-8"))
    lock = json.loads((REPO_ROOT / "quality" / "package-lock.json").read_text(encoding="utf-8"))

    assert package["private"] is True
    assert package["devDependencies"]["jscpd"] == "4.2.2"
    assert (REPO_ROOT / "quality" / ".npmrc").read_text(
        encoding="utf-8"
    ).strip() == "engine-strict=true"
    assert lock["packages"][""].get("devDependencies", {}).get("jscpd") == "4.2.2"
    assert lock["packages"]["node_modules/jscpd"]["version"] == "4.2.2"


def test_repo_ignores_root_ci_failure_log_without_hiding_quality_evidence() -> None:
    gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()

    assert "/_ci_fail.log" in gitignore
    assert "quality/" not in gitignore
    assert "output/" in gitignore
