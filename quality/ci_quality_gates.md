# CI Quality Gates

Date: 2026-06-04  
Mode: progressive enforcement

This file records the governed CI measurement posture for the gateway hardening program. It is the
operator-facing companion to `baseline_report.md`, `quality_scorecard.md`,
`architecture_rules.md`, and `api_governance_rules.md`.

## Current Blocking Gates

The current local and PR-grade blocking gates are:

1. `ruff` lint and format checks,
2. monetary-float governance,
3. `mypy` over `src`,
4. Workbench OpenAPI contract smoke and operation-governance contract checks,
5. migration contract smoke,
6. unit and contract tests,
7. integration tests,
8. coverage with an 84% floor,
9. `pip-audit` with the governed temporary `PYSEC-2026-161` exception,
10. Docker build and local Docker parity in the PR Merge Gate.

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

1. `make check`: 958 unit/contract tests passed.
2. `make ci`: 207 integration tests passed.
3. `make ci`: 1,165 coverage tests passed.
4. Total coverage: 92.80%, above the 84% floor.
5. `pip-audit`: no known vulnerabilities after the governed `PYSEC-2026-161` exception.

## Next Tightening Candidates

1. Keep the quality baseline workflow report-only while findings are classified.
2. Triage remaining Spectral/global tag warnings and decide whether explicit operation IDs should
   replace generated IDs.
3. Promote import-linter contracts after false positives are classified.
4. Add no-new-file/function-above-baseline checks for refactor slices.
5. Add static no-sensitive-observability checks for logs, metrics labels, and diagnostics fields.
