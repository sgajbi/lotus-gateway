# Quality Scorecard

Date: 2026-06-14
Mode: feature-branch evidence refresh

| Dimension | Score | Current status | Next action |
| --- | ---: | --- | --- |
| Build and test reliability | 5/5 | Current portfolio readiness-response extraction branch keeps the blocking refactor threshold green and ratchets the source-file ceiling to 1,477 script-counted lines. Focused ruff, mypy, service/readiness tests, and a trial 1,477-line threshold check passed. Prior merged local `make check` passed with ruff, format check, monetary-float guard, refactor threshold gate, workflow action-runtime gate, mypy over 480 source files, Workbench/OpenAPI contract smoke, and 1,138 unit/contract tests. Prior merged local `make ci` passed with 207 integration tests, 1,345 combined coverage tests, 94.26% total coverage, and no known vulnerabilities after the governed `PYSEC-2026-161` exception | Keep Docker parity blocking in PR Merge Gate |
| Coverage | 4/5 | 94.26% total coverage, above the 84% floor in the latest merged CI evidence | Add targeted middleware/security/error tests |
| Modularity | 4/5 | Current branch state blocks regressions above the 49-line longest-function baseline and the current 1,477-line source-file ceiling; recent slices extracted portfolio readiness response construction, performance evidence artifact handling, portfolio upstream payload handling, removed stale portfolio service wrappers, and extracted portfolio book source loading, portfolio readiness/insight source loading, advisor-brief source mapping, transaction request context, transaction-ledger assembly, transaction page-context defaults, transaction client-kwargs mapping, performance workspace response assembly, portfolio workspace response assembly, portfolio workspace source loading, portfolio workspace payload mapping, portfolio holdings payload mapping, portfolio allocation and position source loading, portfolio catalog payload mapping, allocation response mapping, position-book response mapping, portfolio book response assembly, portfolio workspace performance parsing, portfolio workspace rebalance parsing, source-readiness parsing, transaction summary mapping/context loading, workflow mapping/contracts, transaction contracts, performance snapshot contracts, income/activity contracts, holdings/book contracts, risk contracts, reporting contracts, performance contracts, and performance evidence-view orchestration; `performance_workspace_service.py` is the largest residual hotspot and `portfolio_service.py` is now reduced below it | Continue extraction slices and tighten the source-file ceiling downward |
| Architecture boundaries | 3/5 | Blocking AST tests exist; import-linter is report-only | Classify and enforce no-new-regression |
| API governance | 4/5 | 233 OpenAPI paths and 247 operations; missing summary, description, operation ID, tags, and documented 4xx/5xx response counts are all 0; Spectral remains report-only | Triage Spectral warnings and decide explicit operation ID policy |
| Error consistency | 2/5 | ProblemDetails exists for unhandled exceptions; reporting job and report-batch upstream error mappings now use explicit rule tables with product-safe fallback coverage; the shared generic service-error status mapping is code-owned and tested; advisory-facing product-safe service-error defaults now use typed immutable configs; broader route/upstream error normalization remains a meaningful hardening candidate | Continue normalizing route/upstream errors |
| Observability | 3/5 | Health/readiness/metrics/correlation/audit are present; RFC-0108 fan-out and selected analytics audit posture remain implementation-backed; analytics UI validators enforce separate fan-out log and audit event families; Prometheus collector metric-label contracts are now enforced by a static unit gate | Promote broader structured log, trace, and diagnostics rules into blocking checks |
| Security | 4/5 | Current portfolio readiness-response extraction branch introduces no dependency, network, authentication, caller-context, monetary-float, or error-detail policy changes; latest merged local `make ci` found no known vulnerabilities after the governed `PYSEC-2026-161` exception | Triage bandit and sensitive-data handling checks |
| Documentation | 4/5 | Baseline, scorecard, health report, observability docs, API-governance docs, wiki validation docs, and CI quality-gate docs are refreshed for recent metric-label, reporting error-normalization, shared upstream-error rule, service-error config, quality-baseline artifact hardening, CI action-runtime baseline enforcement, Node 24 runtime opt-in governance, transaction-ledger assembly evidence, portfolio book response assembly evidence, and portfolio allocation source-loading evidence | Keep wiki synced and add diagrams over time |
| Operations readiness | 3/5 | Existing CI/runbook docs and wiki validation posture now distinguish report-only quality baselines from blocking refactor-threshold and workflow action-runtime gates, including the workflow-level Node 24 JavaScript action runtime opt-in | Add incident playbooks and SLO checks |

