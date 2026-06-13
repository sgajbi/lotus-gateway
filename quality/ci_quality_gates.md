# CI Quality Gates

Date: 2026-06-13  
Mode: progressive enforcement

This file records the governed CI measurement posture for the gateway hardening program. It is the
operator-facing companion to `baseline_report.md`, `quality_scorecard.md`,
`architecture_rules.md`, and `api_governance_rules.md`.

## Current Blocking Gates

The current local and PR-grade blocking gates are:

1. `ruff` lint and format checks,
2. monetary-float governance,
3. refactor quality thresholds blocking new growth above the current largest-file and
   longest-function baselines,
4. workflow action-runtime governance for platform-baseline GitHub Actions majors and the
   workflow-level Node 24 JavaScript action opt-in,
5. `mypy` over `src`,
6. Workbench OpenAPI contract smoke, operation-governance contract checks, and global tag-catalog
   coverage,
7. migration contract smoke,
8. unit and contract tests,
9. integration tests,
10. coverage with an 84% floor,
11. `pip-audit` with the governed temporary `PYSEC-2026-161` exception,
12. Docker build and local Docker parity in the PR Merge Gate.

The PR Merge Gate now runs integration tests and the coverage gate in parallel after the
lint/typecheck/unit job. Docker build and Docker parity remain downstream of both jobs so the
merge barrier still requires all PR-grade proof.

## Report-Only Gates

Report-only quality checks should remain advisory until findings are classified:

1. complexity and maintainability,
2. high-confidence dead-code candidates,
3. dependency hygiene,
4. static security scanning beyond dependency vulnerabilities,
5. OpenAPI Spectral warnings,
6. import-linter architecture contracts,
7. documentation and observability scorecard gaps.

The report-only workflow now enforces evidence capture itself: the expected quality-baseline log
files and generated OpenAPI artifact must exist before upload. Tool findings remain report-only;
missing or unusable evidence is treated as a CI measurement defect.

## Progressive Enforcement Plan

1. Baseline/report-only: publish evidence without failing existing delivery lanes.
2. No-new-regression: fail only new violations above the accepted baseline.
3. Threshold enforcement: apply agreed limits for file size, function length, complexity,
   OpenAPI completeness, import boundaries, and high-confidence security findings.
4. Enterprise-readiness: require architecture, API, tests, security, observability, operations,
   documentation, and scorecard evidence before release promotion.

## Current Evidence

Most recent local PR-grade evidence:

1. The previous quality-baseline enforcement branch added
   `scripts/check_refactor_quality_thresholds.py` as a blocking lint-stage gate.
2. Current enforced source-file threshold: no Python source file under `src/app` above 2,000
   physical lines.
3. Current enforced function threshold: no Python function or async function above the remediated
   49-line AST span baseline.
4. `python scripts/check_refactor_quality_thresholds.py`: passed with
   `max_source_file_lines=2100` and `max_function_lines=49`.
5. Feature Lane and PR Merge Gate step names now call out `Lint and Refactor Quality Thresholds`
   so the promoted gate is visible in GitHub logs.
6. Current portfolio workspace payload mapper branch `make check` passed with 1,075
   unit/contract tests.
7. Current portfolio workspace payload mapper branch `make ci` passed with 207 integration tests,
   1,282 coverage tests, 94.07% total coverage, and no known vulnerabilities after the governed
   `PYSEC-2026-161` exception.
8. Current quality-baseline artifact branch focused validation passed with 4 artifact-validator
   unit tests plus ruff and format checks over the new validator and tests. `make check` passed
   with 1,089 unit/contract tests, and `make ci` passed with 207 integration tests, 1,296 coverage
   tests, 94.11% total coverage, and no known vulnerabilities after the governed `PYSEC-2026-161`
   exception.
9. Current source-file threshold ratchet branch focused validation passed with the refactor
   threshold gate at `max_source_file_lines=2000`, 4 refactor-threshold unit tests, ruff check, and
   ruff format check over the touched threshold script and tests. `make check` passed with 1,090
   unit/contract tests, and `make ci` passed with 207 integration tests, 1,297 coverage tests,
   94.11% total coverage, and no known vulnerabilities after the governed `PYSEC-2026-161`
   exception.
10. Current portfolio holdings payload mapper branch focused validation passed with ruff format,
    ruff check, the refactor threshold gate, and 45 focused portfolio holdings/service unit tests.
    `make check` passed with 1,093 unit/contract tests, and `make ci` passed with 207 integration
    tests, 1,300 coverage tests, 94.10% total coverage, and no known vulnerabilities after the
    governed `PYSEC-2026-161` exception.
11. Current portfolio catalog payload mapper branch focused validation passed with ruff check and
    5 focused portfolio catalog/service unit tests. `make check` passed with 1,096 unit/contract
    tests, and `make ci` passed with 207 integration tests, 1,303 coverage tests, 94.10% total
    coverage, and no known vulnerabilities after the governed `PYSEC-2026-161` exception.
12. Prior portfolio allocation response mapper branch focused validation passed with ruff check
    and 9 focused portfolio holdings/allocation service unit tests. `make check` passed with 1,099
    unit/contract tests, and `make ci` passed with 207 integration tests, 1,306 coverage tests,
    94.13% total coverage, and no known vulnerabilities after the governed `PYSEC-2026-161`
    exception.
13. Current portfolio position-book response mapper branch focused validation passed with ruff
    check and 47 focused portfolio position-book/service unit tests. `make check` passed with
    1,101 unit/contract tests, and `make ci` passed with 207 integration tests, 1,308 coverage
    tests, 94.13% total coverage, and no known vulnerabilities after the governed
    `PYSEC-2026-161` exception.
14. Current CI action-runtime baseline branch upgrades Gateway workflows to the platform-required
    core action majors: `actions/checkout@v6`, `actions/setup-python@v6`,
    `actions/setup-node@v5`, and `actions/upload-artifact@v5`. The new
    `scripts/check_workflow_action_runtime.py` validator is part of `make lint` and blocks
    reintroducing older governed action majors. Local `make check` passed with 1,108
    unit/contract tests, and local `make ci` passed with 207 integration tests, 1,315 coverage
    tests, 94.13% total coverage, and no known vulnerabilities after the governed
    `PYSEC-2026-161` exception.
15. Current Node 24 workflow-runtime branch adds
    workflow-level `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: "true"` to governed Gateway workflows and extends
    `scripts/check_workflow_action_runtime.py` so `make lint` blocks workflows that use governed
    GitHub JavaScript actions without the opt-in. Local `make check` passed with 1,112
    unit/contract tests, and local `make ci` passed with 207 integration tests, 1,319 coverage
    tests, 94.13% total coverage, and no known vulnerabilities after the governed
    `PYSEC-2026-161` exception.

## Next Tightening Candidates

1. Keep the quality baseline tool findings report-only while findings are classified; keep artifact
   presence and OpenAPI artifact validity enforced so evidence gaps are visible.
2. Refresh the Spectral warning artifact from the GitHub quality-baseline workflow and decide
   whether explicit operation IDs should replace generated IDs.
3. Promote import-linter contracts after false positives are classified.
4. Continue tightening the enforced source-file threshold downward as the remaining largest services
   are split; `portfolio_service.py` is now 1,718 physical lines, below the current 2,000-line
   ceiling.
5. Extend static no-sensitive-observability checks beyond the new Prometheus metric-label gate to
   broader logs, trace attributes, and diagnostics fields.
