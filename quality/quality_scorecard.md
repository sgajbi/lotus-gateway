# Quality Scorecard

Date: 2026-06-12
Mode: PR-readiness evidence update

| Dimension | Score | Current status | Next action |
| --- | ---: | --- | --- |
| Build and test reliability | 5/5 | `make check` passed with lint, format, monetary-float guard, mypy, contract smoke, and 993 unit/contract tests; `make ci` passed with 207 integration tests, 1,200 coverage tests, and dependency audit | Keep Docker parity blocking in PR Merge Gate |
| Coverage | 4/5 | 93.69% total coverage, above the 84% floor | Add targeted middleware/security/error tests |
| Modularity | 4/5 | Current slice preserves the 49-line longest-function baseline and extracts transaction-ledger request context plus response-row mapping into a reusable mapper; `portfolio_service.py` drops from 3,062 to 2,993 lines | Continue extraction slices and reduce remaining largest-file pressure |
| Architecture boundaries | 3/5 | Blocking AST tests exist; import-linter is report-only | Classify and enforce no-new-regression |
| API governance | 4/5 | 233 OpenAPI paths and 247 operations; missing summary, description, operation ID, tags, and documented 4xx/5xx response counts are all 0; Spectral remains report-only | Triage Spectral warnings and decide explicit operation ID policy |
| Error consistency | 2/5 | ProblemDetails exists for unhandled exceptions | Normalize route/upstream errors |
| Observability | 3/5 | Health/readiness/metrics/correlation/audit present; analytics async polling now separates per-attempt fanout logging from loop orchestration and preserves absolute result URLs under test | Enforce structured log and metric label rules |
| Security | 4/5 | `pip-audit` passed in `make ci` with the governed FastAPI/Starlette exception; no known vulnerabilities found | Triage bandit and sensitive-data handling checks |
| Documentation | 4/5 | Quality scorecard and health evidence updated with current transaction-ledger metrics; no repo-local wiki source changes required for this code-focused mapper extraction | Keep wiki synced and add diagrams over time |
| Operations readiness | 3/5 | Existing CI/runbook docs; operational runbook now consolidated | Add incident playbooks and SLO checks |

## Before/After Evidence

Comparison point: `origin/main` at `62c7a7399944b380eca8ddc7be7ac987a2cd4654` versus the current
transaction-ledger branch before merge.

| Measure | Before | After | Result |
| --- | ---: | ---: | --- |
| Branch commits over `origin/main` | 0 | 1 planned | Narrow closure branch ready for PR review |
| Tracked `src/app` Python files | 444 | 445 | Added reusable transaction-ledger mapper |
| Tracked test files | 160 | 161 | Added focused mapper tests |
| Longest function | 49 lines | 49 lines | Preserved |
| Top function hotspot count at 49 lines | 2 | 2 | Preserved |
| Largest source file | 3,062 lines | 2,993 lines | Improved; `portfolio_service.py` remains largest residual hotspot |
| OpenAPI operations with missing summary/description/tags/errors | 0 | 0 | Preserved |
| Local unit/contract tests | 993 | 993 | Preserved |
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
5. no new function above the current branch maximum of 49 lines and no unclassified largest-file
   growth above the current 2,993-line `portfolio_service.py` maximum.

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
