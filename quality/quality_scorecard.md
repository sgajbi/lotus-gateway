# Quality Scorecard

Date: 2026-06-19
Mode: feature-branch evidence refresh

| Dimension | Score | Current status | Next action |
| --- | ---: | --- | --- |
| Build and test reliability | 5/5 | Current DPM portfolio-memory contract-family boundary branch splits `DpmPortfolioMemorySupportability` and `DpmPortfolioMemoryGatewayResponse` into a focused contract module while preserving the command-center compatibility facade. Focused validation passed with 67 contract/service/quality tests. Local `make check` passed with workflow governance, mypy over 565 source files, OpenAPI smoke, and 1,249 unit/contract tests. The quality-baseline workflow now enforces the 591/49 refactor thresholds as a blocking step while retaining report-only advisory tooling. Prior branch-local `make ci` passed with migration smoke, 209 integration tests, 1,451 combined coverage tests, 94.30% coverage, and no known vulnerabilities after the governed `PYSEC-2026-161` exception. | Run GitHub gates before merge |
| Coverage | 4/5 | 94.30% total coverage across 1,451 combined coverage tests, above the 84% floor in current local `make ci` evidence | Add targeted middleware/security/error tests |
| Modularity | 4/5 | Current branch state blocks regressions above the 49-line longest-function baseline and the current 591-line source-file ceiling; recent slices extracted Workbench common/overview/sandbox contract families, performance calculation evidence helpers, performance workspace detail-view orchestration, risk workspace request-context and cache-policy helpers, portfolio workspace contract family, portfolio workflow orchestration, advisor-brief workflow-pack contracts, Advisor Brief item/source contracts, Advisor Brief source-supportability contracts, Advisor Brief client protocols, proposal lifecycle contracts, proposal lifecycle transition orchestration, DPM PM operating-quality contracts, DPM portfolio-memory contracts, performance workspace context-service policy, portfolio readiness response construction, performance evidence artifact handling, portfolio upstream payload handling, portfolio source-loading/mapping helpers, DPM route families, proposal memo contracts, portfolio liquidity response assembly, Foundation core snapshot parsing, performance horizon-comparison contracts, Advise-owned router groups, DPM router groups, advisor-brief AI narrative mapping, risk workspace response OpenAPI examples, analytics workspace-summary payload construction, portfolio catalog response loading, Workbench overview enrichment orchestration, portfolio insights response assembly, performance horizon row assembly, reporting query contract families, performance workspace response contracts, reporting batch contract families, advisory client protocol-family modules, DPM wave client route-family modules, analytics risk-client route-family modules, Foundation catalog-payload parsing, Lotus Core lookup-client forwarding, and DPM wave protocol-family extraction. `src/app/services/foundation_service.py` is now the single largest residual hotspot at 591 script-counted lines. | Continue with the next cohesive service, client, or contract boundary slice |
| Architecture boundaries | 3/5 | Blocking AST tests exist; import-linter is report-only | Classify and enforce no-new-regression |
| API governance | 4/5 | 233 OpenAPI paths and 247 operations; missing summary, description, operation ID, tags, and documented 4xx/5xx response counts are all 0; Spectral remains report-only | Triage Spectral warnings and decide explicit operation ID policy |
| Error consistency | 2/5 | ProblemDetails exists for unhandled exceptions; reporting job and report-batch upstream error mappings now use explicit rule tables with product-safe fallback coverage; the shared generic service-error status mapping is code-owned and tested; advisory-facing product-safe service-error defaults now use typed immutable configs; broader route/upstream error normalization remains a meaningful hardening candidate | Continue normalizing route/upstream errors |
| Observability | 3/5 | Health/readiness/metrics/correlation/audit are present; RFC-0108 fan-out and selected analytics audit posture remain implementation-backed; analytics UI validators enforce separate fan-out log and audit event families; Prometheus collector metric-label contracts are now enforced by a static unit gate | Promote broader structured log, trace, and diagnostics rules into blocking checks |
| Security | 4/5 | Current DPM portfolio-memory contract extraction introduces no dependency, authentication, caller-context, product-error-detail, upstream error-shape, monetary-float conversion, data-mesh behavior, or runtime behavior changes. Prior full local `make ci` passed `pip-audit` with no known vulnerabilities after the governed `PYSEC-2026-161` exception. | Triage bandit and sensitive-data handling checks |
| Documentation | 4/5 | Baseline, scorecard, health report, architecture rules, observability docs, API-governance docs, wiki validation docs, and CI quality-gate docs are refreshed for recent metric-label, reporting error-normalization, shared upstream-error rule, service-error config, quality-baseline artifact hardening, CI action-runtime baseline enforcement, Node 24 runtime opt-in governance, transaction-ledger assembly evidence, portfolio book response assembly evidence, portfolio allocation source-loading evidence, Workbench overview enrichment evidence, portfolio insights response evidence, and advisory protocol-boundary evidence. | Keep wiki synced and add diagrams over time |
| Operations readiness | 4/5 | Existing CI/runbook docs and wiki validation posture now distinguish advisory quality-baseline tools from blocking refactor-threshold and workflow governance gates. Workflow governance now covers platform-baseline GitHub Actions majors, workflow-level Node 24 JavaScript action runtime opt-in, and explicit job timeouts no higher than 60 minutes. Branch-specific canonical proof passed after rebuilding the Docker-backed Gateway and downstream stack, then rerunning validation after performance lineage materialization completed: `lotus-workbench/output/playwright/live-canonical-advisory-protocol-boundaries-rerun/live-validation-summary.json` records 95 API checks, 2 calculation checks, 29 screenshots, 25/25 ready panel classifications, 28 supportability checks, 10 workflow-pack checks, no missing or non-ready panels, 9/9 RFC36-43 features validated, and 0 RFC36-43 gaps. Companion observability evidence at `lotus-workbench/output/observability-live/advisory-protocol-boundaries-rerun/observability-evidence-manifest.json` records 13/13 DNS checks, 13/13 representative API checks, 4/4 metric checks, 14 log artifacts, and 5/5 observability screenshots, with Gateway logs preserving correlation, request, and trace identifiers. Residual data-mesh limitation is not Gateway-owned: performance contribution source economics remains `SOURCE_LIMITED` for non-source-authored component P&L economics. | Add incident playbooks and SLO checks |

