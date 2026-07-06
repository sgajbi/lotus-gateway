"""Validate Gateway container release evidence before artifact upload."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED_BUILD_KEYS = {
    "git_commit_sha",
    "git_branch",
    "build_timestamp",
    "repo_url",
    "ci_run_id",
    "version",
}
REQUIRED_IMAGE_KEYS = {
    "name",
    "tag",
    "git_sha_tag",
    "digest",
    "digest_ref",
    "same_image_promoted_across_environments",
    "kubernetes_deploys_by_digest",
}
REQUIRED_EVIDENCE_KEYS = {
    "sbom",
    "vulnerability_scan",
    "signature",
    "provenance_attestation",
}
REQUIRED_RUNTIME_KEYS = {
    "git_commit_sha",
    "git_branch",
    "build_timestamp",
    "repo_url",
    "image_digest",
    "ci_run_id",
    "version",
}


def validate_container_release_evidence(
    manifest_path: Path,
    *,
    require_signature: bool = True,
) -> list[str]:
    findings: list[str] = []
    if not manifest_path.is_file():
        return [f"Missing container release manifest: {manifest_path}"]

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"Container release manifest is not valid JSON: {manifest_path}: {exc}"]

    if not isinstance(manifest, dict):
        return [f"Container release manifest must be a JSON object: {manifest_path}"]

    _validate_mapping_keys(findings, manifest, "build", REQUIRED_BUILD_KEYS)
    _validate_mapping_keys(findings, manifest, "image", REQUIRED_IMAGE_KEYS)
    _validate_mapping_keys(findings, manifest, "evidence", REQUIRED_EVIDENCE_KEYS)
    _validate_runtime(findings, manifest)
    _validate_image_digest(findings, manifest)
    _validate_evidence_files(
        findings,
        manifest_path=manifest_path,
        manifest=manifest,
        require_signature=require_signature,
    )
    return findings


def _validate_mapping_keys(
    findings: list[str],
    manifest: dict[str, object],
    key: str,
    required_keys: set[str],
) -> None:
    value = manifest.get(key)
    if not isinstance(value, dict):
        findings.append(f"Container release manifest missing object: {key}")
        return
    missing = sorted(required_keys - set(value))
    for missing_key in missing:
        findings.append(f"Container release manifest missing {key}.{missing_key}")


def _validate_runtime(findings: list[str], manifest: dict[str, object]) -> None:
    runtime = manifest.get("runtime")
    if not isinstance(runtime, dict):
        findings.append("Container release manifest missing object: runtime")
        return
    if runtime.get("version_endpoint") != "/version":
        findings.append("Container release manifest runtime.version_endpoint must be /version")
    metadata_keys = runtime.get("metadata_keys")
    if not isinstance(metadata_keys, list):
        findings.append("Container release manifest runtime.metadata_keys must be a list")
        return
    missing = sorted(REQUIRED_RUNTIME_KEYS - set(metadata_keys))
    for missing_key in missing:
        findings.append(f"Container release manifest missing runtime metadata key: {missing_key}")


def _validate_image_digest(findings: list[str], manifest: dict[str, object]) -> None:
    image = manifest.get("image")
    if not isinstance(image, dict):
        return
    digest = image.get("digest")
    digest_ref = image.get("digest_ref")
    kubernetes_ref = image.get("kubernetes_deploys_by_digest")
    if not isinstance(digest, str) or not digest.startswith("sha256:"):
        findings.append("Container release manifest image.digest must be a sha256 digest")
    if not isinstance(digest_ref, str) or "@sha256:" not in digest_ref:
        findings.append("Container release manifest image.digest_ref must pin by digest")
    if kubernetes_ref != digest_ref:
        findings.append("Kubernetes deployment reference must use the same image digest_ref")
    if image.get("same_image_promoted_across_environments") is not True:
        findings.append("Container release manifest must require same-image promotion")


def _validate_evidence_files(
    findings: list[str],
    *,
    manifest_path: Path,
    manifest: dict[str, object],
    require_signature: bool,
) -> None:
    evidence = manifest.get("evidence")
    if not isinstance(evidence, dict):
        return
    for key in sorted(REQUIRED_EVIDENCE_KEYS):
        value = evidence.get(key)
        if not isinstance(value, str) or not value:
            findings.append(f"Container release manifest evidence.{key} must be a path")
            continue
        if not require_signature and key in {"signature", "provenance_attestation"}:
            continue
        evidence_path = (manifest_path.parent.parent.parent / value).resolve()
        if not evidence_path.is_file():
            findings.append(f"Missing container release evidence file: {value}")
        elif evidence_path.stat().st_size == 0:
            findings.append(f"Empty container release evidence file: {value}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Gateway container release evidence.")
    parser.add_argument(
        "--manifest-path",
        type=Path,
        default=Path("output/container-security/image-release-manifest.json"),
    )
    parser.add_argument("--allow-unsigned", action="store_true")
    args = parser.parse_args()

    findings = validate_container_release_evidence(
        args.manifest_path,
        require_signature=not args.allow_unsigned,
    )
    if findings:
        print("Container release evidence check failed:")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print(f"Container release evidence check passed: {args.manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
