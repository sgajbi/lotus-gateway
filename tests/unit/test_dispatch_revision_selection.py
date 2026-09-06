"""Revision selection, proved by running the shipped shell against real history.

The dispatcher decides which merged revisions receive a release-gate verdict.
Until now that decision was covered by asserting the workflow file CONTAINED a
particular `git rev-list` command string, which is not evidence about behaviour:
the assertion passes whether or not the command selects the right revisions, and
it fails when the command is corrected. That is how the previous enumeration bug
survived — the test required the defective command by name, so fixing the defect
broke the test.

These cases build real Git histories, execute the step's own shell, and assert on
which revisions it dispatched. Rebases are simulated by cherry-picking, so the
landed revisions have different SHAs and identical changes, which is what the
step's patch-id attribution has to cope with. `gh` is replaced by a recording
stub so nothing leaves the machine; every other command is the one that ships.
"""

from __future__ import annotations

import itertools
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "merged-pr-main-releasability.yml"
PR_NUMBER = "744"


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
        # Walk up rather than indexing a fixed number of parents: git resolves to
        # `Git\cmd\git.exe` on one installation and `Git\mingw64\bin\git.EXE` on
        # another, so a fixed depth finds the install root on one layout and
        # `C:\Program Files` on the other -- where both candidates miss and the
        # whole suite silently skips in the environment this exists to support.
        for ancestor in Path(git).resolve().parents:
            for relative in (("bin", "bash.exe"), ("usr", "bin", "bash.exe")):
                candidate = ancestor.joinpath(*relative)
                if candidate.is_file():
                    return str(candidate)
    found = shutil.which("bash")
    if found and "system32" in found.lower():
        # The WSL shim runs in a different filesystem namespace and cannot see
        # these paths; skipping is honest, silently using it is not.
        return None
    return found


BASH = _resolve_bash()

pytestmark = pytest.mark.skipif(
    BASH is None or shutil.which("git") is None,
    reason="bash and git are required to execute the dispatcher's own shell",
)


def _dispatch_script() -> str:
    """The step's shell, taken from the workflow rather than restated here.

    Read as a YAML block scalar by hand rather than with a parser: PyYAML is not
    a dependency of this repository and no other test needs one, so adding it to
    read a single literal block would be a dependency bought for one call.
    """
    lines = WORKFLOW.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if line.strip() not in ("run: |", "run: |-"):
            continue
        key_indent = len(line) - len(line.lstrip())
        body: list[str] = []
        body_indent: int | None = None
        for candidate in lines[index + 1 :]:
            if not candidate.strip():
                body.append("")
                continue
            candidate_indent = len(candidate) - len(candidate.lstrip())
            if candidate_indent <= key_indent:
                break
            if body_indent is None:
                body_indent = candidate_indent
            body.append(candidate[body_indent:])
        script = "\n".join(body)
        if "revisions=" in script and "rev-list" in script:
            return script
    raise AssertionError("no step in the dispatcher enumerates revisions")


# Author identity is what attribution matches on, so the harness must control it
# rather than let two commits land in the same second and match by accident.
_AUTHORED_SECONDS = itertools.count(0)


def _git(repo: Path, *args: str, author_date: str | None = None) -> str:
    environment = dict(os.environ)
    if author_date is not None:
        environment["GIT_AUTHOR_DATE"] = author_date
        environment["GIT_COMMITTER_DATE"] = author_date
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        env=environment,
    )
    if result.returncode != 0:
        # check=True raises without the message, which makes a harness failure
        # look like a defect in the code under test.
        raise AssertionError(
            f"git {' '.join(args)} failed ({result.returncode}): "
            f"{(result.stderr or result.stdout).strip()}"
        )
    return result.stdout.strip()


def _next_author_date() -> str:
    """A distinct, ordered author timestamp for each commit the harness makes."""
    return f"2026-01-01T00:00:{next(_AUTHORED_SECONDS):02d}+00:00"


