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
input, history-date, and aggregate-only fallback tests. That branch batch further lowered
the repository longest-function baseline from 119 lines to 99 lines, reduced
`portfolio_service.py` from 2,744 lines to 2,700 lines, added focused portfolio insight-rule tests,
and passed `make check` with 967 unit/contract tests. The latest focused batch split DPM
exception-summary workflow orchestration, advisor-brief source talking points, advisor-brief
review actions, and portfolio workflow actions, lowering the repository longest-function baseline
from 99 lines to 88 lines. That batch put `portfolio_service.py` at 2,750 lines because
empty-portfolio workflow actions became explicit governed data rather than inline control-flow
literals. The
Workbench performance snapshot parser split then lowered the repository longest-function baseline
from 88 lines to 87 lines. Horizon comparison row-field extraction then lowered the repository
longest-function baseline from 87 lines to 85 lines. Performance workspace summary parsing and
evidence-view mapping splits then lowered the repository longest-function baseline from 85 lines
to 84 lines. Foundation workspace response assembly, PM operating quality summary orchestration,
and risk attribution supportability splits then lowered the repository longest-function baseline
from 84 lines to 82 lines, with `portfolio_service.py` then measured at 2,621 lines. The DPM PM
quality summary context now uses the specific PM operating quality supportability contract type,
keeping the Feature Lane mypy gate green. Attribution trend row parsing, portfolio position
parsing, and performance workspace request-context splits then lowered the repository
longest-function baseline from 82 lines to 80 lines, with `portfolio_service.py` currently
measured at 2,617 lines. Advisor-brief route dependency, portfolio performance snapshot query,
risk drawdown orchestration, core snapshot summary parsing, portfolio workspace response-component,
risk attribution route query, and performance summary route dependency splits then lowered the
repository longest-function baseline from 80 lines to 76 lines. Shell workspace descriptor-state
and rebalance supportability failure-recording splits then lowered the baseline from 76 lines to
74 lines. The 50-commit enterprise-hardening branch then split shared analytics async polling,
workspace-summary payload assembly, portfolio transaction-summary context loading, transaction
page loading, and portfolio book response assembly, lowering the baseline to 62 lines.
`portfolio_service.py` is now measured at 2,076 lines after portfolio liquidity loading,
transaction request-context, transaction page-context, transaction client-kwargs, portfolio
workspace response assembly, portfolio workspace performance parsing, and portfolio workspace
rebalance parsing, portfolio source-readiness parsing, portfolio transaction summary mapping, and
portfolio workflow mapping extractions. The largest-file hotspot has moved to the portfolio
contract module at 2,226 lines.
`performance_workspace_service.py` is now measured at 1,607 lines after response assembly
extraction. The current longest-function baseline is 49 lines. Local `make check` for the current
portfolio workflow mapper branch passed with ruff, format check, monetary-float guard, mypy over
454 source files, Workbench/OpenAPI contract smoke, and 1,031 unit/contract tests. Local
`make ci` passed with 207 integration tests, 1,238 coverage tests, 94.00 percent total coverage,
and `pip-audit` reporting no known vulnerabilities after the governed FastAPI/Starlette exception.
GitHub Feature Lane, PR Merge Gate, Quality Baseline, Docker build, and Docker parity checks were
green before PR #358 merged. The current portfolio workflow mapper branch adds focused workflow
mapper and portfolio service evidence with 46 passing unit tests.
