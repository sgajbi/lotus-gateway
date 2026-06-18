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
  lint, monetary-float governance, refactor thresholds, workflow action-runtime governance,
  typecheck, OpenAPI contract proof, unit tests
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
- CI action-runtime compatibility with the platform baseline:
  `actions/checkout@v6`, `actions/setup-python@v6`, `actions/setup-node@v5`, and
  `actions/upload-artifact@v7`
- Workflow-level Node 24 JavaScript action runtime opt-in through
  `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24`

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
At that point, `portfolio_service.py` was measured at 2,079 lines after portfolio liquidity loading,
transaction request-context, transaction page-context, transaction client-kwargs, portfolio
workspace response assembly, portfolio workspace performance parsing, and portfolio workspace
rebalance parsing, portfolio source-readiness parsing, portfolio transaction summary mapping, and
portfolio workflow mapping extractions. `portfolio.py` was measured at 1,464 lines after
workflow/readiness, transaction-ledger, performance snapshot, and income/activity contract
extractions, and 954 lines after the holdings/book contract extraction.
`performance_workspace_service.py` was measured at 1,704 lines after response assembly
extraction. The current longest-function baseline is 49 lines. Local `make check` for the current
portfolio holdings contract branch passed with ruff, format check, monetary-float guard, mypy over
461 source files, Workbench/OpenAPI contract smoke, and 1,039 unit/contract tests. Local `make ci`
passed with 207 integration tests, 1,246 coverage tests, 94.02 percent total coverage,
and `pip-audit` reporting no known vulnerabilities after the governed FastAPI/Starlette exception.
GitHub Feature Lane, PR Merge Gate, Quality Baseline, Docker build, and Docker parity checks were
green before PR #363 merged. The current portfolio holdings contract branch adds focused holdings
contract compatibility and portfolio OpenAPI evidence with 24 passing focused tests.
PR #364 then merged the holdings contract extraction with all GitHub checks green. The current
risk drawdown contract branch moves drawdown payload models into `risk_workspace_drawdown.py`,
keeps `app.contracts.risk_workspace` as the compatibility import surface, refreshes the governed
monetary-float allowlist for the moved drawdown-at-risk fields, and reduces `risk_workspace.py`
from 2,043 to 1,734 measured lines. Local validation passed with `make check` covering ruff,
format check, monetary-float guard, mypy over 462 source files, Workbench/OpenAPI contract smoke,
and 1,041 unit/contract tests; `make ci` passed with 207 integration tests, 1,248 coverage tests,
94.03% total coverage, and no known vulnerabilities after the governed `PYSEC-2026-161`
exception.
PR #365 then merged the risk drawdown contract extraction with all GitHub checks green. The current
reporting batch contract branch moves batch, worker-run, scheduler, and shared reporting
error-example contracts into `reporting_batches.py` and `reporting_errors.py`, keeps
`app.contracts.reporting` as the compatibility import surface, reduces `reporting.py` from 1,840
to 1,184 measured lines, and has focused evidence from ruff, format check, mypy,
monetary-float guard, and 40 passing reporting batch, contract, and integration tests. Local
validation passed with `make check` covering ruff, format check, monetary-float guard, mypy over
464 source files, Workbench/OpenAPI contract smoke, and 1,044 unit/contract tests; `make ci`
passed with 207 integration tests, 1,251 coverage tests, 94.03% total coverage, and no known
vulnerabilities after the governed `PYSEC-2026-161` exception.
PR #366 then merged the reporting batch contract extraction with all GitHub checks green. The
current reporting query contract branch moves report-job list, lifecycle event, input snapshot,
upstream-call, and snapshot-lineage contracts into `reporting_query.py`, keeps
`app.contracts.reporting` as the compatibility import surface, reduces `reporting.py` from 1,184
to 532 measured lines, and has focused evidence from ruff, mypy, and 7 passing reporting query and
compatibility contract tests. Local `make check` passed with ruff, format check, monetary-float
guard, mypy over 465 source files, Workbench/OpenAPI contract smoke, and 1,048 unit/contract
tests. Local `make ci` passed with 207 integration tests, 1,255 coverage tests, 94.03% total
coverage, and no known vulnerabilities after the governed `PYSEC-2026-161` exception.
PR #367 then merged the reporting query contract extraction with all GitHub checks green. The
current risk concentration contract branch moves concentration payload and driver contracts into
`risk_workspace_concentration.py`, keeps `app.contracts.risk_workspace` as the compatibility
import surface, refreshes the governed monetary-float allowlist for the moved concentration weight
fields, reduces `risk_workspace.py` from 1,647 to 1,343 measured lines, and has focused evidence
from ruff, format check, mypy, monetary-float guard, and 29 passing risk workspace tests. Local
`make check` passed with ruff, format check, monetary-float guard, mypy over 466 source files,
Workbench/OpenAPI contract smoke, and 1,050 unit/contract tests. Local `make ci` passed with 207
integration tests, 1,257 coverage tests, 94.03% total coverage, and no known vulnerabilities after
the governed `PYSEC-2026-161` exception.
PR #368 then merged the risk concentration contract extraction with all GitHub checks green. The
current risk rolling contract branch moves rolling metric summary, series, dependency,
period-result, request-context, and payload contracts into `risk_workspace_rolling.py`, keeps
`app.contracts.risk_workspace` as the compatibility import surface, refreshes the governed
monetary-float allowlist for the moved rolling metric-value field, reduces `risk_workspace.py`
from 1,343 to 969 measured lines, and has focused evidence from ruff, format check, mypy,
monetary-float guard, and 23 passing risk workspace tests. Local `make check` passed with ruff,
format check, monetary-float guard, mypy over 467 source files, Workbench/OpenAPI contract smoke,
and 1,052 unit/contract tests. Local `make ci` passed with 207 integration tests, 1,259 coverage
tests, 94.03% total coverage, and no known vulnerabilities after the governed `PYSEC-2026-161`
exception.
PR #369 then merged the risk rolling contract extraction with all GitHub checks green. The current
risk attribution contract branch moves attribution control, contributor, set, period-result,
methodology-context, and payload contracts into `risk_workspace_attribution.py`, keeps
`app.contracts.risk_workspace` as the compatibility import surface, refreshes the governed
monetary-float allowlist for the moved attribution contribution fields, reduces
`risk_workspace.py` from 969 to 678 measured lines, and has focused evidence from ruff, format
check, mypy, monetary-float guard, and 34 passing risk workspace tests. Local `make check` passed
with ruff, format check, monetary-float guard, mypy over 468 source files, Workbench/OpenAPI
contract smoke, and 1,054 unit/contract tests. Local `make ci` passed with 207 integration tests,
1,261 coverage tests, 94.04% total coverage, and no known vulnerabilities after the governed
`PYSEC-2026-161` exception.
PR #370 then merged the risk attribution contract extraction with all GitHub checks green. The
current performance contribution contract branch moves contribution row, position, level,
smoothing-evidence, source-economics-evidence, and summary contracts into
`performance_contribution.py`, keeps `app.contracts.performance_workspace` as the compatibility
import surface, refreshes the governed monetary-float allowlist for the moved performance
contribution fields, reduces `performance_workspace.py` from 1,539 to 1,499 measured lines, and
has focused evidence from ruff, format check, mypy, monetary-float guard, and 33 passing
performance contribution/workspace/advisor brief tests. Local `make check` passed with ruff,
format check, monetary-float guard, mypy over 469 source files, Workbench/OpenAPI contract smoke,
and 1,056 unit/contract tests. Local `make ci` passed with 207 integration tests, 1,263 coverage
tests, 94.04% total coverage, and no known vulnerabilities after the governed `PYSEC-2026-161`
exception.
PR #371 then merged the performance contribution contract extraction with all GitHub checks green.
The merged performance attribution contract branch moved attribution row, level, reason,
residual-materiality, supportability-evidence, summary, trend-row, and trend-response contracts
into `performance_attribution.py`, keeps `app.contracts.performance_workspace` as the compatibility
import surface, refreshes the governed monetary-float allowlist for the moved performance
attribution fields, reduces `performance_workspace.py` from 1,499 to 1,101 measured lines, and has
focused evidence from ruff, format check, mypy, monetary-float guard, and 74 passing performance
attribution/workspace/advisor brief/OpenAPI tests. Local `make check` passed with ruff, format
check, monetary-float guard, mypy over 470 source files, Workbench/OpenAPI contract smoke, and
1,058 unit/contract tests. Local `make ci` passed with 207 integration tests, 1,265 coverage
tests, 94.05% total coverage, and no known vulnerabilities after the governed `PYSEC-2026-161`
exception.
PR #372 then merged the performance attribution contract extraction with all GitHub checks green.
The merged performance evidence contract branch moved calculation, source-supportability, stage,
upstream-snapshot, artifact, and evidence-view contracts into `performance_evidence.py`, keeps
`app.contracts.performance_workspace` as the compatibility import surface, preserves the governed
monetary-float allowlist without churn, reduces `performance_workspace.py` from 1,101 to 903
measured lines, and has focused evidence from ruff, format check, mypy, monetary-float guard, and
18 passing performance evidence/capabilities/response tests. Local `make check` passed with ruff,
format check, monetary-float guard, mypy over 471 source files, Workbench/OpenAPI contract smoke,
and 1,059 unit/contract tests. Local `make ci` passed with 207 integration tests, 1,266 coverage
tests, 94.05% total coverage, and no known vulnerabilities after the governed `PYSEC-2026-161`
exception.
PR #373 then merged the performance evidence contract extraction with all GitHub checks green.
The then-current performance evidence-view builder branch moved evidence request context, fetch state,
source-supportability collection, durable calculation evidence fetching, and supported/partial/
unavailable evidence response resolution into `performance_workspace_evidence.py`, reduces
`performance_workspace_service.py` from 1,611 to 1,413 measured lines, and has focused evidence
from ruff, format check, mypy, monetary-float guard, and 51 passing performance evidence/service
tests. Local `make check` passed with ruff, format check, monetary-float guard, mypy over 471
source files, Workbench/OpenAPI contract smoke, and 1,063 unit/contract tests. Local `make ci`
passed with 207 integration tests, 1,270 coverage tests, 94.05% total coverage, and no known
vulnerabilities after the governed `PYSEC-2026-161` exception.
PR #374 then merged the performance evidence-view builder extraction with all GitHub checks green.
PR #375 then merged the quality-baseline enforcement branch with all GitHub checks green. That
branch promoted remediated refactor thresholds into the
blocking `make lint` path through `scripts/check_refactor_quality_thresholds.py`. The gate makes
the promoted refactor threshold visible as `Lint and Refactor Quality Thresholds` in Feature Lane
and PR Merge Gate logs, and lets PR Merge Gate integration and coverage jobs run in parallel after
lint/typecheck/unit. Docker build and Docker parity still wait for both integration and coverage.
Subsequent source-file ratchets now fail when any Python source file under `src/app` exceeds 1,489
script-counted lines or any Python function or async function exceeds the current 49-line AST span
baseline. Current focused local evidence: `python scripts/check_refactor_quality_thresholds.py`
passed with `max_source_file_lines=1489` and `max_function_lines=49`.
Local validation for that branch passed with `make check` covering ruff, format check,
monetary-float guard, refactor threshold gate, mypy over 471 source files, Workbench/OpenAPI
contract smoke, and 1,066 unit/contract tests. Local `make ci` passed with 207 integration tests,
1,273 coverage tests, 94.05% total coverage, and no known vulnerabilities after the governed
`PYSEC-2026-161` exception.

