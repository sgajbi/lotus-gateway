from __future__ import annotations

import subprocess
from pathlib import Path

from scripts.compose_provenance import Checkout, checkout_provenance, compose_environment


def _git(repository: Path, *arguments: str) -> None:
    subprocess.run(["git", "-C", str(repository), *arguments], check=True, capture_output=True)


def _checkout(tmp_path: Path) -> Path:
    repository = tmp_path / "checkout"
    repository.mkdir()
    _git(repository, "init")
    _git(repository, "config", "user.email", "gateway@example.test")
    _git(repository, "config", "user.name", "Gateway Test")
    (repository / "tracked.txt").write_text("initial\n", encoding="utf-8")
    _git(repository, "add", "tracked.txt")
    _git(repository, "commit", "-m", "initial")
    return repository


def test_checkout_provenance_preserves_literal_hostile_branch_and_dirty_state(
    tmp_path: Path,
) -> None:
    repository = _checkout(tmp_path)
    branch = "feature/provenance;literal$(not-executed)"
    _git(repository, "checkout", "-b", branch)
    (repository / "tracked.txt").write_text("modified\n", encoding="utf-8")

    provenance = checkout_provenance(
        Checkout("SIBLING", repository, "https://example.test/sibling"),
        timestamp="2026-09-13T00:00:00Z",
    )

    assert provenance["SIBLING_GIT_BRANCH"] == branch
    assert provenance["SIBLING_GIT_COMMIT_SHA"].endswith("-dirty")


def test_environment_values_win_without_expansion_or_normalization(tmp_path: Path) -> None:
    repository = _checkout(tmp_path)
    hostile = "feature/from-environment$(not-executed);literal"

    environment = compose_environment(
        [Checkout("GATEWAY", repository, "https://example.test/gateway")],
        environ={"GATEWAY_GIT_BRANCH": hostile, "GATEWAY_IMAGE_DIGEST": "sha256:provided"},
        timestamp="2026-09-13T00:00:00Z",
    )

    assert environment["GATEWAY_GIT_BRANCH"] == hostile
    assert environment["GATEWAY_IMAGE_DIGEST"] == "sha256:provided"


def test_missing_digest_is_named_not_supplied(tmp_path: Path) -> None:
    environment = compose_environment(
        [Checkout("GATEWAY", _checkout(tmp_path), "https://example.test/gateway")],
        environ={},
        timestamp="2026-09-13T00:00:00Z",
    )

    assert environment["GATEWAY_IMAGE_DIGEST"] == "not-supplied"
