"""Prepare truthful, shell-safe Compose provenance for Lotus checkouts."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class Checkout:
    environment_prefix: str
    repository: Path
    repository_url: str


def _git(repository: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.rstrip("\n")


def checkout_provenance(checkout: Checkout, *, timestamp: str) -> dict[str, str]:
    """Return metadata for the exact checkout Compose will build, without a shell."""
    commit = _git(checkout.repository, "rev-parse", "--verify", "HEAD")
    dirty = bool(_git(checkout.repository, "status", "--porcelain"))
    return {
        f"{checkout.environment_prefix}_GIT_COMMIT_SHA": f"{commit}-dirty" if dirty else commit,
        f"{checkout.environment_prefix}_GIT_BRANCH": _git(
            checkout.repository, "rev-parse", "--abbrev-ref", "HEAD"
        ),
        f"{checkout.environment_prefix}_BUILD_TIMESTAMP": timestamp,
        f"{checkout.environment_prefix}_REPO_URL": checkout.repository_url,
        f"{checkout.environment_prefix}_CI_RUN_ID": "local",
    }


def compose_environment(
    checkouts: Sequence[Checkout], *, environ: Mapping[str, str], timestamp: str
) -> dict[str, str]:
    """Keep supplied values verbatim; derive only values the caller did not supply."""
    prepared = dict(environ)
    for checkout in checkouts:
        for key, value in checkout_provenance(checkout, timestamp=timestamp).items():
            prepared.setdefault(key, value)
        prepared.setdefault(f"{checkout.environment_prefix}_IMAGE_DIGEST", "not-supplied")
    return prepared


def _checkout_from_environment(
    *, prefix: str, path_variable: str | None, default_path: str, repository_url: str
) -> Checkout:
    value = os.environ.get(path_variable, default_path) if path_variable else default_path
    return Checkout(prefix, Path(value).resolve(), repository_url)


def _checkouts(profile: str) -> list[Checkout]:
    checkouts = [
        _checkout_from_environment(
            prefix="GATEWAY",
            path_variable=None,
            default_path=".",
            repository_url="https://github.com/sgajbi/lotus-gateway",
        )
    ]
    if profile != "e2e":
        return checkouts
    checkouts.extend(
        [
            _checkout_from_environment(
                prefix="CORE",
                path_variable="LOTUS_CORE_REPO_PATH",
                default_path="../lotus-core",
                repository_url="https://github.com/sgajbi/lotus-core",
            ),
            _checkout_from_environment(
                prefix="MANAGE",
                path_variable="LOTUS_MANAGE_REPO_PATH",
                default_path="../lotus-manage",
                repository_url="https://github.com/sgajbi/lotus-manage",
            ),
            _checkout_from_environment(
                prefix="REPORT",
                path_variable="LOTUS_REPORT_REPO_PATH",
                default_path="../lotus-report",
                repository_url="https://github.com/sgajbi/lotus-report",
            ),
            _checkout_from_environment(
                prefix="ARCHIVE",
                path_variable="LOTUS_ARCHIVE_REPO_PATH",
                default_path="../lotus-archive",
                repository_url="https://github.com/sgajbi/lotus-archive",
            ),
            _checkout_from_environment(
                prefix="WORKBENCH",
                path_variable="UI_REPO_PATH",
                default_path="../lotus-workbench",
                repository_url="https://github.com/sgajbi/lotus-workbench",
            ),
        ]
    )
    return checkouts


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("gateway", "e2e"), required=True)
    parser.add_argument("compose_arguments", nargs=argparse.REMAINDER)
    arguments = parser.parse_args(argv)
    if not arguments.compose_arguments or arguments.compose_arguments[0] != "--":
        parser.error("pass docker compose arguments after --")

    timestamp = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    environment = compose_environment(
        _checkouts(arguments.profile), environ=os.environ, timestamp=timestamp
    )
    return subprocess.run(
        ["docker", "compose", *arguments.compose_arguments[1:]], env=environment, check=False
    ).returncode


if __name__ == "__main__":
    sys.exit(main())
