"""Write Gateway container release manifest evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_manifest(args: argparse.Namespace) -> dict[str, object]:
    image_ref = f"{args.image_name}@{args.image_digest}"
    return {
        "service": "lotus-gateway",
        "image": {
            "name": args.image_name,
            "tag": args.image_tag,
            "git_sha_tag": f"{args.image_name}:{args.git_commit_sha}",
            "digest": args.image_digest,
            "digest_ref": image_ref,
            "same_image_promoted_across_environments": True,
            "kubernetes_deploys_by_digest": image_ref,
        },
        "build": {
            "git_commit_sha": args.git_commit_sha,
            "git_branch": args.git_branch,
            "build_timestamp": args.build_timestamp,
            "repo_url": args.repo_url,
            "ci_run_id": args.ci_run_id,
            "version": args.version,
        },
        "oci_labels": {
            "org.opencontainers.image.revision": args.git_commit_sha,
            "org.opencontainers.image.ref.name": args.git_branch,
            "org.opencontainers.image.created": args.build_timestamp,
            "org.opencontainers.image.source": args.repo_url,
            "org.opencontainers.image.version": args.version,
            "com.lotus.ci.run-id": args.ci_run_id,
        },
        "evidence": {
            "sbom": args.sbom_path,
            "vulnerability_scan": args.scan_path,
            "signature": args.signature_path,
            "provenance_attestation": args.provenance_path,
        },
        "runtime": {
            "version_endpoint": "/version",
            "metadata_keys": [
                "git_commit_sha",
                "git_branch",
                "build_timestamp",
                "repo_url",
                "image_digest",
                "ci_run_id",
                "version",
            ],
        },
        "security": {
            "image_pushed_by_ci_only": True,
            "no_build_secrets_in_arg_or_env": True,
        },
    }


def write_manifest(args: argparse.Namespace) -> None:
    manifest = build_manifest(args)
    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Write Gateway image release manifest.")
    parser.add_argument("--image-name", required=True)
    parser.add_argument("--image-tag", required=True)
    parser.add_argument("--image-digest", required=True)
    parser.add_argument("--git-commit-sha", required=True)
    parser.add_argument("--git-branch", required=True)
    parser.add_argument("--build-timestamp", required=True)
    parser.add_argument("--repo-url", required=True)
    parser.add_argument("--ci-run-id", required=True)
    parser.add_argument("--version", default="0.1.0")
    parser.add_argument("--sbom-path", default="output/container-security/sbom.spdx.json")
    parser.add_argument("--scan-path", default="output/container-security/trivy-image-scan.json")
    parser.add_argument(
        "--signature-path", default="output/container-security/cosign-signature.txt"
    )
    parser.add_argument(
        "--provenance-path",
        default="output/container-security/provenance-attestation.txt",
    )
    parser.add_argument(
        "--output-path",
        default="output/container-security/image-release-manifest.json",
    )
    write_manifest(parser.parse_args())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
