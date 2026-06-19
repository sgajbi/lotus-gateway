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

The current advisor-brief/proposal contract-boundary branch ratchets the source-file threshold to
811 script-counted lines after moving advisor-brief workflow-pack and task-flow contracts into
`src/app/contracts/advisor_brief_workflow.py` and proposal lifecycle, version, workflow, approval,
and lineage contracts into `src/app/contracts/proposal_lifecycle.py`. It reduces
`src/app/contracts/advisor_brief.py` from 812 to 646 script-counted lines and
`src/app/contracts/proposals.py` from 812 to 431 script-counted lines while preserving
compatibility imports through both facades. Focused validation passed with ruff check, ruff format
check, mypy over 512 source files, 61 advisor-brief/proposal contract/boundary/threshold tests,
and refactor-threshold trials proving `max_source_file_lines=811` passes while `810` fails on
`src/app/services/portfolio_service.py`. Full local `make check` passed with ruff, format check
over 724 files, monetary-float guard, refactor-threshold gate, workflow action-runtime gate, mypy
over 512 source files, OpenAPI smoke, and 1,187 unit/contract tests. Full local `make ci` passed
with migration contract smoke, 209 integration tests, 1,396 combined coverage tests, 94.23% total
coverage, and no known vulnerabilities after the governed `PYSEC-2026-161` exception.

The current portfolio workflow service-boundary branch ratchets the source-file threshold to 794
script-counted lines after moving portfolio workflow orchestration and the latest-transaction probe
into `src/app/services/portfolio_workflow_service.py`. It reduces
`src/app/services/portfolio_service.py` from 811 to 768 script-counted lines while preserving the
public `PortfolioService` surface. Focused validation passed with ruff check, ruff format check,
mypy over touched service files, 68 portfolio service/boundary/threshold tests, and
refactor-threshold trials proving `max_source_file_lines=794` passes while `793` fails on
`src/app/contracts/workbench.py`. Full local `make check` passed with ruff, format check over 725
files, monetary-float guard, refactor-threshold gate, workflow action-runtime gate, mypy over 513
source files, OpenAPI smoke, and 1,188 unit/contract tests. Full local `make ci` passed with
migration contract smoke, 209 integration tests, 1,397 combined coverage tests, 94.23% total
coverage, and no known vulnerabilities after the governed `PYSEC-2026-161` exception.

The current workbench contract-boundary branch ratchets the source-file threshold to 771
script-counted lines after moving common workbench view models, overview and portfolio-360
responses, and sandbox/analytics contracts into `src/app/contracts/workbench_common.py`,
`src/app/contracts/workbench_overview.py`, and `src/app/contracts/workbench_sandbox.py`. It reduces
`src/app/contracts/workbench.py` from 794 to 47 script-counted lines while preserving the public
`app.contracts.workbench` facade. Focused validation passed with ruff check, ruff format check,
mypy over touched contract modules, 118 workbench service/router/contract-boundary/threshold tests,
and the refactor-threshold gate at `max_source_file_lines=771`. Full local `make check` passed with
ruff, format check over 728 files, monetary-float guard, refactor-threshold gate, workflow
action-runtime gate, mypy over 516 source files, OpenAPI smoke, and 1,189 unit/contract tests. Full
local `make ci` passed with migration contract smoke, 209 integration tests, 1,398 combined
coverage tests, 94.24% total coverage, and no known vulnerabilities after the governed
`PYSEC-2026-161` exception.

The current performance evidence-boundary branch extracts performance calculation evidence artifact
retrieval, lineage polling, execution refresh, payload normalization, stage/snapshot mapping, and
artifact URL construction into `src/app/services/performance_calculation_evidence.py`, preserving
the public `app.services.performance_workspace_evidence` facade. The slice reduces
`src/app/services/performance_workspace_evidence.py` from 771 to 461 script-counted lines and
ratchets the source-file threshold to 769 script-counted lines. Focused validation passed with ruff
check, ruff format check, 59 focused performance evidence/workspace/threshold tests, and the
refactor-threshold gate at `max_source_file_lines=769`. Full local `make check` passed with ruff,
format check over 729 files, monetary-float guard, refactor-threshold gate, workflow action-runtime
gate, mypy over 517 source files, OpenAPI smoke, and 1,190 unit/contract tests. Full local
`make ci` passed with migration contract smoke, 209 integration tests, 1,399 combined coverage
tests, 94.24% total coverage, and no known vulnerabilities after the governed `PYSEC-2026-161`
exception.

