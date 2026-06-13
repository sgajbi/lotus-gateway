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
| Python source files under `src/app` | 474 |
| Python test files under `tests` | 188 |
| OpenAPI paths | 233 |
| OpenAPI operations | 247 |

Working-tree verification for the current portfolio position-book response mapper branch shows 1,399
files under `src`, `tests`, `docs`, `wiki`, `.github`, and `scripts`; 474 Python source files
under `src/app`; and 188 Python test files under `tests`.

## Largest Source Files

| Rank | Lines | File |
| ---: | ---: | --- |
| 1 | 1,718 | `src/app/services/portfolio_service.py` |
| 2 | 1,454 | `src/app/services/advisor_brief_service.py` |
| 3 | 1,413 | `src/app/services/performance_workspace_service.py` |
| 4 | 1,258 | `src/app/clients/dpm_client.py` |
| 5 | 1,137 | `src/app/services/dpm_command_center_service.py` |
| 6 | 1,012 | `src/app/clients/advise_client.py` |
| 7 | 1,001 | `src/app/services/dpm_wave_service.py` |
| 8 | 911 | `src/app/contracts/portfolio.py` |
| 9 | 903 | `src/app/contracts/performance_workspace.py` |
| 10 | 884 | `src/app/contracts/proposals.py` |

## Largest Functions

| Rank | Lines | Function | File |
| ---: | ---: | --- | --- |
| 1 | 49 | `get_transaction_ledger` | `src/app/services/portfolio_service.py` |
| 2 | 49 | `get_portfolio_transactions` | `src/app/clients/lotus_core_query_client.py` |
| 3 | 47 | `_build_workspace_descriptor_contract` | `src/app/services/platform_capabilities_shell.py` |
| 4 | 47 | `_build_performance_workspace_response` | `src/app/services/performance_workspace_service.py` |
| 5 | 46 | `get_portfolio_360` | `src/app/services/workbench_service.py` |
| 6 | 46 | `get_performance_attribution_trend` | `src/app/services/performance_workspace_service.py` |
| 7 | 46 | `build_horizon_row_return_fields` | `src/app/services/performance_workspace_horizon.py` |
| 8 | 46 | `_unpack_rebalance_supportability_summary` | `src/app/services/workbench_rebalance_snapshot.py` |
| 9 | 46 | `_performance_payload_from_result` | `src/app/services/workbench_performance_snapshot.py` |
| 10 | 46 | `_parse_core_snapshot` | `src/app/services/foundation_service.py` |

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
    `max_source_file_lines=1728` and `max_function_lines=49` after the latest threshold ratchet.
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
     product-safe unavailable-detail behavior. Full `make check` and `make ci` remain pre-merge
     gates and are recorded before merge.

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

1. no Python source file under `src/app` above 1,728 physical lines,
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
