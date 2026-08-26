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
Run `make duplicate-code` for the pinned production-source duplicate-code detector and ratchet.
The protected baseline is generated and enforced on the Ubuntu/Node 20 Quality Baseline lane.
Node 20 through Node 24 can install and run the diagnostic detector, but do not initialize or
update the checked-in baseline from another operating system or runtime: the detector input is
rooted at `src/app` for stable traversal, but jscpd can still choose a different member of an
equivalent clone family across environments. Use hosted Quality Baseline evidence for baseline
changes until the cross-platform reproducibility follow-up is closed. Node 25+ is rejected by the
strict engine policy until the detector is revalidated and the supported range is deliberately
extended.

## Update Triggers

Update quality docs when thresholds change, new quality evidence is required, an advisory check
becomes blocking, or issue-discovery findings alter the enterprise-readiness posture.