The current risk workspace request-context branch moves risk request-context dataclasses,
latest-business-day fallback, as-of date resolution, and context construction into
`src/app/services/risk_workspace_requests.py`, preserving the `RiskWorkspaceService` orchestration
and cache boundary. The slice reduces `src/app/services/risk_workspace_service.py` from 769 to 633
script-counted lines and ratchets the source-file threshold to 768 script-counted lines. Focused
validation passed with ruff check, 33 focused risk workspace/request/threshold tests, and the
refactor-threshold gate at `max_source_file_lines=768`. Full local `make check` passed with ruff,
format check over 729 files, monetary-float guard, refactor-threshold gate, workflow action-runtime
gate, mypy over 517 source files, OpenAPI smoke, and 1,191 unit/contract tests. Full local
`make ci` passed with migration contract smoke, 209 integration tests, 1,400 combined coverage
tests, 94.25% total coverage, and no known vulnerabilities after the governed `PYSEC-2026-161`
exception.

The current portfolio workspace wrapper-cleanup branch removes stale private pass-through wrappers
around already extracted workspace assembly helpers from `src/app/services/portfolio_service.py`.
The service now calls those helpers directly, preserving the public `PortfolioService` surface while
reducing `portfolio_service.py` from 768 to 716 script-counted lines and ratcheting the source-file
threshold to 754 script-counted lines. Focused validation passed with ruff check, ruff format
check, 52 focused portfolio service/workspace/threshold tests, and the refactor-threshold gate at
`max_source_file_lines=754`. Full local `make check` passed with ruff, format check over 729 files,
monetary-float guard, refactor-threshold gate, workflow action-runtime gate, mypy over 517 source
files, OpenAPI smoke, and 1,191 unit/contract tests. Full local `make ci` passed with migration
contract smoke, 209 integration tests, 1,400 combined coverage tests, 94.25% total coverage, and no
known vulnerabilities after the governed `PYSEC-2026-161` exception.

The current portfolio workspace contract-boundary branch moves portfolio workspace response,
profile, rebalance, reporting, operations, and control-capability contracts into
`src/app/contracts/portfolio_workspace.py` while preserving compatibility imports through
`app.contracts.portfolio`. It reduces `src/app/contracts/portfolio.py` from 754 to 281
script-counted lines, introduces `portfolio_workspace.py` at 503 script-counted lines, moves the
largest residual source-file hotspot to `src/app/services/advisor_brief_source.py` at 742
script-counted lines, and ratchets the source-file threshold to 742 script-counted lines. Focused
validation passed with ruff check, ruff format check, 19 focused workspace
contract/response/control/OpenAPI/threshold tests, and the refactor-threshold gate at
`max_source_file_lines=742`. Full local `make check` passed with ruff, format check over 731
files, monetary-float guard, refactor-threshold gate, workflow action-runtime gate, mypy over 518
source files, OpenAPI smoke, and 1,193 unit/contract tests. Full local `make ci` passed with
migration contract smoke, 209 integration tests, 1,402 combined coverage tests, 94.26% total
coverage, and no known vulnerabilities after the governed `PYSEC-2026-161` exception.

The current advisor-brief source-boundary branch extracts advisor-brief source formatting,
source-contributor ranking, and AI fact-bundle shaping into
`src/app/services/advisor_brief_source_formatting.py`,
`src/app/services/advisor_brief_source_contributors.py`, and
`src/app/services/advisor_brief_source_fact_bundle.py` while preserving the existing
`advisor_brief_source.build_advisor_brief_ai_fact_bundle` compatibility import. It reduces
`advisor_brief_source.py` from 742 to 508 script-counted lines, moves the largest residual
source-file hotspot to `src/app/services/portfolio_service.py` at 714 script-counted lines, and
ratchets the source-file threshold to 714 script-counted lines. Focused validation passed with
ruff check, ruff format check, mypy over touched service modules, 8 advisor-brief source/narrative
tests, and refactor-threshold trials proving `max_source_file_lines=714` passes while `713` fails
on `src/app/services/portfolio_service.py`. Full local `make check` passed with ruff, format check
over 734 files, monetary-float guard, refactor-threshold gate, workflow action-runtime gate, mypy
over 521 source files, OpenAPI smoke, and 1,194 unit/contract tests. Full local `make ci` passed
with migration contract smoke, 209 integration tests, 1,403 combined coverage tests, 94.26% total
coverage, and no known vulnerabilities after the governed `PYSEC-2026-161` exception.

The current portfolio liquidity response-boundary branch moves portfolio liquidity and projected
cashflow response assembly into `src/app/services/portfolio_liquidity_response.py` while preserving
upstream loading in `PortfolioService`. It reduces `portfolio_service.py` from 714 to 689
script-counted lines, moves the largest residual source-file hotspot to
`src/app/clients/advise_client.py` at 712 script-counted lines, and ratchets the source-file
threshold to 712 script-counted lines. Focused validation passed with ruff check, ruff format
check, mypy over touched service modules, 46 focused portfolio service/liquidity tests, and
refactor-threshold trials proving `max_source_file_lines=712` passes while `711` fails on
`src/app/clients/advise_client.py`. Full local `make check` passed with ruff, format check over
736 files, monetary-float guard, refactor-threshold gate, workflow action-runtime gate, mypy over
522 source files, OpenAPI smoke, and 1,196 unit/contract tests. Full local `make ci` passed with
migration contract smoke, 209 integration tests, 1,405 combined coverage tests, 94.27% total
coverage, and no known vulnerabilities after the governed `PYSEC-2026-161` exception.

