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
2. Current enforced source-file threshold: no Python source file under `src/app` above 1,362
   script-counted lines.
3. Current enforced function threshold: no Python function or async function above the remediated
   49-line AST span baseline.
4. `python scripts/check_refactor_quality_thresholds.py`: passed with
   `max_source_file_lines=1362` and `max_function_lines=49`.
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
9. Prior source-file threshold ratchet branch focused validation passed with the then-current
   refactor threshold gate, 4 refactor-threshold unit tests, ruff check, and ruff format check over
   the touched threshold script and tests. The current blocking ceiling is recorded below.
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
    `actions/setup-node@v5`, and `actions/upload-artifact@v7`. The new
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
16. Current upload-artifact runtime branch raises the governed `actions/upload-artifact` baseline
    from `v5` to `v7` after the merged Node 24 opt-in branch proved `v5` still emitted a GitHub
    Node.js 20 deprecation annotation while being forced onto Node 24.
17. Current transaction-ledger assembly branch moves request-context and response assembly
    orchestration into `portfolio_transaction_ledger.py`, reducing `portfolio_service.py` from
    1,816 to 1,804 physical lines while preserving the 49-line longest-function baseline. Focused
    validation passed with 52 portfolio ledger/service tests; local `make check` passed with
    1,114 unit/contract tests, and local `make ci` passed with 207 integration tests, 1,321
    coverage tests, 94.14% total coverage, and no known vulnerabilities after the governed
    `PYSEC-2026-161` exception.
18. Current source-file threshold ratchet branch promotes the remediated 1,804-line largest-source
    baseline into the blocking refactor quality gate so future PRs cannot regrow any `src/app`
    Python source file above the current measured maximum without an explicit governed threshold
    decision. Focused validation passed with 8 threshold/artifact tests; local `make check` passed
    with 1,114 unit/contract tests, and local `make ci` passed with 207 integration tests, 1,321
    coverage tests, 94.14% total coverage, and no known vulnerabilities after the governed
    `PYSEC-2026-161` exception.
19. Current portfolio book response assembly branch moves deterministic book response construction
    into `portfolio_book.py`, reducing `portfolio_service.py` from 1,804 to 1,799 physical lines
    while preserving portfolio identity, cash-balance, allocation, top-position, and full-position
    behavior. Focused validation passed with the refactor threshold gate, ruff check, ruff format
    check, and 65 portfolio book/service/router tests. Local `make check` passed with 1,115
    unit/contract tests, and local `make ci` passed with 207 integration tests, 1,322 coverage
    tests, 94.14% total coverage, and no known vulnerabilities after the governed
    `PYSEC-2026-161` exception.
20. Current portfolio allocation source-loading branch moves allocation page source orchestration
    into `portfolio_holdings_payloads.py`, reducing `portfolio_service.py` from 1,799 to 1,743
    physical lines while preserving AUM, positions, allocation, look-through, reporting-currency,
    and product-safe unavailable-detail behavior. Focused validation passed with the refactor
    threshold gate, ruff check, ruff format check, and 71 portfolio holdings/service/router tests.
    Local `make check` passed with 1,116 unit/contract tests, and local `make ci` passed with 207
    integration tests, 1,323 coverage tests, 94.14% total coverage, and no known vulnerabilities
    after the governed `PYSEC-2026-161` exception.
21. Current portfolio position source-loading branch moves position-book source orchestration into
    `portfolio_holdings_payloads.py`, reducing `portfolio_service.py` from 1,743 to 1,728
    physical lines while preserving AUM, positions, projection, reporting-currency, and
    product-safe unavailable-detail behavior. Focused validation passed with the refactor threshold
    gate, ruff check, ruff format check, and 50 portfolio holdings/service unit tests. Local
    `make check` passed with 1,117 unit/contract tests, and local `make ci` passed with 207
    integration tests, 1,324 coverage tests, 94.14% total coverage, and no known vulnerabilities
    after the governed `PYSEC-2026-161` exception.
