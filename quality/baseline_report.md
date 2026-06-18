# Quality Baseline Report

Date: 2026-06-13
Repository: `lotus-gateway`  
Baseline phase: report-only

## Scope

This baseline covers the current gateway hardening state after the report-only quality governance
lane, router-registry split, performance workspace response split, and advisor-brief response
split, risk drawdown mapper split, risk rolling mapper split, risk attribution mapper split,
risk concentration mapper extraction, shared risk unavailable-envelope helper extraction, and
risk drawdown, rolling, attribution, and summary response module extraction, platform capability
normalization, shell-bootstrap, portfolio workspace-control boundary extraction, performance
horizon parser extraction, foundation core snapshot parser extraction, advisor-brief
narrative-state extraction, platform-capabilities orchestration extraction, performance
attribution trend orchestration extraction, performance evidence-view orchestration extraction,
portfolio exception-summary extraction, performance workspace capability-input extraction,
portfolio workspace assembly extraction, portfolio insight-rule extraction, performance workspace
summary/detail and horizon-context extraction, foundation workspace assembly extraction, risk
rolling/attribution orchestration extraction, shell workspace descriptor-spec extraction, and
transaction query-contract extraction, DPM exception-summary workflow extraction, advisor-brief
source talking-point and review-action extraction, portfolio workflow-action extraction, and
Workbench performance snapshot parser extraction, and horizon comparison row-field extraction.
The latest focused batch also split performance workspace summary parsing and performance
evidence-view mapping, foundation workspace response assembly, PM operating quality summary
orchestration, risk attribution supportability construction, attribution trend row parsing,
portfolio position parsing, and performance workspace request-context assembly. The current
focused batch split advisor-brief and portfolio performance route dependencies, risk drawdown
orchestration, core snapshot summary parsing, portfolio workspace response component assembly,
and risk/performance Workbench route dependency handling. The latest 50-commit hardening branch
then split shared analytics async polling, workspace-summary payload assembly, portfolio
transaction-summary context loading, transaction page loading, and portfolio book response
assembly, then split performance horizon-comparison dependency fetching and row parsing out of
the top-level service method, followed by performance summary/detail route query metadata
extraction, DPM wave PM memo payload/response extraction, and risk summary period/metric-state
extraction, followed by advisor-brief workflow-pack run profile extraction.
The latest performance slice split attribution-trend row orchestration out of the public service
method, then split benchmark-context task construction and gathered-result resolution.
The latest platform-capabilities slice split shell workspace descriptor contract construction out
of the public descriptor helper.
The latest rebalance slice split supportability result validation and summary-count merging out of
the supportability payload extractor.
The latest performance chart slice split frequency-row selection, peer-row validation, point
construction, and active-return calculation out of the public chart-point mapper.
The latest shell-bootstrap slice split supportability, freshness, evidence, versioning, and
caching section construction out of the public bootstrap helper.
The latest performance projection slice split sparkline, unavailable-state, and partial-failure
projection out of the portfolio performance snapshot mapper.
The latest contribution slice split detail-vs-summary merge selection policy out of the public
contribution summary merge mapper.
The latest risk rolling slice split supportability enrichment and fallback warning assembly out of
the public rolling response mapper.
The latest risk drawdown route slice split OpenAPI query parameter descriptors out of the public
drawdown query dependency.
The latest resilience and portfolio boundary slice split HTTP retry control helpers, portfolio
transaction-ledger payload loading, portfolio workspace source gathering, and Lotus Core
transaction query-parameter construction out of previously tied hotspot functions.
The latest performance workspace context-service slice split cache-backed overview loading,
report-window resolution, benchmark context assembly, and analytics-reference end-date fallback
into `performance_workspace_context_service.py`, reducing `performance_workspace_service.py` from
842 to 639 script-counted lines and moving the largest residual hotspot to
`contracts/dpm_command_center.py` at 841 script-counted lines.
The latest DPM PM operating-quality contract slice split PM quality request, supportability,
gateway response, and AI-summary handoff contracts into `dpm_pm_operating_quality.py`, reducing
`dpm_command_center.py` from 841 to 593 script-counted lines and moving the largest residual
hotspots to `contracts/proposals.py` and `contracts/advisor_brief.py` at 812 script-counted lines.
The latest advisor-brief/proposal contract-boundary slice split advisor-brief workflow-pack
contracts into `advisor_brief_workflow.py` and proposal lifecycle/version/workflow/approval/lineage
contracts into `proposal_lifecycle.py`, reducing `advisor_brief.py` from 812 to 646
script-counted lines and `proposals.py` from 812 to 431 script-counted lines. The largest residual
hotspot is now `services/portfolio_service.py` at 811 script-counted lines.
The latest portfolio workflow service-boundary slice moved portfolio workflow orchestration and the
latest-transaction probe into `portfolio_workflow_service.py`, reducing `portfolio_service.py` from
811 to 768 script-counted lines while preserving the public `PortfolioService` surface. The largest
residual hotspot is now `contracts/workbench.py` at 794 script-counted lines.
The latest workbench contract-boundary slice split common workbench view models, overview and
portfolio-360 responses, and sandbox/analytics contracts into dedicated modules while preserving
the public `app.contracts.workbench` facade. `workbench.py` is reduced from 794 to 47
script-counted lines, and the largest residual hotspot is now
`services/performance_workspace_evidence.py` at 771 script-counted lines.
The latest performance evidence-boundary slice split calculation evidence artifact retrieval,
lineage polling, execution refresh, payload normalization, stage/snapshot mapping, and artifact URL
construction into `services/performance_calculation_evidence.py` while preserving the public
`app.services.performance_workspace_evidence` facade. `performance_workspace_evidence.py` is
reduced from 771 to 461 script-counted lines, and the largest residual hotspot is now
`services/risk_workspace_service.py` at 769 script-counted lines.
The latest risk workspace request-context slice moved request-context dataclasses,
latest-business-day fallback, as-of date resolution, and context construction into
`services/risk_workspace_requests.py`, reducing `risk_workspace_service.py` from 769 to 633
script-counted lines. The largest residual hotspot is now `services/portfolio_service.py` at 768
script-counted lines.
The latest error-mapping slice split foundation optional-upstream unavailable handling and archive
document error response mapping into smaller, reusable helpers while preserving safe error payload
contracts.
The latest risk drawdown slice split valid result iteration and period partial-failure recording
out of the drawdown period-result mapper.
The latest performance workspace slice split response-part construction and attribution-trend
context assembly out of the remaining 54-line performance workspace orchestration helpers,
lowering the repository longest-function baseline to 53 lines.
The latest benchmark and risk attribution slice split benchmark catalog failure/option parsing
helpers and risk attribution response-part assembly out of tied 53-line mappers, reducing
`parse_benchmark_catalog_result` to 43 lines and `map_attribution_response` to 36 lines while
keeping the current longest-function baseline at 53 lines.
The latest portfolio and core snapshot slice split portfolio insight source loading and current
position projection out of tied 53-line functions, reducing `get_portfolio_insights` to 27 lines
and `extract_current_positions` to 19 lines while keeping the current longest-function baseline at
53 lines.
The latest performance router slice split horizon-comparison query metadata out of the public
dependency function, reducing `build_performance_horizon_comparison_query` to 16 lines while
keeping the current longest-function baseline at 53 lines.
The latest advisor-brief slice split repeated source-metric construction into a shared helper,
reducing `_build_source_metrics` to 48 lines and lowering the repository longest-function baseline
to 52 lines.
The latest Workbench route and analytics slice split risk concentration query metadata and
Workbench analytics response-part construction out of tied 52-line functions, reducing
`get_workbench_risk_concentration` to 26 lines and `get_workbench_analytics` to 35 lines while
keeping the current longest-function baseline at 52 lines.
The latest rebalance and readiness slice split Workbench rebalance unavailable recording and
portfolio readiness indicator assembly out of tied 52-line helpers, reducing
`_unpack_rebalance_payload` to 44 lines and `_build_readiness_indicators` to 32 lines while
keeping the current longest-function baseline at 52 lines.
The latest HTTP resilience slice split JSON retry response handling, request-error handling, and
attempt orchestration out of `request_with_retry`, lowering the repository longest-function
baseline to 51 lines while preserving focused retry behavior tests.
The latest DPM proof-pack slice split Lotus AI PM memo workflow execution and product-safe AI error
mapping out of `request_proof_pack_pm_memo`, reducing that public service method from 51 lines to
27 lines while preserving focused unit and router integration tests.
The latest portfolio readiness slice split concurrent readiness source loading into a typed
`PortfolioReadinessSources` helper, reducing `get_portfolio_readiness` from 51 lines to 28 lines
while preserving focused unit and router integration tests.
The latest performance capability slice split detail-capability assembly into a typed helper,
reducing `build_workspace_capabilities` from 51 lines to 35 lines while preserving capability
contract tests.
The latest portfolio allocation slice split raw AUM, positions, and allocation query result loading
into a typed helper, reducing `_load_portfolio_allocation_payloads` from 51 lines to 31 lines while
preserving focused unit and router integration tests.
The latest Workbench sandbox slice split optional policy feedback state assembly into a typed helper,
reducing `apply_sandbox_changes` from 51 lines to 46 lines while preserving focused unit and router
integration tests.
The latest performance evidence slice split evidence-view response resolution into a focused helper,
reducing `_build_evidence_view` from 51 lines to 33 lines and lowering the repository
longest-function baseline to 50 lines while preserving focused evidence-view tests.
The final PR-readiness batch split proposal list query metadata, Workbench rebalance unavailable
payload recording, render output-format supportability, workspace-summary request context,
benchmark catalog result parsing, chart-point row normalization, attribution result payload
parsing, comparative-summary economics normalization, analytics async poll-attempt handling, and
rolling risk request-context construction. These slices preserve public behavior, add focused
tests where new branch coverage was useful, and reduce the tracked longest-function baseline from
50 lines on `origin/main` to 49 lines at branch head `1b2a4e5`.
The current closure slice extracts portfolio position-book summary derivation, position parsing,
valuation fallback handling, cash-position summarization, and top-position ranking into
`portfolio_position_book.py`. This preserves allocation and position-book behavior while reducing
`portfolio_service.py` from 3,337 to 3,241 lines and keeping the 49-line longest-function baseline.
The current transaction-ledger slice extracts transaction-ledger request context and response-row
mapping into `portfolio_transaction_ledger.py`. This preserves ledger metadata, transaction
identifier, quantization, upstream filter, and cache behavior while reducing `portfolio_service.py`
from 3,062 to 2,993 lines and keeping the 49-line longest-function baseline.
The current Lotus Core transaction query-parameter slice extracts deterministic transaction-filter
parameter construction into `lotus_core_transaction_params.py`. This preserves the public client
signature and route contract while reducing `lotus_core_query_client.py` from 622 to 574 measured
lines and removing `_portfolio_transaction_query_params` from the top function-hotspot list.
The current portfolio liquidity payload slice extracts concurrent AUM, cash-balance, and projected
cashflow upstream loading into `portfolio_liquidity_payloads.py`. This preserves liquidity endpoint
behavior while reducing `portfolio_service.py` from 2,993 to 2,968 measured lines and removing
`_load_portfolio_liquidity_payloads` from the top function-hotspot list.
The current merged transaction request-context slice separates transaction request context and
cache-key construction from public ledger orchestration, reducing `portfolio_service.py` from
2,968 to 2,898 measured lines while preserving upstream transaction filter and cache behavior.
The current merged performance workspace response slice extracts summary-view and response-part
assembly into `performance_workspace_response.py`, reducing `performance_workspace_service.py`
from 1,724 to 1,607 measured lines while preserving the response contract.
The current merged portfolio workspace response slice extracts response component/parts models and
pure final response assembly into `portfolio_workspace_response.py`, reducing
`portfolio_service.py` from 2,898 to 2,872 measured lines while preserving the 49-line
longest-function baseline.
The current transaction client-kwargs slice moves upstream argument projection into
`portfolio_transaction_ledger.py`, reducing `portfolio_service.py` from 2,872 to 2,854 measured
lines while preserving the 49-line longest-function baseline.
The current transaction page-context slice moves income/activity transaction page defaults into
`portfolio_transaction_ledger.py`, reducing `portfolio_service.py` from 2,854 to 2,797 measured
lines while preserving the 49-line longest-function baseline and removing
`_get_portfolio_transactions_result` from the top hotspot list.
The current portfolio workspace performance parser slice moves upstream performance summary
payload parsing into `portfolio_workspace_performance.py`, reducing `portfolio_service.py` from
2,797 to 2,772 measured lines while preserving the 49-line longest-function baseline.
The current portfolio workspace rebalance parser slice moves manage-owned rebalance run and
supportability payload parsing into `portfolio_workspace_rebalance.py`, reducing
`portfolio_service.py` from 2,772 to 2,729 measured lines while preserving the 49-line
longest-function baseline.
The current portfolio source-readiness parser slice moves source-readiness bucket, reason,
supportability, and indicator mapping into `portfolio_source_readiness.py`, reducing
`portfolio_service.py` from 2,729 to 2,629 measured lines while preserving the 49-line
longest-function baseline.
The current portfolio transaction summary mapper slice moves income/activity response mapping,
money aggregation, tax bucketing, and transaction-date filtering into
`portfolio_transaction_summary.py`, reducing `portfolio_service.py` from 2,629 to 2,438 measured
lines while preserving the 49-line longest-function baseline.
The current portfolio workflow mapper slice moves workflow launch cues, readiness status labels,
empty-book action sequencing, and supported-cue action ordering into `portfolio_workflow.py`,
reducing `portfolio_service.py` from 2,438 to 2,076 measured lines while preserving the 49-line
longest-function baseline. The largest source-file hotspot is now the portfolio contract module,
not the portfolio orchestration service.
The current portfolio workflow contract slice moves readiness and workflow response contracts into
`portfolio_workflow.py`, keeps `app.contracts.portfolio` as the compatibility import surface, and
reduces `portfolio.py` from 2,226 to 1,974 measured lines while preserving OpenAPI schema names and
the 49-line longest-function baseline.
The current portfolio transaction contract slice moves transaction row and ledger response
contracts into `portfolio_transactions.py`, keeps `app.contracts.portfolio` as the compatibility
import surface, and reduces `portfolio.py` from 1,885 to 1,717 measured lines while preserving
OpenAPI schema names and the 49-line longest-function baseline.
The current portfolio performance snapshot contract slice moves the shared partial-failure DTO
and performance snapshot response models into focused contract modules, keeps
`app.contracts.portfolio` as the compatibility import surface, refreshes the governed monetary
float allowlist for the moved percentage fields, and reduces `portfolio.py` from 1,717 to 1,632
measured lines while preserving OpenAPI schema names and the 49-line longest-function baseline.
The current portfolio income/activity contract slice moves money summary, income summary, and
activity summary response models into `portfolio_activity_income.py`, keeps
`app.contracts.portfolio` as the compatibility import surface, refreshes the governed monetary
float allowlist for the moved money fields, and reduces `portfolio.py` from 1,632 to 1,464
measured lines while preserving OpenAPI schema names and the 49-line longest-function baseline.
The current portfolio holdings contract slice moves shared portfolio identity/summary models into
`portfolio_core.py` and holdings/book response models into `portfolio_holdings.py`, keeps
`app.contracts.portfolio` as the compatibility import surface, refreshes the governed monetary
float allowlist for the moved position and allocation fields, and reduces `portfolio.py` from
1,464 to 954 measured lines while preserving OpenAPI schema names and the 49-line
longest-function baseline.
The current risk drawdown contract slice moves drawdown payload models into
`risk_workspace_drawdown.py`, keeps `app.contracts.risk_workspace` as the compatibility import
surface, refreshes the governed monetary float allowlist for the moved drawdown-at-risk fields,
and reduces `risk_workspace.py` from 2,043 to 1,734 measured lines while preserving OpenAPI schema
names and the 49-line longest-function baseline.
The current reporting batch contract slice moves batch, worker-run, scheduler, and shared
reporting error-example contracts into `reporting_batches.py` and `reporting_errors.py`, keeps
`app.contracts.reporting` as the compatibility import surface, and reduces `reporting.py` from
1,840 to 1,184 measured lines while preserving OpenAPI schema names and the 49-line
longest-function baseline.
The current reporting query contract slice moves report-job list, lifecycle event, input snapshot,
upstream-call, and snapshot-lineage contracts into `reporting_query.py`, keeps
`app.contracts.reporting` as the compatibility import surface, and reduces `reporting.py` from
1,184 to 532 measured lines while preserving OpenAPI schema names and the 49-line
longest-function baseline.
The current risk concentration contract slice moves concentration payload and driver contracts
into `risk_workspace_concentration.py`, keeps `app.contracts.risk_workspace` as the compatibility
import surface, refreshes the governed monetary float allowlist for the moved concentration weight
fields, and reduces `risk_workspace.py` from 1,647 to 1,343 measured lines while preserving
OpenAPI schema names and the 49-line longest-function baseline.
The current risk rolling contract slice moves rolling metric summary, series, dependency,
period-result, request-context, and payload contracts into `risk_workspace_rolling.py`, keeps
`app.contracts.risk_workspace` as the compatibility import surface, refreshes the governed
monetary float allowlist for the moved rolling metric-value field, and reduces
`risk_workspace.py` from 1,343 to 969 measured lines while preserving OpenAPI schema names and the
49-line longest-function baseline.
The current risk attribution contract slice moves attribution control, contributor, set,
period-result, methodology-context, and payload contracts into `risk_workspace_attribution.py`,
keeps `app.contracts.risk_workspace` as the compatibility import surface, refreshes the governed
monetary float allowlist for the moved attribution contribution fields, and reduces
`risk_workspace.py` from 969 to 678 measured lines while preserving OpenAPI schema names and the
49-line longest-function baseline.
The current performance contribution contract slice moves contribution row, position, level,
smoothing-evidence, source-economics-evidence, and summary contracts into
`performance_contribution.py`, keeps `app.contracts.performance_workspace` as the compatibility
import surface, refreshes the governed monetary float allowlist for the moved performance
contribution fields, and reduces `performance_workspace.py` from 1,539 to 1,499 measured lines
while preserving OpenAPI schema names and the 49-line longest-function baseline.
The current performance attribution contract slice moves attribution row, level, reason,
residual-materiality, supportability-evidence, summary, trend-row, and trend-response contracts
into `performance_attribution.py`, keeps `app.contracts.performance_workspace` as the
compatibility import surface, refreshes the governed monetary float allowlist for the moved
performance attribution fields, and reduces `performance_workspace.py` from 1,499 to 1,101
measured lines while preserving OpenAPI schema names and the 49-line longest-function baseline.
The current performance evidence contract slice moves calculation, source-supportability, stage,
upstream-snapshot, artifact, and evidence-view contracts into `performance_evidence.py`, keeps
`app.contracts.performance_workspace` as the compatibility import surface, preserves the monetary
float allowlist without churn, and reduces `performance_workspace.py` from 1,101 to 903 measured
lines while preserving OpenAPI schema names and the 49-line longest-function baseline.
The current performance evidence-view builder slice moves evidence request context, fetch state,
source-supportability collection, durable calculation evidence fetching, and supported/partial/
unavailable evidence response resolution into `performance_workspace_evidence.py`, reducing
`performance_workspace_service.py` from 1,611 to 1,413 measured lines while preserving the
49-line longest-function baseline and the Workbench performance evidence API contract.
The current portfolio transaction-summary context slice moves reporting-window resolution, YTD
transaction pagination, defensive page-row extraction, reporting-currency fallback, and
requested-window filtering into `portfolio_transaction_summary.py`, reducing
`portfolio_service.py` from 1,970 to 1,888 physical lines while preserving income/activity summary
behavior and the 49-line longest-function baseline.
The current portfolio workspace payload mapper slice moves portfolio identity/profile projection,
workspace summary construction, cashflow outlook projection, display-name fallback, and operations
readiness projection into `portfolio_workspace_payloads.py`, reducing `portfolio_service.py` from
1,888 to 1,826 physical lines while preserving workspace response behavior and the 49-line
longest-function baseline.
The current portfolio catalog payload mapper slice moves portfolio catalog item projection,
metadata alias handling, display-name fallback, and deterministic sort order into
`portfolio_catalog_payloads.py`, reducing `portfolio_service.py` from 1,779 to 1,764 physical
lines while preserving catalog response behavior and the 49-line longest-function baseline.
The prior portfolio allocation response mapper slice moves allocation response projection and
look-through capability parsing into `portfolio_holdings_payloads.py`, reducing
`portfolio_service.py` from 1,764 to 1,740 physical lines while preserving allocation summary,
view, reporting-currency, and look-through behavior.
The current portfolio position-book response mapper slice moves position-book response assembly into
`portfolio_position_book.py`, reducing `portfolio_service.py` from 1,740 to 1,718 physical lines
while preserving resolved/requested/default as-of-date precedence, summary, full positions, and
top-position behavior.
It is intended to make quality debt visible before introducing stricter CI gates. Findings are not
yet enforced unless they are already covered by existing repo-native gates.