The current portfolio position source-loading branch preserves the same gate posture while
ratcheting the blocking source-file threshold to 1,728 physical lines after extracting
position-book source loading into `portfolio_holdings_payloads.py`. Local `make check` passed with
ruff, format check, monetary-float guard, refactor threshold gate, mypy over 475 source files,
Workbench/OpenAPI contract smoke, and 1,117 unit/contract tests. Local `make ci` passed with 207
integration tests, 1,324 coverage tests, 94.14% total coverage, and no known vulnerabilities after
the governed `PYSEC-2026-161` exception.

The current portfolio workspace source-loading branch continues the same refactor threshold posture
by ratcheting the blocking source-file threshold to 1,659 physical lines after extracting workspace
source and analytics fan-out into `portfolio_workspace_sources.py`. Focused validation passed with
ruff, format check, touched-module mypy, the refactor threshold gate, and 44 portfolio
workspace/service unit tests. Local `make check` passed with ruff, format check,
monetary-float guard, refactor threshold gate, workflow action-runtime gate, mypy over 476 source
files, Workbench/OpenAPI contract smoke, and 1,119 unit/contract tests. Local `make ci` passed with
207 integration tests, 1,326 combined coverage tests, 94.16% total coverage, and no known
vulnerabilities after the governed `PYSEC-2026-161` exception.

