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
4. `mypy` over `src`,
5. Workbench OpenAPI contract smoke, operation-governance contract checks, and global tag-catalog
   coverage,
6. migration contract smoke,
7. unit and contract tests,
8. integration tests,
9. coverage with an 84% floor,
10. `pip-audit` with the governed temporary `PYSEC-2026-161` exception,
11. Docker build and local Docker parity in the PR Merge Gate.

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

## Progressive Enforcement Plan

1. Baseline/report-only: publish evidence without failing existing delivery lanes.
2. No-new-regression: fail only new violations above the accepted baseline.
3. Threshold enforcement: apply agreed limits for file size, function length, complexity,
   OpenAPI completeness, import boundaries, and high-confidence security findings.
4. Enterprise-readiness: require architecture, API, tests, security, observability, operations,
   documentation, and scorecard evidence before release promotion.

## Current Evidence

Most recent local PR-grade evidence:

1. Current branch adds `scripts/check_refactor_quality_thresholds.py` as a blocking lint-stage
   gate.
2. Current enforced source-file threshold: no Python source file under `src/app` above 2,100
   physical lines.
3. Current enforced function threshold: no Python function or async function above the remediated
   49-line AST span baseline.
4. `python scripts/check_refactor_quality_thresholds.py`: passed with
   `max_source_file_lines=2100` and `max_function_lines=49`.
5. Feature Lane and PR Merge Gate step names now call out `Lint and Refactor Quality Thresholds`
   so the promoted gate is visible in GitHub logs.
6. Current branch `make check` passed with 1,066 unit/contract tests.
7. Current branch `make ci` passed with 207 integration tests and 1,273 coverage tests; total
   coverage was 94.05%, and `pip-audit` found no known vulnerabilities after the governed
   `PYSEC-2026-161` exception.

## Next Tightening Candidates

1. Keep the quality baseline workflow report-only while findings are classified.
2. Refresh the Spectral warning artifact from the GitHub quality-baseline workflow and decide
   whether explicit operation IDs should replace generated IDs.
3. Promote import-linter contracts after false positives are classified.
4. Tighten the enforced source-file threshold downward as the remaining largest services are split.
5. Add static no-sensitive-observability checks for logs, metrics labels, and diagnostics fields.