## Repository Size

| Measure | Current value |
| --- | ---: |
| Counted files under `src`, `tests`, `docs`, `wiki`, `.github`, `scripts` | 1,399 |
| Python source files under `src/app` | 477 |
| Python test files under `tests` | 192 |
| OpenAPI paths | 233 |
| OpenAPI operations | 247 |

Working-tree verification for the current workbench enrichment boundary branch shows 1,759 counted
files under `src`, `tests`, `docs`, `wiki`, `.github`, and `scripts`, 530 Python source files under
`src/app`, and 213 Python test files under `tests`.

## Largest Source Files

| Rank | Lines | File |
| ---: | ---: | --- |
| 1 | 680 | `src/app/services/portfolio_service.py` |
| 2 | 667 | `src/app/services/performance_workspace_horizon.py` |
| 3 | 664 | `src/app/contracts/reporting_query.py` |
| 4 | 662 | `src/app/contracts/reporting_batches.py` |
| 5 | 658 | `src/app/services/proposal_service.py` |
| 6 | 651 | `src/app/contracts/performance_workspace.py` |
| 7 | 646 | `src/app/contracts/advisor_brief.py` |
| 8 | 639 | `src/app/services/performance_workspace_service.py` |
| 9 | 632 | `src/app/router_registry.py` |
| 10 | 632 | `src/app/services/risk_workspace_service.py` |

