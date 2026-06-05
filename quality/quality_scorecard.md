# Quality Scorecard

Date: 2026-06-05
Mode: PR-readiness evidence update

| Dimension | Score | Current status | Next action |
| --- | ---: | --- | --- |
| Build and test reliability | 5/5 | `make ci` passed on `1b2a4e5` with lint, format, mypy, migration smoke, 207 integration tests, 1,193 coverage tests, and dependency audit | Keep Docker parity blocking in PR Merge Gate |
| Coverage | 4/5 | 93.67% total coverage, above the 84% floor | Add targeted middleware/security/error tests |
| Modularity | 4/5 | Current branch reduced the longest-function baseline from 50 lines on `origin/main` to 49 lines and removed multiple parser, polling, route-query, response-part, and request-context hotspots from the top list; largest-file pressure remains with `portfolio_service.py` at 3,337 tracked lines | Continue extraction slices and reduce largest-file pressure |
| Architecture boundaries | 3/5 | Blocking AST tests exist; import-linter is report-only | Classify and enforce no-new-regression |
| API governance | 4/5 | 233 OpenAPI paths and 247 operations; missing summary, description, operation ID, tags, and documented 4xx/5xx response counts are all 0; Spectral remains report-only | Triage Spectral warnings and decide explicit operation ID policy |
| Error consistency | 2/5 | ProblemDetails exists for unhandled exceptions | Normalize route/upstream errors |
| Observability | 3/5 | Health/readiness/metrics/correlation/audit present; analytics async polling now separates per-attempt fanout logging from loop orchestration and preserves absolute result URLs under test | Enforce structured log and metric label rules |
| Security | 4/5 | `pip-audit` passed in `make ci` with the governed FastAPI/Starlette exception; no known vulnerabilities found | Triage bandit and sensitive-data handling checks |
| Documentation | 4/5 | Quality scorecard and health evidence updated with current branch metrics; no repo-local wiki source changes required for this code-focused slice | Keep wiki synced and add diagrams over time |
| Operations readiness | 3/5 | Existing CI/runbook docs; operational runbook now consolidated | Add incident playbooks and SLO checks |

## Before/After Evidence

Comparison point: `origin/main` at `e7260c11a911c608e009eced048c912aaee83725` versus current
branch head `1b2a4e5acba6b93e93160bb291e4a19aa92f95df`.

| Measure | Before | After | Result |
| --- | ---: | ---: | --- |
| Branch commits over `origin/main` | 0 | 50 | Targeted non-squash history ready for PR review |
| Tracked `src/app` Python files | 443 | 443 | Stable module inventory |
| Tracked test files | 159 | 159 | Stable test module inventory |
| Longest function | 50 lines | 49 lines | Improved |
| Top function hotspot count at 50 lines | 2 | 0 | Improved |
| Largest source file | 3,289 lines | 3,337 lines | Not improved; known residual risk |
| OpenAPI operations with missing summary/description/tags/errors | 0 | 0 | Preserved |
| Local coverage tests | prior branch evidence 1,176 | 1,193 | Improved |
| Total coverage | 93.47% | 93.67% | Improved |
| Dependency audit | governed pass | governed pass, no known vulnerabilities | Preserved |

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
   growth above the current 3,337-line `portfolio_service.py` maximum.

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