The prior advisor-brief source mapper branch kept the 1,659-line source-file threshold while
extracting source-context, fallback narrative, source-metric, supportability, route, and AI
fact-bundle shaping into `advisor_brief_source.py`. Focused validation passed with ruff check,
ruff format check, the refactor threshold gate, and 37 advisor-brief/source/boundary/threshold unit
tests. Local `make check` passed with ruff, format check, monetary-float guard, refactor threshold
gate, workflow action-runtime gate, mypy over 477 source files, Workbench/OpenAPI contract smoke,
and 1,123 unit/contract tests. Local `make ci` passed with 207 integration tests, 1,330 combined
coverage tests, 94.18% total coverage, and no known vulnerabilities after the governed
`PYSEC-2026-161` exception.

The current portfolio readiness/insight source-loading branch ratchets the source-file threshold
to 1,607 script-counted lines after extracting readiness and insight source fan-out into
`portfolio_readiness_insight_sources.py`. Focused validation passed with ruff check, ruff format
check, touched-module mypy, the refactor threshold gate, and 62 helper/service/boundary/threshold
unit tests. Local `make check` passed with ruff, format check, monetary-float guard, refactor
threshold gate, workflow action-runtime gate, mypy over 478 source files, Workbench/OpenAPI
contract smoke, and 1,126 unit/contract tests. Local `make ci` passed with 207 integration tests,
1,333 combined coverage tests, 94.19% total coverage, and no known vulnerabilities after the
governed `PYSEC-2026-161` exception.