The previous risk workspace example-boundary branch moves response OpenAPI examples into
`src/app/contracts/risk_workspace_examples.py` while preserving the public
`app.contracts.risk_workspace` response model names. It reduces `risk_workspace.py` from 709 to
312 script-counted lines, keeps the extracted example module at 379 script-counted lines, moves the
largest residual source-file hotspot to `src/app/services/dpm_wave_service.py` at 700
script-counted lines, and ratchets the source-file threshold to 700 script-counted lines. Focused
validation passed with ruff check, ruff format check, mypy over touched risk contract modules,
16 focused risk workspace contract/OpenAPI tests, 4 refactor-threshold tests, and
refactor-threshold trials proving `max_source_file_lines=700` passes while `699` fails on
`src/app/services/dpm_wave_service.py`. Full local `make check` and `make ci` passed:
`make check` covered ruff, format check over 739 files, monetary-float guard,
refactor-threshold gate, workflow action-runtime gate, mypy over 524 source files, OpenAPI smoke,
and 1,210 unit/contract tests; `make ci` covered migration contract smoke, 209 integration tests,
1,419 combined coverage tests, 94.29% total coverage, and no known vulnerabilities after the
governed `PYSEC-2026-161` exception.

The current DPM command-center exception-summary boundary branch moves Manage-owned
exception-summary AI handoff orchestration into
`src/app/services/dpm_command_center_exception_summary.py` while preserving the public
`DpmCommandCenterService` method surface. It also centralizes shared product-safe Manage
command-center error raising in `src/app/services/dpm_command_center_errors.py`. It reduces
`dpm_command_center_service.py` from 695 to 521 script-counted lines, keeps the extracted
exception-summary module at 187 script-counted lines, moves the largest residual source-file
hotspot to `src/app/services/advisory_client_protocols.py` at 692 script-counted lines, and
ratchets the source-file threshold to 692 script-counted lines. Focused validation passed with
ruff check, ruff format check, mypy over four touched DPM command-center service modules,
74 focused DPM command-center service/router/boundary tests, and refactor-threshold trials proving
`max_source_file_lines=692` passes while `691` fails on
`src/app/services/advisory_client_protocols.py`. Full local `make check` and `make ci` passed:
`make check` covered ruff, format check over 743 files, monetary-float guard,
refactor-threshold gate, workflow action-runtime gate, mypy over 527 source files, OpenAPI smoke,
and 1,212 unit/contract tests; `make ci` covered migration contract smoke, 209 integration tests,
1,421 combined coverage tests, 94.29% total coverage, and no known vulnerabilities after the
governed `PYSEC-2026-161` exception.

The current Advisor Brief client-protocol boundary branch moves Advisor Brief AI and Advise client
protocol surfaces into `src/app/services/advisor_brief_client_protocols.py` while preserving
service, supportability, and workflow-pack protocol contracts. It reduces
`advisory_client_protocols.py` from 692 to 630 script-counted lines, creates a focused
63-line Advisor Brief protocol module, moves the largest residual source-file hotspot to
`src/app/clients/lotus_analytics_client.py` and `src/app/services/portfolio_service.py` at 689
script-counted lines, and ratchets the source-file threshold to 689 script-counted lines. Focused
validation passed with ruff check, ruff format check, mypy over the touched advisory protocol and
Advisor Brief service modules, 51 focused Advisor Brief service/supportability/workflow-pack/
boundary tests, and refactor-threshold trials proving `max_source_file_lines=689` passes while
`688` fails on `src/app/clients/lotus_analytics_client.py` and
`src/app/services/portfolio_service.py`. Full local `make check` and `make ci` passed:
`make check` covered ruff, format check over 744 files, monetary-float guard,
refactor-threshold gate, workflow action-runtime gate, mypy over 528 source files, OpenAPI smoke,
and 1,213 unit/contract tests; `make ci` covered migration contract smoke, 209 integration tests,
1,422 combined coverage tests, 94.29% total coverage, and no known vulnerabilities after the
governed `PYSEC-2026-161` exception.

