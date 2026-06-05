# Quality Baseline Report

Date: 2026-06-05
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
It is intended to make quality debt visible before introducing stricter CI gates. Findings are not
yet enforced unless they are already covered by existing repo-native gates.

## Repository Size

| Measure | Current value |
| --- | ---: |
| Counted files under `src`, `tests`, `docs`, `wiki`, `.github`, `scripts` | 676 |
| Python source files under `src/app` | 443 |
| Python test files under `tests` | 158 |
| OpenAPI paths | 233 |
| OpenAPI operations | 247 |

## Largest Source Files

| Rank | Lines | File |
| ---: | ---: | --- |
| 1 | 3,183 | `src/app/services/portfolio_service.py` |
| 2 | 2,226 | `src/app/contracts/portfolio.py` |
| 3 | 2,043 | `src/app/contracts/risk_workspace.py` |
| 4 | 1,840 | `src/app/contracts/reporting.py` |
| 5 | 1,712 | `src/app/services/performance_workspace_service.py` |
| 6 | 1,606 | `src/app/contracts/performance_workspace.py` |
| 7 | 1,581 | `src/app/services/advisor_brief_service.py` |
| 8 | 1,362 | `src/app/clients/dpm_client.py` |
| 9 | 1,217 | `src/app/services/dpm_command_center_service.py` |
| 10 | 1,098 | `src/app/clients/advise_client.py` |

## Largest Functions

| Rank | Lines | Function | File |
| ---: | ---: | --- | --- |
| 1 | 54 | `_unpack_optional_upstream` | `src/app/services/foundation_service.py` |
| 2 | 54 | `_raise_archive_error` | `src/app/services/archive_document_service.py` |
| 3 | 54 | `_map_drawdown_period_results` | `src/app/services/risk_workspace_drawdown.py` |
| 4 | 54 | `_build_performance_workspace_response` | `src/app/services/performance_workspace_service.py` |
| 5 | 54 | `_build_attribution_trend_request_context` | `src/app/services/performance_workspace_service.py` |
| 6 | 53 | `parse_benchmark_catalog_result` | `src/app/services/performance_workspace_benchmarks.py` |
| 7 | 53 | `map_attribution_response` | `src/app/services/risk_workspace_attribution.py` |
| 8 | 53 | `get_portfolio_insights` | `src/app/services/portfolio_service.py` |
| 9 | 53 | `extract_current_positions` | `src/app/services/workbench_core_snapshot.py` |
| 10 | 53 | `build_performance_horizon_comparison_query` | `src/app/routers/workbench_performance_modules.py` |

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

1. Current focused branch: `tests/unit/test_http_resilience.py` passed with 15 tests.
2. Current focused branch: portfolio transaction-ledger tests passed with 4 selected tests.
3. Current focused branch: portfolio workspace tests passed with 7 selected tests.
4. Current focused branch: Lotus Core transaction client tests passed with 2 selected tests.
5. Latest merged PR-grade evidence: `make check` passed with 969 unit/contract tests.
6. Latest merged PR-grade evidence: `make ci` passed with 207 integration tests on commit `b8f01c4`.
7. Latest merged PR-grade evidence: `make ci` passed with 1,176 coverage tests on commit `b8f01c4`.
8. Coverage: 93.36%.
9. `pip-audit`: no known vulnerabilities after the governed `PYSEC-2026-161` exception.

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
2. no new function above the current longest-function baseline of 54 lines,
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

Current generated OpenAPI evidence:

| Check | Count |
| --- | ---: |
| Paths | 170 |
| Operations | 170 |
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
