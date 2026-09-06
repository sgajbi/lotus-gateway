"""Revision selection, proved by running the shipped shell against real history.

The dispatcher decides which merged revisions receive a release-gate verdict.
Until now that decision was covered by asserting the workflow file CONTAINED a
particular `git rev-list` command string, which is not evidence about behaviour:
the assertion passes whether or not the command selects the right revisions, and
it fails when the command is corrected. That is how the previous enumeration bug
survived — the test required the defective command by name, so fixing the defect
broke the test.

These cases build real Git histories, execute the step's own shell, and assert on
which revisions it dispatched. `gh` is replaced by a recording stub so nothing
leaves the machine; every other command is the one that ships.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "merged-pr-main-releasability.yml"


def _resolve_bash() -> str | None:
    """A bash that can see the paths this harness uses.

    On Windows `bash` on PATH is often the WSL shim, which runs in a different
    filesystem namespace and fails with execvpe(/bin/bash). Git for Windows ships
    the bash that CI's scripts are written for, so it is located through git
    itself rather than by hardcoding an installation directory -- the same rule
    the documentation convention states: no drive letters, no assumed layout.
    """
    git = shutil.which("git")
    if git:
        git_root = Path(git).resolve().parents[2]
        for candidate in (git_root / "bin" / "bash.exe", git_root / "usr" / "bin" / "bash.exe"):
            if candidate.is_file():
                return str(candidate)
    found = shutil.which("bash")
    if found and "system32" in found.lower():
        return None
    return found


BASH = _resolve_bash()

pytestmark = pytest.mark.skipif(
    BASH is None or shutil.which("git") is None,
    reason="bash and git are required to execute the dispatcher's own shell",
)


def _dispatch_script() -> str:
    """The step's shell, taken from the workflow rather than restated here."""
    document = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    for job in document["jobs"].values():
        for step in job.get("steps", []):
            run = step.get("run", "")
            if "revisions=" in run and "rev-list" in run:
                return run
    raise AssertionError("no step in the dispatcher enumerates revisions")


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _commit(repo: Path, name: str) -> str:
    (repo / name).write_text(f"{name}\n", encoding="utf-8")
    _git(repo, "add", name)
    _git(repo, "commit", "--quiet", "-m", f"add {name}")
    return _git(repo, "rev-parse", "HEAD")


def _new_repo(tmp_path: Path, name: str) -> Path:
    repo = tmp_path / name
    repo.mkdir()
    _git(repo, "init", "--quiet", "--initial-branch=main")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "Test")
    # The step runs `git fetch origin main`, which is part of what is being
    # exercised. Point origin at the repository itself so the fetch is real
    # rather than stubbed away -- a fetch that never runs would hide an
    # enumeration that depends on refs it brings in.
    _git(repo, "remote", "add", "origin", str(repo))
    return repo


def _run_dispatch(
    repo: Path, tmp_path: Path, *, merge_sha: str, base_sha: str, commit_count: int
) -> tuple[int, str, list[str]]:
    """Execute the real step. Returns (exit code, output, dispatched revisions)."""
    bin_dir = tmp_path / f"bin-{merge_sha[:8]}"
    bin_dir.mkdir(exist_ok=True)
    calls = tmp_path / f"gh-calls-{merge_sha[:8]}.txt"
    calls.write_text("", encoding="utf-8")

    # A GET on a dispatch tag must report "absent" so the create path runs; the
    # shipped code tests that by EXIT CODE, never by output, because `gh api
    # --jq` writes a 404 body to stdout and an output test reads it as a SHA.
    stub = bin_dir / "gh"
    stub.write_text(
        "#!/bin/sh\n"
        f'echo "$@" >> "{calls.as_posix()}"\n'
        'case "$*" in\n'
        "  *git/ref/tags/*) exit 1 ;;\n"
        "  *) exit 0 ;;\n"
        "esac\n",
        encoding="utf-8",
        newline="\n",
    )
    stub.chmod(0o755)

    environment = dict(os.environ)
    environment.update(
        {
            "PATH": f"{bin_dir.as_posix()}{os.pathsep}{environment['PATH']}",
            "MERGE_COMMIT_SHA": merge_sha,
            "BASE_SHA": base_sha,
            "COMMIT_COUNT": str(commit_count),
            "PR_NUMBER": "744",
            "GITHUB_REPOSITORY": "sgajbi/lotus-gateway",
            "GH_TOKEN": "stub-token-not-a-credential",
        }
    )

    # Written to a file rather than passed with -c. Windows rebuilds an argument
    # list into a single command string, which mangles a multi-line script's
    # quoting and newlines; a file also matches how Actions runs the step.
    script = tmp_path / f"step-{merge_sha[:8]}.sh"
    script.write_text(_dispatch_script(), encoding="utf-8", newline="\n")

    result = subprocess.run(
        [BASH, str(script)],
        capture_output=True,
        text=True,
        cwd=str(repo),
        env=environment,
    )

    # Read the WORKFLOW DISPATCH calls, not the tag writes. A revision is gated
    # when the gate is asked to run for it; the tag is only how the ref is named,
    # and counting both reports every revision twice.
    dispatched = [
        line.split("expected_sha=", 1)[1].split()[0]
        for line in calls.read_text(encoding="utf-8").splitlines()
        if "workflow run" in line and "expected_sha=" in line
    ]
    return result.returncode, result.stdout + result.stderr, dispatched