The current workbench enrichment boundary branch moves Workbench overview performance and
rebalance enrichment orchestration into `src/app/services/workbench_overview_enrichment.py`.
It preserves public Workbench overview, portfolio-360, and analytics behavior while reducing
`src/app/services/workbench_service.py` from 685 to 562 script-counted lines, moves the largest
residual source-file hotspot to `src/app/services/portfolio_service.py` at 680 script-counted
lines, and ratchets the source-file threshold to 680 script-counted lines. Focused validation
passed with ruff check, ruff format check, mypy over the touched Workbench service/enrichment
modules, 114 focused Workbench/refactor tests, and refactor-threshold trials proving
`max_source_file_lines=680` passes while `679` fails on
`src/app/services/portfolio_service.py`. Full local `make check` passed with ruff, format check
over 748 files, monetary-float guard, refactor-threshold gate, workflow action-runtime gate, mypy
over 530 source files, OpenAPI smoke, and 1,219 unit/contract tests. Full local `make ci` passed
with migration contract smoke, 209 integration tests, 1,428 combined coverage tests, 94.31% total
coverage, and no known vulnerabilities after the governed `PYSEC-2026-161` exception.

The same branch was validated against the live canonical front-office stack after rebuilding the
`lotus-gateway` container from the branch. `Validate-LotusFrontOfficeCanonical.ps1` passed for
`PB_SG_GLOBAL_BAL_001` and `BMK_PB_GLOBAL_BALANCED_60_40`, writing evidence to
`lotus-workbench/output/playwright/live-canonical-gateway-workbench-boundaries/`: the summary
records 29 screenshots, 25 ready panel classifications, 2 calculation checks, 28 supportability
checks, and 10 workflow-pack checks. Companion observability evidence in
`lotus-workbench/output/observability-live/20260618-194325/` records 13/13 API checks at HTTP 200,
4/4 metric checks at HTTP 200, 14 log artifacts, and 5/5 observability screenshots at HTTP 200.

The current portfolio insights response boundary branch moves portfolio insights response assembly
from `src/app/services/portfolio_service.py` into
`src/app/services/portfolio_insight_response.py`. It preserves portfolio insights source loading
and insight/exception semantics while reducing `src/app/services/portfolio_service.py` from 680 to
589 script-counted lines, moves the largest residual source-file hotspot to
`src/app/services/performance_workspace_horizon.py` at 667 script-counted lines, and ratchets the
source-file threshold to 667 script-counted lines. Focused validation passed with ruff check, ruff
format, mypy over the touched portfolio service/response modules, 43 focused portfolio unit tests,
and refactor-threshold trials proving `max_source_file_lines=667` passes while `666` fails on
`src/app/services/performance_workspace_horizon.py`. Full local `make check` passed with ruff,
format check over 750 files, monetary-float guard, refactor-threshold gate, workflow
action-runtime gate, mypy over 531 source files, Workbench contract smoke, and 1,220 unit/contract
tests. Full local `make ci` passed with migration contract smoke, 209 integration tests, 1,429
combined coverage tests, 94.31% total coverage, and no known vulnerabilities after the governed
`PYSEC-2026-161` exception.

The current performance horizon row-boundary branch moves horizon comparison row assembly from
`src/app/services/performance_workspace_horizon.py` into
`src/app/services/performance_workspace_horizon_rows.py`. It preserves horizon comparison
semantics while reducing `src/app/services/performance_workspace_horizon.py` from 667 to 441
script-counted lines, moves the largest residual source-file hotspot to
`src/app/contracts/reporting_query.py` at 664 script-counted lines, and ratchets the source-file
threshold to 664 script-counted lines. Focused validation passed with ruff check, ruff format,
mypy over the touched performance horizon modules, 32 focused horizon and service-boundary unit
tests, and refactor-threshold trials proving `max_source_file_lines=664` passes while `663` fails
on `src/app/contracts/reporting_query.py`. Full local `make check` passed with ruff, format check
over 751 files, monetary-float guard, refactor-threshold gate, workflow action-runtime gate, mypy
over 532 source files, Workbench contract smoke, and 1,220 unit/contract tests. Full local
`make ci` passed with migration contract smoke, 209 integration tests, 1,429 combined coverage
tests, 94.32% total coverage, and no known vulnerabilities after the governed `PYSEC-2026-161`
exception.

The same branch was validated against the live canonical front-office stack after targeted-refresh
rebuilt only `lotus-gateway` from this branch. `Validate-LotusFrontOfficeCanonical.ps1` passed for
`PB_SG_GLOBAL_BAL_001` and `BMK_PB_GLOBAL_BALANCED_60_40`, writing evidence to
`lotus-workbench/output/playwright/live-canonical-gateway-performance-horizon-rows/`: the summary
records 94 API checks, 29 screenshots, 25 ready panel classifications, 2 calculation checks, 28
supportability checks, 10 workflow-pack checks, 12 advisory journey checks, 0 non-demo screenshots,
and 0 non-ready panels.

