import json
from pathlib import Path

from scripts.check_main_release_evidence import (
    EXPECTED_MAIN_RELEASE_LOGS,
    validate_main_release_evidence,
)


def test_validate_main_release_evidence_accepts_complete_evidence(tmp_path: Path) -> None:
    artifact_dir, openapi_path, demo_dir = _write_main_release_evidence(tmp_path)

    findings = validate_main_release_evidence(
        artifact_dir=artifact_dir,
        openapi_path=openapi_path,
        demo_dir=demo_dir,
    )

    assert findings == []


def test_validate_main_release_evidence_reports_missing_log(tmp_path: Path) -> None:
    artifact_dir, openapi_path, demo_dir = _write_main_release_evidence(tmp_path)
    missing_log = artifact_dir / EXPECTED_MAIN_RELEASE_LOGS[0]
    missing_log.unlink()

    findings = validate_main_release_evidence(
        artifact_dir=artifact_dir,
        openapi_path=openapi_path,
        demo_dir=demo_dir,
    )

    assert findings == [f"Missing main release evidence log: {missing_log}"]


def test_validate_main_release_evidence_reports_empty_demo_directory(tmp_path: Path) -> None:
    artifact_dir, openapi_path, demo_dir = _write_main_release_evidence(tmp_path)
    for path in demo_dir.iterdir():
        path.unlink()

    findings = validate_main_release_evidence(
        artifact_dir=artifact_dir,
        openapi_path=openapi_path,
        demo_dir=demo_dir,
    )

    assert findings == [f"Empty demo certification evidence directory: {demo_dir}"]


def _write_main_release_evidence(tmp_path: Path) -> tuple[Path, Path, Path]:
    artifact_dir = tmp_path / "output/main-releasability"
    artifact_dir.mkdir(parents=True)
    for log_name in EXPECTED_MAIN_RELEASE_LOGS:
        (artifact_dir / log_name).write_text(f"{log_name} evidence\n", encoding="utf-8")
    openapi_path = tmp_path / "openapi.json"
    openapi_path.write_text(
        json.dumps({"openapi": "3.1.0", "paths": {"/version": {"get": {}}}}),
        encoding="utf-8",
    )
    demo_dir = tmp_path / "output/demo-certification"
    demo_dir.mkdir()
    (demo_dir / "gateway-demo-certification.json").write_text("{}", encoding="utf-8")
    return artifact_dir, openapi_path, demo_dir
