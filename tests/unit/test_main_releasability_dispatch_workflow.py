from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_DIR = REPO_ROOT / ".github" / "workflows"


def _git_bash() -> str | None:
    """Find the Bash that can execute Actions' shipped shell on this host."""
    git = shutil.which("git")
    if git:
        for ancestor in Path(git).resolve().parents:
            for relative in (("bin", "bash.exe"), ("usr", "bin", "bash.exe")):
                candidate = ancestor.joinpath(*relative)
                if candidate.is_file():
                    return str(candidate)
    bash = shutil.which("bash")
    return None if bash and "system32" in bash.lower() else bash


def _assertion_script() -> str:
    """Read the exact assertion body from the shipped workflow, not a copy."""
    lines = (WORKFLOW_DIR / "main-releasability.yml").read_text(encoding="utf-8").splitlines()
    start = next(
        index
        for index, line in enumerate(lines)
        if line.strip() == "- name: Assert expected merged PR SHA"
    )
    run_index = next(
        index for index in range(start, len(lines)) if lines[index].strip() == "run: |"
    )
    key_indent = len(lines[run_index]) - len(lines[run_index].lstrip())
    body: list[str] = []
    body_indent: int | None = None
    for line in lines[run_index + 1 :]:
        if not line.strip():
            body.append("")
            continue
        indent = len(line) - len(line.lstrip())
        if indent <= key_indent:
            break
        if body_indent is None:
            body_indent = indent
        body.append(line[body_indent:])
    return "\n".join(body)


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=False
    )
    if result.returncode:
        raise AssertionError(result.stderr or result.stdout)
    return result.stdout.strip()


def _source_proof_repo(tmp_path: Path) -> tuple[Path, str, str]:
    repo = tmp_path / "source-proof"
    repo.mkdir()
    _git(repo, "init", "--quiet", "--initial-branch=main")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "Test")
    (repo / "main.txt").write_text("main\n", encoding="utf-8")
    _git(repo, "add", "main.txt")
    _git(repo, "commit", "--quiet", "-m", "main")
    accepted = _git(repo, "rev-parse", "HEAD")
    _git(repo, "checkout", "--quiet", "-b", "off-main")
    (repo / "off-main.txt").write_text("off-main\n", encoding="utf-8")
    _git(repo, "add", "off-main.txt")
    _git(repo, "commit", "--quiet", "-m", "off-main")
    rejected = _git(repo, "rev-parse", "HEAD")
    _git(repo, "remote", "add", "origin", str(repo))
    return repo, accepted, rejected


@pytest.mark.skipif(_git_bash() is None, reason="Git Bash is required to execute the shipped guard")
def test_source_pinned_assertion_accepts_main_ancestry_and_refuses_off_main_sha(
    tmp_path: Path,
) -> None:
    """Execute the shipped source guard against real Git history, both ways."""
    repo, accepted, rejected = _source_proof_repo(tmp_path)
    bash = _git_bash()
    assert bash is not None
    script = tmp_path / "assert-source.sh"
    script.write_text(_assertion_script(), encoding="utf-8", newline="\n")

    environment = dict(os.environ)
    environment.update({"GITHUB_SHA": "workflow-definition-sha", "TRIGGERING_PR": "754"})

    _git(repo, "checkout", "--quiet", accepted)
    environment["EXPECTED_SHA"] = accepted
    valid = subprocess.run(
        [bash, str(script)], cwd=repo, env=environment, capture_output=True, text=True
    )
    assert valid.returncode == 0, valid.stderr or valid.stdout
    assert "ancestor of main" in valid.stdout

    _git(repo, "checkout", "--quiet", rejected)
    environment["EXPECTED_SHA"] = rejected
    invalid = subprocess.run(
        [bash, str(script)], cwd=repo, env=environment, capture_output=True, text=True
    )
    assert invalid.returncode != 0
    assert "not an ancestor of freshly fetched main" in invalid.stdout