The reporting query contract-boundary branch splits report job status, job-search,
snapshot-lineage, and example contracts behind the existing
`src/app/contracts/reporting_query.py` compatibility facade. It reduces
`src/app/contracts/reporting_query.py` from 664 to 41 script-counted lines, moves the largest
residual source-file hotspot to `src/app/contracts/reporting_batches.py` at 662 script-counted
lines, and ratchets the source-file threshold to 662 script-counted lines. Focused validation
passed with 11 reporting query/threshold tests and refactor-threshold trials proving
`max_source_file_lines=662` passes while `661` fails on
`src/app/contracts/reporting_batches.py`. Full local `make check` passed with ruff, format check
over 755 files, monetary-float guard, refactor-threshold gate, workflow action-runtime gate, mypy
over 536 source files, Workbench contract smoke, and 1,220 unit/contract tests. Full local
`make ci` passed with migration contract smoke, 209 integration tests, 1,429 combined coverage
tests, 94.32% total coverage, and no known vulnerabilities after the governed `PYSEC-2026-161`
exception. GitHub checks passed, PR #447 was merged to `main`, and post-merge wiki publication
completed with `DiffCount 0`.

The performance/reporting contract-boundary branch splits performance workspace common,
summary-response, and details-response contracts behind the existing
`src/app/contracts/performance_workspace.py` compatibility facade, reducing that facade to 79
script-counted lines. It also splits report-batch examples, shared status literals,
materialization/status/control contracts, worker runtime contracts, and scheduler contracts behind
the existing `src/app/contracts/reporting_batches.py` compatibility facade, reducing that facade to
75 script-counted lines. The branch ratchets the source-file threshold to 658 script-counted lines.
Focused validation passed with 18 reporting/performance contract and boundary tests,
`python scripts/check_monetary_float_usage.py --update-allowlist`, the monetary-float guard with
159 allowlisted findings, and refactor-threshold trials proving `max_source_file_lines=658` passes
while `657` fails on `src/app/services/proposal_service.py`. Full local `make check` passed with
ruff, format check over 764 files, monetary-float guard, refactor-threshold gate, workflow
action-runtime gate, mypy over 544 source files, OpenAPI smoke, and 1,225 unit/contract tests.
Full local `make ci` passed with migration contract smoke, 209 integration tests, 1,434 combined
coverage tests, 94.33% total coverage, and no known vulnerabilities after the governed
`PYSEC-2026-161` exception. GitHub checks passed, PR #448 was merged to `main`, and post-merge
wiki publication completed with `DiffCount 0`.

The same branch was validated against the live canonical front-office stack after rebuilding the
`lotus-gateway` container, restoring the canonical `lotus-advise` runtime after an initial
missing-container failure, and reseeding `PB_SG_GLOBAL_BAL_001`. `npm run live:validate` passed for
`PB_SG_GLOBAL_BAL_001` and `BMK_PB_GLOBAL_BALANCED_60_40`, writing evidence to
`lotus-workbench/output/playwright/live-canonical/live-validation-summary.json` generated at
`2026-06-18T14:46:17.019Z`: the summary records 94 API checks, 29 screenshots, 25 ready panel
classifications, 2 calculation checks, 28 supportability checks, 10 workflow-pack checks, and 12
advisory journey checks.

The proposal service-boundary branch moves submit, risk approval, compliance approval, client
consent, and shared approval-payload orchestration into
`src/app/services/proposal_transition_service.py` while preserving the public `ProposalService`
method surface. `src/app/services/proposal_service.py` is reduced from 658 to 520 script-counted
lines, and the blocking source-file threshold is ratcheted to 646 script-counted lines. Focused
validation passed with 42 proposal-service, service-boundary, and threshold tests, and
refactor-threshold trials prove `max_source_file_lines=646` passes while `645` fails on
`src/app/contracts/advisor_brief.py`. Full local `make check` passed with ruff, format check over
765 files, monetary-float guard, refactor-threshold gate, workflow action-runtime gate, mypy over
545 source files, OpenAPI smoke, and 1,226 unit/contract tests. Full local `make ci` passed with
migration contract smoke, 209 integration tests, 1,435 combined coverage tests, 94.32% total
coverage, and no known vulnerabilities after the governed `PYSEC-2026-161` exception. GitHub
checks and post-merge wiki publication remain pending for this branch.