## Largest Functions

| Rank | Lines | Function | File |
| ---: | ---: | --- | --- |
| 1 | 49 | `get_transaction_ledger` | `src/app/services/portfolio_transaction_service.py` |
| 2 | 49 | `get_portfolio_transactions` | `src/app/clients/lotus_core_query_client.py` |
| 3 | 47 | `_build_workspace_descriptor_contract` | `src/app/services/platform_capabilities_shell.py` |
| 4 | 47 | `_build_performance_workspace_response` | `src/app/services/performance_workspace_service.py` |
| 5 | 46 | `get_portfolio_360` | `src/app/services/workbench_service.py` |
| 6 | 46 | `get_performance_attribution_trend` | `src/app/services/performance_workspace_trend_service.py` |
| 7 | 46 | `build_horizon_row_return_fields` | `src/app/services/performance_workspace_horizon.py` |
| 8 | 46 | `_unpack_rebalance_supportability_summary` | `src/app/services/workbench_rebalance_snapshot.py` |
| 9 | 46 | `_performance_payload_from_result` | `src/app/services/workbench_performance_snapshot.py` |
| 10 | 46 | `get_performance_attribution_trend` | `src/app/services/performance_workspace_trend_service.py` |

## Existing Blocking Gates

Current repo-native gates already cover:

1. ruff lint and format check,
2. monetary-float governance,
3. mypy on `src`,
4. Workbench OpenAPI contract smoke and operation-governance contract checks,
5. migration contract smoke,
6. unit and contract tests,
7. integration tests,
8. coverage with an 84% floor,
9. `pip-audit` with one governed FastAPI/Starlette exception,
10. Docker build and local Docker parity in the PR Merge Gate.

Most recent local evidence:

1. Latest merged response-assembly slice: `make check` passed with ruff, format check,
   monetary-float guard, mypy over 449 source files, Workbench/OpenAPI contract smoke, and 1,001
   unit/contract tests.
2. Current focused branch: `tests/unit/test_http_resilience.py` passed with 15 tests after JSON
   retry attempt extraction.
3. Current focused branch: DPM proof-pack service tests passed with 8 tests after PM memo workflow
   execution extraction.
4. Current focused branch: DPM proof-pack router PM memo integration test passed with 1 selected
   test after PM memo workflow execution extraction.
5. Current focused branch: portfolio readiness unit tests passed with 2 selected tests after source
   loading extraction.
6. Current focused branch: portfolio readiness router integration tests passed with 2 selected
   tests after source loading extraction.
7. Current focused branch: performance workspace capability tests passed with 5 tests after detail
   capability extraction.
8. Current focused branch: portfolio allocation unit tests passed with 3 selected tests after
   query-result extraction.
9. Current focused branch: portfolio allocation router integration test passed with 1 selected test
   after query-result extraction.
10. Current focused branch: Workbench sandbox unit tests passed with 5 selected tests after policy
    state extraction.
11. Current focused branch: Workbench sandbox router integration test passed with 1 selected test
    after policy state extraction.
12. Current focused branch: performance workspace evidence-view tests passed with 3 selected tests
    after response-resolution extraction.
13. Current focused branch: portfolio transaction-ledger tests passed with 8 tests after
    transaction page-context extraction.
14. Current focused branch: portfolio workspace tests passed with 7 selected tests.
15. Current focused branch: Lotus Core transaction client tests passed with 2 selected tests.
16. Current focused branch: foundation optional-upstream tests passed with 4 selected tests.
17. Current focused branch: archive document service tests passed with 8 tests.
18. Current focused branch: risk drawdown unit tests passed with 4 selected tests.
19. Current focused branch: risk drawdown router integration test passed with 1 selected test.
20. Current focused branch: performance workspace response tests passed with 5 selected tests.
21. Current focused branch: attribution-trend unit tests passed with 3 selected tests.
22. Current focused branch: attribution-trend router integration tests passed with 3 selected tests.
23. Current focused branch: benchmark catalog module tests passed with 8 tests.
24. Current focused branch: risk attribution module tests passed with 4 tests.
25. Current focused branch: risk attribution service tests passed with 5 selected tests.
26. Current focused branch: risk attribution router integration test passed with 1 selected test.
27. Current focused branch: portfolio insight service tests passed with 6 selected tests.
28. Current focused branch: portfolio insight service/router tests passed with 8 selected tests.
29. Current focused branch: current-position unit tests passed with 5 selected tests.
30. Current focused branch: current-position router tests passed with 2 selected tests.
31. Current focused branch: performance horizon comparison router tests passed with 3 selected tests.
32. Current focused branch: advisor brief service/router tests passed with 24 selected tests.
33. Current focused branch: risk concentration router test passed with 1 selected test.
34. Current focused branch: Workbench analytics tests passed with 7 selected tests.
35. Current focused branch: Workbench rebalance tests passed with 3 selected tests.
36. Current focused branch: portfolio readiness tests passed with 4 selected tests.
37. PR #353 PR-grade evidence: `make ci` passed with 207 integration tests.
38. PR #353 PR-grade evidence: `make ci` passed with 1,209 unit, contract, and integration
    coverage tests.
39. Coverage: 93.70%, above the 84% floor.
40. `pip-audit`: no known vulnerabilities after the governed `PYSEC-2026-161` exception.
41. Current closure slice: `tests/unit/test_portfolio_position_book.py` plus focused portfolio
    service position/allocation tests passed with 9 selected tests after mapper extraction.
42. Current transaction-ledger slice: `tests/unit/test_portfolio_transaction_ledger.py` plus
    `tests/unit/test_portfolio_service.py` passed with 48 selected tests after mapper extraction.
43. Current performance workspace response slice: `tests/unit/test_performance_workspace_response.py`
    passed with direct response assembly coverage.
44. Current portfolio workspace response slice:
    `tests/unit/test_portfolio_workspace_response.py tests/unit/test_portfolio_workspace_controls.py`
    passed with 5 selected tests after response assembly extraction.
45. Current transaction client-kwargs branch: `make check` passed with ruff, format check,
    monetary-float guard, mypy over 449 source files, Workbench/OpenAPI contract smoke, and 1,002
    unit/contract tests.
46. Current transaction client-kwargs branch: `make ci` passed with 207 integration tests and
    1,209 combined coverage tests; total coverage remained 93.70%, and `pip-audit` found no known
    vulnerabilities after the governed `PYSEC-2026-161` exception.
47. Current transaction page-context branch: `make check` passed with ruff, format check,
    monetary-float guard, mypy over 449 source files, Workbench/OpenAPI contract smoke, and 1,003
    unit/contract tests.
48. Current transaction page-context branch: `make ci` passed with 207 integration tests and 1,210
    combined coverage tests; total coverage remained 93.70%, and `pip-audit` found no known
    vulnerabilities after the governed `PYSEC-2026-161` exception.
49. Current portfolio workspace performance parser branch: `make check` passed with ruff, format
    check, monetary-float guard, mypy over 450 source files, Workbench/OpenAPI contract smoke, and
    1,008 unit/contract tests.
50. Current portfolio workspace performance parser branch: `make ci` passed with 207 integration
    tests and 1,215 combined coverage tests; total coverage is 93.74%, and `pip-audit` found no
    known vulnerabilities after the governed `PYSEC-2026-161` exception.
51. Current portfolio workspace rebalance parser branch: `make check` passed with ruff, format
    check, monetary-float guard, mypy over 451 source files, Workbench/OpenAPI contract smoke, and
    1,014 unit/contract tests.
