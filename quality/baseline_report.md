# Quality Baseline Report

Date: 2026-06-04
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
and risk/performance Workbench route dependency handling.
It is intended to make quality debt visible before introducing stricter CI gates. Findings are not
yet enforced unless they are already covered by existing repo-native gates.

## Repository Size

| Measure | Current value |
| --- | ---: |
| Counted files under `src`, `tests`, `docs`, `wiki`, `.github`, `scripts` | 676 |
| Python source files under `src/app` | 442 |
| Python test files under `tests` | 158 |
| OpenAPI paths | 170 |
| OpenAPI operations | 170 |

## Largest Source Files

| Rank | Lines | File |
| ---: | ---: | --- |
| 1 | 2,795 | `src/app/services/portfolio_service.py` |
| 2 | 2,226 | `src/app/contracts/portfolio.py` |
| 3 | 2,043 | `src/app/contracts/risk_workspace.py` |
| 4 | 1,840 | `src/app/contracts/reporting.py` |
| 5 | 1,606 | `src/app/contracts/performance_workspace.py` |
| 6 | 1,541 | `src/app/services/performance_workspace_service.py` |
| 7 | 1,538 | `src/app/services/advisor_brief_service.py` |
| 8 | 1,362 | `src/app/clients/dpm_client.py` |
| 9 | 1,172 | `src/app/services/dpm_command_center_service.py` |
| 10 | 1,098 | `src/app/clients/advise_client.py` |

## Largest Functions

| Rank | Lines | Function | File |
| ---: | ---: | --- | --- |
| 1 | 74 | `list_report_jobs` | `src/app/routers/reporting_job_search.py` |
| 2 | 74 | `build_portfolio_performance_snapshot_query` | `src/app/routers/portfolio_performance.py` |
| 3 | 74 | `_post_analytics_request` | `src/app/clients/lotus_analytics_client.py` |
| 4 | 73 | `historical_snapshot_module_capabilities` | `src/app/services/portfolio_workspace_controls.py` |
| 5 | 73 | `_load_overview_enrichment` | `src/app/services/workbench_service.py` |
| 6 | 73 | `_build_attribution_trend_request_context` | `src/app/services/performance_workspace_service.py` |
| 7 | 72 | `get_summary` | `src/app/services/risk_workspace_service.py` |
| 8 | 72 | `get_performance_attribution_trend` | `src/app/routers/workbench_performance_attribution_trend.py` |
| 9 | 72 | `_build_performance_workspace_response` | `src/app/services/performance_workspace_service.py` |
| 10 | 71 | `reporting_currency_module_capabilities` | `src/app/services/portfolio_workspace_controls.py` |

## Existing Blocking Gates

Current repo-native gates already cover:

1. ruff lint and format check,
2. monetary-float governance,
3. mypy on `src`,
4. Workbench OpenAPI contract smoke,
5. migration contract smoke,
6. unit and contract tests,
7. integration tests,
8. coverage with an 84% floor,
9. `pip-audit` with one governed FastAPI/Starlette exception,
10. Docker build and local Docker parity in the PR Merge Gate.

Most recent local evidence:

1. `make check`: 967 unit/contract tests passed.
2. `make ci`: 207 integration tests passed.
3. `make ci`: 1,171 coverage tests passed.
4. Coverage: 92.84%.
5. `pip-audit`: no known vulnerabilities after the governed `PYSEC-2026-161` exception.

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
2. no new function above the current longest-function baseline of 74 lines,
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
| Missing description | 3 |
| Missing operation ID | 0 |
| Missing tags | 4 |
| Missing 4xx/5xx response | 4 |
| Spectral warnings from `.spectral.yaml` plus `spectral:oas` | 186 |

Important nuance: operation IDs are present in generated OpenAPI, but only two explicit router
`operation_id=` declarations were found. Future governance should decide whether generated IDs are
acceptable or whether stable explicit operation IDs are required for all public endpoints.

The first Spectral smoke found no errors. Most warnings are generated by the inherited
`spectral:oas` baseline for missing global tag declarations; the custom Lotus rules highlight the
same health and metrics documentation gaps listed above.

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
4. Fail only new regressions.
5. Promote agreed thresholds into blocking Feature Lane and PR Merge Gate checks.