The advisor-brief contract-boundary branch moves Advisor Brief presentation/source item contracts
into `src/app/contracts/advisor_brief_items.py` and source-supportability contracts into
`src/app/contracts/advisor_brief_supportability.py` while preserving the public
`app.contracts.advisor_brief` import surface. `src/app/contracts/advisor_brief.py` is reduced from
646 to 398 script-counted lines, and the blocking source-file threshold is ratcheted to 639
script-counted lines. Focused validation passed with 39 contract-boundary, threshold, Advisor Brief
service/supportability, and Workbench contract tests plus mypy over 547 source files.
Refactor-threshold trials prove `max_source_file_lines=639` passes while `638` fails on
`src/app/services/performance_workspace_service.py`. Full local `make check` passed with ruff,
format check over 767 files, monetary-float guard, refactor-threshold gate, workflow action-runtime
gate, mypy over 547 source files, Workbench/OpenAPI contract smoke, and 1,227 unit/contract tests.
Full local `make ci` passed with migration contract smoke, 209 integration tests, 1,436 combined
coverage tests, 94.33% total coverage, and no known vulnerabilities after the governed
`PYSEC-2026-161` exception. GitHub checks and post-merge wiki publication remain pending for this
branch.

The performance workspace boundary branch moves detail-view orchestration into
`src/app/services/performance_workspace_detail_views.py` while preserving the public
`PerformanceWorkspaceService` surface. It reduces `src/app/services/performance_workspace_service.py`
below the previous top-file ceiling and ratchets the blocking source-file threshold to 632
script-counted lines. Focused validation passed with 69 targeted performance workspace
detail/service-boundary/threshold tests. Full local `make check` passed with ruff, format check over 769 files,
monetary-float guard, refactor threshold gate, workflow action-runtime baseline, mypy over 548
source files, OpenAPI smoke, and 1,231 unit/contract tests. Full local `make ci` passed with
migration contract smoke, 209 integration tests, 1,440 combined coverage tests, 94.33% total
coverage, and no known vulnerabilities after the governed `PYSEC-2026-161` exception.
Refactor-threshold trials prove `max_source_file_lines=632` passes while `631` fails on
`src/app/router_registry.py` and `src/app/services/risk_workspace_service.py`.

The prior DPM router-group boundary branch moved DPM command-center, campaign, proof-pack,
construction, and wave router registration groups into `src/app/router_groups/dpm.py` while
preserving concrete route registration order in `src/app/router_registry.py`. Focused validation
passed with ruff check, ruff format check, 29 router-boundary and DPM command-center/wave contract
tests, and refactor-threshold trials proving `max_source_file_lines=632` still passes while `631`
now fails only on `src/app/services/risk_workspace_service.py`. Full local `make check` passed with
ruff, format check over 770 files, monetary-float guard, refactor threshold gate, workflow
action-runtime baseline, mypy over 549 source files, OpenAPI smoke, and 1,233 unit/contract tests.
Full local `make ci` passed with migration contract smoke, 209 integration tests, 1,442 combined
coverage tests, 94.33% total coverage, and no known vulnerabilities after the governed
`PYSEC-2026-161` exception. The same branch was validated against the live canonical
front-office stack after rebuilding the Docker-backed Gateway and downstream stack:
`lotus-workbench/output/playwright/live-canonical-dpm-router-boundary/live-validation-summary.json`
passed for `PB_SG_GLOBAL_BAL_001` with 94 API checks, 2 calculation checks, 29 screenshots,
25/25 ready panel classifications, 28 supportability checks, 10 workflow-pack checks, no missing
or non-ready panels, 9/9 RFC36-43 features validated, and 0 RFC36-43 gaps. Companion
observability evidence at `lotus-workbench/output/observability-live/20260619-083718/observability-evidence-manifest.json`
captured 13/13 DNS checks, 13/13 representative API checks, 4/4 metrics checks, 14 log artifacts,
and the validation summary link. GitHub checks and post-merge wiki publication remain pending for
this branch.

The current risk workspace cache-boundary branch moves risk workspace cache-key construction and
replay-time cache-status/correlation stamping into `src/app/services/risk_workspace_cache.py` while
preserving risk workspace response behavior. The branch ratchets the blocking source-file threshold
from 632 to 630 script-counted lines. Focused validation passed with ruff check, ruff format check,
mypy over the touched risk workspace service modules, 54 risk workspace cache/service/boundary/
threshold tests, and refactor-threshold trials proving `max_source_file_lines=630` passes while
`629` fails only on `src/app/services/advisory_client_protocols.py`. Full local `make check`
passed with ruff, format check over 772 files, monetary-float guard, refactor threshold gate,
workflow action-runtime baseline, mypy over 550 source files, OpenAPI smoke, and 1,236
unit/contract tests. Full local `make ci` passed with migration contract smoke, 209 integration
tests, 1,445 combined coverage tests, 94.33% total coverage, and no known vulnerabilities after the
governed `PYSEC-2026-161` exception. Branch-specific live canonical validation passed after
rebuilding the Docker-backed Gateway and downstream stack:
`lotus-workbench/output/playwright/live-canonical-risk-workspace-cache-boundary/live-validation-summary.json`
records 94 API checks, 2 calculation checks, 29 screenshots, 25/25 ready panel classifications,
28 supportability checks, 10 workflow-pack checks, no missing or non-ready panels, 9/9 RFC36-43
features validated, and 0 RFC36-43 gaps. Companion observability evidence at
`lotus-workbench/output/observability-live/risk-workspace-cache-boundary-20260619/observability-evidence-manifest.json`
records 13/13 DNS checks, 13/13 representative API checks, 4/4 metric checks, 14 log artifacts,
and 5/5 observability screenshots. GitHub checks and post-merge wiki publication remain pending
for this branch.