52. Current portfolio workspace rebalance parser branch: `make ci` passed with 207 integration
    tests and 1,221 combined coverage tests; total coverage is 93.78%, and `pip-audit` found no
    known vulnerabilities after the governed `PYSEC-2026-161` exception.
53. Current portfolio source-readiness parser branch: `make check` passed with ruff, format check,
    monetary-float guard, mypy over 452 source files, Workbench/OpenAPI contract smoke, and 1,024
    unit/contract tests.
54. Current portfolio source-readiness parser branch: `make ci` passed with 207 integration tests
    and 1,231 combined coverage tests; total coverage is 93.89%, and `pip-audit` found no known
    vulnerabilities after the governed `PYSEC-2026-161` exception.
55. Current portfolio transaction summary mapper branch: focused validation passed with ruff,
    format, and 57 transaction summary, portfolio service, and transaction ledger unit tests.
56. Current portfolio transaction summary mapper branch: `make check` passed with ruff, format
    check, monetary-float guard, mypy over 453 source files, Workbench/OpenAPI contract smoke, and
    1,029 unit/contract tests.
57. Current portfolio transaction summary mapper branch: `make ci` passed with 207 integration
    tests and 1,236 combined coverage tests; total coverage is 93.95%, and `pip-audit` found no
    known vulnerabilities after the governed `PYSEC-2026-161` exception.
58. Current portfolio workflow mapper branch: focused validation passed with ruff, mypy over the
    touched service modules, diff whitespace checks, and 46 workflow/portfolio service unit tests.
59. Current portfolio workflow mapper branch: `make check` passed with ruff, format check,
    monetary-float guard, mypy over 454 source files, Workbench/OpenAPI contract smoke, and 1,031
    unit/contract tests.
60. Current portfolio workflow mapper branch: `make ci` passed with 207 integration tests and
    1,238 combined coverage tests; total coverage is 94.00%, and `pip-audit` found no known
    vulnerabilities after the governed `PYSEC-2026-161` exception.
61. Current portfolio workflow contract branch: focused validation passed with ruff, mypy over the
    touched contract/router/service modules, and 23 workflow contract/source-readiness/OpenAPI
    contract tests.
62. Current portfolio workflow contract branch: `make check` passed with ruff, format check,
    monetary-float guard, mypy over 455 source files, Workbench/OpenAPI contract smoke, and 1,032
    unit/contract tests.
63. Current portfolio workflow contract branch: `make ci` passed with 207 integration tests and
    1,239 combined coverage tests; total coverage is 94.01%, and `pip-audit` found no known
    vulnerabilities after the governed `PYSEC-2026-161` exception.
64. Current portfolio transaction contract branch: focused validation passed with ruff, mypy over
    the touched contract/router/service modules, and 17 transaction contract/ledger/OpenAPI
    contract tests.
65. Current portfolio transaction contract branch: `make check` passed with ruff, format check,
    monetary-float guard, mypy over 456 source files, Workbench/OpenAPI contract smoke, and 1,033
    unit/contract tests.
66. Current portfolio transaction contract branch: `make ci` passed with 207 integration tests and
    1,240 combined coverage tests; total coverage is 94.01%, and `pip-audit` found no known
    vulnerabilities after the governed `PYSEC-2026-161` exception.
67. Current portfolio performance snapshot contract branch: focused validation passed with ruff,
    mypy over the touched contract/router/service modules, monetary-float guard, diff whitespace
    checks, and 24 performance snapshot/workspace/OpenAPI contract tests.
68. Current portfolio performance snapshot contract branch: `make check` passed with ruff, format
    check, monetary-float guard, mypy over 458 source files, Workbench/OpenAPI contract smoke, and
    1,034 unit/contract tests.
69. Current portfolio performance snapshot contract branch: `make ci` passed with 207 integration
    tests and 1,241 combined coverage tests; total coverage is 94.01%, and `pip-audit` found no
    known vulnerabilities after the governed `PYSEC-2026-161` exception.
70. Current portfolio income/activity contract branch: focused validation passed with ruff, mypy
    over the touched contract/router/service modules, monetary-float guard, diff whitespace checks,
    and 17 income/activity summary, insight, and portfolio OpenAPI contract tests.
71. Current portfolio income/activity contract branch: `make check` passed with ruff, format
    check, monetary-float guard, mypy over 459 source files, Workbench/OpenAPI contract smoke, and
    1,035 unit/contract tests.
72. Current portfolio income/activity contract branch: `make ci` passed with 207 integration tests
    and 1,242 combined coverage tests; total coverage is 94.02%, and `pip-audit` found no known
    vulnerabilities after the governed `PYSEC-2026-161` exception.
73. Current risk drawdown contract branch: focused validation passed with ruff, format check, mypy
    over the touched contract/service modules, monetary-float guard, and 31 risk workspace
    contract/service tests.
74. Current risk drawdown contract branch: `make check` passed with ruff, format check,
    monetary-float guard, mypy over 462 source files, Workbench/OpenAPI contract smoke, and 1,041
    unit/contract tests.
75. Current risk drawdown contract branch: `make ci` passed with 207 integration tests and 1,248
    combined coverage tests; total coverage is 94.03%, and `pip-audit` found no known
    vulnerabilities after the governed `PYSEC-2026-161` exception.
76. Current reporting batch contract branch: focused validation passed with ruff, format check,
    monetary-float guard, mypy over the touched contract/router/service modules, and 40 reporting
    batch, contract, and integration tests.
77. Current reporting batch contract branch: `make check` passed with ruff, format check,
    monetary-float guard, mypy over 464 source files, Workbench/OpenAPI contract smoke, and 1,044
    unit/contract tests.
78. Current reporting batch contract branch: `make ci` passed with 207 integration tests and 1,251
    combined coverage tests; total coverage is 94.03%, and `pip-audit` found no known
    vulnerabilities after the governed `PYSEC-2026-161` exception.
79. Current performance contribution contract branch focused validation passed with ruff format,
    ruff check, mypy over the touched contract/service modules, monetary-float guard, and 33
    performance contribution/workspace/advisor brief tests.
80. Current performance contribution contract branch: `make check` passed with ruff, format check,
    monetary-float guard, mypy over 469 source files, Workbench/OpenAPI contract smoke, and 1,056
    unit/contract tests.
81. Current performance contribution contract branch: `make ci` passed with 207 integration tests
    and 1,263 combined coverage tests; total coverage is 94.04%, and `pip-audit` found no known
    vulnerabilities after the governed `PYSEC-2026-161` exception.
82. Latest merged performance attribution contract slice focused validation passed with ruff format,
    ruff check, mypy over the touched contract/service/router modules, monetary-float guard, and
    74 performance attribution/workspace/advisor brief/OpenAPI tests.
83. Latest merged performance attribution contract slice: `make check` passed with ruff, format check,
    monetary-float guard, mypy over 470 source files, Workbench/OpenAPI contract smoke, and 1,058
    unit/contract tests.
84. Latest merged performance attribution contract slice: `make ci` passed with 207 integration tests
    and 1,265 combined coverage tests; total coverage is 94.05%, and `pip-audit` found no known
    vulnerabilities after the governed `PYSEC-2026-161` exception.
85. Merged performance evidence contract branch focused validation passed with ruff format, ruff
    check, mypy over touched contract/service modules, monetary-float guard, and 18 performance
    evidence/capabilities/response tests.
86. Latest merged performance evidence contract slice: `make check` passed with ruff, format check,
    monetary-float guard, mypy over 471 source files, Workbench/OpenAPI contract smoke, and 1,059
    unit/contract tests.
87. Latest merged performance evidence contract slice: `make ci` passed with 207 integration tests and
    1,266 combined coverage tests; total coverage is 94.05%, and `pip-audit` found no known
    vulnerabilities after the governed `PYSEC-2026-161` exception.
88. Current performance evidence-view builder branch focused validation passed with ruff format,
    ruff check, mypy over touched service modules, monetary-float guard, and 51 focused
    performance evidence/service tests.
89. Current performance evidence-view builder branch: `make check` passed with ruff, format check,
    monetary-float guard, mypy over 471 source files, Workbench/OpenAPI contract smoke, and 1,063
    unit/contract tests.
90. Current performance evidence-view builder branch: `make ci` passed with 207 integration tests
    and 1,270 combined coverage tests; total coverage is 94.05%, and `pip-audit` found no known
    vulnerabilities after the governed `PYSEC-2026-161` exception.
91. Merged quality-baseline enforcement branch promoted the remediated file/function-size
    baseline into `make lint` through `scripts/check_refactor_quality_thresholds.py`.
92. `python scripts/check_refactor_quality_thresholds.py` now passes with
    `max_source_file_lines=1041` and `max_function_lines=49` after the latest threshold ratchet.
93. Merged quality-baseline enforcement branch: `make check` passed with ruff, format check,
    monetary-float guard, refactor threshold gate, mypy over 471 source files, Workbench/OpenAPI
    contract smoke, and 1,066 unit/contract tests.
94. Merged quality-baseline enforcement branch: `make ci` passed with 207 integration tests and
    1,273 combined coverage tests; total coverage is 94.05%, and `pip-audit` found no known
    vulnerabilities after the governed `PYSEC-2026-161` exception.
95. Current portfolio transaction-summary context branch focused validation passed with ruff
    check, ruff format check, mypy over touched service modules, and 51 portfolio summary/service
    unit tests.
96. Current portfolio transaction-summary context branch: `make check` passed with ruff, format
    check, monetary-float guard, refactor threshold gate, mypy over 471 source files,
    Workbench/OpenAPI contract smoke, and 1,070 unit/contract tests.
97. Current portfolio transaction-summary context branch: `make ci` passed with 207 integration
    tests and 1,277 combined coverage tests; total coverage is 94.08%, and `pip-audit` found no
    known vulnerabilities after the governed `PYSEC-2026-161` exception.
98. Current portfolio workspace payload mapper branch focused validation passed with ruff check,
    ruff format check, mypy over touched service modules, and 48 portfolio workspace/service unit
    tests.
99. Current portfolio workspace payload mapper branch: `make check` passed with ruff, format
    check, monetary-float guard, refactor threshold gate, mypy over 472 source files,
    Workbench/OpenAPI contract smoke, and 1,075 unit/contract tests.
