# Quality Baseline Report

Date: 2026-06-02  
Repository: `lotus-gateway`  
Baseline phase: report-only

## Scope

This baseline covers the current gateway hardening state after the report-only quality governance
lane, router-registry split, performance workspace response split, and advisor-brief response
split, risk drawdown mapper split, and risk rolling mapper split. It is intended to make quality
debt visible before introducing stricter CI gates. Findings are not yet enforced unless they are
already covered by existing repo-native gates.

## Repository Size

| Measure | Current value |
| --- | ---: |
| Counted files under `src`, `tests`, `docs`, `wiki`, `.github`, `scripts` | 645 |
| Python source files under `src/app` | 431 |
| Python test files under `tests` | 150 |
| OpenAPI paths | 170 |
| OpenAPI operations | 170 |

## Largest Source Files

| Rank | Lines | File |
| ---: | ---: | --- |
| 1 | 3,016 | `src/app/services/portfolio_service.py` |
| 2 | 2,226 | `src/app/contracts/portfolio.py` |
| 3 | 2,063 | `src/app/services/risk_workspace_service.py` |
| 4 | 2,043 | `src/app/contracts/risk_workspace.py` |
| 5 | 1,840 | `src/app/contracts/reporting.py` |
| 6 | 1,606 | `src/app/contracts/performance_workspace.py` |
| 7 | 1,392 | `src/app/services/advisor_brief_service.py` |
| 8 | 1,362 | `src/app/clients/dpm_client.py` |
| 9 | 1,152 | `src/app/services/performance_workspace_service.py` |
| 10 | 1,098 | `src/app/clients/advise_client.py` |

## Largest Functions

| Rank | Lines | Function | File |
| ---: | ---: | --- | --- |
| 1 | 195 | `_build_normalized_capabilities` | `src/app/services/platform_capabilities_service.py` |
| 2 | 191 | `_build_workspace_control_capabilities` | `src/app/services/portfolio_service.py` |
| 3 | 172 | `parse_horizon_comparison_result` | `src/app/services/performance_workspace_horizon.py` |
| 4 | 153 | `_parse_core_snapshot` | `src/app/services/foundation_service.py` |
| 5 | 144 | `_build_advisor_brief_narrative_state` | `src/app/services/advisor_brief_service.py` |
| 6 | 143 | `get_platform_capabilities` | `src/app/services/platform_capabilities_service.py` |
| 7 | 141 | `_map_attribution_response` | `src/app/services/risk_workspace_service.py` |
| 8 | 135 | `get_performance_attribution_trend` | `src/app/services/performance_workspace_service.py` |
| 9 | 134 | `_build_shell_bootstrap` | `src/app/services/platform_capabilities_service.py` |
| 10 | 134 | `_build_evidence_view` | `src/app/services/performance_workspace_service.py` |

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

1. `make check`: 934 unit/contract tests passed.
2. `make ci`: 207 integration tests passed.
3. `make ci`: 1,141 coverage tests passed.
4. Coverage: 92.65%.
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
2. no new function above the current longest-function baseline of 195 lines,
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
