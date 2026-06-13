# Quality Scorecard

Date: 2026-06-13
Mode: feature-branch evidence refresh

| Dimension | Score | Current status | Next action |
| --- | ---: | --- | --- |
| Build and test reliability | 5/5 | Current portfolio holdings payload mapper branch keeps the blocking refactor threshold gate green at the 2,000-line source-file ceiling; `make check` passed with ruff, format check, monetary-float guard, the refactor threshold gate, mypy over 473 source files, Workbench/OpenAPI contract smoke, and 1,093 unit/contract tests; `make ci` passed with 207 integration tests, 1,300 coverage tests, 94.10% total coverage, and dependency audit | Keep Docker parity blocking in PR Merge Gate |
| Coverage | 4/5 | 94.10% total coverage, above the 84% floor | Add targeted middleware/security/error tests |
| Modularity | 4/5 | Current branch state blocks regressions above the 49-line longest-function baseline and the current 2,000-line source-file ceiling; recent slices extracted transaction request context, transaction page-context defaults, transaction client-kwargs mapping, performance workspace response assembly, portfolio workspace response assembly, portfolio workspace payload mapping, portfolio holdings payload mapping, portfolio workspace performance parsing, portfolio workspace rebalance parsing, portfolio source-readiness parsing, portfolio transaction summary mapping, portfolio transaction-summary context loading, portfolio workflow mapping, portfolio workflow contracts, portfolio transaction contracts, portfolio performance snapshot contracts, portfolio income/activity contracts, portfolio holdings/book contracts, risk drawdown contracts, reporting batch contracts, reporting query contracts, risk concentration contracts, risk rolling contracts, risk attribution contracts, performance contribution contracts, performance attribution contracts, performance evidence contracts, and performance evidence-view orchestration; `portfolio_service.py` remains the largest residual hotspot | Continue extraction slices and tighten the source-file ceiling downward |
| Architecture boundaries | 3/5 | Blocking AST tests exist; import-linter is report-only | Classify and enforce no-new-regression |
| API governance | 4/5 | 233 OpenAPI paths and 247 operations; missing summary, description, operation ID, tags, and documented 4xx/5xx response counts are all 0; Spectral remains report-only | Triage Spectral warnings and decide explicit operation ID policy |
| Error consistency | 2/5 | ProblemDetails exists for unhandled exceptions; reporting job and report-batch upstream error mappings now use explicit rule tables with product-safe fallback coverage; the shared generic service-error status mapping is code-owned and tested; advisory-facing product-safe service-error defaults now use typed immutable configs; broader route/upstream error normalization remains a meaningful hardening candidate | Continue normalizing route/upstream errors |
| Observability | 3/5 | Health/readiness/metrics/correlation/audit are present; RFC-0108 fan-out and selected analytics audit posture remain implementation-backed; analytics UI validators enforce separate fan-out log and audit event families; Prometheus collector metric-label contracts are now enforced by a static unit gate | Promote broader structured log, trace, and diagnostics rules into blocking checks |
| Security | 4/5 | Current portfolio holdings payload mapper branch `pip-audit` found no known vulnerabilities after the governed `PYSEC-2026-161` exception; monetary-float guard passed after relocating approved quantized response float conversions into the holdings mapper | Triage bandit and sensitive-data handling checks |
| Documentation | 4/5 | Baseline, scorecard, health report, observability docs, API-governance docs, and CI quality-gate docs are refreshed for recent metric-label, reporting error-normalization, shared upstream-error rule, service-error config, and quality-baseline artifact hardening | Keep wiki synced and add diagrams over time |
| Operations readiness | 3/5 | Existing CI/runbook docs and wiki validation posture now distinguish report-only quality baselines from the blocking refactor threshold gate | Add incident playbooks and SLO checks |

## Before/After Evidence