The current advisory protocol-boundary branch splits the mixed advisory client protocol surface
into focused bank-demo proof, copilot, workspace, cockpit, policy, and proposal protocol modules.
The public `app.services.advisory_client_protocols` facade remains for compatibility, while
advisory services import their focused protocol families directly. The branch ratchets the
blocking source-file threshold from 630 to 628 script-counted lines. Focused validation passed with
ruff check, mypy over `src`, 67 protocol/service-boundary tests, and refactor-threshold trials
proving `max_source_file_lines=628` passes while `627` fails only on
`src/app/clients/dpm_wave_client.py`. Full local `make check` passed with ruff, format check over
779 files, monetary-float guard, refactor threshold gate, workflow action-runtime baseline, mypy
over 556 source files, OpenAPI smoke, and 1,239 unit/contract tests. Full local `make ci` passed
with migration contract smoke, 209 integration tests, 1,448 combined coverage tests, 94.30% total
coverage, and no known vulnerabilities after the governed `PYSEC-2026-161` exception. GitHub
checks and post-merge wiki publication remain pending for this branch. Branch-specific live
canonical validation passed after rebuilding the Docker-backed Gateway and downstream stack, then
rerunning after performance lineage materialization completed:
`lotus-workbench/output/playwright/live-canonical-advisory-protocol-boundaries-rerun/live-validation-summary.json`
records 95 API checks, 2 calculation checks, 29 screenshots, 25/25 ready panel classifications,
28 supportability checks, 10 workflow-pack checks, no missing or non-ready panels, 9/9 RFC36-43
features validated, and 0 RFC36-43 gaps. Companion observability evidence at
`lotus-workbench/output/observability-live/advisory-protocol-boundaries-rerun/observability-evidence-manifest.json`
records 13/13 DNS checks, 13/13 representative API checks, 4/4 metric checks, 14 log artifacts,
5/5 observability screenshots, Gateway correlation/request/trace IDs, 58 fan-out events, and 14
audit events. Residual data-mesh limitation is not Gateway-owned: performance contribution source
economics remains `SOURCE_LIMITED` for non-source-authored component P&L economics.

The current DPM wave client-boundary branch splits Manage rebalance-wave core,
campaign-definition, and campaign-workflow route forwarding into focused client mixins behind the
public `DpmWaveClientMixin` compatibility facade. It reduces
`src/app/clients/dpm_wave_client.py` from 628 to 11 script-counted lines and ratchets the blocking
source-file threshold from 628 to 623 script-counted lines, making
`src/app/clients/lotus_analytics_client.py` the source-file ceiling blocker. Focused validation
passed with ruff over touched files, 8 DPM client/threshold tests, and
`python scripts/check_refactor_quality_thresholds.py` at `max_source_file_lines=623`. The Quality
Baseline workflow now runs `Enforce Refactored Source Thresholds` as a blocking step and captures
`output/quality-baseline/refactor-thresholds.txt` before uploading advisory quality reports.
All GitHub workflow jobs now declare explicit bounded `timeout-minutes` values, and the workflow
governance guard blocks missing or unbounded job timeouts alongside action-runtime and Node 24
opt-in drift.
Full local `make check` passed with workflow governance, mypy over 560 source files, OpenAPI smoke,
and 1,242 unit/contract tests. Full local `make ci` passed with migration contract smoke, 209
integration tests, 1,451 combined coverage tests, 94.30% total coverage, and no known
vulnerabilities after the governed `PYSEC-2026-161` exception.

The current analytics risk-client boundary branch splits risk calculate, concentration, drawdown,
rolling metrics, and historical-attribution forwarding into
`src/app/clients/lotus_analytics_risk_client.py` while preserving the public
`LotusAnalyticsClient` surface. It reduces `src/app/clients/lotus_analytics_client.py` from 623 to
560 script-counted lines and ratchets the blocking source-file threshold from 623 to 618
script-counted lines, making `src/app/services/foundation_service.py` the source-file ceiling
blocker. Local `make check` passed with workflow governance, mypy over 561 source files, OpenAPI
smoke, and 1,243 unit/contract tests.

