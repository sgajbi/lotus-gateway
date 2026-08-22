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
    assert 'dispatch_ref="main-releasability-${MERGE_COMMIT_SHA}"' in text
    assert 'gh api "repos/$GITHUB_REPOSITORY/git/ref/tags/$dispatch_ref"' in text
    assert '-f ref="refs/tags/$dispatch_ref"' in text
    assert '-f sha="$MERGE_COMMIT_SHA"' in text
    assert "Dispatch ref $dispatch_ref points to $existing_ref_sha" in text
    assert "github.event.pull_request.merge_commit_sha" in text
    assert '-f expected_sha="$MERGE_COMMIT_SHA"' in text
    assert '-f triggering_pr="$PR_NUMBER"' in text
    assert '-f source_branch="main"' in text


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
