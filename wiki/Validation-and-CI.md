# Validation and CI

## Lane model

`lotus-gateway` uses:

1. `Remote Feature Lane`
2. `Pull Request Merge Gate`
3. `Main Releasability Gate`
4. platform-facing validation for cross-app experience changes
5. `Quality Baseline`
   report-only evidence for progressive enterprise-readiness gates

## Local command mapping

- `make check`
  lint, typecheck, OpenAPI contract proof, unit tests
- `make ci`
  migration smoke, integration tests, coverage, security audit
- `make ci-local`
  local feature-lane validation
- `make ci-local-docker`
  Docker parity for the integration boundary

## What the gates protect

- workbench-facing contract integrity
- startup and migration truth
- upstream composition safety
- live integration-boundary parity

## Quality baseline lane

The Quality Baseline workflow is report-only. It installs the optional `quality` dependency group
and records evidence for:

- complexity and maintainability through `radon` and `xenon`
- high-confidence dead-code candidates through `vulture`
- dependency hygiene through `deptry`
- security findings through `bandit` and `pip-audit`
- import-boundary contracts through `import-linter`
- docstring baseline through `interrogate`
- OpenAPI governance through Spectral and `.spectral.yaml`

The lane must not replace `make check` or `make ci`. It exists to classify current baseline
findings, then promote only agreed no-new-regression checks into blocking Feature Lane and PR Merge
Gate enforcement.

Current baseline truth lives in:

- [quality/baseline_report.md](../quality/baseline_report.md)
- [quality/quality_scorecard.md](../quality/quality_scorecard.md)
- [quality/architecture_rules.md](../quality/architecture_rules.md)
- [quality/api_governance_rules.md](../quality/api_governance_rules.md)

Latest enterprise-hardening evidence: the portfolio exception-summary extraction lowered the
repository longest-function baseline from 133 lines to 127 lines and reduced
`portfolio_service.py` from 2,839 lines to 2,744 lines while preserving focused portfolio insight
and router contract tests. The performance workspace capability-input extraction then lowered the
repository longest-function baseline from 127 lines to 119 lines while adding focused capability
input, history-date, and aggregate-only fallback tests. The current branch batch further lowered
the repository longest-function baseline from 119 lines to 99 lines, reduced
`portfolio_service.py` from 2,744 lines to 2,700 lines, added focused portfolio insight-rule tests,
and passed `make check` with 967 unit/contract tests. The latest focused batch split DPM
exception-summary workflow orchestration, advisor-brief source talking points, advisor-brief
review actions, and portfolio workflow actions, lowering the repository longest-function baseline
from 99 lines to 88 lines. `portfolio_service.py` is now 2,750 lines because empty-portfolio
workflow actions are explicit governed data rather than inline control-flow literals. The
Workbench performance snapshot parser split then lowered the repository longest-function baseline
from 88 lines to 87 lines.
