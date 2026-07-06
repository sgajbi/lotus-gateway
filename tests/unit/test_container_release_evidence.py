import json
from pathlib import Path

from scripts.check_container_release_evidence import validate_container_release_evidence
from scripts.write_container_release_manifest import build_manifest


def _write_evidence(root: Path, relative_path: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{relative_path} evidence\n", encoding="utf-8")


def test_container_release_manifest_validates_complete_evidence(tmp_path: Path) -> None:
    for relative_path in (
        "output/container-security/sbom.spdx.json",
        "output/container-security/trivy-image-scan.json",
        "output/container-security/cosign-signature.txt",
        "output/container-security/provenance-attestation.txt",
    ):
        _write_evidence(tmp_path, relative_path)
    manifest_path = tmp_path / "output/container-security/image-release-manifest.json"
    args = _args(output_path=str(manifest_path))
    manifest_path.write_text(json.dumps(build_manifest(args)), encoding="utf-8")

    assert validate_container_release_evidence(manifest_path) == []


def test_container_release_manifest_requires_digest_pinned_kubernetes_ref(
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "output/container-security/image-release-manifest.json"
    manifest_path.parent.mkdir(parents=True)
    manifest = build_manifest(_args(output_path=str(manifest_path)))
    manifest["image"]["kubernetes_deploys_by_digest"] = "ghcr.io/sgajbi/lotus-gateway:latest"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    findings = validate_container_release_evidence(manifest_path, require_signature=False)

    assert "Kubernetes deployment reference must use the same image digest_ref" in findings


def test_container_release_manifest_allows_unsigned_pr_evidence_but_requires_scan_and_sbom(
    tmp_path: Path,
) -> None:
    for relative_path in (
        "output/container-security/sbom.spdx.json",
        "output/container-security/trivy-image-scan.json",
    ):
        _write_evidence(tmp_path, relative_path)
    manifest_path = tmp_path / "output/container-security/image-release-manifest.json"
    args = _args(output_path=str(manifest_path))
    manifest_path.write_text(json.dumps(build_manifest(args)), encoding="utf-8")

    assert validate_container_release_evidence(manifest_path, require_signature=False) == []


def _args(**overrides):
    class Args:
        image_name = "ghcr.io/sgajbi/lotus-gateway"
        image_tag = "abc123"
        image_digest = "sha256:abc123"
        git_commit_sha = "abc123"
        git_branch = "main"
        build_timestamp = "2026-07-06T05:00:00Z"
        repo_url = "https://github.com/sgajbi/lotus-gateway"
        ci_run_id = "1234"
        version = "0.1.0"
        sbom_path = "output/container-security/sbom.spdx.json"
        scan_path = "output/container-security/trivy-image-scan.json"
        signature_path = "output/container-security/cosign-signature.txt"
        provenance_path = "output/container-security/provenance-attestation.txt"
        output_path = "output/container-security/image-release-manifest.json"

    args = Args()
    for key, value in overrides.items():
        setattr(args, key, value)
    return args
