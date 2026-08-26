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

The protected Quality Baseline runs the pinned duplicate-code detector twice from `src/app` with a
`**/*.py` pattern and identical jscpd 4.2.2 options. Each report is checked against
`quality/duplicate_code_baseline.json` for clone count, duplicated lines, duplicated percentage,
and stable source-pair/normalised-fragment occurrence fingerprints, with Python-version-independent
AST scope evidence, canonical source-side selection with reported column boundaries, line-shift-safe
occurrence ordering, and tokenizer-shape-independent f-string spans. The reproducibility checker
also fails when the two reports differ in normalized candidate identities or aggregate metrics.
Incomplete token streams and unmatched delimiters are sent through a comment-safe lexical fallback
that normalizes operator/layout spacing without including interpreter exception-message text in
identity decisions; complete f-string expressions receive the same layout normalization on the
token path while conversion, debug-expression, and format-specification text remains preserved.
The scope digest identifies enclosing
class/function names without hashing mutable scope bodies or adjacent source lines, so blank,
comment, and unrelated statements beside an unchanged clone do not invalidate it. Same-scope
relocation is an explicit identity trade-off; fragment normalization preserves quoted literal
contents and reconstructs f-string spans while collapsing layout whitespace. The protected baseline
and repeated-run evidence are generated and enforced on Ubuntu/Node 20. The repeated-run gate
detects nondeterminism within that authoritative environment; it does not hide or assert
cross-operating-system candidate equivalence, and no union baseline is permitted.
Detector
failure, malformed evidence, or a stale fingerprint after a cleanup fails the quality result;
cleanup improvements must be banked through a reviewed baseline update before the clone can return.
The duplicate-code result is evaluated after the other baseline producers and artifact upload so a
failed ratchet cannot hide the remaining diagnostics.
Duplicate-tool installation failures follow the same deferred-evidence path and remain hard failures
at the final duplicate-ratchet result.
