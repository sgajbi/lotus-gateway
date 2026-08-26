# Quality Guide

## Responsibility

`quality/` owns Gateway enterprise-readiness baseline evidence, architecture rules, API governance
rules, and scorecards used to ratchet maintainability without hiding known gaps.

## Boundary Rules

| Area | Rule | Evidence |
| --- | --- | --- |
| Baseline | Keep baseline reports truthful and tied to generated evidence. | `quality/baseline_report.md` |
| Scorecard | Update scorecards when gates, thresholds, or issue-discovery posture changes. | `quality/quality_scorecard.md` |
| Architecture | Architecture rules should reinforce router/service/client boundaries. | `quality/architecture_rules.md` |
| CI signal | Promote only deterministic, low-noise checks into blocking lanes. | `wiki/Validation-and-CI.md` |

## Validation

Run `make lint` for refactor thresholds, workflow runtime governance, agent quality evidence, and
folder-guide validation. Run quality-baseline workflow evidence checks before relying on reports.
Run `make duplicate-code` for the pinned production-source duplicate-code detector, ratchet, and
repeated-run candidate-set check. The protected baseline is generated and enforced on the Ubuntu /
Node 20 Quality Baseline lane, which runs the detector twice with identical inputs and fails closed
on candidate or metric drift. Node 20 through Node 24 can install and run the same local check, but
do not initialize or update the checked-in baseline from another operating system or runtime:
cross-operating-system equivalence is not claimed by the repeated-run check. Use
`make duplicate-code-protected` when the host runtime selects different candidates; it provisions
the pinned Linux/Node 20 fallback in a checkout-specific Compose project and runs the same ratchet
and repeated-run proof. It mounts the checkout read-only at a dedicated source root, keeps writable
dependency and output volumes outside that mount, and copies the scan report before teardown into
a run-unique caller-created `output/duplicate-code-protected/` directory, so native-Linux runs do not leave root-owned artifacts
while mismatch diagnostics remain available. Use hosted Quality Baseline evidence for reviewed baseline changes. Node
25+ is rejected by the strict engine policy until the detector is revalidated and the supported
range is deliberately extended.

## Update Triggers

Update quality docs when thresholds change, new quality evidence is required, an advisory check
becomes blocking, or issue-discovery findings alter the enterprise-readiness posture.
