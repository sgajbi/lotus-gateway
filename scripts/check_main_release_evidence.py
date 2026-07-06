"""Validate retained Main Releasability evidence before upload."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

EXPECTED_MAIN_RELEASE_LOGS = (
    "coverage.txt",
    "workflow-governance.txt",
    "agent-quality-evidence.txt",
    "security.txt",
    "demo-certification.txt",
)


def validate_main_release_evidence(
    *,
    artifact_dir: Path,
    openapi_path: Path,
    demo_dir: Path,
) -> list[str]:
    findings: list[str] = []
    if not artifact_dir.is_dir():
        return [f"Missing main release evidence directory: {artifact_dir}"]
    for log_name in EXPECTED_MAIN_RELEASE_LOGS:
        log_path = artifact_dir / log_name
        if not log_path.is_file():
            findings.append(f"Missing main release evidence log: {log_path}")
        elif log_path.stat().st_size == 0:
            findings.append(f"Empty main release evidence log: {log_path}")

    _validate_openapi(findings, openapi_path)
    if not demo_dir.is_dir():
        findings.append(f"Missing demo certification evidence directory: {demo_dir}")
    elif not any(demo_dir.iterdir()):
        findings.append(f"Empty demo certification evidence directory: {demo_dir}")
    return findings


def _validate_openapi(findings: list[str], openapi_path: Path) -> None:
    if not openapi_path.is_file():
        findings.append(f"Missing generated OpenAPI artifact: {openapi_path}")
        return
    try:
        openapi_document = json.loads(openapi_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        findings.append(f"Generated OpenAPI artifact is not valid JSON: {openapi_path}: {exc}")
        return
    if not isinstance(openapi_document, dict):
        findings.append(f"Generated OpenAPI artifact must contain a JSON object: {openapi_path}")
        return
    if not openapi_document.get("openapi"):
        findings.append(f"Generated OpenAPI artifact is missing 'openapi': {openapi_path}")
    if not isinstance(openapi_document.get("paths"), dict) or not openapi_document["paths"]:
        findings.append(f"Generated OpenAPI artifact is missing non-empty 'paths': {openapi_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate main release evidence artifacts.")
    parser.add_argument("--artifact-dir", type=Path, default=Path("output/main-releasability"))
    parser.add_argument("--openapi-path", type=Path, default=Path("openapi.json"))
    parser.add_argument("--demo-dir", type=Path, default=Path("output/demo-certification"))
    args = parser.parse_args()

    findings = validate_main_release_evidence(
        artifact_dir=args.artifact_dir,
        openapi_path=args.openapi_path,
        demo_dir=args.demo_dir,
    )
    if findings:
        print("Main release evidence check failed:")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print(
        "Main release evidence check passed: "
        f"logs={len(EXPECTED_MAIN_RELEASE_LOGS)}, openapi={args.openapi_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
