# Quality Scorecard

Date: 2026-06-18
Mode: feature-branch evidence refresh

| Dimension | Score | Current status | Next action |
| --- | ---: | --- | --- |
| Build and test reliability | 5/5 | Current workbench contract-boundary branch ratchets the blocking refactor threshold from 794 to 771 script-counted lines after moving common workbench view models, overview and portfolio-360 responses, and sandbox/analytics contracts into dedicated modules behind the public `app.contracts.workbench` facade. Focused validation passed with ruff check, ruff format, mypy over touched contract modules, 118 focused workbench service/router/contract-boundary/threshold tests, and refactor-threshold trials proving `max_source_file_lines=771` passes. Full local `make check` passed with ruff, format check over 728 files, monetary-float guard, refactor-threshold gate, workflow action-runtime gate, mypy over 516 source files, OpenAPI smoke, and 1,189 unit/contract tests. Full local `make ci` passed with migration contract smoke, 209 integration tests, 1,398 combined coverage tests, 94.24% total coverage, and no known vulnerabilities after the governed `PYSEC-2026-161` exception. | Keep Docker parity blocking in PR Merge Gate |
| Coverage | 4/5 | 94.24% total coverage, above the 84% floor in current local `make ci` evidence | Add targeted middleware/security/error tests |
| Modularity | 4/5 | Current branch state blocks regressions above the 49-line longest-function baseline and the current 771-line source-file ceiling; recent slices extracted Workbench common/overview/sandbox contract families, portfolio workflow orchestration, advisor-brief workflow-pack contracts, proposal lifecycle contracts, DPM PM operating-quality contracts, performance workspace context-service policy, portfolio workspace component parser policy, portfolio readiness response construction, performance evidence artifact handling, portfolio upstream payload handling, removed stale portfolio service wrappers, portfolio source-loading/mapping helpers, DPM PM operating-quality/construction/proof-pack/wave upstream client route families, portfolio cached upstream access, DPM PM operating-quality service orchestration, performance trend service orchestration, Advise bank-demo proof/workspace/policy upstream routes, DPM wave AI handoff orchestration, portfolio transaction workflow orchestration, proposal memo contracts, portfolio liquidity contracts, Foundation core snapshot parsing, performance horizon-comparison contracts, Advise-owned router groups, advisor-brief AI narrative mapping, and proposal memo service forwarding into dedicated modules. `src/app/contracts/workbench.py` is reduced from 794 to 47 script-counted lines; `src/app/services/performance_workspace_evidence.py` is now the largest residual hotspot at 771 script-counted lines. | Continue extraction slices and tighten the source-file ceiling downward |
| Architecture boundaries | 3/5 | Blocking AST tests exist; import-linter is report-only | Classify and enforce no-new-regression |
| API governance | 4/5 | 233 OpenAPI paths and 247 operations; missing summary, description, operation ID, tags, and documented 4xx/5xx response counts are all 0; Spectral remains report-only | Triage Spectral warnings and decide explicit operation ID policy |
| Error consistency | 2/5 | ProblemDetails exists for unhandled exceptions; reporting job and report-batch upstream error mappings now use explicit rule tables with product-safe fallback coverage; the shared generic service-error status mapping is code-owned and tested; advisory-facing product-safe service-error defaults now use typed immutable configs; broader route/upstream error normalization remains a meaningful hardening candidate | Continue normalizing route/upstream errors |
| Observability | 3/5 | Health/readiness/metrics/correlation/audit are present; RFC-0108 fan-out and selected analytics audit posture remain implementation-backed; analytics UI validators enforce separate fan-out log and audit event families; Prometheus collector metric-label contracts are now enforced by a static unit gate | Promote broader structured log, trace, and diagnostics rules into blocking checks |
| Security | 4/5 | Current workbench contract-boundary branch introduces no dependency, authentication, caller-context, or product-error-detail policy changes; monetary-float allowlist remains at 159 governed findings after path refresh for moved workbench contract fields; full local `make ci` security audit reported no known vulnerabilities after the governed `PYSEC-2026-161` exception | Triage bandit and sensitive-data handling checks |
| Documentation | 4/5 | Baseline, scorecard, health report, observability docs, API-governance docs, wiki validation docs, and CI quality-gate docs are refreshed for recent metric-label, reporting error-normalization, shared upstream-error rule, service-error config, quality-baseline artifact hardening, CI action-runtime baseline enforcement, Node 24 runtime opt-in governance, transaction-ledger assembly evidence, portfolio book response assembly evidence, and portfolio allocation source-loading evidence | Keep wiki synced and add diagrams over time |
| Operations readiness | 3/5 | Existing CI/runbook docs and wiki validation posture now distinguish report-only quality baselines from blocking refactor-threshold and workflow action-runtime gates, including the workflow-level Node 24 JavaScript action runtime opt-in | Add incident playbooks and SLO checks |