def test_merged_pr_main_releasability_dispatcher_targets_main_gate() -> None:
    workflow = WORKFLOW_DIR / "merged-pr-main-releasability.yml"
    text = workflow.read_text(encoding="utf-8")

    assert "name: Merged PR Main Releasability Dispatch" in text
    assert "pull_request_target:" in text
    assert "types: [closed]" in text
    assert "actions: write" in text
    assert "contents: read" in text
    assert "github.event.pull_request.merged == true" in text
    assert "github.event.pull_request.base.ref == 'main'" in text
    assert "timeout-minutes: 10" in text
    assert "set -euo pipefail" in text
    assert "gh workflow run main-releasability.yml" in text
    assert "--ref main" in text
    assert "dispatch_ref=" not in text
    assert "repos/$GITHUB_REPOSITORY/git/refs" not in text
    assert "github.event.pull_request.merge_commit_sha" in text
    assert '-f expected_sha="$revision"' in text
    # Every revision the PR put on main is gated, not only the merge SHA
    # (36 of 45 commits over 28-31 Aug were ungated in lotus-report before
    # the sibling fix this ports; rebase-only merging is what makes the
    # enumeration correct, so its assertion must fail loudly on change).
    assert "COMMIT_COUNT: ${{ github.event.pull_request.commits }}" in text
    # WHICH revisions get selected is proved by executing this step against real
    # Git histories in test_dispatch_revision_selection.py, not asserted here.
    # This file previously required the enumeration command by name, which is a
    # test that passes whether or not the command selects correctly and fails
    # when it is corrected -- it pinned the defective walk as the contract, so
    # fixing the defect broke the test. Behaviour belongs where it can be run.
    assert "BASE_SHA: ${{ github.event.pull_request.base.sha }}" in text
    assert "fetch-depth: 0" in text
    # Rebase-only merging is what makes the enumeration correct, and it is
    # MEASURED on the commits rather than read from the repository's declared
    # merge settings: that read needs a permission the workflow token may not
    # hold, and a declared posture is weaker evidence than the history it
    # predicts. Each invariant kills a distinct way the window can be wrong.
    assert "allow_rebase_merge" not in text, (
        "the settings read is the dependency this replaced; measuring the "
        "invariant needs no token at all"
    )
    # A merge commit's second parent would send the walk into main's history.
    assert 'merge_parents="$(git rev-list --parents -n 1 "$MERGE_COMMIT_SHA" | wc -w)"' in text
    # The validation pass must not reuse $revision: the ordering checks below
    # locate the dispatch loop by that header.
    assert "for candidate in $revisions; do" in text
    assert '[ "$merge_parents" -ne 2 ]' in text
    # A squash lands one commit however many the PR held, so the walk would
    # return commits earlier PRs put on main. Those are single-parent and
    # contiguous, so only base-ancestry catches them.
    assert "BASE_SHA: ${{ github.event.pull_request.base.sha }}" in text
    assert 'git merge-base --is-ancestor "$candidate" "$BASE_SHA"' in text
    assert '[ -z "$BASE_SHA" ]' in text, "an absent base must refuse, not skip the check"
    # A gap would mean the walk crossed history the PR did not add.
    assert 'actual_parent="$(git rev-parse "${candidate}^")"' in text
    assert '[ "$actual_parent" != "$previous" ]' in text
    # Each gh call names itself on failure: a bare 403 identifies neither the
    # operation nor its permission, which is what made three dispatcher
    # failures across two repositories unattributable.
    assert "run_gh()" in text
    assert 'output="$("$@" 2>&1)" || status=$?' in text, (
        "`if !` inverts the result, so $? inside the branch is the negation's 0 "
        "and every diagnostic reads 'exit 0'; `|| status=$?` captures the real "
        "status and still keeps set -e from aborting first"
    )
    assert '-f sha="$revision" >/dev/null' not in text, (
        "a redirect on the run_gh call applies to the whole function, including "
        "its ::error:: line, so the diagnostic vanishes exactly when it fires"
    )
    assert '-f triggering_pr="$PR_NUMBER"' in text
    assert '-f source_branch="main"' in text
    # Ancestry is judged against the freshly fetched main, and a revision that
    # is not main history is refused BEFORE any tag is created or gate
    # dispatched: the guard must sit inside the loop, after the detach onto
    # FETCH_HEAD and ahead of both the tag write and the workflow dispatch.
    assert "git checkout --quiet --detach FETCH_HEAD" in text
    guard = 'if ! git merge-base --is-ancestor "$revision" HEAD; then'
    assert guard in text
    assert text.index("git fetch origin main --quiet") < text.index(
        "git checkout --quiet --detach FETCH_HEAD"
    )
    assert text.index("git checkout --quiet --detach FETCH_HEAD") < text.index(
        "for revision in $revisions; do"
    )
    assert text.index("for revision in $revisions; do") < text.index(guard)
    assert text.index(guard) < text.index("gh workflow run main-releasability.yml")
    # The guard and dispatch must both sit INSIDE the loop body:
    # everything ordered above must come before the loop's closing done.
    loop_end = text.index("\n          done", text.index("for revision in $revisions; do"))
    assert text.index(guard) < loop_end
    assert text.index("gh workflow run main-releasability.yml") < loop_end


