from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_DIR = REPO_ROOT / ".github" / "workflows"


def test_merged_pr_main_releasability_dispatcher_targets_main_gate() -> None:
    workflow = WORKFLOW_DIR / "merged-pr-main-releasability.yml"
    text = workflow.read_text(encoding="utf-8")

    assert "name: Merged PR Main Releasability Dispatch" in text
    assert "pull_request_target:" in text
    assert "types: [closed]" in text
    assert "actions: write" in text
    assert "contents: write" in text
    assert "github.event.pull_request.merged == true" in text
    assert "github.event.pull_request.base.ref == 'main'" in text
    assert "timeout-minutes: 10" in text
    assert "set -euo pipefail" in text
    assert "gh workflow run main-releasability.yml" in text
    assert "--ref main" not in text
    assert '--ref "$dispatch_ref"' in text
    assert 'dispatch_ref="main-releasability-${revision}"' in text
    assert 'gh api "repos/$GITHUB_REPOSITORY/git/ref/tags/$dispatch_ref"' in text
    assert '-f ref="refs/tags/$dispatch_ref"' in text
    assert '-f sha="$revision"' in text
    assert "Dispatch ref $dispatch_ref points to $existing_ref_sha" in text
    assert "github.event.pull_request.merge_commit_sha" in text
    assert '-f expected_sha="$revision"' in text
    # Every revision the PR put on main is gated, not only the merge SHA
    # (36 of 45 commits over 28-31 Aug were ungated in lotus-report before
    # the sibling fix this ports; rebase-only merging is what makes the
    # enumeration correct, so its assertion must fail loudly on change).
    assert "COMMIT_COUNT: ${{ github.event.pull_request.commits }}" in text
    assert 'git rev-list -n "$COMMIT_COUNT" "$MERGE_COMMIT_SHA" | tac' in text
    assert "for revision in $revisions; do" in text
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
    assert text.index(guard) < text.index('dispatch_ref="main-releasability-${revision}"')
    assert text.index(guard) < text.index('-f ref="refs/tags/$dispatch_ref"')
    assert text.index(guard) < text.index("gh workflow run main-releasability.yml")
    # The guard, tag write, and dispatch must all sit INSIDE the loop body:
    # everything ordered above must come before the loop's closing done.
    loop_end = text.index("\n          done", text.index("for revision in $revisions; do"))
    assert text.index(guard) < loop_end
    assert text.index('-f ref="refs/tags/$dispatch_ref"') < loop_end
    assert text.index("gh workflow run main-releasability.yml") < loop_end


def test_main_releasability_gate_remains_dispatchable_and_main_bound() -> None:
    workflow = WORKFLOW_DIR / "main-releasability.yml"
    text = workflow.read_text(encoding="utf-8")

    assert "name: Main Releasability Gate" in text
    assert "workflow_dispatch:" in text
    assert "expected_sha:" in text
    assert "triggering_pr:" in text
    assert "source_branch:" in text
    assert 'default: "main"' not in text
    assert "LOTUS_RELEASE_SOURCE_BRANCH: ${{ inputs.source_branch || github.ref_name }}" in text
    assert '--build-arg LOTUS_GIT_BRANCH="${LOTUS_RELEASE_SOURCE_BRANCH}"' in text
    assert '--git-branch "${LOTUS_RELEASE_SOURCE_BRANCH}"' in text
    assert "group: ${{ github.workflow }}-${{ github.sha }}" in text
    assert "inputs.expected_sha || github.sha" not in text
    assert "group: ${{ github.workflow }}-${{ github.ref }}" not in text
    assert "git rev-parse HEAD" in text
    assert "  push:\n" not in text
    assert "branches: [ main ]" not in text


def test_operator_guidance_keeps_expected_sha_validation_only() -> None:
    text = (REPO_ROOT / "wiki" / "Validation-and-CI.md").read_text(encoding="utf-8")

    assert "isolated by the checked-out GitHub SHA" in text
    assert "expected_sha` is validation-only" in text
    assert "isolated by the expected merge SHA" not in text


def test_coverage_audit_workflow_runs_the_fail_closed_audit() -> None:
    text = (WORKFLOW_DIR / "main-gate-coverage-audit.yml").read_text(encoding="utf-8")

    assert "schedule:" in text
    assert "workflow_dispatch" in text
    assert "python scripts/audit_main_gate_coverage.py" in text
    assert "--fail-on-gap" in text