The current portfolio book source-loading branch ratchets the source-file threshold to 1,589
script-counted lines after extracting portfolio book source fan-out into
`portfolio_book_sources.py`. Focused validation passed with ruff check, ruff format check,
touched-module mypy, the refactor threshold gate, and 64 helper/service/boundary/threshold unit
tests. Local `make check` passed with ruff, format check, monetary-float guard, refactor
threshold gate, workflow action-runtime gate, mypy over 479 source files, Workbench/OpenAPI
contract smoke, and 1,128 unit/contract tests. Local `make ci` passed with 207 integration tests,
1,335 combined coverage tests, 94.20% total coverage, and no known vulnerabilities after the
governed `PYSEC-2026-161` exception.

The current portfolio service wrapper-cleanup branch ratchets the source-file threshold to 1,553
script-counted lines after removing stale local pass-through wrappers from `portfolio_service.py`.
Focused validation passed with ruff check, ruff format check, touched-module mypy, the refactor
threshold gate, and 68 service/boundary/threshold/docs unit tests. Local `make check` passed with
ruff, format check, monetary-float guard, refactor threshold gate, workflow action-runtime gate,
mypy over 479 source files, Workbench/OpenAPI contract smoke, and 1,129 unit/contract tests. Local
`make ci` passed with 207 integration tests, 1,336 combined coverage tests, 94.24% total coverage,
and no known vulnerabilities after the governed `PYSEC-2026-161` exception.

The current portfolio upstream-payload extraction branch ratchets the source-file threshold to
1,489 script-counted lines after moving portfolio-specific payload requiring, optional
partial-failure recording, product-safe upstream error detail construction, and client-error
mapping into `portfolio_upstream_payloads.py`. Focused validation passed with ruff check, ruff
format check, touched-module mypy, the refactor threshold gate, and 63 service/boundary/helper
unit tests. Local `make check` passed with ruff, format check, monetary-float guard, refactor
threshold gate, workflow action-runtime gate, mypy over 480 source files, Workbench/OpenAPI
contract smoke, and 1,134 unit/contract tests. Local `make ci` passed with 207 integration tests,
1,341 combined coverage tests, 94.24% total coverage, and no known vulnerabilities after the
governed `PYSEC-2026-161` exception.

The current portfolio upstream-access extraction branch ratchets the source-file threshold to
1,217 script-counted lines after moving cached Lotus Core, performance, and DPM upstream result
acquisition into `portfolio_upstream_access.py`. It reduces `portfolio_service.py` from 1,237 to
980 script-counted lines while preserving cache keys, optional-client behavior, source fan-out call
shapes, and the public `PortfolioService` API. Focused validation passed with ruff check,
touched-module mypy, 42 portfolio service tests, and trial refactor threshold gates proving
`max_source_file_lines=1217` passes while `1216` fails. Local `make check` passed with ruff,
format check, monetary-float guard, refactor threshold gate, workflow action-runtime gate, mypy
over 487 source files, Workbench/OpenAPI contract smoke, and 1,161 unit/contract tests. Local
`make ci` passed with 207 integration tests, 1,368 combined coverage tests, 94.26% total coverage,
migration contract smoke, and no known vulnerabilities after the governed `PYSEC-2026-161`
exception.