100. Current portfolio workspace payload mapper branch: `make ci` passed with 207 integration
     tests and 1,282 combined coverage tests; total coverage is 94.07%, and `pip-audit` found no
     known vulnerabilities after the governed `PYSEC-2026-161` exception.
101. Current Bank-Buyable observability controls branch: `make check` passed with ruff, format
     check, monetary-float guard, refactor threshold gate, mypy over 472 source files,
     Workbench/OpenAPI contract smoke, and 1,077 unit/contract tests. `make ci` passed with 207
     integration tests and 1,284 combined coverage tests; total coverage is 94.07%, and
     `pip-audit` found no known vulnerabilities after the governed `PYSEC-2026-161` exception.
102. Current Bank-Buyable metric-label contract branch: focused validation passed with 24
     observability unit tests plus ruff, format check, and mypy over the touched observability
     module. `make check` passed with ruff, format check, monetary-float guard, refactor threshold
     gate, mypy over 472 source files, Workbench/OpenAPI contract smoke, and 1,079 unit/contract
     tests. `make ci` passed with 207 integration tests and 1,286 combined coverage tests; total
     coverage is 94.07%, and `pip-audit` found no known vulnerabilities after the governed
     `PYSEC-2026-161` exception.
103. Current Bank-Buyable error-normalization branch focused validation passed with 26 reporting
     and upstream-envelope unit tests plus ruff, format check, mypy over the reporting error mapper,
     and the refactor threshold gate. `make check` passed with ruff, format check,
     monetary-float guard, refactor threshold gate, mypy over 472 source files,
     Workbench/OpenAPI contract smoke, and 1,082 unit/contract tests. `make ci` passed with 207
     integration tests and 1,289 combined coverage tests; total coverage is 94.10%, and
     `pip-audit` found no known vulnerabilities after the governed `PYSEC-2026-161` exception.
104. Current Bank-Buyable upstream-error rule branch focused validation passed with 18
     upstream-envelope unit tests plus ruff, format check, and mypy over the shared upstream
     envelope helper. `make check` passed with ruff, format check, monetary-float guard, refactor
     threshold gate, mypy over 472 source files, Workbench/OpenAPI contract smoke, and 1,084
     unit/contract tests. `make ci` passed with 207 integration tests and 1,291 combined coverage
     tests; total coverage is 94.10%, and `pip-audit` found no known vulnerabilities after the
     governed `PYSEC-2026-161` exception.
105. Current Bank-Buyable service-error config branch focused validation passed with 31
     upstream-envelope and advisory service unit tests plus ruff, format check, and mypy over the
     shared upstream envelope helper and migrated advisory service modules. `make check` passed
     with ruff, format check, monetary-float guard, refactor threshold gate, mypy over 472 source
     files, Workbench/OpenAPI contract smoke, and 1,085 unit/contract tests. `make ci` passed with
     207 integration tests and 1,292 combined coverage tests; total coverage is 94.11%, and
     `pip-audit` found no known vulnerabilities after the governed `PYSEC-2026-161` exception.
106. Current Bank-Buyable quality-baseline artifact branch focused validation passed with 4
     quality-baseline artifact unit tests plus ruff and format checks over the new validator and
     tests. The quality-baseline workflow now validates that expected report-only logs and
     generated OpenAPI evidence exist before artifact upload, while individual quality tools remain
     report-only. `make check` passed with ruff, format check, monetary-float guard, refactor
     threshold gate, mypy over 472 source files, Workbench/OpenAPI contract smoke, and 1,089
     unit/contract tests. `make ci` passed with 207 integration tests and 1,296 combined coverage
     tests; total coverage is 94.11%, and `pip-audit` found no known vulnerabilities after the
     governed `PYSEC-2026-161` exception.
107. Current Bank-Buyable source-file threshold ratchet branch focused validation passed with the
     refactor threshold gate at `max_source_file_lines=1804`, 8 refactor-threshold/artifact unit
     tests, ruff check, and ruff format check over the touched threshold script and tests.
     `make check` passed with ruff, format check, monetary-float guard, refactor threshold gate,
     mypy over 474 source files, Workbench/OpenAPI contract smoke, and 1,114 unit/contract tests.
     `make ci` passed with 207 integration tests and 1,321 combined coverage tests; total coverage
     is 94.14%, and `pip-audit` found no known vulnerabilities after the governed
     `PYSEC-2026-161` exception.
108. Current portfolio holdings payload mapper branch focused validation passed with ruff format,
     ruff check, the refactor threshold gate, and 45 focused portfolio holdings/service unit tests.
     The slice extracts allocation-view and cash-balance payload mapping into
     `portfolio_holdings_payloads.py`, reducing `portfolio_service.py` from 1,826 to 1,779
     physical lines while preserving the 49-line longest-function baseline. The monetary-float
     allowlist was refreshed because approved quantized response float conversions moved from the
     service into the new mapper; the guard remains at 159 findings, all allowlisted. `make check`
     passed with ruff, format check, monetary-float guard, refactor threshold gate, mypy over 473
     source files, Workbench/OpenAPI contract smoke, and 1,093 unit/contract tests. `make ci`
     passed with 207 integration tests and 1,300 combined coverage tests; total coverage is
     94.10%, and `pip-audit` found no known vulnerabilities after the governed `PYSEC-2026-161`
     exception.
109. Current portfolio catalog payload mapper branch focused validation passed with ruff check and
     5 focused portfolio catalog/service unit tests. The slice extracts deterministic catalog item
     projection into `portfolio_catalog_payloads.py`, reducing `portfolio_service.py` from 1,779
     to 1,764 physical lines while preserving catalog sorting, identity metadata aliases, and
     display-name fallback behavior. `make check` passed with ruff, format check,
     monetary-float guard, refactor threshold gate, mypy over 474 source files,
     Workbench/OpenAPI contract smoke, and 1,096 unit/contract tests. `make ci` passed with 207
     integration tests and 1,303 combined coverage tests; total coverage is 94.10%, and
     `pip-audit` found no known vulnerabilities after the governed `PYSEC-2026-161` exception.
110. Prior portfolio allocation response mapper branch focused validation passed with ruff check
     and 9 focused portfolio holdings/allocation service unit tests. The slice extracts allocation
     response construction and look-through capability parsing into
     `portfolio_holdings_payloads.py`, reducing `portfolio_service.py` from 1,764 to 1,740
     physical lines while preserving allocation summary, view, reporting-currency, and
     look-through behavior. `make check` passed with ruff, format check, monetary-float guard,
     refactor threshold gate, mypy over 474 source files, Workbench/OpenAPI contract smoke, and
     1,099 unit/contract tests. `make ci` passed with 207 integration tests and 1,306 combined
     coverage tests; total coverage is 94.13%, and `pip-audit` found no known vulnerabilities
     after the governed `PYSEC-2026-161` exception.
111. Current portfolio position-book response mapper branch focused validation passed with ruff
     check and 47 focused portfolio position-book/service unit tests. The slice extracts
     position-book response construction into `portfolio_position_book.py`, reducing
     `portfolio_service.py` from 1,740 to 1,718 physical lines while preserving summary,
     top-position, full-position, and resolved/requested/default as-of-date behavior. `make check`
     passed with ruff, format check, monetary-float guard, refactor threshold gate, mypy over 474
     source files, Workbench/OpenAPI contract smoke, and 1,101 unit/contract tests. `make ci`
     passed with 207 integration tests and 1,308 combined coverage tests; total coverage is
     94.13%, and `pip-audit` found no known vulnerabilities after the governed `PYSEC-2026-161`
     exception.
112. Current portfolio book response assembly branch focused validation passed with ruff check,
     ruff format check, the refactor threshold gate at `max_source_file_lines=1799`, and 65
     focused portfolio book/service/router tests. The slice extracts deterministic portfolio book
     response assembly into `portfolio_book.py`, reducing `portfolio_service.py` from 1,804 to
     1,799 physical lines while preserving portfolio identity, cash-balance, allocation,
     top-position, and full-position behavior. `make check` passed with ruff, format check,
     monetary-float guard, refactor threshold gate, mypy over 475 source files,
     Workbench/OpenAPI contract smoke, and 1,115 unit/contract tests. `make ci` passed with 207
     integration tests and 1,322 combined coverage tests; total coverage is 94.14%, and
     `pip-audit` found no known vulnerabilities after the governed `PYSEC-2026-161` exception.
113. Current portfolio allocation source-loading branch focused validation passed with ruff check,
     ruff format check, the refactor threshold gate at `max_source_file_lines=1743`, and 71
     focused portfolio holdings/service/router tests. The slice extracts allocation source loading
     into `portfolio_holdings_payloads.py`, reducing `portfolio_service.py` from 1,799 to 1,743
     physical lines while preserving AUM, positions, allocation, look-through, reporting-currency,
     and product-safe unavailable-detail behavior. `make check` passed with ruff, format check,
     monetary-float guard, refactor threshold gate, mypy over 475 source files,
     Workbench/OpenAPI contract smoke, and 1,116 unit/contract tests. `make ci` passed with 207
     integration tests and 1,323 combined coverage tests; total coverage is 94.14%, and
     `pip-audit` found no known vulnerabilities after the governed `PYSEC-2026-161` exception.
114. Current portfolio position source-loading branch focused validation passed with ruff check,
     ruff format check, the refactor threshold gate at `max_source_file_lines=1728`, and 50
     focused portfolio holdings/service unit tests. The slice extracts position-book source
     loading into `portfolio_holdings_payloads.py`, reducing `portfolio_service.py` from 1,743 to
     1,728 physical lines while preserving AUM, positions, projection, reporting-currency, and
     product-safe unavailable-detail behavior. `make check` passed with ruff, format check,
     monetary-float guard, refactor threshold gate, mypy over 475 source files, Workbench/OpenAPI
     contract smoke, and 1,117 unit/contract tests. `make ci` passed with 207 integration tests
     and 1,324 combined coverage tests; total coverage is 94.14%, and `pip-audit` found no known
     vulnerabilities after the governed `PYSEC-2026-161` exception.