## Before/After Evidence

Comparison point: the prior scorecard state after the portfolio liquidity payload-loader slice
versus the current portfolio position-book response mapper branch after PRs #349 through #387 plus
the current branch.

| Measure | Prior scorecard | Current branch | Result |
| --- | ---: | ---: | --- |
| Counted files under `src`, `tests`, `docs`, `wiki`, `.github`, `scripts` | 1,265 | 1,399 | Added focused modules, tests, quality evidence, and wiki source |
| Tracked `src/app` Python files | 447 | 479 | Added focused portfolio/performance response helpers and workspace/readiness/transaction summary/workflow mapper and contract modules plus risk drawdown, reporting batch, reporting query, risk concentration, risk rolling, risk attribution, performance contribution, performance attribution, performance evidence, portfolio workspace payload, portfolio holdings payload, portfolio catalog payload, position-book mapper, portfolio book response, portfolio workspace source-loading, portfolio readiness/insight source-loading, portfolio book source-loading, and advisor-brief source mapper modules |
| Tracked Python test files | 162 | 194 | Added focused request-context, response-assembly, workspace parser, source-readiness parser, transaction summary mapper/context, workspace payload mapper, holdings payload mapper, catalog payload mapper, position-book mapper, portfolio book response, workspace source-loading, readiness/insight source-loading, book source-loading, advisor-brief source mapper, workflow mapper, workflow contract, transaction contract, performance snapshot contract, income/activity contract, holdings contract, risk drawdown contract, reporting batch contract, reporting query contract, risk concentration contract, risk rolling contract, risk attribution contract, performance contribution contract, performance attribution contract, metric-label contract, reporting error-normalization, quality-artifact, threshold-ratchet, and workflow action-runtime tests |
| Longest function | 49 lines | 49 lines | Preserved |
| Top function hotspot count at 49 lines | 2 | 2 | Preserved |
| Largest source file | 2,968 lines | 1,477 script-counted lines | Improved and protected by the 1,477-line blocking threshold; `src/app/services/performance_workspace_service.py` is the largest residual hotspot after extracting portfolio readiness-response helpers, while `portfolio_service.py` is reduced from 1,489 to 1,453 lines and `advisor_brief_service.py` is reduced from 1,454 to 861 script-counted lines after extracting source mapping into `advisor_brief_source.py` |
| `performance_workspace.py` | 1,539 lines | 903 lines | Improved through performance contribution, attribution, and evidence contract extraction |
| OpenAPI operations with missing summary/description/tags/errors | 0 | 0 | Preserved |
| Local unit/contract tests | 996 | 1,129 | Added focused readiness/insight source-loading, book source-loading, and stale-wrapper boundary tests plus focused response/request boundary, workspace parser, workspace payload mapper, holdings payload mapper, allocation and position source-loading, position-book mapper, portfolio book response, workspace source-loading, advisor-brief source mapper, analytics observability event-boundary, Prometheus metric-label contract, source-readiness parser, transaction summary mapper/context tests, transaction-ledger assembly tests, workflow mapper, workflow contract, transaction contract, performance snapshot contract, income/activity contract, holdings contract, risk drawdown contract, reporting batch contract, reporting query contract, risk concentration contract, risk rolling contract, risk attribution contract, performance contribution contract, performance attribution contract, performance evidence compatibility tests, performance evidence-view builder tests, reporting error-normalization tests, upstream-error rule tests, quality-artifact tests, refactor threshold gate tests, and workflow action-runtime tests |
| Local coverage tests | 1,203 | 1,336 | Added focused coverage while preserving total coverage |
| Total coverage | 93.69% | 94.26% | Improved |
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
   current 1,477-line blocking ceiling.

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