The current DPM PM operating-quality service-boundary branch ratchets the source-file threshold to
1,206 script-counted lines after moving PM operating-quality policy, score-run, fairness-analysis,
review-action, summary-invocation, and AI summary workflow-pack service orchestration into
`dpm_pm_operating_quality_service.py`. It reduces `dpm_command_center_service.py` from 1,217 to
695 script-counted lines while preserving the public `DpmCommandCenterService` surface,
manage-owned evidence boundaries, and `lotus-ai` workflow-pack execution behavior. Focused
validation passed with ruff check, touched-module mypy, 48 DPM command-center service/contract
tests, and trial refactor threshold gates proving `max_source_file_lines=1206` passes while
`1205` fails. Local `make check` passed with ruff, format check, monetary-float guard, refactor
threshold gate, workflow action-runtime gate, mypy over 488 source files, Workbench/OpenAPI
contract smoke, and 1,161 unit/contract tests. Local `make ci` passed with 207 integration tests,
1,368 combined coverage tests, 94.27% total coverage, migration contract smoke, and no known
vulnerabilities after the governed `PYSEC-2026-161` exception.

The current performance trend service-boundary branch ratchets the source-file threshold to 1,098
script-counted lines after moving performance horizon-comparison and attribution-trend service
orchestration into `performance_workspace_trend_service.py`. It reduces
`performance_workspace_service.py` from 1,206 to 842 script-counted lines while preserving the
public `PerformanceWorkspaceService` surface. Focused validation passed with ruff check,
touched-module mypy, 67 performance workspace trend/horizon/attribution/context/control tests, and
trial refactor threshold gates proving `max_source_file_lines=1098` passes while `1097` fails.
Local `make check` passed with ruff, format check, monetary-float guard, refactor threshold gate,
workflow action-runtime gate, mypy over 489 source files, Workbench/OpenAPI contract smoke, and
1,162 unit/contract tests. Local `make ci` passed with 207 integration tests, 1,369 combined
coverage tests, 94.26% total coverage, migration contract smoke, and no known vulnerabilities after
the governed `PYSEC-2026-161` exception.

The merged Advise bank-demo proof client-boundary branch ratcheted the source-file threshold to
1,093 script-counted lines after moving RFC-0028 bank-demo proof upstream route methods into
`advise_bank_demo_proof_client.py`. It reduces `advise_client.py` from 1,098 to 1,062
script-counted lines while preserving the public `AdviseClient` surface. Focused validation passed
with ruff check, ruff format check, touched-client mypy, 14 Advise client boundary/factory,
bank-demo proof router, Advise route-coverage, and refactor-threshold tests, and the refactor
threshold gate at `max_source_file_lines=1093`. Full local `make check` and `make ci` evidence
is green: `make check` passed with ruff, format check, monetary-float guard, refactor threshold
gate, workflow action-runtime gate, mypy over 490 source files, Workbench/OpenAPI contract smoke,
and 1,163 unit/contract tests; `make ci` passed with 207 integration tests, 1,370 combined
coverage tests, 94.24% total coverage, migration contract smoke, and no known vulnerabilities
after the governed `PYSEC-2026-161` exception.

The current DPM wave AI handoff boundary branch ratchets the source-file threshold to 1,062
script-counted lines after moving PM memo and operations handoff summary workflow-pack
orchestration into `dpm_wave_ai_handoff.py`. It reduces `dpm_wave_service.py` from 1,093 to 692
script-counted lines while preserving the public `DpmWaveService` surface. Focused validation
passed with ruff check, ruff format check, touched-module mypy, 38 DPM wave
service/boundary/contract/router tests, and trial refactor threshold gates proving
`max_source_file_lines=1062` passes while `1061` fails. Full local `make check` and `make ci`
evidence is green: `make check` passed with ruff, format check, monetary-float guard, refactor
threshold gate, workflow action-runtime gate, mypy over 491 source files, Workbench/OpenAPI
contract smoke, and 1,164 unit/contract tests; `make ci` passed with 207 integration tests, 1,371
combined coverage tests, 94.25% total coverage, migration contract smoke, and no known
vulnerabilities after the governed `PYSEC-2026-161` exception.