def _commit(repo: Path, name: str, *, body: str | None = None, subject: str | None = None) -> str:
    (repo / name).write_text(body if body is not None else f"{name}\n", encoding="utf-8")
    _git(repo, "add", name)
    _git(
        repo,
        "commit",
        "--quiet",
        "-m",
        subject if subject is not None else f"add {name}",
        author_date=_next_author_date(),
    )
    return _git(repo, "rev-parse", "HEAD")


def _new_repo(tmp_path: Path, name: str) -> Path:
    repo = tmp_path / name
    repo.mkdir()
    _git(repo, "init", "--quiet", "--initial-branch=main")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "Test")
    # The step runs `git fetch origin ...`, which is part of what is being
    # exercised. Point origin at the repository itself so those fetches are real
    # rather than stubbed away.
    _git(repo, "remote", "add", "origin", str(repo))
    return repo


def _publish_pr_head(repo: Path, head: str) -> None:
    """Expose the PR's own commits where the step fetches them from."""
    _git(repo, "update-ref", f"refs/pull/{PR_NUMBER}/head", head)


def _patch_id(repo: Path, commit: str) -> str:
    """The stable patch-id of a commit, as the workflow computes it."""
    show = subprocess.run(["git", "-C", str(repo), "show", commit], capture_output=True, check=True)
    result = subprocess.run(
        ["git", "-C", str(repo), "patch-id", "--stable"],
        input=show.stdout,
        capture_output=True,
        check=True,
    )
    return result.stdout.decode().split(" ")[0]


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
            "PR_NUMBER": PR_NUMBER,
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

    The landed revisions are cherry-picks, so their SHAs differ from the PR's
    while their changes are identical -- which is exactly what a rebase produces
    and what attribution has to accept.
    """
    repo = _new_repo(tmp_path, "rebased")
    _commit(repo, "root")
    base = _commit(repo, "base")

    _git(repo, "checkout", "--quiet", "-b", "pr")
    kept_one = _commit(repo, "pr-one")
    kept_two = _commit(repo, "pr-two")
    _commit(repo, "pr-dropped")
    _publish_pr_head(repo, _git(repo, "rev-parse", "HEAD"))

    _git(repo, "checkout", "--quiet", "main")
    _git(repo, "cherry-pick", kept_one, kept_two)
    landed = _git(repo, "rev-list", "--reverse", f"{base}..HEAD").split()

    code, output, dispatched = _run_dispatch(
        repo, tmp_path, merge_sha=landed[-1], base_sha=base, commit_count=3
    )

    assert code == 0, output
    assert dispatched == landed, "exactly the revisions this PR added, in order"
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

    _git(repo, "checkout", "--quiet", "-b", "pr")
    mine = _commit(repo, "my-only-commit")
    _publish_pr_head(repo, mine)

    _git(repo, "checkout", "--quiet", "main")
    _commit(repo, "other-pr-one")
    _commit(repo, "other-pr-two")
    _git(repo, "cherry-pick", mine)
    tip = _git(repo, "rev-parse", "HEAD")

    code, output, dispatched = _run_dispatch(
        repo, tmp_path, merge_sha=tip, base_sha=base, commit_count=1
    )

    assert code != 0, "over-claiming revisions must refuse, not proceed"
    assert dispatched == [], "nothing may be dispatched when the window over-claims"
    assert "did not add" in output or "Refusing" in output, output


def test_a_squash_is_refused_because_its_change_is_not_the_prs(tmp_path: Path) -> None:
    """A squash contradicts the rebase-only rule and must fail closed.

    Both a squash and a legitimate rebase land fewer revisions than
    pull_request.commits reports, so the count cannot separate them. The change
    can: a rebase preserves each commit's patch, while a squash combines them
    into one whose patch matches no individual commit of the PR.

    Refusing leaves that landed revision ungated, which the fail-closed coverage
    audit reports. A dispatcher that quietly gated it would absorb the
    merge-method drift and leave nothing to notice it.
    """
    repo = _new_repo(tmp_path, "squashed")
    _commit(repo, "root")
    base = _commit(repo, "base")

    _git(repo, "checkout", "--quiet", "-b", "pr")
    _commit(repo, "part-one")
    _commit(repo, "part-two")
    _publish_pr_head(repo, _git(repo, "rev-parse", "HEAD"))

    _git(repo, "checkout", "--quiet", "main")
    (repo / "part-one").write_text("part-one\n", encoding="utf-8")
    (repo / "part-two").write_text("part-two\n", encoding="utf-8")
    _git(repo, "add", "part-one", "part-two")
    # A squash is a new authoring act: its own date, and a combined change that
    # matches no single commit of the PR.
    _git(
        repo,
        "commit",
        "--quiet",
        "-m",
        "Add both parts (#744)",
        author_date=_next_author_date(),
    )
    squashed = _git(repo, "rev-parse", "HEAD")

    code, output, dispatched = _run_dispatch(
        repo, tmp_path, merge_sha=squashed, base_sha=base, commit_count=2
    )

    assert code != 0, "squash-merging contradicts the rebase-only rule and must fail closed"
    assert dispatched == [], "nothing may be dispatched when the merge method is not a rebase"
    assert "matches no commit" in output, output


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
    _publish_pr_head(repo, _git(repo, "rev-parse", "HEAD"))
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


def test_offsetting_count_mismatches_are_refused(tmp_path: Path) -> None:
    """Main advances by one while the rebase drops one, so the counts cancel.

    The range then holds an unrelated revision plus the remaining PR commits, and
    enumerated_count equals pull_request.commits. Every structural check passes,
    so without attributing revisions to the PR by their CHANGE this dispatches
    another PR's work under this PR's number.
    """
    repo = _new_repo(tmp_path, "offsetting")
    _commit(repo, "root")
    base = _commit(repo, "base")

    _git(repo, "checkout", "--quiet", "-b", "pr")
    kept_one = _commit(repo, "pr-kept-one")
    kept_two = _commit(repo, "pr-kept-two")
    _commit(repo, "pr-dropped")
    _publish_pr_head(repo, _git(repo, "rev-parse", "HEAD"))

    _git(repo, "checkout", "--quiet", "main")
    _commit(repo, "unrelated-main-advance")
    _git(repo, "cherry-pick", kept_one, kept_two)
    tip = _git(repo, "rev-parse", "HEAD")

    code, output, dispatched = _run_dispatch(
        repo, tmp_path, merge_sha=tip, base_sha=base, commit_count=3
    )

    assert code != 0, "an offsetting mismatch must still refuse"
    assert dispatched == [], "no revision may be dispatched from an unattributable window"
    assert "matches no commit" in output, output


def test_a_duplicate_subject_cannot_admit_an_unrelated_revision(tmp_path: Path) -> None:
    """A subject is not an identity, and sharing one must not attribute a revision.

    An unrelated main commit titled the same as one of the PR's commits makes a
    completely different change and was authored by a different act. Attribution
    matches on the change or on the author identity a rebase preserves exactly,
    never on subject text, so this window is refused rather than dispatched under
    the wrong PR.
    """
    repo = _new_repo(tmp_path, "duplicate-subject")
    _commit(repo, "root")
    base = _commit(repo, "base")

    _git(repo, "checkout", "--quiet", "-b", "pr")
    pr_fix = _commit(repo, "app.py", body="import os\n", subject="fix lint")
    _publish_pr_head(repo, pr_fix)

    _git(repo, "checkout", "--quiet", "main")
    # Same headline, different change, different author act: a commit from a
    # merge that landed underneath this PR.
    _commit(repo, "other.py", body="import sys\n", subject="fix lint")
    _git(repo, "cherry-pick", pr_fix)
    tip = _git(repo, "rev-parse", "HEAD")

    code, output, dispatched = _run_dispatch(
        repo, tmp_path, merge_sha=tip, base_sha=base, commit_count=2
    )

    assert code != 0, "a same-titled unrelated revision must not be attributed to this PR"
    assert dispatched == [], "nothing may be dispatched from a window holding foreign work"
    assert "matches no commit" in output, output


def test_every_landed_revision_is_dispatched_in_ancestry_order(tmp_path: Path) -> None:
    """Coverage and ordering together: no revision skipped, oldest first.

    Ordering matters because a verdict is recorded per revision; dispatching the
    tip first would leave an earlier revision's gate reporting against history
    that already moved past it.
    """
    repo = _new_repo(tmp_path, "ordered")
    _commit(repo, "root")
    base = _commit(repo, "base")

    _git(repo, "checkout", "--quiet", "-b", "pr")
    pr_commits = [_commit(repo, f"pr-{index}") for index in range(1, 5)]
    _publish_pr_head(repo, _git(repo, "rev-parse", "HEAD"))

    _git(repo, "checkout", "--quiet", "main")
    _git(repo, "cherry-pick", *pr_commits)
    landed = _git(repo, "rev-list", "--reverse", f"{base}..HEAD").split()

    code, output, dispatched = _run_dispatch(
        repo, tmp_path, merge_sha=landed[-1], base_sha=base, commit_count=4
    )

    assert code == 0, output
    assert dispatched == landed, "every landed revision, oldest first"
    assert len(dispatched) == 4


def test_a_rebase_over_changed_context_is_still_attributed(tmp_path: Path) -> None:
    """patch-id is not rebase-stable, and the subject carries the match.

    `git patch-id --stable` is stable across git versions and hunk ordering, not
    across content: the id hashes the diff including its context lines. When main
    changes a line near the PR's change, the cleanly rebased commit hashes
    differently from the original. Requiring patch-id alone would refuse this
    legitimate rebase and dispatch nothing -- the coverage hole this enumeration
    exists to close, arriving by a stricter route.
    """
    # Separation of three lines, measured: closer conflicts, further leaves the
    # patch-id unchanged because patch-id ignores line numbers. At three the
    # rebase is clean AND main's line sits inside the PR hunk's recorded context.
    original = [f"line{number}\n" for number in range(1, 41)]
    pr_lines = list(original)
    pr_lines[9] = "PR_CHANGE\n"
    main_lines = list(original)
    main_lines[12] = "MAIN_CHANGE\n"

    repo = _new_repo(tmp_path, "changed-context")
    _commit(repo, "root")
    base = _commit(repo, "module.py", body="".join(original), subject="add module")

    _git(repo, "checkout", "--quiet", "-b", "pr")
    pr_change = _commit(
        repo,
        "module.py",
        body="".join(pr_lines),
        subject="rewrite line 10",
    )
    _publish_pr_head(repo, pr_change)

    _git(repo, "checkout", "--quiet", "main")
    # main's own change is NOT part of the PR, so the base moves with it -- which
    # is what GitHub records when the PR is re-synchronised before merging. The
    # window is then exactly the rebased commit.
    base = _commit(
        repo,
        "module.py",
        body="".join(main_lines),
        subject="rewrite line 13",
    )
    _git(repo, "cherry-pick", pr_change)
    landed_tip = _git(repo, "rev-parse", "HEAD")

    original_id = _patch_id(repo, pr_change)
    landed_id = _patch_id(repo, landed_tip)
    assert original_id != landed_id, (
        "this case is only meaningful if the rebase changed the patch-id; "
        "if git ever makes these equal the case must be rebuilt"
    )

    code, output, dispatched = _run_dispatch(
        repo, tmp_path, merge_sha=landed_tip, base_sha=base, commit_count=1
    )

    assert code == 0, output
    assert landed_tip in dispatched, "a legitimate rebase must still be gated"
