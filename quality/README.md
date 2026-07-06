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

## Update Triggers

Update quality docs when thresholds change, new quality evidence is required, an advisory check
becomes blocking, or issue-discovery findings alter the enterprise-readiness posture.
