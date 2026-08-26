# Quality Baseline event matrix

The Quality Baseline workflow uses one authoritative automated event for feature revisions:
`pull_request` targeting `main`. This keeps the ratcheted quality result attached to the protected
PR check without running the same analysis again when the feature branch is pushed.

| Event | Result | Purpose |
| --- | --- | --- |
| Feature-branch push before a PR exists | No Quality Baseline run | Avoid an unreviewed duplicate; open the PR to request the authoritative check. |
| PR opened or synchronized | One run for the PR head SHA | Produce the protected `Quality Baseline / Ratcheted Trend Gate` check. |
| New commit on an existing PR | One new run for the new head SHA | The concurrency key changes with the revision; stale in-progress work is cancelled. |
| Manual dispatch | One operator-requested run for `github.sha` | Preserve explicit diagnostics or revalidation without changing the PR trigger contract. |

The workflow concurrency group is keyed by the pull-request number, so a newer synchronized
revision cancels stale work from the same PR even though its head SHA changed. Manual dispatch uses
the unique `github.run_id`, so diagnostics cannot cancel or be cancelled by the protected PR check.
Manual dispatch remains available, but it is not a replacement for the protected PR check.

No quality step, threshold, artifact, or ratchet is removed by this event policy.

The protected Quality Baseline also runs the pinned duplicate-code detector over
`src/app/**/*.py`. Its report is checked against `quality/duplicate_code_baseline.json` for clone
count, duplicated lines, duplicated percentage, and stable source-pair/normalised-fragment
occurrence fingerprints, with Python-version-independent AST scope evidence, canonical source-side
selection with reported column boundaries, line-shift-safe occurrence ordering, and
tokenizer-shape-independent f-string spans.
The scope digest identifies enclosing
class/function names without hashing mutable scope bodies or adjacent source lines, so blank,
comment, and unrelated statements beside an unchanged clone do not invalidate it. Same-scope
relocation is an explicit identity trade-off; fragment normalization preserves quoted literal
contents and reconstructs f-string spans while collapsing layout whitespace. The protected baseline
is generated and enforced on
Ubuntu/Node 20; cross-platform detector candidate-selection drift is tracked separately and must
not be hidden by a union baseline.
Detector
failure, malformed evidence, or a stale fingerprint after a cleanup fails the quality result;
cleanup improvements must be banked through a reviewed baseline update before the clone can return.
The duplicate-code result is evaluated after the other baseline producers and artifact upload so a
failed ratchet cannot hide the remaining diagnostics.
Duplicate-tool installation failures follow the same deferred-evidence path and remain hard failures
at the final duplicate-ratchet result.
