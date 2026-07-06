from __future__ import annotations

import os
from collections.abc import Mapping

BUILD_METADATA_ENV = {
    "version": "LOTUS_APP_VERSION",
    "git_commit_sha": "LOTUS_GIT_COMMIT_SHA",
    "git_branch": "LOTUS_GIT_BRANCH",
    "build_timestamp": "LOTUS_BUILD_TIMESTAMP",
    "repo_url": "LOTUS_REPO_URL",
    "image_digest": "LOTUS_IMAGE_DIGEST",
    "ci_run_id": "LOTUS_CI_RUN_ID",
}
DEFAULT_BUILD_METADATA = {
    "version": "0.1.0",
    "git_commit_sha": "unknown",
    "git_branch": "unknown",
    "build_timestamp": "unknown",
    "repo_url": "unknown",
    "image_digest": "unknown",
    "ci_run_id": "unknown",
}


def gateway_build_metadata(environ: Mapping[str, str] | None = None) -> dict[str, str]:
    source = environ if environ is not None else os.environ
    metadata = {"service": "lotus-gateway"}
    for key, env_name in BUILD_METADATA_ENV.items():
        metadata[key] = source.get(env_name, DEFAULT_BUILD_METADATA[key]).strip() or "unknown"
    return metadata