def test_a_rebase_that_makes_the_commit_count_stale_still_gates_what_landed(
    tmp_path: Path,
) -> None:
    """The case that broke PR #744.

    pull_request.commits described the branch before it was updated from main.
    Three were reported, two landed. Counting back three from the tip reached
    base.sha itself, and since a commit is its own ancestor the new-to-main guard
    refused the whole dispatch, gating nothing.
    """
    repo = _new_repo(tmp_path, "rebased")
    _commit(repo, "root")
    base = _commit(repo, "base")
    first = _commit(repo, "pr-one")
    second = _commit(repo, "pr-two")

    code, output, dispatched = _run_dispatch(
        repo, tmp_path, merge_sha=second, base_sha=base, commit_count=3
    )

    assert code == 0, output
    assert dispatched == [first, second], "exactly the revisions this PR added, in order"
    assert base not in dispatched, "the base predates the PR and must never be gated"
    assert "::notice::" in output, "a stale count is reported, not hidden"


def test_a_stale_base_that_spans_another_merge_is_refused(tmp_path: Path) -> None:
    """Concurrent main advancement, which the range alone does not solve.

    base.sha is the base branch as of the PR's last synchronisation, not as of
    the merge. When main advances underneath an un-synchronised PR, base..tip
    spans the other merges too. Those revisions are contiguous and single-parent,
    so every structural check passes while the run record would claim another
    PR's work under this PR's number.
    """
    repo = _new_repo(tmp_path, "stale-base")
    _commit(repo, "root")
    base = _commit(repo, "base")
    _commit(repo, "other-pr-one")
    _commit(repo, "other-pr-two")
    mine = _commit(repo, "my-only-commit")

    code, output, dispatched = _run_dispatch(
        repo, tmp_path, merge_sha=mine, base_sha=base, commit_count=1
    )

    assert code != 0, "over-claiming revisions must refuse, not proceed"
    assert dispatched == [], "nothing may be dispatched when the window over-claims"
    assert "did not add" in output or "Refusing" in output, output


def test_a_squash_gates_the_single_revision_that_landed(tmp_path: Path) -> None:
    """A squash reports more commits than it lands, and coverage is still complete.

    Main gains exactly one revision, so exactly one verdict is required. Refusing
    here would leave that landed revision ungated, which is worse than the
    deviation from rebase-only merging. The mismatch is surfaced rather than
    silently accepted.
    """
    repo = _new_repo(tmp_path, "squashed")
    _commit(repo, "root")
    base = _commit(repo, "base")
    squashed = _commit(repo, "everything-at-once")

    code, output, dispatched = _run_dispatch(
        repo, tmp_path, merge_sha=squashed, base_sha=base, commit_count=3
    )

    assert code == 0, output
    assert dispatched == [squashed]
    assert "::notice::" in output, "a squash must be reported, not silently treated as a rebase"


def test_a_true_merge_commit_is_refused(tmp_path: Path) -> None:
    """Per-commit enumeration assumes one parent; a merge commit has two.

    This is the rebase-only rule itself, and it must keep failing loudly. The
    range enumeration made the count-based overshoot impossible, which could
    easily have been mistaken for making this check unnecessary.
    """
    repo = _new_repo(tmp_path, "true-merge")
    _commit(repo, "root")
    base = _commit(repo, "base")
    _git(repo, "checkout", "--quiet", "-b", "side")
    _commit(repo, "side-work")
    _git(repo, "checkout", "--quiet", "main")
    _commit(repo, "main-work")
    _git(repo, "merge", "--quiet", "--no-ff", "-m", "merge side", "side")
    merge_sha = _git(repo, "rev-parse", "HEAD")

    code, output, dispatched = _run_dispatch(
        repo, tmp_path, merge_sha=merge_sha, base_sha=base, commit_count=2
    )

    assert code != 0, "a two-parent merge must be refused"
    assert dispatched == []
    assert "parent" in output.lower(), output


def test_every_landed_revision_is_dispatched_in_ancestry_order(tmp_path: Path) -> None:
    """Coverage and ordering together: no revision skipped, oldest first.

    Ordering matters because a verdict is recorded per revision; dispatching the
    tip first would leave an earlier revision's gate reporting against history
    that already moved past it.
    """
    repo = _new_repo(tmp_path, "ordered")
    _commit(repo, "root")
    base = _commit(repo, "base")
    landed = [_commit(repo, f"pr-{index}") for index in range(1, 5)]

    code, output, dispatched = _run_dispatch(
        repo, tmp_path, merge_sha=landed[-1], base_sha=base, commit_count=4
    )

    assert code == 0, output
    assert dispatched == landed, "every landed revision, oldest first"
