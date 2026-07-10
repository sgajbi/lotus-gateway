# Quality Scorecard

Date: 2026-06-21
Mode: feature-branch evidence refresh

| Dimension | Score | Current status | Next action |
| --- | ---: | --- | --- |
| Build and test reliability | 5/5 | Current Workbench rebalance supportability extraction keeps CI-enforcement truth intact while ratcheting the blocking source-file/function threshold from 350/49 to 348/49. The Quality Baseline workflow still enforces refactor thresholds, workflow-governance validation, and agent quality evidence as blocking steps, requiring `refactor-thresholds.txt`, `workflow-governance.txt`, `agent-quality-evidence.txt`, and report-only demo-certification log evidence before artifact upload. `scripts/check_agent_quality_evidence.py` keeps the executable 348/49 ratchet, `src/app/router_groups/dpm.py` hotspot evidence, and durable scorecard/context guidance synchronized for future agent work. | Monitor GitHub Feature Lane and PR Merge Gate after push |
| Coverage | 4/5 | 94.30% total coverage across 1,451 combined coverage tests, above the 84% floor in current local `make ci` evidence | Add targeted middleware/security/error tests |
| Modularity | 4/5 | Current branch state blocks regressions above the 49-line longest-function baseline and the current 348-line source-file ceiling. This slice moves Workbench rebalance supportability parsing into `src/app/services/workbench_rebalance_supportability.py` while preserving the public `parse_rebalance_snapshot` surface. The largest residual hotspot is now `src/app/router_groups/dpm.py` at 348 lines. | Continue with the next cohesive 348-line hotspot slice |
| Architecture boundaries | 3/5 | Blocking AST tests exist; import-linter is report-only | Classify and enforce no-new-regression |
| API governance | 4/5 | 233 OpenAPI paths and 247 operations; missing summary, description, operation ID, tags, and documented 4xx/5xx response counts are all 0; Spectral remains report-only | Triage Spectral warnings and decide explicit operation ID policy |
| Error consistency | 2/5 | ProblemDetails exists for unhandled exceptions; reporting job and report-batch upstream error mappings now use explicit rule tables with product-safe fallback coverage; the shared generic service-error status mapping is code-owned and tested; advisory-facing product-safe service-error defaults now use typed immutable configs; broader route/upstream error normalization remains a meaningful hardening candidate | Continue normalizing route/upstream errors |
| Observability | 3/5 | Health/readiness/metrics/correlation/audit are present; RFC-0108 fan-out and selected analytics audit posture remain implementation-backed; analytics UI validators enforce separate fan-out log and audit event families; Prometheus collector metric-label contracts are now enforced by a static unit gate | Promote broader structured log, trace, and diagnostics rules into blocking checks |
| Security | 4/5 | Current Workbench rebalance supportability extraction introduces no dependency, authentication, caller-context, product-error-detail, upstream error-shape, data-mesh behavior, or runtime behavior changes. Monetary-float governance remains at 150 findings with 152 allowlisted. Prior full local `make ci` passed `pip-audit` with no known vulnerabilities after the governed `PYSEC-2026-161` exception. | Triage bandit and sensitive-data handling checks |
| Documentation | 4/5 | Baseline, scorecard, health report, architecture rules, observability docs, API-governance docs, wiki validation docs, and CI quality-gate docs are refreshed for recent metric-label, reporting error-normalization, shared upstream-error rule, service-error config, quality-baseline artifact hardening, workflow-governance artifact enforcement, CI action-runtime baseline enforcement, Node 24 runtime opt-in governance, transaction-ledger assembly evidence, portfolio book response assembly evidence, portfolio allocation source-loading evidence, Workbench overview enrichment evidence, portfolio insights response evidence, and advisory protocol-boundary evidence. | Keep wiki synced and add diagrams over time |
| Operations readiness | 4/5 | Existing CI/runbook docs and wiki validation posture now distinguish advisory quality-baseline tools from blocking refactor-threshold and workflow governance gates. Workflow governance now covers platform-baseline GitHub Actions majors, workflow-level Node 24 JavaScript action runtime opt-in, and explicit job timeouts no higher than 60 minutes; Quality Baseline now emits and validates a blocking workflow-governance evidence artifact. Current branch adds report-only `make demo-certification`, which writes `output/demo-certification/gateway-demo-certification.json` after five real Gateway API calls and 24 deterministic assertions over readiness, Workbench overview, portfolio-360 projected state, and sandbox policy feedback for `PB_SG_GLOBAL_BAL_001`. Branch-specific canonical proof passed after rebuilding the Docker-backed Gateway and downstream stack, then rerunning validation after performance lineage materialization completed: `lotus-workbench/output/playwright/live-canonical-advisory-protocol-boundaries-rerun/live-validation-summary.json` records 95 API checks, 2 calculation checks, 29 screenshots, 25/25 ready panel classifications, 28 supportability checks, 10 workflow-pack checks, no missing or non-ready panels, 9/9 RFC36-43 features validated, and 0 RFC36-43 gaps. Companion observability evidence at `lotus-workbench/output/observability-live/advisory-protocol-boundaries-rerun/observability-evidence-manifest.json` records 13/13 DNS checks, 13/13 representative API checks, 4/4 metric checks, 14 log artifacts, and 5/5 observability screenshots, with Gateway logs preserving correlation, request, and trace identifiers. Residual data-mesh limitation is not Gateway-owned: performance contribution source economics remains `SOURCE_LIMITED` for non-source-authored component P&L economics. | Promote demo certification only after repeated low-noise CI evidence and policy-backed exception handling |