115. Current portfolio workspace source-loading branch focused validation passed with ruff check,
     ruff format check, touched-module mypy, the refactor threshold gate at
     `max_source_file_lines=1659`, and 44 focused portfolio workspace/service unit tests. The
     slice extracts workspace source and analytics fan-out into `portfolio_workspace_sources.py`,
     reducing `portfolio_service.py` from 1,728 to 1,659 physical lines while preserving
     portfolio, AUM, support overview, projected cashflow, cash-balance, readiness, performance,
     rebalance, and rebalance-supportability call shapes. Local `make check` passed with ruff,
     format check, monetary-float guard, refactor threshold gate, workflow action-runtime gate,
     mypy over 476 source files, Workbench/OpenAPI contract smoke, and 1,119 unit/contract tests.
     Local `make ci` passed with 207 integration tests and 1,326 combined coverage tests; total
     coverage is 94.16%, and `pip-audit` found no known vulnerabilities after the governed
     `PYSEC-2026-161` exception.
116. Prior advisor-brief source mapper branch focused validation passed with ruff check, ruff
     format check, `scripts/check_refactor_quality_thresholds.py` at
     `max_source_file_lines=1659`, and 37 focused advisor-brief/source/boundary/threshold unit
     tests. The slice extracts source-context, fallback narrative, source-metric, supportability,
     route, and AI fact-bundle shaping into `advisor_brief_source.py`, reducing
     `advisor_brief_service.py` from 1,454 to 861 physical lines while preserving
     workflow-pack runtime orchestration in the service. Local `make check` passed with ruff,
     format check, monetary-float guard, refactor threshold gate, workflow action-runtime gate,
     mypy over 477 source files, Workbench/OpenAPI contract smoke, and 1,123 unit/contract tests.
     Local `make ci` passed with 207 integration tests and 1,330 combined coverage tests; total
     coverage is 94.18%, and `pip-audit` found no known vulnerabilities after the governed
     `PYSEC-2026-161` exception.
117. Current portfolio readiness/insight source-loading branch focused validation passed with
     ruff check, ruff format check, touched-module mypy,
     `scripts/check_refactor_quality_thresholds.py` at `max_source_file_lines=1607`, and 62
     focused helper/service/boundary/threshold unit tests. The slice extracts readiness and
     insight source fan-out bundle construction into `portfolio_readiness_insight_sources.py`,
     reducing `portfolio_service.py` from 1,659 to 1,607 script-counted lines while preserving
     workspace, source-readiness, positions, allocations, transaction-probe, and activity-summary
     request behavior. Local `make check` passed with ruff, format check, monetary-float guard,
     refactor threshold gate, workflow action-runtime gate, mypy over 478 source files,
     Workbench/OpenAPI contract smoke, and 1,126 unit/contract tests. Local `make ci` passed with
     207 integration tests and 1,333 combined coverage tests; total coverage is 94.19%, and
     `pip-audit` found no known vulnerabilities after the governed `PYSEC-2026-161` exception.
118. Current portfolio book source-loading branch focused validation passed with ruff check,
     ruff format check, touched-module mypy,
     `scripts/check_refactor_quality_thresholds.py` at `max_source_file_lines=1589`, and 64
     focused helper/service/boundary/threshold unit tests. The slice extracts portfolio book
     source fan-out bundle construction into `portfolio_book_sources.py`, reducing
     `portfolio_service.py` from 1,607 to 1,589 script-counted lines while preserving allocation,
     position, cash-balance, portfolio-profile, projection, and reporting-currency request
     behavior. Local `make check` passed with ruff, format check, monetary-float guard, refactor
     threshold gate, workflow action-runtime gate, mypy over 479 source files,
     Workbench/OpenAPI contract smoke, and 1,128 unit/contract tests. Local `make ci` passed with
     207 integration tests and 1,335 combined coverage tests; total coverage is 94.20%, and
     `pip-audit` found no known vulnerabilities after the governed `PYSEC-2026-161` exception.
119. Current portfolio service wrapper-cleanup branch focused validation passed with ruff check,
     ruff format check, touched-module mypy, the refactor threshold gate at
     `max_source_file_lines=1553`, and 68 focused service/boundary/threshold/docs unit tests. The
     slice removes stale local pass-through wrappers for portfolio identity/profile parsing,
     workspace control-capability construction, optional text conversion, and unused optional-int
     conversion, reducing `portfolio_service.py` from 1,589 to 1,553 script-counted lines while
     preserving direct use of the extracted helper modules. Local `make check` passed with ruff,
     format check, monetary-float guard, refactor threshold gate, workflow action-runtime gate,
     mypy over 479 source files, Workbench/OpenAPI contract smoke, and 1,129 unit/contract tests.
     Local `make ci` passed with 207 integration tests and 1,336 combined coverage tests; total
     coverage is 94.24%, and `pip-audit` found no known vulnerabilities after the governed
     `PYSEC-2026-161` exception.
120. Prior merged portfolio upstream-payload extraction branch focused validation passed with ruff
     check, ruff format check, touched-module mypy, the refactor threshold gate at
     `max_source_file_lines=1489`, and 63 focused service/boundary/helper unit tests. The slice
     moves portfolio-specific payload requiring, optional partial-failure recording, product-safe
     upstream error detail construction, and client-error mapping into
     `portfolio_upstream_payloads.py`, reducing `portfolio_service.py` from 1,553 to 1,489
     script-counted lines while preserving upstream response behavior and partial-failure shape.
     Local `make check` passed with ruff, format check, monetary-float guard, refactor threshold
     gate, workflow action-runtime gate, mypy over 480 source files, Workbench/OpenAPI contract
     smoke, and 1,134 unit/contract tests. Local `make ci` passed with 207 integration tests,
     1,341 combined coverage tests, 94.24% total coverage, and no known vulnerabilities after the
     governed `PYSEC-2026-161` exception.
121. Current portfolio readiness-response extraction branch focused validation passed with ruff
     check, touched-module mypy, 46 service/readiness unit tests, and a trial refactor threshold
     gate at `max_source_file_lines=1477`. The slice moves source-owned readiness response
     construction and reporting-readiness fallback policy into
     `portfolio_readiness_response.py`, reducing `portfolio_service.py` from 1,489 to 1,453 lines
     while preserving readiness response behavior.
122. Prior performance workspace request-context extraction branch focused validation passed with
     ruff check, ruff format check, touched-module mypy, 61 service/context/boundary unit tests,
     and a trial refactor threshold gate at `max_source_file_lines=1453`. The slice moves
     workspace, horizon, and attribution-trend request-context policy into
     `performance_workspace_context.py`, reducing `performance_workspace_service.py` from 1,477
     to 1,206 script-counted lines while preserving normalization, benchmark, warning, and
     partial-failure behavior. Local `make check` passed with ruff, format check, monetary-float
     guard, refactor threshold gate, workflow action-runtime gate, mypy over 482 source files,
     Workbench/OpenAPI contract smoke, and 1,150 unit/contract tests. Local `make ci` passed with
     207 integration tests, 1,357 combined coverage tests, 94.30% total coverage, and no known
     vulnerabilities after the governed `PYSEC-2026-161` exception.
123. Current portfolio workspace component parser extraction branch focused validation passed with
     ruff check, ruff format check, touched-module mypy, 67 service/component/boundary unit tests,
     and a trial refactor threshold gate at `max_source_file_lines=1362`. The slice moves
     workspace assembly state, summary/cashflow/performance/rebalance/operations parsing,
     reporting-readiness part assembly, and resolved-as-of-date extraction into
     `portfolio_workspace_components.py`, reducing `portfolio_service.py` from 1,453 to 1,237
     script-counted lines while preserving optional-upstream warning and partial-failure behavior.
124. Current concrete-route registration fix focused validation passed with ruff check, ruff
     format check, mypy over `router_registry.py`, and 15 route/contract tests. The fix registers
     concrete `APIRoute` entries instead of FastAPI lazy included-router placeholders so route
     enumeration, route-coverage contract tests, lookup/platform TestClient requests, and
     Prometheus route-name middleware remain compatible with the current FastAPI routing runtime.
125. Current portfolio workspace component parser branch local `make check` passed with ruff,
     format check, monetary-float guard, refactor threshold gate, workflow action-runtime gate,
     mypy over 483 source files, Workbench/OpenAPI contract smoke, and 1,158 unit/contract tests.
     Local `make ci` passed with 207 integration tests, 1,365 combined coverage tests, 94.31%
     total coverage, migration contract smoke, and no known vulnerabilities after the governed
     `PYSEC-2026-161` exception.
126. Current DPM construction/proof-pack client-boundary branch focused validation passed with
     ruff check, ruff format check, touched-client mypy, 180 upstream-client and DPM client
     boundary unit tests, and the refactor threshold gate. The slice moves construction-alternative
     and proof-pack upstream route methods into `dpm_construction_client.py` and
     `dpm_proof_pack_client.py`, reducing `dpm_client.py` from 1,121 to 1,041 physical lines while
     preserving public `DpmClient` methods, idempotency headers, route paths, operation names,
     shared observed fan-out transport, and Markdown binary response decoding. Local `make check`
     passed with ruff, format check, monetary-float guard, refactor threshold gate, workflow
     action-runtime gate, mypy over 486 source files, Workbench/OpenAPI contract smoke, and 1,161
     unit/contract tests. Local `make ci` passed with 207 integration tests, 1,368 combined
     coverage tests, 94.26% total coverage, migration contract smoke, and no known vulnerabilities
     after the governed `PYSEC-2026-161` exception.