def test_main_releasability_gate_remains_dispatchable_and_main_bound() -> None:
    workflow = WORKFLOW_DIR / "main-releasability.yml"
    text = workflow.read_text(encoding="utf-8")

    assert "name: Main Releasability Gate" in text
    assert "run-name: Main Releasability · ${{ inputs.expected_sha || github.sha }}" in text
    assert "workflow_dispatch:" in text
    assert "expected_sha:" in text
    assert "triggering_pr:" in text
    assert "source_branch:" in text
    assert 'default: "main"' not in text
    evaluated_ref = "${{ inputs.expected_sha || github.sha }}"
    assert "LOTUS_RELEASE_SOURCE_BRANCH: ${{ inputs.source_branch || github.ref_name }}" in text
    assert f"EVALUATED_SHA: {evaluated_ref}" in text
    assert "WORKFLOW_DEFINITION_SHA: ${{ github.sha }}" in text
    assert f"IMAGE_TAG: {evaluated_ref}" in text
    assert text.count("uses: actions/checkout@v6") == 8
    assert text.count(f"ref: {evaluated_ref}") == 8
    assert 'git merge-base --is-ancestor "$EXPECTED_SHA" FETCH_HEAD' in text
    assert "Workflow definition SHA: ${GITHUB_SHA}" in text
    assert '--build-arg LOTUS_GIT_BRANCH="${LOTUS_RELEASE_SOURCE_BRANCH}"' in text
    assert '--git-branch "${LOTUS_RELEASE_SOURCE_BRANCH}"' in text
    assert "group: ${{ github.workflow }}-${{ inputs.expected_sha || github.sha }}" in text
    assert '"sha1": "${WORKFLOW_DEFINITION_SHA}"' in text
    assert '"sha1": "${EVALUATED_SHA}"' in text
    assert '--build-arg LOTUS_GIT_COMMIT_SHA="${EVALUATED_SHA}"' in text
    assert '--git-commit-sha "${EVALUATED_SHA}"' in text
    assert "group: ${{ github.workflow }}-${{ github.sha }}" not in text
    assert "group: ${{ github.workflow }}-${{ github.ref }}" not in text
    assert "git rev-parse HEAD" in text
    assert "  push:\n" not in text
    assert "branches: [ main ]" not in text


def test_operator_guidance_explains_source_pinned_dispatch() -> None:
    text = (REPO_ROOT / "wiki" / "Validation-and-CI.md").read_text(encoding="utf-8")

    assert "isolated by the evaluated source SHA" in text
    assert "every checkout is pinned to `expected_sha`" in text
    assert "workflow-definition SHA" in text


def test_coverage_audit_workflow_runs_the_fail_closed_audit() -> None:
    text = (WORKFLOW_DIR / "main-gate-coverage-audit.yml").read_text(encoding="utf-8")

    assert "schedule:" in text
    assert "workflow_dispatch" in text
    assert "python scripts/audit_main_gate_coverage.py" in text
    assert "--fail-on-gap" in text
