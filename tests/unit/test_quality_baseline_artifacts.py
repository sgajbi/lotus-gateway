import json
from pathlib import Path

from scripts.check_quality_baseline_artifacts import (
    EXPECTED_BASELINE_LOGS,
    validate_quality_baseline_artifacts,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_complete_artifacts(tmp_path: Path) -> tuple[Path, Path]:
    artifact_dir = tmp_path / "quality-baseline"
    artifact_dir.mkdir()
    for log_name in EXPECTED_BASELINE_LOGS:
        (artifact_dir / log_name).write_text(f"{log_name} evidence\n", encoding="utf-8")

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


def test_validate_quality_baseline_artifacts_reports_missing_log(tmp_path: Path) -> None:
    artifact_dir, openapi_path = _write_complete_artifacts(tmp_path)
    missing_log = artifact_dir / EXPECTED_BASELINE_LOGS[0]
    missing_log.unlink()

    findings = validate_quality_baseline_artifacts(
        artifact_dir=artifact_dir,
        openapi_path=openapi_path,
    )

    assert findings == [f"Missing quality baseline log: {missing_log}"]


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
    assert "--max-source-file-lines 556" in workflow
    assert "--max-function-lines 49" in workflow
    assert "output/quality-baseline/refactor-thresholds.txt" in workflow
    assert "Validate Quality Baseline Artifact Set" in workflow
    assert "python scripts/check_quality_baseline_artifacts.py" in workflow
    assert "if-no-files-found: error" in workflow