## Before/After Evidence

Comparison point: the prior scorecard state after the portfolio liquidity payload-loader slice
versus the current risk workspace cache-boundary branch after PRs #349 through #452 plus the
current branch.

| Measure | Prior scorecard | Current branch | Result |
| --- | ---: | ---: | --- |
| Counted files under `src`, `tests`, `docs`, `wiki`, `.github`, `scripts` | 1,265 | 2,188 | Added focused modules, tests, quality evidence, and wiki source |
| Tracked `src/app` Python files | 447 | 662 | Added focused portfolio/performance response helpers and workspace/readiness/transaction summary/workflow mapper and contract modules plus performance workspace evidence response/state modules, performance workspace evidence-service orchestration, response-service orchestration, risk drawdown payload mapping, Workbench rebalance supportability/value helpers, DPM command-center core, DPM exception-summary, and outcome-review contract modules, portfolio transaction activity summary, portfolio transaction income summary, portfolio transaction amount helpers, portfolio client protocol module, Workbench sandbox service mixin, proposal delivery-posture service mixin, proposal lifecycle query-service mixin, proposal lifecycle summary/workflow/lineage/envelope contract modules, Workbench common/overview/sandbox contract modules, Workbench snapshot-context helper, risk rolling window mapper, risk workspace attribution mapping module, risk workspace response-loading module, performance contribution payload mapping module, performance attribution supportability parser module, performance attribution trend parser and contract modules, reporting batch client mixin, performance workspace benchmark catalog parser, Foundation core market-value parser, domain-product trust contract module, Lotus Core simulation-session routes, Advise proposal memo and proposal delivery client mixins, DPM PM operating-quality summary workflow and summary-invocation service mixins, risk workspace attribution service mixin, analytics performance client mixin, reporting job contract module, performance calculation evidence boundary, risk drawdown, reporting batch, reporting query, risk concentration, risk rolling, risk attribution, risk workspace examples, performance contribution, performance attribution, performance evidence, performance horizon, performance horizon row assembly, portfolio workspace payload, portfolio holdings payload, portfolio holdings orchestration, portfolio position-book contract module, analytics UI field-governance module, DPM wave campaign-definition contracts, advisor-brief workflow-pack contracts, Advisor Brief item/source contracts, Advisor Brief source-supportability contracts, Advisor Brief source-narrative helpers, HTTP retry-policy helpers, DPM command-center core service mixin, Advisor Brief client protocols, proposal lifecycle contracts, proposal lifecycle transition orchestration, DPM PM operating-quality contracts, DPM portfolio-memory contracts, Foundation optional-workspace parsing, performance workspace context-service policy, portfolio readiness response construction, performance evidence artifact handling, portfolio upstream payload handling, portfolio source-loading/mapping helpers, DPM route families, proposal memo contracts, portfolio liquidity contract module, Foundation core snapshot mapper, Advise-owned router-group module, DPM wave protocol module, platform capability workspace-descriptor module, and Lotus Core portfolio-query route-family mixin |
| Tracked Python test files | 162 | 237 | Added focused request-context, response-assembly, workspace parser, source-readiness parser, transaction summary mapper/context, workspace payload mapper, holdings payload mapper, catalog payload mapper, analytics workspace payload mapper, Workbench snapshot-context, Workbench rebalance snapshot boundary, reporting job contract, position-book mapper, portfolio book response, workspace source-loading, readiness/insight source-loading, book source-loading, advisor-brief source and narrative mapper, workflow mapper, workflow contract, transaction contract, performance snapshot contract, income/activity contract, holdings contract, risk drawdown contract, reporting batch contract, reporting query contract, risk concentration contract, risk rolling window, risk rolling contract, risk attribution contract, risk workspace example, performance contribution contract, performance contribution payload-boundary, performance attribution contract, performance horizon contract, metric-label contract, reporting error-normalization, DPM client boundary, Advise client boundary, DPM wave service boundary, risk drawdown supportability boundary, DPM command-center exception-summary boundary, quality-artifact, transaction workflow boundary, contract module boundary, threshold-ratchet, workflow action-runtime, agent quality evidence, demo certification evidence, benchmark catalog boundary, and Foundation core snapshot mapper tests |
| Longest function | 49 lines | 49 lines | Preserved |
| Top function hotspot count at 49 lines | 2 | 2 | Preserved |
| Largest source file | 2,968 lines | 348 lines | Improved and protected by the 348-line blocking threshold; `src/app/router_groups/dpm.py` is the evidence-selected largest residual hotspot after extracting Workbench rebalance supportability parsing |
| `performance_workspace.py` | 1,539 lines | 79 lines | Improved through performance contribution, attribution, evidence, horizon-comparison, common, summary, and details contract extraction |
| OpenAPI operations with missing summary/description/tags/errors | 0 | 0 | Preserved |
| Local unit/contract tests | 996 | 1,376 | Added focused proposal lifecycle contract-boundary and lifecycle query service-boundary pins plus focused performance calculation evidence boundary tests, performance workspace context/boundary tests, response-service boundary test, Workbench rebalance snapshot boundary test, risk drawdown payload-boundary test, performance contribution payload-boundary test, risk workspace response-loading boundary test, and the existing focused contract/service boundary coverage |
| Local coverage tests | 1,203 | 1,440 | Added focused coverage while preserving total coverage |
| Total coverage | 93.69% | 94.30% | Improved |
| Dependency audit | governed pass | governed pass, no known vulnerabilities after the `PYSEC-2026-161` exception | Preserved |

## Phase Gates

### Phase 1: Baseline/Report-Only

Status: active.

Required evidence:

1. baseline reports exist under `quality/`,
2. architecture and API governance rules are documented,
3. quality-baseline CI workflow exists and blocks regressions above the refactored 348/49
   source-size/function-size baseline plus workflow-governance drift while retaining advisory
   reports,
4. existing Feature Lane and PR Merge Gate remain stable except for promoted no-regression checks.

### Phase 2: Fail Only New Regressions

Candidate thresholds:

1. no new missing OpenAPI summary, description, tag, or standard error response,
2. no new forbidden imports,
3. no new high-confidence dead-code findings,
4. no new high-severity bandit findings,
5. no new function above the current maximum of 49 lines and no Python source file above the
   current 348-line blocking ceiling.

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