The previous DPM wave client-boundary branch ratcheted the source-file threshold to 980
script-counted lines after moving rebalance-wave and campaign workflow upstream route methods into
`dpm_wave_client.py`. It reduced `dpm_client.py` from 1,041 to 452 script-counted lines while
preserving the public `DpmClient` surface. Focused validation passed with ruff check, ruff format
check, 101 DPM upstream-client/boundary tests, and the refactor threshold gate at
`max_source_file_lines=980`. Full local `make check` passed with ruff, format check,
monetary-float guard, refactor threshold gate, workflow action-runtime gate, mypy over 493 source
files, Workbench/OpenAPI contract smoke, and 1,166 unit/contract tests. Full local `make ci`
passed with 207 integration tests, 1,373 combined coverage tests, 94.21% total coverage, migration
contract smoke, and no known vulnerabilities after the governed `PYSEC-2026-161` exception.

The previous portfolio transaction-boundary branch ratcheted the source-file threshold to 979
script-counted lines after moving transaction ledger, income summary, and activity summary
orchestration into `portfolio_transaction_service.py`. It reduces `portfolio_service.py` from 980
script-counted lines to 811 physical lines while preserving the public `PortfolioService` surface.
Focused validation passed with ruff check, ruff format check, touched-service mypy, 19
transaction/service-boundary tests, and refactor-threshold trials proving
`max_source_file_lines=979` passes while `978` fails on `src/app/contracts/proposals.py`. Full
local `make check` passed with ruff, format check, monetary-float guard, refactor threshold gate,
workflow action-runtime gate, mypy over 494 source files, Workbench/OpenAPI contract smoke, and
1,167 unit/contract tests. Full local `make ci` passed with 207 integration tests, 1,374 combined
coverage tests, 94.22% total coverage, migration contract smoke, and no known vulnerabilities
after the governed `PYSEC-2026-161` exception.

The previous proposal memo contract-boundary branch ratcheted the source-file threshold to 954
script-counted lines after moving memo-specific proposal request and envelope contracts into
`proposal_memos.py`. It reduced `src/app/contracts/proposals.py` from 979 to 828 script-counted
lines while preserving the public `app.contracts.proposals` import surface. Focused validation
passed with proposal contract tests, contract-boundary tests, and refactor-threshold trials proving
`max_source_file_lines=954` passes while `953` fails on `src/app/contracts/portfolio.py`. Full
local `make check` passed with ruff, format check, monetary-float guard, refactor threshold gate,
workflow action-runtime gate, mypy over 496 source files, Workbench/OpenAPI contract smoke, and
1,168 unit/contract tests. Full local `make ci` passed with 207 integration tests, 1,375 combined
coverage tests, 94.22% total coverage, migration contract smoke, and no known vulnerabilities
after the governed `PYSEC-2026-161` exception.

The current portfolio liquidity contract-boundary branch ratchets the source-file threshold to 951
script-counted lines after moving liquidity and projected-cashflow contracts into
`portfolio_liquidity.py`. It reduces `src/app/contracts/portfolio.py` from 954 to 754
script-counted lines while preserving the public `app.contracts.portfolio` import surface. Full
local `make check` passed with 1,169 unit/contract tests, and full local `make ci` passed with 207
integration tests, 1,376 combined coverage tests, 94.22% total coverage, migration contract smoke,
and no known vulnerabilities after the governed `PYSEC-2026-161` exception. Focused
refactor-threshold trials prove `max_source_file_lines=951` passes while `950` fails on
`src/app/services/foundation_service.py`.

The merged Foundation core-snapshot mapper branch ratcheted the source-file threshold to 930
script-counted lines after moving lotus-core snapshot parsing, defensive payload normalization,
allocation bucketing, top-position mapping, and market-value extraction into
`foundation_core_snapshot.py`. It reduces `src/app/services/foundation_service.py` from 951 to 618
script-counted lines while preserving Foundation workspace response behavior. Focused validation
passed with ruff check, ruff format, mypy over touched service modules, 31 focused
foundation/refactor unit, contract, and integration tests, and refactor-threshold trials proving
`max_source_file_lines=930` passes while `929` fails on
`src/app/contracts/performance_workspace.py`. Full local `make check` passed with ruff, format
check, monetary-float guard, refactor threshold gate, workflow action-runtime gate, mypy over 498
source files, Workbench/OpenAPI contract smoke, and 1,171 unit/contract tests. Full local `make ci`
passed with 207 integration tests, 1,378 combined coverage tests, 94.23% total coverage, migration
contract smoke, and no known vulnerabilities after the governed `PYSEC-2026-161` exception.

