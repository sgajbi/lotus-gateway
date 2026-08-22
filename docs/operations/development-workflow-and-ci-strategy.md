# Development Workflow and CI Strategy

This repository follows the platform standard for engineering workflow, CI tiering, and merge hygiene.

Canonical standard:
- `lotus-platform/platform-standards/Development-Workflow-and-CI-Strategy-Standard.md`

## Required model
1. Branch from `main` and keep one branch per RFC/slice.
2. Use PR-first delivery (no direct commits to `main`).
3. Keep PR checks fast and meaningful (blocking).
4. Run heavier checks in scheduled/manual/mainline tiers.
5. Merge only with green required checks.
6. Use rebase merge and delete the feature branch after merge.
7. Always finish with `local = remote = main`.

PR auto-merge is rebase-only for linear history. The `Queue Auto Merge` helper uses
`LOTUS_AUTOMERGE_TOKEN` with `gh pr merge --auto --rebase --delete-branch`; when that token is not
available, the helper emits a warning and exits successfully so an authorized human or release actor
can perform the rebase merge without leaving a false red CI check.

Merged PRs into `main` are followed by the `Merged PR Main Releasability Dispatch` workflow, which
creates or reuses an immutable `main-releasability-<merge-sha>` validation tag and dispatches
`main-releasability.yml` through that tag after GitHub reports a closed pull request as merged. The
dispatcher passes `expected_sha=<merge-sha>` and `source_branch=main`, so the workflow validates the
exact merged commit while release metadata, provenance, manifests, and `/version` continue to
describe the mainline source branch instead of the synthetic dispatch tag. This preserves exact-main
Main Releasability evidence across both automated and authorized manual rebase merges without a
mutable-`main` race. Main Releasability concurrency is always keyed by the checked-out GitHub SHA;
`expected_sha` is an assertion rather than a scheduling identity. Reruns for one revision therefore
supersede only that revision, and a malformed manual input cannot cancel evidence for a different
merged commit.
The main releasability workflow is intentionally `workflow_dispatch`-only; the merged-PR dispatcher
is the single automatic post-merge path and prevents duplicate push-triggered and dispatch-triggered
main releasability runs for the same merge.