127. Current portfolio upstream-access extraction branch focused validation passed with ruff check,
     touched-module mypy, 42 portfolio service tests, and trial refactor threshold gates proving
     `max_source_file_lines=1217` passes while `1216` fails. The slice moves cached Lotus Core,
     performance, and DPM upstream result acquisition into `portfolio_upstream_access.py`,
     reducing `portfolio_service.py` from 1,237 to 980 script-counted lines while preserving
     cache keys, optional-client behavior, source fan-out call shapes, and the public
     `PortfolioService` API. Local `make check` passed with ruff, format check,
     monetary-float guard, refactor threshold gate, workflow action-runtime gate, mypy over 487
     source files, Workbench/OpenAPI contract smoke, and 1,161 unit/contract tests. Local
     `make ci` passed with 207 integration tests, 1,368 combined coverage tests, 94.26% total
     coverage, migration contract smoke, and no known vulnerabilities after the governed
     `PYSEC-2026-161` exception.
128. Current DPM PM operating-quality service-boundary branch focused validation passed with ruff
     check, touched-module mypy, 48 DPM command-center service/contract tests, and trial refactor
     threshold gates proving `max_source_file_lines=1206` passes while `1205` fails. The slice
     moves PM operating-quality policy, score-run, fairness-analysis, review-action,
     summary-invocation, and AI summary workflow-pack service orchestration into
     `dpm_pm_operating_quality_service.py`, reducing `dpm_command_center_service.py` from 1,217 to
     695 script-counted lines while preserving the public `DpmCommandCenterService` surface,
     manage-owned evidence boundaries, and `lotus-ai` workflow-pack execution behavior. Local
     `make check` passed with ruff, format check, monetary-float guard, refactor threshold gate,
     workflow action-runtime gate, mypy over 488 source files, Workbench/OpenAPI contract smoke,
     and 1,161 unit/contract tests. Local `make ci` passed with 207 integration tests, 1,368
     combined coverage tests, 94.27% total coverage, migration contract smoke, and no known
     vulnerabilities after the governed `PYSEC-2026-161` exception.
129. Current performance trend service-boundary branch focused validation passed with ruff check,
     touched-module mypy, 67 performance workspace trend/horizon/attribution/context/control tests,
     and trial refactor threshold gates proving `max_source_file_lines=1098` passes while `1097`
     fails. The slice moves performance horizon-comparison and attribution-trend service
     orchestration into `performance_workspace_trend_service.py`, reducing
     `performance_workspace_service.py` from 1,206 to 842 script-counted lines while preserving the
     public `PerformanceWorkspaceService` surface. Full local `make check` passed with ruff, format
     check, monetary-float guard, refactor threshold gate, workflow action-runtime gate, mypy over
     489 source files, Workbench/OpenAPI contract smoke, and 1,162 unit/contract tests. Full local
     `make ci` passed with 207 integration tests, 1,369 combined coverage tests, 94.26% total
     coverage, migration contract smoke, and no known vulnerabilities after the governed
     `PYSEC-2026-161` exception.
130. Merged Advise bank-demo proof client-boundary branch focused validation passed with ruff
     check, ruff format check, touched-client mypy, 14 Advise client boundary/factory, bank-demo
     proof router, Advise route-coverage, and refactor-threshold tests, and the refactor threshold
     gate at `max_source_file_lines=1093`. The slice moves RFC-0028 bank-demo proof upstream route
     methods into `advise_bank_demo_proof_client.py`, reducing `advise_client.py` from 1,098 to
     1,062 script-counted lines while preserving the public `AdviseClient` surface. Full local
     `make check` passed with ruff, format check, monetary-float guard, refactor threshold gate,
     workflow action-runtime gate, mypy over 490 source files, Workbench/OpenAPI contract smoke,
     and 1,163 unit/contract tests. Full local `make ci` passed with 207 integration tests, 1,370
     combined coverage tests, 94.24% total coverage, migration contract smoke, and no known
     vulnerabilities after the governed `PYSEC-2026-161` exception.
131. Current DPM wave AI handoff boundary branch focused validation passed with ruff format check,
     ruff check, touched-module mypy, 38 DPM wave service/boundary/contract/router tests, and
     trial refactor threshold gates proving `max_source_file_lines=1062` passes while `1061`
     fails. The slice moves DPM wave PM memo and operations handoff summary workflow-pack
     orchestration into `dpm_wave_ai_handoff.py`, reducing `dpm_wave_service.py` from 1,093 to 692
     script-counted lines while preserving the public `DpmWaveService` surface. Full local
     `make check` passed with ruff, format check, monetary-float guard, refactor threshold gate,
     workflow action-runtime gate, mypy over 491 source files, Workbench/OpenAPI contract smoke,
     and 1,164 unit/contract tests. Full local `make ci` passed with 207 integration tests, 1,371
     combined coverage tests, 94.25% total coverage, migration contract smoke, and no known
     vulnerabilities after the governed `PYSEC-2026-161` exception.
132. Current Foundation core-snapshot mapper branch focused validation passed with ruff check,
     ruff format, touched-module mypy, 31 foundation/refactor unit, contract, and integration
     tests, and trial refactor threshold gates proving `max_source_file_lines=930` passes while
     `929` fails on `src/app/contracts/performance_workspace.py`. The slice moves lotus-core
     snapshot parsing, defensive payload normalization, allocation bucketing, top-position
     mapping, and market-value extraction into `foundation_core_snapshot.py`, reducing
     `foundation_service.py` from 951 to 618 script-counted lines while preserving Foundation
     workspace response behavior. Full local `make check` passed with ruff, format check,
     monetary-float guard, refactor threshold gate, workflow action-runtime gate, mypy over 498
     source files, Workbench/OpenAPI contract smoke, and 1,171 unit/contract tests. Full local
     `make ci` passed with 207 integration tests, 1,378 combined coverage tests, 94.23% total
     coverage, migration contract smoke, and no known vulnerabilities after the governed
     `PYSEC-2026-161` exception.
133. Merged performance horizon contract branch focused validation passed with ruff check, ruff
     format, touched-module mypy, 46 performance/workbench contract and integration tests, and
     trial refactor threshold gates proving `max_source_file_lines=914` passes while `913` fails
     on `src/app/clients/advise_client.py`. The slice moves benchmark option and
     horizon-comparison response models into `performance_horizon.py`, reducing
     `performance_workspace.py` from 930 to 651 script-counted lines while preserving the public
     `app.contracts.performance_workspace` import surface. Full local `make check` passed with
     1,178 unit/contract tests. Full local `make ci` passed with 209 integration tests, 1,387
     combined coverage tests, 94.18% total coverage, migration contract smoke, and no known
     vulnerabilities after the governed `PYSEC-2026-161` exception.
134. Merged Advise policy client-boundary branch focused validation passed with ruff check, ruff
     format, touched-module mypy, 187 upstream/client-boundary/policy-router tests, and trial
     refactor threshold gates proving `max_source_file_lines=872` passes while `871` fails on
     `src/app/router_registry.py`. The slice moves advisory policy-pack, policy-evaluation,
     sign-off, report-package, and AI-evidence route methods into `advise_policy_client.py`,
     reducing `advise_client.py` from 914 to 712 script-counted lines while preserving the public
     `AdviseClient` surface. Full local `make check` passed with 1,179 unit/contract tests. Full
     local `make ci` passed with 209 integration tests, 1,388 combined coverage tests, 94.16%
     total coverage, migration contract smoke, and no known vulnerabilities after the governed
     `PYSEC-2026-161` exception.
135. Merged advisory router-group branch focused validation passed with ruff check, ruff format,
     touched-module mypy, 10 router-registry/refactor-threshold tests, and the refactor threshold
     gate at `max_source_file_lines=861`. The slice moves Advise-owned route-family imports and
     group tuples into `router_groups/advisory.py`, reducing `router_registry.py` from 872 to 632
     script-counted lines while preserving concrete route registration. Full local `make check`
     passed with ruff, format check over 716 files, monetary-float guard, refactor-threshold gate,
     workflow action-runtime gate, mypy over 506 source files, OpenAPI smoke, and 1,180
     unit/contract tests. Full local `make ci` passed with 209 integration tests, 1,389 combined
     coverage tests, 94.17% total coverage, migration contract smoke, and no known vulnerabilities
     after the governed `PYSEC-2026-161` exception.
136. Merged advisor brief narrative mapper branch moves AI task-request construction, AI
     narrative parsing, fallback audit normalization, and AI evidence-reference mapping from
     `advisor_brief_service.py` into `advisor_brief_narrative.py`, reducing
     `advisor_brief_service.py` from 861 to 435 script-counted lines. Focused validation passed
     with ruff check, ruff format, 24 advisor-brief source/narrative/service unit tests, and
     refactor-threshold trials proving `max_source_file_lines=854` passes while `853` fails on
     `src/app/services/proposal_service.py`. Full local `make check` passed with ruff, format
     check over 719 files, monetary-float guard, refactor-threshold gate, workflow action-runtime
     gate, mypy over 507 source files, OpenAPI smoke, and 1,184 unit/contract tests. Full local
     `make ci` passed with 209 integration tests, 1,393 combined coverage tests, 94.22% total
     coverage, migration contract smoke, and no known vulnerabilities after the governed
     `PYSEC-2026-161` exception.
137. Current proposal memo service branch moves proposal memo create/read/projection/review,
     report-package event/request, AI-commentary request, lineage, and replay-evidence forwarding
     from `proposal_service.py` into `proposal_memo_service.py`, reducing
     `proposal_service.py` from 854 to 658 script-counted lines. Focused validation passed with
     ruff check, ruff format, 13 proposal-service unit tests, and refactor-threshold trials proving
     `max_source_file_lines=842` passes while `841` fails on
     `src/app/services/performance_workspace_service.py`. Full local `make check` passed with
     ruff, format check over 720 files, monetary-float guard, refactor-threshold gate, workflow
     action-runtime gate, mypy over 508 source files, OpenAPI smoke, and 1,184 unit/contract tests.
     Full local `make ci` passed with 209 integration tests, 1,393 combined coverage tests, 94.21%
     total coverage, migration contract smoke, and no known vulnerabilities after the governed
     `PYSEC-2026-161` exception.