22. Current portfolio workspace source-loading branch moves workspace source and analytics fan-out
    into `portfolio_workspace_sources.py`, reducing `portfolio_service.py` from 1,728 to 1,659
    physical lines while preserving portfolio, AUM, support overview, projected cashflow,
    cash-balance, readiness, performance, rebalance, and rebalance-supportability call shapes.
    Focused validation passed with the refactor threshold gate, ruff check, ruff format check,
    touched-module mypy, and 44 portfolio workspace/service unit tests. Local `make check` passed
    with ruff, format check, monetary-float guard, refactor threshold gate, workflow action-runtime
    gate, mypy over 476 source files, Workbench/OpenAPI contract smoke, and 1,119 unit/contract
    tests. Local `make ci` passed with 207 integration tests, 1,326 combined coverage tests,
    94.16% total coverage, and no known vulnerabilities after the governed `PYSEC-2026-161`
    exception.
23. Prior advisor-brief source mapper branch moves source-context, fallback narrative,
    source-metric, supportability, route, and AI fact-bundle shaping into
    `advisor_brief_source.py`, reducing `advisor_brief_service.py` from 1,454 to 861 physical
    lines while preserving the advisor-brief orchestration and workflow-pack runtime boundary.
    Focused validation passed with ruff check, ruff format check, the refactor threshold gate, and
    37 advisor-brief/source/boundary/threshold unit tests. Local `make check` passed with ruff,
    format check, monetary-float guard, refactor threshold gate, workflow action-runtime gate,
    mypy over 477 source files, Workbench/OpenAPI contract smoke, and 1,123 unit/contract tests.
    Local `make ci` passed with 207 integration tests, 1,330 combined coverage tests, 94.18% total
    coverage, and no known vulnerabilities after the governed `PYSEC-2026-161` exception.
24. Current portfolio readiness/insight source-loading branch moves readiness and insight fan-out
    source bundle construction into `portfolio_readiness_insight_sources.py`, reducing
    `portfolio_service.py` from 1,659 to 1,607 script-counted lines while preserving workspace,
    source-readiness, positions, allocations, transaction-probe, and activity-summary request
    behavior. Focused validation passed with ruff check, ruff format check, touched-module mypy,
    the refactor threshold gate, and 62 helper/service/boundary/threshold unit tests. Local
    `make check` passed with ruff, format check, monetary-float guard, refactor threshold gate,
    workflow action-runtime gate, mypy over 478 source files, Workbench/OpenAPI contract smoke,
    and 1,126 unit/contract tests. Local `make ci` passed with 207 integration tests, 1,333
    combined coverage tests, 94.19% total coverage, and no known vulnerabilities after the
    governed `PYSEC-2026-161` exception.
25. Current portfolio book source-loading branch moves portfolio book source fan-out bundle
    construction into `portfolio_book_sources.py`, reducing `portfolio_service.py` from 1,607 to
    1,589 script-counted lines while preserving allocation, position, cash-balance,
    portfolio-profile, projection, and reporting-currency request behavior. Focused validation
    passed with ruff check, ruff format check, touched-module mypy, the refactor threshold gate,
    and 64 helper/service/boundary/threshold unit tests. Local `make check` passed with ruff,
    format check, monetary-float guard, refactor threshold gate, workflow action-runtime gate,
    mypy over 479 source files, Workbench/OpenAPI contract smoke, and 1,128 unit/contract tests.
    Local `make ci` passed with 207 integration tests and 1,335 combined coverage tests; total
    coverage is 94.20%, and `pip-audit` found no known vulnerabilities after the governed
    `PYSEC-2026-161` exception.
26. Current portfolio service wrapper-cleanup branch removes stale local pass-through wrappers for
    portfolio identity/profile parsing, workspace control-capability construction, optional text
    conversion, and unused optional-int conversion, reducing `portfolio_service.py` from 1,589 to
    1,553 script-counted lines while preserving direct use of extracted helper modules. Focused
    validation passed with ruff check, ruff format check, touched-module mypy, the refactor
    threshold gate, and 68 service/boundary/threshold/docs unit tests. Local `make check` passed
    with ruff, format check, monetary-float guard, refactor threshold gate, workflow
    action-runtime gate, mypy over 479 source files, Workbench/OpenAPI contract smoke, and 1,129
    unit/contract tests. Local `make ci` passed with 207 integration tests and 1,336 combined
    coverage tests; total coverage is 94.24%, and `pip-audit` found no known vulnerabilities
    after the governed `PYSEC-2026-161` exception.