The merged performance horizon contract branch ratcheted the source-file threshold to 914
script-counted lines after moving benchmark option and horizon-comparison response models into
`performance_horizon.py`. It reduces `src/app/contracts/performance_workspace.py` from 930 to 651
script-counted lines while preserving the public `app.contracts.performance_workspace` import
surface. Focused validation passed with ruff check, ruff format, mypy over touched performance
contract modules, 46 focused performance/workbench contract and integration tests, and
refactor-threshold trials proving `max_source_file_lines=914` passes while `913` fails on
`src/app/clients/advise_client.py`. Full local `make check` passed with 1,178 unit/contract tests.
Full local `make ci` passed with 209 integration tests, 1,387 combined coverage tests, 94.18% total
coverage, migration contract smoke, and no known vulnerabilities after the governed
`PYSEC-2026-161` exception.

The merged Advise policy client-boundary branch ratcheted the source-file threshold to 872
script-counted lines after moving advisory policy-pack, policy-evaluation, sign-off,
report-package, and AI-evidence route methods into `advise_policy_client.py`. It reduces
`src/app/clients/advise_client.py` from 914 to 712 script-counted lines while preserving the public
`AdviseClient` surface. Focused validation passed with ruff check, ruff format, mypy over touched
Advise client modules, 187 focused upstream/client-boundary/policy-router tests, and
refactor-threshold trials proving `max_source_file_lines=872` passes while `871` fails on
`src/app/router_registry.py`. Full local `make check` passed with 1,179 unit/contract tests. Full
local `make ci` passed with 209 integration tests, 1,388 combined coverage tests, 94.16% total
coverage, migration contract smoke, and no known vulnerabilities after the governed
`PYSEC-2026-161` exception.

The merged advisory router-group branch ratchets the source-file threshold to 861 script-counted
lines after moving Advise-owned route-family imports and router group tuples into
`src/app/router_groups/advisory.py`. It reduces `src/app/router_registry.py` from 872 to 632
script-counted lines while preserving concrete route registration. Focused validation passed with
ruff check, ruff format check, touched-module mypy, 10 router-registry/refactor-threshold tests,
and the refactor threshold gate at `max_source_file_lines=861`. Full local `make check` passed
with ruff, format check over 716 files, monetary-float guard, refactor-threshold gate,
workflow action-runtime gate, mypy over 506 source files, Workbench/OpenAPI contract smoke, and
1,180 unit/contract tests. Full local `make ci` passed with 209 integration tests, 1,389 combined
coverage tests, 94.17% total coverage, migration contract smoke, and no known vulnerabilities
after the governed `PYSEC-2026-161` exception.

The merged advisor brief narrative mapper branch ratchets the source-file threshold to 854
script-counted lines after moving AI task-request construction, AI narrative parsing, fallback
audit normalization, and AI evidence-reference mapping into
`src/app/services/advisor_brief_narrative.py`. It reduces
`src/app/services/advisor_brief_service.py` from 861 to 435 script-counted lines while preserving
advisor brief orchestration and review-action behavior. Focused validation passed with ruff check,
ruff format check, 24 advisor-brief source/narrative/service unit tests, and refactor-threshold
trials proving `max_source_file_lines=854` passes while `853` fails on
`src/app/services/proposal_service.py`. Full local `make check` passed with ruff, format check
over 719 files, monetary-float guard, refactor-threshold gate, workflow action-runtime gate, mypy
over 507 source files, Workbench/OpenAPI contract smoke, and 1,184 unit/contract tests. Full local
`make ci` passed with 209 integration tests, 1,393 combined coverage tests, 94.22% total coverage,
migration contract smoke, and no known vulnerabilities after the governed `PYSEC-2026-161`
exception.

The current proposal memo service branch ratchets the source-file threshold to 842 script-counted
lines after moving proposal memo create/read/projection/review, report-package event/request,
AI-commentary request, lineage, and replay-evidence forwarding into
`src/app/services/proposal_memo_service.py`. It reduces `src/app/services/proposal_service.py`
from 854 to 658 script-counted lines while preserving gateway forwarding, product-safe upstream
error handling, and source-owned memo/report-package payloads. Focused validation passed with ruff
check, ruff format check, 13 proposal-service unit tests, and refactor-threshold trials proving
`max_source_file_lines=842` passes while `841` fails on
`src/app/services/performance_workspace_service.py`. Full local `make check` passed with ruff,
format check over 720 files, monetary-float guard, refactor-threshold gate, workflow
action-runtime gate, mypy over 508 source files, Workbench/OpenAPI contract smoke, and 1,184
unit/contract tests. Full local `make ci` passed with 209 integration tests, 1,393 combined
coverage tests, 94.21% total coverage, migration contract smoke, and no known vulnerabilities
after the governed `PYSEC-2026-161` exception.