138. Current performance workspace context-service branch moves cache-backed overview loading,
     report-window resolution, benchmark context assembly, and analytics-reference end-date
     fallback from `performance_workspace_service.py` into
     `performance_workspace_context_service.py`, reducing `performance_workspace_service.py` from
     842 to 639 script-counted lines. Focused validation passed with ruff check, ruff format,
     mypy over 509 source files, 36 performance workspace service unit tests, and
     refactor-threshold trials proving `max_source_file_lines=841` passes while `840` fails on
     `src/app/contracts/dpm_command_center.py`. Full local `make check` passed with ruff, format
     check over 721 files, monetary-float guard, refactor-threshold gate, workflow action-runtime
     gate, mypy over 509 source files, OpenAPI smoke, and 1,184 unit/contract tests. Full local
     `make ci` passed with 209 integration tests, 1,393 combined coverage tests, 94.22% total
     coverage, migration contract smoke, and no known vulnerabilities after the governed
     `PYSEC-2026-161` exception.
139. Current DPM PM operating-quality contract branch moves PM quality request, supportability,
     gateway response, and AI-summary handoff contracts from `dpm_command_center.py` into
     `dpm_pm_operating_quality.py`, reducing `dpm_command_center.py` from 841 to 593
     script-counted lines while preserving compatibility imports through the command-center
     facade. Focused validation passed with ruff check, ruff format, mypy over 510 source files,
     17 focused contract/boundary/threshold tests, and refactor-threshold trials proving
     `max_source_file_lines=812` passes while `811` fails on `src/app/contracts/advisor_brief.py`
     and `src/app/contracts/proposals.py`. Full local `make check` passed with ruff, format check
     over 722 files, monetary-float guard, refactor-threshold gate, workflow action-runtime gate,
     mypy over 510 source files, OpenAPI smoke, and 1,185 unit/contract tests. Full local
     `make ci` passed with migration contract smoke, 209 integration tests, 1,394 combined
     coverage tests, 94.22% total coverage, and no known vulnerabilities after the governed
     `PYSEC-2026-161` exception.
140. Current advisor-brief/proposal contract-boundary branch moves advisor-brief workflow-pack
     and task-flow contracts into `advisor_brief_workflow.py`, reducing `advisor_brief.py` from
     812 to 646 script-counted lines, and moves proposal lifecycle, version, workflow, approval,
     and lineage contracts into `proposal_lifecycle.py`, reducing `proposals.py` from 812 to 431
     script-counted lines. Compatibility imports remain through the existing advisor-brief and
     proposal facades. Focused validation passed with ruff check, ruff format, mypy over 512 source
     files, 61 advisor-brief/proposal contract/boundary/threshold tests, and refactor-threshold trials
     proving `max_source_file_lines=811` passes while `810` fails on
     `src/app/services/portfolio_service.py`. Full local `make check` passed with ruff, format
     check over 724 files, monetary-float guard, refactor-threshold gate, workflow action-runtime
     gate, mypy over 512 source files, OpenAPI smoke, and 1,187 unit/contract tests. Full local
     `make ci` passed with migration contract smoke, 209 integration tests, 1,396 combined
     coverage tests, 94.23% total coverage, and no known vulnerabilities after the governed
     `PYSEC-2026-161` exception.
141. Current portfolio workflow service-boundary branch moves portfolio workflow orchestration and
     the latest-transaction probe into `portfolio_workflow_service.py`, reducing
     `portfolio_service.py` from 811 to 768 script-counted lines while preserving the public
     `PortfolioService` surface. Focused validation passed with ruff check, ruff format, mypy over
     touched service files, 68 portfolio service/boundary/threshold tests, and refactor-threshold trials
     proving `max_source_file_lines=794` passes while `793` fails on
     `src/app/contracts/workbench.py`. Full local `make check` passed with ruff, format check over
     725 files, monetary-float guard, refactor-threshold gate, workflow action-runtime gate, mypy
     over 513 source files, OpenAPI smoke, and 1,188 unit/contract tests. Full local `make ci`
     passed with migration contract smoke, 209 integration tests, 1,397 combined coverage tests,
     94.23% total coverage, and no known vulnerabilities after the governed `PYSEC-2026-161`
     exception.
142. Previous workbench contract-boundary branch moves common workbench view models, overview and
     portfolio-360 responses, and sandbox/analytics contracts into `workbench_common.py`,
     `workbench_overview.py`, and `workbench_sandbox.py`, reducing `workbench.py` from 794 to 47
     script-counted lines while preserving the public `app.contracts.workbench` facade. Focused
     validation passed with ruff check, ruff format, mypy over touched contract modules, 118
     workbench service/router/contract-boundary/threshold tests, and the refactor-threshold gate at
     `max_source_file_lines=771`. Full local `make check` passed with ruff, format check over 728
     files, monetary-float guard, refactor-threshold gate, workflow action-runtime gate, mypy over
     516 source files, OpenAPI smoke, and 1,189 unit/contract tests. Full local `make ci` passed
     with migration contract smoke, 209 integration tests, 1,398 combined coverage tests, 94.24%
     total coverage, and no known vulnerabilities after the governed `PYSEC-2026-161` exception.
143. Current performance evidence-boundary branch extracts performance calculation evidence
     artifact retrieval, lineage polling, execution refresh, payload normalization, stage/snapshot
     mapping, and artifact URL construction into `performance_calculation_evidence.py`. The public
     `performance_workspace_evidence.py` facade is preserved for existing callers and tests, while
     the orchestration module drops from 771 to 461 script-counted lines. The blocking source-file
     threshold is ratcheted from 771 to 769 lines, making `risk_workspace_service.py` the largest
     residual source-file hotspot.
144. Current risk workspace request-context branch moves risk request-context dataclasses,
     latest-business-day fallback, as-of date resolution, and context construction into
     `risk_workspace_requests.py`. `RiskWorkspaceService` remains the orchestration and cache
     boundary, while `risk_workspace_service.py` drops from 769 to 633 script-counted lines. The
     blocking source-file threshold is ratcheted from 769 to 768 lines, making
     `portfolio_service.py` the largest residual source-file hotspot.

## Tooling Availability Baseline

The local shell did not expose `radon`, `xenon`, `vulture`, `deptry`, `bandit`, `spectral`,
`lint-imports`, `interrogate`, or `pyright` as commands before this slice. `pyproject.toml` now
declares a `quality` optional dependency group for Python quality tools, and the new Quality
Baseline workflow installs Python and Node quality tooling explicitly.
The quality-baseline artifact validator enforces that the expected report-only log set and
generated `openapi.json` exist before upload; individual quality tools remain report-only so
existing findings can still be classified from uploaded evidence.

## Complexity And Maintainability Gaps

Report-only complexity tools are being introduced now. Current manual size evidence already shows
large-file and long-function hotspots in service, contract, and client code.
The remediated size baselines are now partially enforced through `make lint`:

1. no Python source file under `src/app` above 667 script-counted lines,
2. no function or async function above the current longest-function baseline of 49 lines.

The remaining enforcement candidates should be:

1. no regression in average cyclomatic complexity after `radon` baselines are collected in CI,
2. no new architecture import-linter violations after contracts are reviewed.

## Dead Code Gaps

`vulture` is not yet part of existing blocking CI. The new workflow runs it report-only with
`--min-confidence 80`. Findings must be triaged before enforcement because routers, FastAPI
dependency injection, Pydantic models, and test fixtures can produce false positives.

## Dependency And Security Gaps

`pip-audit` is already blocking through `make security-audit`. `bandit` and `deptry` are added as
report-only quality checks. Baseline findings should be triaged before making them blocking.

## OpenAPI Gaps

Current generated OpenAPI evidence for this working-tree baseline:

| Check | Count |
| --- | ---: |
| Paths | 233 |
| Operations | 247 |
| Missing summary | 0 |
| Missing description | 0 |
| Missing operation ID | 0 |
| Missing tags | 0 |
| Missing 4xx/5xx response | 0 |
| Operation tags missing global description | 0 |
| Spectral warnings from `.spectral.yaml` plus `spectral:oas` | 186, not rerun locally |

Important nuance: operation IDs are present in generated OpenAPI, but only two explicit router
`operation_id=` declarations were found. Future governance should decide whether generated IDs are
acceptable or whether stable explicit operation IDs are required for all public endpoints.

The OpenAPI operation-governance contract test now fails if any public operation is missing a
description, tags, at least one documented 4xx/5xx response, or a global tag declaration with a
description. The first Spectral smoke found no errors. Spectral was not available in the local
shell for this update, so the warning count remains the last collected report-only baseline until
the GitHub quality-baseline workflow reruns.

## Architecture Violations And Watchlist

Existing unit tests already enforce several service-layer boundaries. `.importlinter` expands the
report-only baseline for routers, middleware, contracts, and services. A text scan found router
references matching downstream-client patterns; many may be type hints, dependency injection, or
service imports rather than concrete client construction. These must be classified before
enforcement.

## Documentation Gaps

Existing README, wiki, RFCs, and standards are substantial. Gaps now addressed by new baseline docs:

1. consolidated architecture overview at `docs/architecture.md`,
2. API governance at `docs/api-governance.md`,
3. observability at `docs/observability.md`,
4. security at `docs/security.md`,
5. operations runbook at `docs/operations-runbook.md`,
6. supported-features summary at `docs/supported-features.md`,
7. quality scorecard and health reports under `quality/`.

## Observability Gaps

Current code and docs include health, readiness, metrics, correlation, selected analytics audit
logs, and diagnostics lookup. Remaining baseline gaps:

1. analytics UI structured logging/audit field allowlists are covered by unit tests, including
   separate fan-out log and audit event-family enforcement,
2. broader structured logging/audit field allowlists are not yet scored across all gateway
   telemetry in CI,
3. tracing propagation beyond correlation IDs is not yet governed by a blocking test,
4. Prometheus collector metric-label rules are enforced by a static unit gate for gateway metric
   definitions; broader non-Prometheus telemetry label scoring remains future hardening.

## Next Gates

1. Keep Quality Baseline workflow report-only.
2. Classify baseline findings and false positives.
3. Review uploaded quality log artifacts from GitHub Actions.
4. Promote the OpenAPI operation-governance contract test through Feature Lane evidence.
5. Fail only new regressions for remaining report-only findings.
6. Promote agreed thresholds into blocking Feature Lane and PR Merge Gate checks.
