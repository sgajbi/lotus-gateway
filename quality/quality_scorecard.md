# Quality Scorecard

Date: 2026-06-13
Mode: feature-branch evidence refresh

| Dimension | Score | Current status | Next action |
| --- | ---: | --- | --- |
| Build and test reliability | 5/5 | Current portfolio workspace payload mapper branch keeps the blocking refactor threshold gate green; `make check` passed with ruff, format check, monetary-float guard, the refactor threshold gate, mypy over 472 source files, Workbench/OpenAPI contract smoke, and 1,075 unit/contract tests; `make ci` passed with 207 integration tests, 1,282 coverage tests, 94.07% total coverage, and dependency audit | Keep Docker parity blocking in PR Merge Gate |
| Coverage | 4/5 | 94.07% total coverage, above the 84% floor | Add targeted middleware/security/error tests |
| Modularity | 4/5 | Current branch state blocks regressions above the 49-line longest-function baseline and the current 2,100-line source-file ceiling; recent slices extracted transaction request context, transaction page-context defaults, transaction client-kwargs mapping, performance workspace response assembly, portfolio workspace response assembly, portfolio workspace payload mapping, portfolio workspace performance parsing, portfolio workspace rebalance parsing, portfolio source-readiness parsing, portfolio transaction summary mapping, portfolio transaction-summary context loading, portfolio workflow mapping, portfolio workflow contracts, portfolio transaction contracts, portfolio performance snapshot contracts, portfolio income/activity contracts, portfolio holdings/book contracts, risk drawdown contracts, reporting batch contracts, reporting query contracts, risk concentration contracts, risk rolling contracts, risk attribution contracts, performance contribution contracts, performance attribution contracts, performance evidence contracts, and performance evidence-view orchestration; `portfolio_service.py` remains the largest residual hotspot | Continue extraction slices and tighten the source-file ceiling downward |
| Architecture boundaries | 3/5 | Blocking AST tests exist; import-linter is report-only | Classify and enforce no-new-regression |
| API governance | 4/5 | 233 OpenAPI paths and 247 operations; missing summary, description, operation ID, tags, and documented 4xx/5xx response counts are all 0; Spectral remains report-only | Triage Spectral warnings and decide explicit operation ID policy |
| Error consistency | 2/5 | ProblemDetails exists for unhandled exceptions; route/upstream error normalization remains a meaningful hardening candidate | Normalize route/upstream errors |
| Observability | 3/5 | Health/readiness/metrics/correlation/audit are present; RFC-0108 fan-out and selected analytics audit posture remain implementation-backed | Enforce structured log and metric label rules |
| Security | 4/5 | Current portfolio workspace payload mapper branch `pip-audit` found no known vulnerabilities after the governed `PYSEC-2026-161` exception; monetary-float guard passed with one allowlist relocation for an unchanged quantized response float conversion | Triage bandit and sensitive-data handling checks |
| Documentation | 4/5 | Baseline, scorecard, health report, and wiki validation evidence are refreshed to current branch metrics after the current portfolio workspace payload mapper slice | Keep wiki synced and add diagrams over time |
| Operations readiness | 3/5 | Existing CI/runbook docs and wiki validation posture now distinguish report-only quality baselines from the blocking refactor threshold gate | Add incident playbooks and SLO checks |

## Before/After Evidence

Comparison point: the prior scorecard state after the portfolio liquidity payload-loader slice
versus the current portfolio workspace payload mapper branch after PRs #349, #350, #351, #352,
#353, #354, #355, #356, #357, #358, #359, #360, #361, #362, #363, #364, #365, #366, #367,
#368, #369, #370, #371, and #372.

| Measure | Prior scorecard | Current branch | Result |
| --- | ---: | ---: | --- |
| Counted files under `src`, `tests`, `docs`, `wiki`, `.github`, `scripts` | 1,265 | 1,385 | Added focused modules, tests, quality evidence, and wiki source |
| Tracked `src/app` Python files | 447 | 472 | Added focused portfolio/performance response helpers and workspace/readiness/transaction summary/workflow mapper and contract modules plus risk drawdown, reporting batch, reporting query, risk concentration, risk rolling, risk attribution, performance contribution, performance attribution, performance evidence, and portfolio workspace payload modules |
| Tracked Python test files | 162 | 184 | Added focused request-context, response-assembly, workspace parser, source-readiness parser, transaction summary mapper/context, workspace payload mapper, workflow mapper, workflow contract, transaction contract, performance snapshot contract, income/activity contract, holdings contract, risk drawdown contract, reporting batch contract, reporting query contract, risk concentration contract, risk rolling contract, risk attribution contract, performance contribution contract, and performance attribution contract tests |
| Longest function | 49 lines | 49 lines | Preserved |
| Top function hotspot count at 49 lines | 2 | 2 | Preserved |
| Largest source file | 2,968 lines | 1,826 physical lines | Improved and now protected by the 2,100-line blocking threshold; `src/app/services/portfolio_service.py` remains the largest residual hotspot after extracting workspace payload mapping, transaction-summary context loading, and after reducing `performance_workspace.py` to 903 measured lines, `portfolio.py` to 911 measured lines, `risk_workspace.py` to 678 measured lines, and `reporting.py` to 532 measured lines |
| `performance_workspace.py` | 1,539 lines | 903 lines | Improved through performance contribution, attribution, and evidence contract extraction |
| OpenAPI operations with missing summary/description/tags/errors | 0 | 0 | Preserved |
| Local unit/contract tests | 996 | 1,075 | Added focused response/request boundary, workspace parser, workspace payload mapper, source-readiness parser, transaction summary mapper/context tests, workflow mapper, workflow contract, transaction contract, performance snapshot contract, income/activity contract, holdings contract, risk drawdown contract, reporting batch contract, reporting query contract, risk concentration contract, risk rolling contract, risk attribution contract, performance contribution contract, performance attribution contract, performance evidence compatibility tests, performance evidence-view builder tests, and refactor threshold gate tests |
| Local coverage tests | 1,203 | 1,282 | Added focused coverage while preserving total coverage |
| Total coverage | 93.69% | 94.07% | Improved |
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
   current 2,100-line blocking ceiling.

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
