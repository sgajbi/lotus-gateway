# Quality Baseline Report

Date: 2026-06-12
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
It is intended to make quality debt visible before introducing stricter CI gates. Findings are not
yet enforced unless they are already covered by existing repo-native gates.

## Repository Size

| Measure | Current value |
| --- | ---: |
| Counted files under `src`, `tests`, `docs`, `wiki`, `.github`, `scripts` | 1,297 |
| Python source files under `src/app` | 449 |
| Python test files under `tests` | 164 |
| OpenAPI paths | 233 |
| OpenAPI operations | 247 |

Working-tree verification for the current transaction page-context branch shows 1,297 files under
`src`, `tests`, `docs`, `wiki`, `.github`, and `scripts`; 449 Python source files under `src/app`;
and 164 Python test files under `tests`.

## Largest Source Files

| Rank | Lines | File |
| ---: | ---: | --- |
| 1 | 2,797 | `src/app/services/portfolio_service.py` |
| 2 | 2,123 | `src/app/contracts/portfolio.py` |
| 3 | 1,940 | `src/app/contracts/risk_workspace.py` |
| 4 | 1,731 | `src/app/contracts/reporting.py` |
| 5 | 1,607 | `src/app/services/performance_workspace_service.py` |
| 6 | 1,539 | `src/app/contracts/performance_workspace.py` |
| 7 | 1,452 | `src/app/services/advisor_brief_service.py` |
| 8 | 1,258 | `src/app/clients/dpm_client.py` |
| 9 | 1,137 | `src/app/services/dpm_command_center_service.py` |
| 10 | 1,012 | `src/app/clients/advise_client.py` |

## Largest Functions

| Rank | Lines | Function | File |
| ---: | ---: | --- | --- |
| 1 | 49 | `get_transaction_ledger` | `src/app/services/portfolio_service.py` |
| 2 | 49 | `get_portfolio_transactions` | `src/app/clients/lotus_core_query_client.py` |
| 3 | 47 | `_build_workspace_descriptor_contract` | `src/app/services/platform_capabilities_shell.py` |
| 4 | 47 | `_build_performance_workspace_response` | `src/app/services/performance_workspace_service.py` |
| 5 | 46 | `get_portfolio_360` | `src/app/services/workbench_service.py` |
| 6 | 46 | `_unpack_rebalance_supportability_summary` | `src/app/services/workbench_rebalance_snapshot.py` |
| 7 | 46 | `_performance_payload_from_result` | `src/app/services/workbench_performance_snapshot.py` |
| 8 | 46 | `_assemble_portfolio_workspace_components` | `src/app/services/portfolio_service.py` |
| 9 | 46 | `get_performance_attribution_trend` | `src/app/services/performance_workspace_service.py` |
| 10 | 46 | `build_horizon_row_return_fields` | `src/app/services/performance_workspace_horizon.py` |

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

## Tooling Availability Baseline

The local shell did not expose `radon`, `xenon`, `vulture`, `deptry`, `bandit`, `spectral`,
`lint-imports`, `interrogate`, or `pyright` as commands before this slice. `pyproject.toml` now
declares a `quality` optional dependency group for Python quality tools, and the new Quality
Baseline workflow installs Python and Node quality tooling explicitly.

## Complexity And Maintainability Gaps

Report-only complexity tools are being introduced now. Current manual size evidence already shows
large-file and long-function hotspots in service, contract, and client code.
The first enforcement candidates should be:

1. no new service file above the current largest-file baseline,
2. no new function above the current longest-function baseline of 49 lines,
3. no regression in average cyclomatic complexity after `radon` baselines are collected in CI,
4. no new architecture import-linter violations after contracts are reviewed.

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

1. no central observability runbook existed at `docs/observability.md`,
2. structured logging/audit field allowlists are documented in repository context but not yet
   scored in CI,
3. tracing propagation beyond correlation IDs is not yet governed by a blocking test,
4. metrics label-cardinality rules are not yet enforced by a static gate.

## Next Gates

1. Keep Quality Baseline workflow report-only.
2. Classify baseline findings and false positives.
3. Review uploaded quality log artifacts from GitHub Actions.
4. Promote the OpenAPI operation-governance contract test through Feature Lane evidence.
5. Fail only new regressions for remaining report-only findings.
6. Promote agreed thresholds into blocking Feature Lane and PR Merge Gate checks.
