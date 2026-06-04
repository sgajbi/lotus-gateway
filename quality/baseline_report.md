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
extraction and DPM wave PM memo payload/response extraction.
It is intended to make quality debt visible before introducing stricter CI gates. Findings are not
yet enforced unless they are already covered by existing repo-native gates.

## Repository Size

| Measure | Current value |
| --- | ---: |
| Counted files under `src`, `tests`, `docs`, `wiki`, `.github`, `scripts` | 676 |
| Python source files under `src/app` | 442 |
| Python test files under `tests` | 158 |
| OpenAPI paths | 233 |
| OpenAPI operations | 247 |

## Largest Source Files

| Rank | Lines | File |
| ---: | ---: | --- |
| 1 | 3,155 | `src/app/services/portfolio_service.py` |
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
| 1 | 56 | `map_summary_response` | `src/app/services/risk_workspace_summary.py` |
| 2 | 56 | `load_advisor_brief_workflow_pack_run` | `src/app/services/advisor_brief_workflow_pack.py` |
| 3 | 56 | `get_performance_attribution_trend` | `src/app/services/performance_workspace_service.py` |
| 4 | 56 | `fetch_benchmark_context` | `src/app/services/performance_workspace_benchmarks.py` |
| 5 | 56 | `build_workspace_descriptor` | `src/app/services/platform_capabilities_shell.py` |
| 6 | 56 | `_extract_rebalance_supportability_payload` | `src/app/services/workbench_rebalance_snapshot.py` |
| 7 | 55 | `build_workspace_chart_points` | `src/app/services/performance_workspace_chart_points.py` |
| 8 | 55 | `build_shell_bootstrap` | `src/app/services/platform_capabilities_shell.py` |
| 9 | 54 | `request_with_retry` | `src/app/clients/http_resilience.py` |
| 10 | 54 | `project_portfolio_performance_snapshot` | `src/app/services/performance_workspace_projection.py` |

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

1. `make check`: 967 unit/contract tests passed on commit `6836e69`.
2. `make ci`: 207 integration tests passed on commit `e1e7980`.
3. `make ci`: 1,174 coverage tests passed on commit `e1e7980`.
4. Coverage: 93.32%.
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
2. no new function above the current longest-function baseline of 56 lines,
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