27. Prior merged portfolio upstream-payload extraction branch moves portfolio-specific payload requiring,
    optional partial-failure recording, product-safe upstream error detail construction, and
    client-error mapping into `portfolio_upstream_payloads.py`, reducing `portfolio_service.py`
    from 1,553 to 1,489 script-counted lines while preserving upstream response behavior and
    partial-failure shape. Focused validation passed with ruff check, ruff format check,
    touched-module mypy, the refactor threshold gate, and 63 service/boundary/helper unit tests.
    Local `make check` passed with ruff, format check, monetary-float guard, refactor threshold
    gate, workflow action-runtime gate, mypy over 480 source files, Workbench/OpenAPI contract
    smoke, and 1,134 unit/contract tests. Local `make ci` passed with 207 integration tests,
    1,341 combined coverage tests, 94.24% total coverage, and no known vulnerabilities after the
    governed `PYSEC-2026-161` exception.
28. Current portfolio readiness-response extraction branch moves source-owned readiness response
    construction and reporting-readiness fallback policy into `portfolio_readiness_response.py`,
    reducing `portfolio_service.py` from 1,489 to 1,453 lines while preserving readiness response
    behavior. Focused validation passed with ruff check, touched-module mypy, 46 service/readiness
    unit tests, and a trial refactor threshold gate at `max_source_file_lines=1477`.
29. Prior performance workspace request-context extraction branch moves workspace, horizon, and
    attribution-trend request-context policy into `performance_workspace_context.py`, reducing
    `performance_workspace_service.py` from 1,477 to 1,206 script-counted lines while preserving
    normalization, benchmark, warning, and partial-failure behavior. Focused validation passed with
    ruff check, ruff format check, touched-module mypy, 61 service/context/boundary unit tests,
    and a trial refactor threshold gate at `max_source_file_lines=1453`. Local `make check` passed
    with ruff, format check, monetary-float guard, refactor threshold gate, workflow
    action-runtime gate, mypy over 482 source files, Workbench/OpenAPI contract smoke, and 1,150
    unit/contract tests. Local `make ci` passed with 207 integration tests, 1,357 combined
    coverage tests, 94.30% total coverage, and no known vulnerabilities after the governed
    `PYSEC-2026-161` exception.
30. Current portfolio workspace component parser extraction branch moves workspace assembly state,
    summary/cashflow/performance/rebalance/operations parsing, reporting-readiness part assembly,
    and resolved-as-of-date extraction into `portfolio_workspace_components.py`, reducing
    `portfolio_service.py` from 1,453 to 1,237 script-counted lines while preserving optional
    upstream warning and partial-failure behavior. Focused validation passed with ruff check,
    ruff format check, touched-module mypy, 67 service/component/boundary unit tests, and a trial
    refactor threshold gate at `max_source_file_lines=1362`.
31. Current concrete-route registration fix expands registered gateway routers into concrete
    `APIRoute` entries so route enumeration, contract tests, and Prometheus route-name middleware
    do not see FastAPI lazy included-router placeholders. Focused validation passed with ruff
    check, ruff format check, mypy over `router_registry.py`, and 15 route/contract tests.
32. Current portfolio workspace component parser branch full local gates passed: `make check`
    passed with ruff, format check, monetary-float guard, refactor threshold gate, workflow
    action-runtime gate, mypy over 483 source files, Workbench/OpenAPI contract smoke, and 1,158
    unit/contract tests. `make ci` passed with 207 integration tests, 1,365 combined coverage
    tests, 94.31% total coverage, migration contract smoke, and no known vulnerabilities after
    the governed `PYSEC-2026-161` exception.

## Next Tightening Candidates

1. Keep the quality baseline tool findings report-only while findings are classified; keep artifact
   presence and OpenAPI artifact validity enforced so evidence gaps are visible.
2. Refresh the Spectral warning artifact from the GitHub quality-baseline workflow and decide
   whether explicit operation IDs should replace generated IDs.
3. Promote import-linter contracts after false positives are classified.
4. Continue tightening the enforced source-file threshold downward as the remaining largest clients
   and services are split; `dpm_client.py` is now the largest file at 1,362 script-counted lines
   and defines the current blocking ceiling.
5. Extend static no-sensitive-observability checks beyond the new Prometheus metric-label gate to
   broader logs, trace attributes, and diagnostics fields.