## Before/After Evidence

Comparison point: the prior scorecard state after the portfolio liquidity payload-loader slice
versus the current Advise policy client-boundary branch after PRs #349 through #422 plus the
current branch.

| Measure | Prior scorecard | Current branch | Result |
| --- | ---: | ---: | --- |
| Counted files under `src`, `tests`, `docs`, `wiki`, `.github`, `scripts` | 1,265 | 1,711 | Added focused modules, tests, quality evidence, and wiki source |
| Tracked `src/app` Python files | 447 | 516 | Added focused portfolio/performance response helpers and workspace/readiness/transaction summary/workflow mapper and contract modules plus Workbench common/overview/sandbox contract modules, risk drawdown, reporting batch, reporting query, risk concentration, risk rolling, risk attribution, performance contribution, performance attribution, performance evidence, performance horizon, portfolio workspace payload, portfolio holdings payload, portfolio catalog payload, position-book mapper, portfolio book response, portfolio workspace source-loading, portfolio readiness/insight source-loading, portfolio book source-loading, portfolio workflow service-boundary mixin, advisor-brief source and narrative mapper modules, advisor-brief workflow contract module, proposal lifecycle contract module, DPM PM operating-quality contract module, DPM PM operating-quality/construction/proof-pack/wave client mixins, portfolio upstream-access mixin, portfolio transaction service mixin, DPM PM operating-quality service mixin, performance trend service mixin, Advise bank-demo proof/workspace/policy client mixins, DPM wave AI handoff mixin, proposal memo contract modules, portfolio liquidity contract module, Foundation core snapshot mapper, and Advise-owned router-group module |
| Tracked Python test files | 162 | 207 | Added focused request-context, response-assembly, workspace parser, source-readiness parser, transaction summary mapper/context, workspace payload mapper, holdings payload mapper, catalog payload mapper, position-book mapper, portfolio book response, workspace source-loading, readiness/insight source-loading, book source-loading, advisor-brief source and narrative mapper, workflow mapper, workflow contract, transaction contract, performance snapshot contract, income/activity contract, holdings contract, risk drawdown contract, reporting batch contract, reporting query contract, risk concentration contract, risk rolling contract, risk attribution contract, performance contribution contract, performance attribution contract, performance horizon contract, metric-label contract, reporting error-normalization, DPM client boundary, Advise client boundary, DPM wave service boundary, quality-artifact, transaction workflow boundary, contract module boundary, threshold-ratchet, workflow action-runtime, and Foundation core snapshot mapper tests |
| Longest function | 49 lines | 49 lines | Preserved |
| Top function hotspot count at 49 lines | 2 | 2 | Preserved |
| Largest source file | 2,968 lines | 771 script-counted lines | Improved and protected by the 771-line blocking threshold; `src/app/services/performance_workspace_evidence.py` is the largest residual hotspot after reducing `src/app/contracts/workbench.py` from 794 to 47 script-counted lines |
| `performance_workspace.py` | 1,539 lines | 651 lines | Improved through performance contribution, attribution, evidence, and horizon-comparison contract extraction |
| OpenAPI operations with missing summary/description/tags/errors | 0 | 0 | Preserved |
| Local unit/contract tests | 996 | 1,189 | Added focused performance workspace context/boundary tests, workbench contract-boundary tests, portfolio workflow service-boundary tests, portfolio workspace component parser and concrete-route registration tests, readiness/insight source-loading, book source-loading, and stale-wrapper boundary tests plus focused response/request boundary, workspace parser, workspace payload mapper, holdings payload mapper, allocation and position source-loading, position-book mapper, portfolio book response, workspace source-loading, advisor-brief source and narrative mapper, analytics observability event-boundary, Prometheus metric-label contract, source-readiness parser, transaction summary mapper/context tests, transaction-ledger assembly tests, transaction workflow boundary tests, workflow mapper, workflow contract, transaction contract, performance snapshot contract, income/activity contract, holdings contract, risk drawdown contract, reporting batch contract, reporting query contract, risk concentration contract, risk rolling contract, risk attribution contract, performance contribution contract, performance attribution contract, performance evidence compatibility tests, performance evidence-view builder tests, performance horizon contract tests, reporting error-normalization tests, upstream-error rule tests, quality-artifact tests, refactor threshold gate tests, workflow action-runtime tests, contract module boundary tests, DPM client boundary tests, Advise client boundary tests, DPM wave service boundary tests, Advise workspace and policy client boundary tests, Foundation core snapshot mapper tests, and advisory router-group boundary tests |
| Local coverage tests | 1,203 | 1,398 | Added focused coverage while preserving total coverage |
| Total coverage | 93.69% | 94.24% | Improved |
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
   current 771-line blocking ceiling.

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
