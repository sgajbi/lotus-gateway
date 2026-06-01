# Quality Scorecard

Date: 2026-06-02  
Mode: baseline/report-only

| Dimension | Score | Baseline status | Next action |
| --- | ---: | --- | --- |
| Build and test reliability | 4/5 | Strong repo-native gates and green PR lanes | Keep Docker parity blocking |
| Coverage | 4/5 | 92.60% total coverage | Add targeted middleware/security/error tests |
| Modularity | 2/5 | Large services and contracts remain | Continue extraction slices |
| Architecture boundaries | 3/5 | Blocking AST tests exist; import-linter is report-only | Classify and enforce no-new-regression |
| API governance | 3/5 | Good generated OpenAPI; minor description/tag/error gaps | Add Spectral artifact and explicit API tests |
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
5. no new file/function above the current baseline maxima.

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
