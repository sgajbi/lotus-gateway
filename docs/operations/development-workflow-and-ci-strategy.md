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
dispatches `main-releasability.yml` from governed `main` after GitHub reports a closed pull request
as merged. It passes `expected_sha=<merge-sha>` with
`source_branch=main`. The workflow definition is therefore governed main, while every job checks
out and validates the exact merged source. Release metadata, provenance, manifests, and `/version`
record their distinct evaluated-source and workflow-definition identities. This preserves exact-main
Main Releasability evidence across both automated and authorized manual rebase merges without a
mutable-`main` race. Main Releasability concurrency is keyed by the evaluated source SHA;
`expected_sha` identifies the evaluated source and the scheduling identity. The dispatcher invokes
the workflow from `main`, so GitHub reads the governed workflow definition, then every release-gate
checkout pins to that immutable source SHA. The first job proves it remains an ancestor of freshly
fetched `main` and records it separately from the workflow-definition SHA. Reruns for one revision
therefore supersede only that revision, while a malformed input is refused before release evidence
is emitted.
The main releasability workflow is intentionally `workflow_dispatch`-only; the merged-PR dispatcher
is the single automatic post-merge path and prevents duplicate push-triggered and dispatch-triggered
main releasability runs for the same merge.

Duplicate-code regression protection is deliberate in both release authorities. The required
Quality Baseline check owns pull-request enforcement after collecting its full diagnostic artifact
set. Main Releasability then runs the same pinned `make duplicate-code` detector, versioned
baseline ratchet, and repeated-run reproducibility check after exact-revision assertion. Its
`main-duplicate-code-evidence` artifact preserves the merged-SHA detector output; neither lane is a
substitute for the other. The Main Releasability container job depends on the duplicate-code job,
so registry push, signing, and provenance side effects cannot begin for a revision that fails the
ratchet.
