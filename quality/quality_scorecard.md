# Quality Scorecard

Date: 2026-06-12
Mode: feature-branch evidence refresh

| Dimension | Score | Current status | Next action |
| --- | ---: | --- | --- |
| Build and test reliability | 5/5 | Current branch evidence includes `make check` with ruff, format, monetary-float guard, mypy over 450 source files, contract smoke, and 1,008 unit/contract tests; `make ci` passed with 207 integration tests, 1,215 coverage tests, Docker-equivalent GitHub gates, and dependency audit | Keep Docker parity blocking in PR Merge Gate |
| Coverage | 4/5 | 93.74% total coverage, above the 84% floor | Add targeted middleware/security/error tests |
| Modularity | 4/5 | Current branch state preserves the 49-line longest-function baseline; recent slices extracted transaction request context, transaction page-context defaults, transaction client-kwargs mapping, performance workspace response assembly, portfolio workspace response assembly, portfolio workspace performance parsing, and portfolio workspace rebalance parsing; `portfolio_service.py` is now 2,729 measured lines | Continue extraction slices and reduce remaining largest-file pressure |
| Architecture boundaries | 3/5 | Blocking AST tests exist; import-linter is report-only | Classify and enforce no-new-regression |
| API governance | 4/5 | 233 OpenAPI paths and 247 operations; missing summary, description, operation ID, tags, and documented 4xx/5xx response counts are all 0; Spectral remains report-only | Triage Spectral warnings and decide explicit operation ID policy |
| Error consistency | 2/5 | ProblemDetails exists for unhandled exceptions; route/upstream error normalization remains a meaningful hardening candidate | Normalize route/upstream errors |
| Observability | 3/5 | Health/readiness/metrics/correlation/audit are present; RFC-0108 fan-out and selected analytics audit posture remain implementation-backed | Enforce structured log and metric label rules |
| Security | 4/5 | `pip-audit` passed in current branch `make ci` with the governed FastAPI/Starlette exception; no known vulnerabilities found | Triage bandit and sensitive-data handling checks |
| Documentation | 4/5 | Baseline, scorecard, health report, and wiki validation evidence are refreshed to current branch metrics after PR #355 and the current focused rebalance parser slice | Keep wiki synced and add diagrams over time |
| Operations readiness | 3/5 | Existing CI/runbook docs and wiki validation posture describe the report-only quality lane | Add incident playbooks and SLO checks |

## Before/After Evidence

Comparison point: the prior scorecard state after the portfolio liquidity payload-loader slice
versus the current portfolio workspace rebalance parser branch after PRs #349, #350, #351,
#352, #353, #354, and #355.

| Measure | Prior scorecard | Current branch | Result |
| --- | ---: | ---: | --- |
| Counted files under `src`, `tests`, `docs`, `wiki`, `.github`, `scripts` | 1,265 | 1,303 | Added focused modules, tests, and quality evidence |
| Tracked `src/app` Python files | 447 | 451 | Added focused portfolio/performance response helpers and workspace parser modules |
| Tracked Python test files | 162 | 166 | Added focused request-context, response-assembly, workspace performance parser, and workspace rebalance parser tests |
| Longest function | 49 lines | 49 lines | Preserved |
| Top function hotspot count at 49 lines | 2 | 2 | Preserved |
| Largest source file | 2,968 lines | 2,729 lines | Improved; `portfolio_service.py` remains largest residual hotspot |
| `performance_workspace_service.py` | 1,724 lines | 1,607 lines | Improved through response assembly extraction |
| OpenAPI operations with missing summary/description/tags/errors | 0 | 0 | Preserved |
| Local unit/contract tests | 996 | 1,008 | Added focused response/request boundary and workspace performance parser tests |
| Local coverage tests | 1,203 | 1,215 | Added focused coverage while preserving total coverage |
| Total coverage | 93.69% | 93.74% | Improved |
| Dependency audit | governed pass | governed pass, no known vulnerabilities after the `PYSEC-2026-161` exception | Preserved |

## Phase Gates

### Phase 1: Baseline/Report-Only

Status: active.

Required evidence:

1. baseline reports exist under `quality/`,
2. architecture and API governance rules are documented,
3. report-only CI workflow exists,
4. existing Feature Lane and PR Merge Gate remain unchanged.

### Phase 2: Fail Only New Regressions

Candidate thresholds:

1. no new missing OpenAPI summary, description, tag, or standard error response,
2. no new forbidden imports,
3. no new high-confidence dead-code findings,
4. no new high-severity bandit findings,
5. no new function above the current maximum of 49 lines and no unclassified largest-file growth
   above the current 2,729-line `portfolio_service.py` maximum.

### Phase 3: Enforce Agreed Thresholds

Candidate targets:

1. no service file above 1,500 lines,
2. no function above 150 lines without an explicit exception,
3. coverage floor moves from 84% to a governed target,
4. Spectral and import-linter become blocking.

### Phase 4: Enterprise-Readiness Gate

Candidate release checks:

1. scorecard average at least 4/5,
2. no unclassified security or architecture findings,
3. OpenAPI quality gate fully green,
4. docs/wiki/runbooks current and published,
5. operational diagnostics and SLO evidence available.