The current performance workspace context-service branch ratchets the source-file threshold to 841
script-counted lines after moving cache-backed overview loading, report-window resolution,
benchmark context assembly, and analytics-reference end-date fallback into
`src/app/services/performance_workspace_context_service.py`. It reduces
`src/app/services/performance_workspace_service.py` from 842 to 639 script-counted lines while
preserving workspace summary/detail, trend, cache, warning, and partial-failure behavior. Focused
validation passed with ruff check, ruff format check, mypy over 509 source files, 36 performance
workspace service unit tests, and refactor-threshold trials proving `max_source_file_lines=841`
passes while `840` fails on `src/app/contracts/dpm_command_center.py`. Full local `make check`
passed with ruff, format check over 721 files, monetary-float guard, refactor-threshold gate,
workflow action-runtime gate, mypy over 509 source files, Workbench/OpenAPI contract smoke, and
1,184 unit/contract tests. Full local `make ci` passed with 209 integration tests, 1,393 combined
coverage tests, 94.22% total coverage, migration contract smoke, and no known vulnerabilities
after the governed `PYSEC-2026-161` exception.

The current DPM PM operating-quality contract branch ratchets the source-file threshold to 812
script-counted lines after moving PM quality request, supportability, gateway response, and
AI-summary handoff contracts into `src/app/contracts/dpm_pm_operating_quality.py`. It reduces
`src/app/contracts/dpm_command_center.py` from 841 to 593 script-counted lines while preserving
compatibility imports through the command-center facade. Focused validation passed with ruff check,
ruff format check, mypy over 510 source files, 17 focused contract/boundary/threshold tests, and
refactor-threshold trials proving `max_source_file_lines=812` passes while `811` fails on
`src/app/contracts/advisor_brief.py` and `src/app/contracts/proposals.py`. Full local `make check`
passed with ruff, format check over 722 files, monetary-float guard, refactor-threshold gate,
workflow action-runtime gate, mypy over 510 source files, OpenAPI smoke, and 1,185 unit/contract
tests. Full local `make ci` passed with migration contract smoke, 209 integration tests, 1,394
combined coverage tests, 94.22% total coverage, and no known vulnerabilities after the governed
`PYSEC-2026-161` exception.

The current portfolio transaction-summary context branch moves reporting-window resolution, YTD
transaction pagination, defensive page-row extraction, reporting-currency fallback, and
requested-window filtering into `portfolio_transaction_summary.py`. It reduces
`portfolio_service.py` from 1,970 to 1,888 physical lines while preserving income/activity summary
behavior and the 49-line longest-function baseline. Focused local validation passed with ruff
check, ruff format check, mypy over touched service modules, and 51 portfolio summary/service
unit tests. Local `make check` passed with ruff, format check, monetary-float guard, refactor
threshold gate, mypy over 471 source files, Workbench/OpenAPI contract smoke, and 1,070
unit/contract tests. Local `make ci` passed with 207 integration tests, 1,277 coverage tests,
94.08% total coverage, and no known vulnerabilities after the governed `PYSEC-2026-161`
exception.

The current portfolio workspace payload mapper branch moves portfolio identity/profile
projection, workspace summary construction, cashflow outlook projection, display-name fallback,
and operations readiness projection into `portfolio_workspace_payloads.py`. It reduces
`portfolio_service.py` from 1,888 to 1,826 physical lines while preserving workspace response
behavior and the 49-line longest-function baseline. Focused local validation passed with ruff
check, ruff format check, mypy over touched service modules, and 48 portfolio workspace/service
unit tests. Local `make check` passed with ruff, format check, monetary-float guard, refactor
threshold gate, mypy over 472 source files, Workbench/OpenAPI contract smoke, and 1,075
unit/contract tests. Local `make ci` passed with 207 integration tests, 1,282 coverage tests,
94.07% total coverage, and no known vulnerabilities after the governed `PYSEC-2026-161`
exception.