The current Foundation catalog-payload boundary branch splits portfolio catalog item parsing into
`src/app/services/foundation_catalog_payloads.py` while preserving the public `FoundationService`
surface. It reduces `src/app/services/foundation_service.py` from 618 to 591 script-counted lines
and ratchets the blocking source-file threshold from 618 to 610 script-counted lines, making
`src/app/clients/lotus_core_query_client.py` the source-file ceiling blocker. Focused validation
passed with 26 Foundation catalog/service and quality-threshold tests. Full local `make check`
passed with workflow governance, mypy over 562 source files, OpenAPI smoke, and 1,245 unit/contract
tests.

The current Lotus Core lookup-client boundary branch splits portfolio, instrument, and currency
lookup forwarding into `src/app/clients/lotus_core_lookup_client.py` while preserving the public
`LotusCoreQueryClient` surface. It reduces `src/app/clients/lotus_core_query_client.py` from 610 to
535 script-counted lines and ratchets the blocking source-file threshold from 610 to 606
script-counted lines, making `src/app/services/dpm_client_protocols.py` the source-file ceiling
blocker. Focused validation passed with 188 upstream/core client tests. Full local `make check`
passed with workflow governance, mypy over 563 source files, OpenAPI smoke, and 1,246 unit/contract
tests.

The current DPM wave protocol-family boundary branch splits `DpmWaveClient` into
`src/app/services/dpm_wave_client_protocols.py` and updates DPM wave services to import that focused
protocol module directly. It reduces `src/app/services/dpm_client_protocols.py` from 606 to 322
script-counted lines and ratchets the blocking source-file threshold from 606 to 595 script-counted
lines, making `src/app/contracts/dpm_command_center.py` the source-file ceiling blocker. Focused
validation passed with 52 DPM wave/service-boundary tests. Full local `make check` passed with
workflow governance, mypy over 564 source files, OpenAPI smoke, and 1,248 unit/contract tests.

The current DPM portfolio-memory contract-family boundary branch splits
`DpmPortfolioMemorySupportability` and `DpmPortfolioMemoryGatewayResponse` into
`src/app/contracts/dpm_portfolio_memory.py` while preserving the public `dpm_command_center`
compatibility facade. It moves the largest residual source-file hotspot to
`src/app/services/foundation_service.py` at 591 script-counted lines and ratchets the blocking
source-file threshold from 595 to 591 script-counted lines. Focused validation passed with 59
contract/service tests and 67 contract/service/quality tests after adding threshold artifact
assertions. Full local `make check` passed with workflow governance, mypy over 565 source files,
OpenAPI smoke, and 1,249 unit/contract tests.

The previous analytics/catalog boundary branch moves analytics workspace-summary request payload
construction into `src/app/clients/lotus_analytics_workspace_payloads.py` and portfolio catalog
response loading into `src/app/services/portfolio_catalog_payloads.py` while preserving public
client and `PortfolioService` behavior. It reduces `src/app/clients/lotus_analytics_client.py`
from 689 to 623 script-counted lines and `src/app/services/portfolio_service.py` from 689 to 680
script-counted lines, moves the largest residual source-file hotspot to
`src/app/services/workbench_service.py` at 685 script-counted lines, and ratchets the source-file
threshold to 685 script-counted lines. Focused validation passed with ruff check, ruff format
check, mypy over the touched analytics client/payload and portfolio service/catalog modules, 233
focused upstream-client and portfolio service/catalog tests, and refactor-threshold trials proving
`max_source_file_lines=685` passes while `684` fails on
`src/app/services/workbench_service.py`. Full local `make check` and `make ci` passed:
`make check` covered ruff, format check over 746 files, monetary-float guard,
refactor-threshold gate, workflow action-runtime gate, mypy over 529 source files, OpenAPI smoke,
and 1,216 unit/contract tests; `make ci` covered migration contract smoke, 209 integration tests,
1,425 combined coverage tests, 94.29% total coverage, and no known vulnerabilities after the
governed `PYSEC-2026-161` exception.

The same branch was validated against the live canonical front-office stack after rebuilding the
`lotus-gateway` container from the branch. `Validate-LotusFrontOfficeCanonical.ps1` passed for
`PB_SG_GLOBAL_BAL_001` and `BMK_PB_GLOBAL_BALANCED_60_40`, writing evidence to
`lotus-workbench/output/playwright/live-canonical-gateway-client-catalog/`: the summary records 29
screenshots, 25 ready panel classifications, 2 calculation checks, 28 supportability checks, and
10 workflow-pack checks. Companion observability evidence in
`lotus-workbench/output/observability-live/20260618-190935/` records 13/13 API checks at HTTP 200,
4/4 metric checks at HTTP 200, 14 log artifacts, and 5/5 observability screenshots at HTTP 200.

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