Comparison point: the prior scorecard state after the portfolio liquidity payload-loader slice
versus the current portfolio holdings payload mapper branch after PRs #349, #350, #351, #352,
#353, #354, #355, #356, #357, #358, #359, #360, #361, #362, #363, #364, #365, #366, #367,
#368, #369, #370, #371, #372, #373, #374, #375, #376, #377, #378, #379, #380, #381, #382, and
#383 plus the current branch.

| Measure | Prior scorecard | Current branch | Result |
| --- | ---: | ---: | --- |
| Counted files under `src`, `tests`, `docs`, `wiki`, `.github`, `scripts` | 1,265 | 1,395 | Added focused modules, tests, quality evidence, and wiki source |
| Tracked `src/app` Python files | 447 | 473 | Added focused portfolio/performance response helpers and workspace/readiness/transaction summary/workflow mapper and contract modules plus risk drawdown, reporting batch, reporting query, risk concentration, risk rolling, risk attribution, performance contribution, performance attribution, performance evidence, portfolio workspace payload, and portfolio holdings payload modules |
| Tracked Python test files | 162 | 187 | Added focused request-context, response-assembly, workspace parser, source-readiness parser, transaction summary mapper/context, workspace payload mapper, holdings payload mapper, workflow mapper, workflow contract, transaction contract, performance snapshot contract, income/activity contract, holdings contract, risk drawdown contract, reporting batch contract, reporting query contract, risk concentration contract, risk rolling contract, risk attribution contract, performance contribution contract, performance attribution contract, metric-label contract, reporting error-normalization, quality-artifact, and threshold-ratchet tests |
| Longest function | 49 lines | 49 lines | Preserved |
| Top function hotspot count at 49 lines | 2 | 2 | Preserved |
| Largest source file | 2,968 lines | 1,779 physical lines | Improved and now protected by the 2,000-line blocking threshold; `src/app/services/portfolio_service.py` remains the largest residual hotspot after extracting workspace payload mapping, holdings payload mapping, and transaction-summary context loading; `performance_workspace.py`, `portfolio.py`, `risk_workspace.py`, and `reporting.py` remain smaller residual contract hotspots |
| `performance_workspace.py` | 1,539 lines | 903 lines | Improved through performance contribution, attribution, and evidence contract extraction |
| OpenAPI operations with missing summary/description/tags/errors | 0 | 0 | Preserved |
| Local unit/contract tests | 996 | 1,093 | Added focused response/request boundary, workspace parser, workspace payload mapper, holdings payload mapper, analytics observability event-boundary, Prometheus metric-label contract, source-readiness parser, transaction summary mapper/context tests, workflow mapper, workflow contract, transaction contract, performance snapshot contract, income/activity contract, holdings contract, risk drawdown contract, reporting batch contract, reporting query contract, risk concentration contract, risk rolling contract, risk attribution contract, performance contribution contract, performance attribution contract, performance evidence compatibility tests, performance evidence-view builder tests, reporting error-normalization tests, upstream-error rule tests, quality-artifact tests, and refactor threshold gate tests |
| Local coverage tests | 1,203 | 1,300 | Added focused coverage while preserving total coverage |
| Total coverage | 93.69% | 94.10% | Improved |
| Dependency audit | governed pass | governed pass, no known vulnerabilities after the `PYSEC-2026-161` exception | Preserved |

## Phase Gates

### Phase 1: Baseline/Report-Only

Status: active.

Required evidence:

1. baseline reports exist under `quality/`,
2. architecture and API governance rules are documented,
3. report-only CI workflow exists,
4. existing Feature Lane and PR Merge Gate remain stable except for promoted no-regression checks.

### Phase 2: Fail Only New Regressions

Candidate thresholds:

1. no new missing OpenAPI summary, description, tag, or standard error response,
2. no new forbidden imports,
3. no new high-confidence dead-code findings,
4. no new high-severity bandit findings,
5. no new function above the current maximum of 49 lines and no Python source file above the
   current 2,000-line blocking ceiling.

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
