"""Validate that the quality baseline produced usable evidence artifacts."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

EXPECTED_BASELINE_LOGS = (
    "refactor-thresholds.txt",
    "workflow-governance.txt",
    "agent-quality-evidence.txt",
    "ruff.txt",
    "mypy.txt",
    "coverage.txt",
    "duplicate-code.txt",
    "duplicate-code-reproducibility.txt",
    "duplicate-code-ratchet.txt",
    "duplicate-code-reproducibility-ratchet.txt",
    "import-linter.txt",
    "complexity.txt",
    "vulture.txt",
    "deptry.txt",
    "security.txt",
    "interrogate.txt",
    "spectral.txt",
    "demo-certification.txt",
    "quality-ratchet.txt",
)

QUALITY_TOOL_LOGS = (
    "ruff.txt",
    "mypy.txt",
    "coverage.txt",
    "duplicate-code.txt",
    "duplicate-code-reproducibility.txt",
    "duplicate-code-ratchet.txt",
    "duplicate-code-reproducibility-ratchet.txt",
    "import-linter.txt",
    "complexity.txt",
    "vulture.txt",
    "deptry.txt",
    "security.txt",
    "interrogate.txt",
    "spectral.txt",
    "demo-certification.txt",
)
QUALITY_COMMAND_STATUS_PATTERN = re.compile(r"^QUALITY_COMMAND_STATUS=(.*)$", re.MULTILINE)


def validate_quality_baseline_artifacts(
    *,
    artifact_dir: Path,
    openapi_path: Path,
) -> list[str]:
    """Return validation findings for missing or unusable quality-baseline artifacts."""

    findings: list[str] = []
    if not artifact_dir.is_dir():
        findings.append(f"Missing quality baseline artifact directory: {artifact_dir}")
        return findings

    for log_name in EXPECTED_BASELINE_LOGS:
        log_path = artifact_dir / log_name
        if not log_path.is_file():
            findings.append(f"Missing quality baseline log: {log_path}")
            continue
        if log_path.stat().st_size == 0:
            findings.append(f"Empty quality baseline log: {log_path}")

    for log_name in QUALITY_TOOL_LOGS:
        log_path = artifact_dir / log_name
        if not log_path.is_file() or log_path.stat().st_size == 0:
            continue
        markers = QUALITY_COMMAND_STATUS_PATTERN.findall(log_path.read_text(encoding="utf-8"))
        if len(markers) != 1:
            findings.append(
                "Expected exactly one QUALITY_COMMAND_STATUS marker in "
                f"{log_path}, found {len(markers)}"
            )
            continue
        status = markers[0].strip()
        if not status.isdecimal():
            findings.append(
                "Invalid QUALITY_COMMAND_STATUS marker in "
                f"{log_path}: expected a non-negative integer, received {status!r}"
            )

    if not openapi_path.is_file():
        findings.append(f"Missing generated OpenAPI artifact: {openapi_path}")
        return findings

    if openapi_path.stat().st_size == 0:
        findings.append(f"Empty generated OpenAPI artifact: {openapi_path}")
        return findings

    try:
        openapi_document = json.loads(openapi_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        findings.append(f"Generated OpenAPI artifact is not valid JSON: {openapi_path}: {exc}")
        return findings

    if not isinstance(openapi_document, dict):
        findings.append(f"Generated OpenAPI artifact must contain a JSON object: {openapi_path}")
        return findings

    if not openapi_document.get("openapi"):
        findings.append(f"Generated OpenAPI artifact is missing 'openapi': {openapi_path}")
    if not isinstance(openapi_document.get("paths"), dict) or not openapi_document["paths"]:
        findings.append(f"Generated OpenAPI artifact is missing non-empty 'paths': {openapi_path}")

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate quality baseline artifacts before upload.",
    )
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=Path("output/quality-baseline"),
        help="Directory containing quality baseline logs.",
    )
    parser.add_argument(
        "--openapi-path",
        type=Path,
        default=Path("openapi.json"),
        help="Generated OpenAPI JSON artifact path.",
    )
    args = parser.parse_args()

    findings = validate_quality_baseline_artifacts(
        artifact_dir=args.artifact_dir,
        openapi_path=args.openapi_path,
    )
    if findings:
        print("Quality baseline artifact check failed:")
        for finding in findings:
            print(f"- {finding}")
        return 1

    print(
        "Quality baseline artifact check passed: "
        f"logs={len(EXPECTED_BASELINE_LOGS)}, openapi={args.openapi_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