## Before/After Evidence

Comparison point: the prior scorecard state after the portfolio liquidity payload-loader slice
versus the current risk workspace cache-boundary branch after PRs #349 through #452 plus the
current branch.

| Measure | Prior scorecard | Current branch | Result |
| --- | ---: | ---: | --- |
| Counted files under `src`, `tests`, `docs`, `wiki`, `.github`, `scripts` | 1,265 | 1,765 | Added focused modules, tests, quality evidence, and wiki source |
| Tracked `src/app` Python files | 447 | 534 | Added focused portfolio/performance response helpers and workspace/readiness/transaction summary/workflow mapper and contract modules plus Workbench common/overview/sandbox contract modules, performance calculation evidence boundary, risk drawdown, reporting batch, reporting query, risk concentration, risk rolling, risk attribution, risk workspace examples, performance contribution, performance attribution, performance evidence, performance horizon, performance horizon row assembly, portfolio workspace payload, portfolio holdings payload, portfolio catalog payload, analytics workspace payload, position-book mapper, portfolio book response, portfolio workspace source-loading, portfolio readiness/insight source-loading, portfolio book source-loading, portfolio workflow service-boundary mixin, advisor-brief source and narrative mapper modules, advisor-brief client-protocol module, advisor-brief workflow contract module, proposal lifecycle contract module, DPM PM operating-quality contract module, DPM portfolio-memory contract module, DPM PM operating-quality/construction/proof-pack/wave client mixins, portfolio upstream-access mixin, portfolio transaction service mixin, DPM PM operating-quality service mixin, performance trend service mixin, Advise bank-demo proof/workspace/policy/proposal client mixins, DPM wave AI handoff mixin, DPM wave campaign-definition mixin, DPM command-center exception-summary mixin, shared command-center error helper, proposal memo contract modules, portfolio liquidity contract module, Foundation core snapshot mapper, Advise-owned router-group module, and DPM wave protocol module |
| Tracked Python test files | 162 | 214 | Added focused request-context, response-assembly, workspace parser, source-readiness parser, transaction summary mapper/context, workspace payload mapper, holdings payload mapper, catalog payload mapper, analytics workspace payload mapper, position-book mapper, portfolio book response, workspace source-loading, readiness/insight source-loading, book source-loading, advisor-brief source and narrative mapper, workflow mapper, workflow contract, transaction contract, performance snapshot contract, income/activity contract, holdings contract, risk drawdown contract, reporting batch contract, reporting query contract, risk concentration contract, risk rolling contract, risk attribution contract, risk workspace example, performance contribution contract, performance attribution contract, performance horizon contract, metric-label contract, reporting error-normalization, DPM client boundary, Advise client boundary, DPM wave service boundary, DPM command-center exception-summary boundary, quality-artifact, transaction workflow boundary, contract module boundary, threshold-ratchet, workflow action-runtime, and Foundation core snapshot mapper tests |
| Longest function | 49 lines | 49 lines | Preserved |
| Top function hotspot count at 49 lines | 2 | 2 | Preserved |
| Largest source file | 2,968 lines | 591 script-counted lines | Improved and protected by the 591-line blocking threshold; `src/app/services/foundation_service.py` is the single largest residual hotspot after splitting DPM portfolio-memory contracts |
| `performance_workspace.py` | 1,539 lines | 79 lines | Improved through performance contribution, attribution, evidence, horizon-comparison, common, summary, and details contract extraction |
| OpenAPI operations with missing summary/description/tags/errors | 0 | 0 | Preserved |
| Local unit/contract tests | 996 | 1,249 | Added focused performance calculation evidence boundary tests, performance workspace context/boundary tests, workbench contract-boundary tests, portfolio workflow service-boundary tests, portfolio workspace component parser and concrete-route registration tests, workspace contract-boundary compatibility tests, readiness/insight source-loading, book source-loading, and stale-wrapper tests plus focused response/request boundary, workspace parser, workspace payload mapper, holdings payload mapper, allocation and position source-loading, position-book mapper, portfolio book response, liquidity response assembly, workspace source-loading, advisor-brief source and narrative mapper, advisor-brief fact-bundle compatibility, analytics observability event-boundary, analytics workspace payload mapper, Prometheus metric-label contract, source-readiness parser, transaction summary mapper/context tests, transaction-ledger assembly tests, transaction workflow boundary tests, workflow mapper, workflow contract, transaction contract, performance snapshot contract, income/activity contract, holdings contract, risk drawdown contract, reporting batch contract, reporting query contract, risk concentration contract, risk rolling contract, risk attribution contract, performance contribution contract, performance attribution contract, performance evidence compatibility tests, performance evidence-view builder tests, performance horizon contract tests, reporting error-normalization tests, upstream-error rule tests, quality-artifact tests, refactor threshold gate tests, workflow action-runtime tests, contract module boundary tests, Advisor Brief item/supportability contract-boundary tests, DPM portfolio-memory contract-boundary tests, DPM client boundary tests, Advise client boundary tests, DPM wave service boundary tests, DPM wave campaign-definition boundary tests, DPM command-center exception-summary boundary tests, Advisor Brief client-protocol boundary tests, Advise workspace and policy client boundary tests, Foundation core snapshot mapper tests, advisory router-group boundary tests, performance/reporting compatibility-facade tests, Lotus Core lookup-client boundary tests, DPM wave protocol-family boundary tests, and expanded Advise proposal upstream-client route tests |
| Local coverage tests | 1,203 | 1,440 | Added focused coverage while preserving total coverage |
| Total coverage | 93.69% | 94.30% | Improved |
| Dependency audit | governed pass | governed pass, no known vulnerabilities after the `PYSEC-2026-161` exception | Preserved |

## Phase Gates

### Phase 1: Baseline/Report-Only

Status: active.

Required evidence:

1. baseline reports exist under `quality/`,
2. architecture and API governance rules are documented,
3. quality-baseline CI workflow exists and blocks regressions above the refactored 591/49
   source-size/function-size baseline while retaining advisory reports,
4. existing Feature Lane and PR Merge Gate remain stable except for promoted no-regression checks.

### Phase 2: Fail Only New Regressions

Candidate thresholds:

1. no new missing OpenAPI summary, description, tag, or standard error response,
2. no new forbidden imports,
3. no new high-confidence dead-code findings,
4. no new high-severity bandit findings,
5. no new function above the current maximum of 49 lines and no Python source file above the
   current 591-line blocking ceiling.

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
