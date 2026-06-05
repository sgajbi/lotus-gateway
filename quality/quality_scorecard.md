# Quality Scorecard

Date: 2026-06-05
Mode: baseline/report-only

| Dimension | Score | Baseline status | Next action |
| --- | ---: | --- | --- |
| Build and test reliability | 4/5 | Strong repo-native gates and green PR lanes | Keep Docker parity blocking |
| Coverage | 4/5 | 93.36% total coverage | Add targeted middleware/security/error tests |
| Modularity | 3/5 | Portfolio workspace assembly, portfolio insight rules, position parsing, performance workspace summary/detail, horizon, attribution-trend, and request contexts, foundation workspace assembly and response composition, risk drawdown/rolling/attribution orchestration and attribution supportability, shell workspace descriptor specs and descriptor state, transaction query contracts, DPM exception-summary and PM quality summary workflow orchestration, advisor-brief talking-point/review-action/route dependency orchestration, portfolio workflow-action and workspace response-component assembly, Workbench performance snapshot parsing and route query extraction, horizon comparison row-field projection, performance workspace summary parsing and route dependencies, risk attribution route query extraction, rebalance supportability failure recording, performance evidence-view mapping, performance workspace capability inputs, core snapshot summary parsing, portfolio exception summaries, performance attribution trend orchestration, platform-capabilities orchestration, advisor-brief narrative state, foundation snapshot parser, performance horizon parser, portfolio workspace controls, platform capability normalization, shell bootstrap, shared analytics request polling, workspace-summary payload assembly, portfolio transaction-summary context, transaction page loading, portfolio book response assembly, performance horizon-comparison dependency phases, performance summary/detail route query metadata, DPM wave PM memo payload/response construction, risk summary period/metric-state mapping, advisor-brief workflow-pack run profile extraction, attribution-trend row orchestration, benchmark-context task/result handling, shell descriptor contract construction, rebalance supportability result validation, performance chart-point construction, shell-bootstrap section assembly, performance snapshot projection, contribution summary merge policy, risk rolling response supportability orchestration, risk drawdown route query metadata, HTTP retry control helpers, portfolio transaction-ledger payload loading, portfolio workspace source gathering, and core transaction query-parameter construction extracted; large services and contracts remain | Continue extraction slices and reduce largest-file pressure |
| Architecture boundaries | 3/5 | Blocking AST tests exist; import-linter is report-only | Classify and enforce no-new-regression |
| API governance | 4/5 | Operation-level description, tag, error-response, and global tag-catalog gaps closed and contract-tested; Spectral remains report-only and needs a refreshed warning artifact | Triage Spectral warnings and decide explicit operation ID policy |
| Error consistency | 2/5 | ProblemDetails exists for unhandled exceptions | Normalize route/upstream errors |
| Observability | 3/5 | Health/readiness/metrics/correlation/audit present | Enforce structured log and metric label rules |
| Security | 3/5 | `pip-audit` blocking; no bandit baseline yet | Triage bandit and sensitive-data handling checks |
| Documentation | 3/5 | Strong README/wiki/RFC base; quality docs newly added | Keep wiki synced and add diagrams over time |
| Operations readiness | 3/5 | Existing CI/runbook docs; operational runbook now consolidated | Add incident playbooks and SLO checks |

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
5. no new file/function above the current branch maxima of 3,183 file lines and 54 function lines.

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
