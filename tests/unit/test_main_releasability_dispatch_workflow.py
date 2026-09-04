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
    assert '"$merge_methods" != "false,false,true"' in text
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
    assert text.index("for revision in $revisions; do") < text.index(guard)
    assert text.index(guard) < text.index('dispatch_ref="main-releasability-${revision}"')
    assert text.index(guard) < text.index('-f ref="refs/tags/$dispatch_ref"')
    assert text.index(guard) < text.index("gh workflow run main-releasability.yml")


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
