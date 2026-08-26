# CI Quality Gates

Date: 2026-06-19
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
   workflow-level Node 24 JavaScript action opt-in plus bounded job timeouts,
5. agent quality evidence governance through `scripts/check_agent_quality_evidence.py`, which
   keeps the executable 315/49 ratchet, the current evidence-selected largest hotspot
   `src/app/contracts/dpm_pm_operating_quality.py`, and durable
   scorecard/context guidance in sync,
6. proposal decision-vocabulary governance through
   `scripts/check_proposal_decision_vocabulary.py`, which requires an external source for the
   blocking gate, rejects implicit packaged self-comparison, and reconciles the current Advise
   producer artifact in protected and scheduled CI,
7. PR issue-lifecycle text governance through `make pr-issue-lifecycle`: the Pull Request Merge
   Gate rejects malformed or negated auto-close wording and accepts only a standalone intended
   closure such as `Closes #123`; keep-open work uses `Keep #123 open`; opening, synchronization,
   reopening, or a title/body edit starts fresh lifecycle evidence,
8. `mypy` over `src`,
9. Workbench OpenAPI contract smoke, operation-governance contract checks, and global tag-catalog
   coverage,
10. migration contract smoke,
11. unit and contract tests,
12. integration tests,
13. coverage with an 84% floor,
14. `pip-audit` with the governed temporary `PYSEC-2026-161` exception,
15. Docker build and local Docker parity in the PR Merge Gate,
16. container release evidence in PR and main Docker lanes: Git-SHA image tagging, OCI build
   labels, SBOM generation, pre-push Trivy image scan that fails on fixable HIGH/CRITICAL
   findings, release manifest generation, and artifact upload,
17. main-only CI image promotion controls: GHCR push by CI, bounded retry only for its transient
    `unknown blob` response (three total attempts with retained per-attempt logs), digest capture,
    cosign signing, provenance attestation, and Kubernetes deployment reference by digest. Other
    push errors remain immediate hard failures.

The PR Merge Gate now runs integration tests and the coverage gate in parallel after the
lint/typecheck/unit job. Docker build and Docker parity remain downstream of both jobs so the
merge barrier still requires all PR-grade proof.

The Main Releasability Gate retains `main-releasability-release-evidence`, including coverage log,
workflow-governance proof, agent-quality proof, dependency/security proof, generated OpenAPI,
demo-certification evidence, and `output/demo-certification/`. It also retains
`main-container-release-evidence`, including SBOM, vulnerability scan, image release manifest,
signature output, and provenance attestation for the digest-pinned promoted image.

## Ratcheted Trend Gates

The broader quality tools retain their current known findings, but the Quality Baseline workflow
now fails when any measured metric regresses beyond the checked-in ratchet in
`quality/quality_ratchet.json`:

1. coverage must remain at or above 94.77%,
2. architecture import-contract failures must not exceed 11,
3. Xenon complexity blocks must not exceed 2,
4. Vulture findings must not exceed 24,
5. Deptry findings must not exceed 21. This ratchet banks the measured post-#645 improvement;
   a later run at 22 findings must fail rather than spend the recovered headroom,
6. security severity counts must remain at Undefined 0, Low <=2, Medium <=1, and High 0,
7. Interrogate documentation coverage must not fall below 1.6%, and
8. Spectral OpenAPI problems must not exceed 4.
9. duplicate-code clone count must not exceed 86, duplicated lines must not exceed 1,720, and
   duplicated percentage must not exceed 1.98%; stable source-pair/normalised-fragment
   occurrence fingerprints must not gain a
   new finding. The detector is pinned in `quality/package-lock.json` and scans production
   `src/app/**/*.py` only. The protected lane runs the same detector twice and fails if normalized
   candidate identities or aggregate metrics differ; local `make duplicate-code` runs the same
   repeated check when the pinned Node runtime is available. `make duplicate-code-protected` runs
   that same proof in the pinned Linux/Node 20 image for hosts with different local selection,
   using a checkout-specific Compose project and scoped cleanup. It mounts the checkout read-only
   at a dedicated source root, keeps writable dependency and output volumes outside that mount,
   and copies the scan report before teardown into a run-unique caller-created
   `output/duplicate-code-protected/` directory. This prevents
   root-owned checkout artifacts on native Linux while retaining mismatch diagnostics and proves same-environment
   determinism without claiming unverified cross-operating-system equivalence.

`scripts/check_quality_baseline_ratchet.py` publishes current value, baseline, delta, threshold,
and remediation command for every metric. A baseline update requires an explicit reviewed change;
CI never updates the baseline automatically. The following tools remain advisory in absolute terms
until individual findings are remediated and promoted to clean thresholds:

1. complexity and maintainability,
2. high-confidence dead-code candidates,
3. dependency hygiene,
4. static security scanning beyond dependency vulnerabilities,
5. OpenAPI Spectral warnings,
6. import-linter architecture contracts,
7. documentation and observability scorecard gaps,
8. Gateway demo certification until repeated Quality Baseline runs prove deterministic, low-noise
   behavior and a remediation/exception policy is approved.

Duplicate-code enforcement is intentionally no-new-regression rather than an immediate cleanup
campaign. `scripts/check_duplicate_code_ratchet.py` validates the pinned jscpd report, whose input
root is explicitly `src/app` with a `**/*.py` pattern to avoid checkout-root traversal drift, and rejects
out-of-scope paths and detector failures, reports both source locations, and compares stable
source-pair/normalised-fragment occurrence fingerprints so removing one known clone cannot mask a
different new clone between the same files. When source-root mode is enabled, the fragment is
selected from the canonical source side and the detector's reported start/end columns are honored
so reverse report orientation or an unrelated same-line prefix cannot change its identity.
A stable, Python-version-independent AST scope digest
distinguishes replacements in different class/function scopes without hashing mutable scope bodies.
The identity deliberately does not hash adjacent source lines: blank, comment, or unrelated
statements beside an unchanged clone must not invalidate its fingerprint. Same-scope relocation is
a documented identity trade-off because position-sensitive anchors would make ordinary edits
fragile. Fragment normalization uses Python tokenization to preserve actual string-token contents.
Complete f-string spans are reconstructed so Python 3.11's single `STRING` token and Python
3.12+'s `FSTRING_*` tokens produce the same identity, with an explicit comment-safe lexical
fallback for incomplete detector fragments. Incomplete token streams and unmatched delimiters are
never fingerprinted directly; the fallback performs token-like operator/layout normalization while
preserving literal and comment contents; complete f-string expression layout is normalized on both
tokenizer paths while conversion, debug-expression, and format-specification text is preserved.
Path selection does not depend on interpreter error message text. Occurrence
ordinals are assigned by measured location order but are not themselves part of the absolute source
coordinates, so unrelated line shifts or non-local body edits do not invalidate every fingerprint.
A removed clone creates a stale-fingerprint failure until a reviewed `--update-baseline` banks the
improvement; this prevents the removed duplication from being silently reintroduced later. When
unexpected findings, metric regressions, or detector failures are also present, the checker
truthfully reports that `--update-baseline` is blocked until those conditions are resolved.

The quality-baseline workflow now enforces the already-remediated source-size, function-size,
workflow-governance, and agent quality evidence thresholds, plus the no-new-regression ratchet,
after all baseline producers have had a chance to emit evidence; the duplicate-code result remains a
hard gate in a final post-upload step. It also enforces evidence capture itself: the expected quality-baseline log files,
workflow-governance proof, agent-quality-evidence proof, generated OpenAPI artifact, and ratchet
evidence must exist before upload. Missing or unusable evidence is treated as a CI measurement
defect.

Duplicate-tool installation is allowed to record its failure and let the remaining baseline
producers run; the final duplicate-ratchet result then fails closed after evidence upload. This
keeps registry, lockfile, or supported-runtime failures diagnosable without weakening the gate.

Every report-producing quality tool log also carries exactly one
`QUALITY_COMMAND_STATUS=<non-negative integer>` marker written from the producer process exit
status. A non-zero status with baseline findings is explicit known-debt trend evidence; it is not
silently converted to a clean result. Missing, malformed, or duplicate status markers fail the
artifact gate because the measurement cannot be trusted. A tool that fails before producing a
parseable result is rejected by the ratchet parser rather than counted as zero findings.

Quality Baseline uses `pull_request` targeting `main` as the sole authoritative automated feature
event. Feature-branch pushes do not start a duplicate run; PR creation and synchronization produce
one protected check per head SHA. Manual dispatch remains available for operator-requested
revalidation. The concurrency group keys pull-request runs by PR number, cancelling stale work
across synchronized revisions, while manual runs use a unique run ID; the full event matrix is
documented in `docs/quality-baseline-event-matrix.md`.

The Gateway demo certification command is now repo-native through `make demo-certification`. It
writes `output/demo-certification/gateway-demo-certification.json` and is run in Quality Baseline
with `continue-on-error: true`, capturing `output/quality-baseline/demo-certification.txt`; its
pass/fail result is not yet part of the ratchet because deterministic demo stability and exception
policy remain under review.
Promotion to a blocking Feature Lane or PR Merge Gate step is explicitly deferred until
`lotus-ci-enforcement-governance` intake proves stability, false-positive behavior, lane placement,
and exception policy.

## Progressive Enforcement Plan

1. Baseline/report-only: publish evidence without failing existing delivery lanes.
2. No-new-regression: fail only new violations above the accepted baseline. This is now enforced
   by the quality-baseline ratchet.
3. Threshold enforcement: apply agreed limits for file size, function length, complexity,
   OpenAPI completeness, import boundaries, and high-confidence security findings.
4. Enterprise-readiness: require architecture, API, tests, security, observability, operations,
   documentation, and scorecard evidence before release promotion.

## Current Evidence

Most recent local PR-grade evidence:

1. The previous quality-baseline enforcement branch added
   `scripts/check_refactor_quality_thresholds.py` as a blocking lint-stage gate.
2. Current enforced source-file threshold: no Python source file under `src/app` above 360
   script-counted lines.
3. Current enforced function threshold: no Python function or async function above the remediated
   49-line AST span baseline.
4. `python scripts/check_refactor_quality_thresholds.py`: passed with
   `max_source_file_lines=360` and `max_function_lines=49`.
5. Current risk rolling window-boundary slice focused validation passed with 33 risk rolling
   window, service, refactor-threshold, and quality-artifact tests. The slice ratchets the
   source-file ceiling to 521 script-counted lines with
   `src/app/services/dpm_command_center_service.py` now the largest residual hotspot.
6. Quality Baseline now runs blocking `Enforce Refactored Source Thresholds` and
   `Enforce Workflow Governance` steps, capturing both
   `output/quality-baseline/refactor-thresholds.txt` and
   `output/quality-baseline/workflow-governance.txt` before uploading report-only evidence.
7. Quality Baseline and `make lint` now run the blocking agent quality evidence gate through
   `scripts/check_agent_quality_evidence.py`, proving the executable 315/49 ratchet still matches
   current source truth and that durable scorecard/context guidance names
   `src/app/contracts/dpm_pm_operating_quality.py` as the current evidence-selected 315-line
   hotspot after the #664 ownership splits.
8. Current Gateway demo certification slice adds `make demo-certification`, which calls five real
   Gateway FastAPI endpoints with deterministic synthetic upstream fixtures and writes
   `output/demo-certification/gateway-demo-certification.json`. The current local run passed 24
   assertions over readiness, Workbench overview, portfolio-360 projected state, and sandbox
   policy feedback for `PB_SG_GLOBAL_BAL_001`; CI wiring is report-only and captures
   `output/quality-baseline/demo-certification.txt`.
9. Current risk workspace attribution mapping extraction moves upstream attribution period, set,
   contributor, quality-flag, and numeric coercion mapping into
   `src/app/services/risk_workspace_attribution_mapping.py` while preserving public
   `map_attribution_response` behavior. It reduces
   `src/app/services/risk_workspace_attribution.py` from 408 to 274 lines and ratchets the
   blocking threshold from 408/49 to 406/49 because
   `src/app/clients/advise_proposal_client.py` is now the sole 406-line hotspot; threshold trials
   prove 406 passes while 405 fails only on that file. Focused validation includes risk workspace
   attribution, risk workspace service, service-boundary, refactor-threshold, and agent quality
   evidence checks.
10. Current Advise proposal delivery client extraction moves report-request, delivery-summary,
   delivery-event, execution-handoff, execution-status, and execution-update upstream routes into
   `src/app/clients/advise_proposal_delivery_client.py` while preserving the public
   `AdviseClient` method surface. It reduces
   `src/app/clients/advise_proposal_client.py` below the blocking ceiling and ratchets the
   blocking threshold from 406/49 to 405/49 because
   `src/app/contracts/proposal_lifecycle.py` and `src/app/services/proposal_service.py` are now
   the tied 405-line hotspots; threshold trials prove 405 passes while 404 fails only on those
   two files. Focused validation includes Advise client-boundary, refactor-threshold,
   quality-baseline artifact, and agent quality evidence checks.
11. Current risk workspace response-loading extraction moves summary, concentration, drawdown,
   rolling, and Sharpe fallback upstream response loading into
   `src/app/services/risk_workspace_response_loading.py` while preserving `RiskWorkspaceService`
   cache and correlation behavior. It reduces `src/app/services/risk_workspace_service.py` from
   402 to 222 lines and ratchets the blocking threshold from 402/49 to 399/49 because
   `src/app/services/dpm_proof_pack_service.py` is now the sole 399-line hotspot; threshold trials
   prove 399 passes while 398 fails only on that file. Focused validation includes risk workspace
   service, service-boundary, refactor-threshold, quality-baseline artifact, and agent quality
   evidence checks; full local `make check` passed with workflow governance, refactor thresholds,
   agent quality evidence, mypy over 626 source files, OpenAPI smoke, and 1,313 unit/contract
   tests.
12. Current DPM proof-pack supportability extraction moves Manage proof-pack supportability
   derivation into `src/app/services/dpm_proof_pack_supportability.py` while preserving
   generation, lookup, Markdown, report-input, AI-evidence-input, product-safe Manage error
   mapping, and Lotus AI PM memo handoff behavior. It reduces
   `src/app/services/dpm_proof_pack_service.py` from 399 to 315 lines and ratchets the blocking
   threshold from 399/49 to 398/49 because `src/app/contracts/advisor_brief.py` is now the sole
   398-line hotspot; threshold trials prove 398 passes while 397 fails only on that file. Focused
   validation includes DPM proof-pack service, service-boundary, refactor-threshold,
   quality-baseline artifact, and agent quality evidence checks.
13. Current Advisor Brief example-boundary extraction moves the static response OpenAPI example
   into `src/app/contracts/advisor_brief_examples.py` while preserving
   `AdvisorBriefResponse` schema behavior. It reduces `src/app/contracts/advisor_brief.py` from
   398 to 207 lines and ratchets the blocking threshold from 398/49 to 397/49 because
   `src/app/services/advisor_brief_service.py` and
   `src/app/services/risk_workspace_attribution_controls.py` are the tied 397-line hotspots;
   threshold trials prove 397 passes while 396 fails on those files. Focused validation includes
   contract-module boundary, Workbench Advisor Brief OpenAPI, refactor-threshold, and agent
   quality evidence checks.
14. Current risk attribution supportability extraction moves benchmark exposure supportability
   item construction into `src/app/services/risk_workspace_attribution_supportability.py` while
   preserving risk attribution control option behavior. It reduces
   `src/app/services/risk_workspace_attribution_controls.py` below the previous 397-line ceiling
   and ratchets the blocking threshold from 397/49 to 394/49 because
   `src/app/services/dpm_command_center_service.py` is now the largest source file; threshold
   trials prove 394 passes while 393 fails on that file. Focused validation includes risk
   attribution controls, risk attribution mapper, service-boundary, refactor-threshold, and agent
   quality evidence checks.
15. Current DPM command-center response extraction moves product-safe command-center,
   outcome-review, and portfolio-memory response envelope assembly into
   `src/app/services/dpm_command_center_response.py` while preserving `DpmCommandCenterService`
   route orchestration and Manage upstream error semantics. It reduces
   `src/app/services/dpm_command_center_service.py` below the previous 394-line ceiling and ratchets
   the blocking threshold from 394/49 to 388/49 because
   `src/app/services/platform_capabilities_workspace_descriptors.py` is now the largest source
   file; threshold trials prove 388 passes while 387 fails on that file. Focused validation
   includes DPM command-center service, service-boundary, refactor-threshold, and agent quality
   evidence checks.
16. Current platform workspace descriptor spec extraction moves static shell workspace descriptor
   specs and the shell bootstrap contract constant into
   `src/app/services/platform_capabilities_workspace_descriptor_specs.py` while preserving shell
   bootstrap descriptor behavior. It reduces
   `src/app/services/platform_capabilities_workspace_descriptors.py` below the previous 388-line
   ceiling and ratchets the blocking threshold from 388/49 to 385/49 because
   `src/app/observability/analytics_ui.py` is now the largest source file; threshold trials prove
   385 passes while 384 fails on that file. Focused validation includes platform capabilities
   shell/service, service-boundary, refactor-threshold, and agent quality evidence checks.
17. Current analytics UI metric extraction moves Gateway analytics Prometheus collector
   definitions, metric-label contracts, and bounded metric recording into
   `src/app/observability/analytics_ui_metrics.py` while preserving the public
   `app.observability.analytics_ui` import surface and no-sensitive-label behavior. It reduces
   `src/app/observability/analytics_ui.py` below the previous 385-line ceiling and ratchets the
   blocking threshold from 385/49 to 383/49 because
   `src/app/services/dpm_pm_operating_quality_service.py` is now the largest source file; threshold
   trials prove 383 passes while 382 fails on that file. Focused validation includes analytics UI
   observability contracts, Prometheus label contracts, refactor-threshold, and agent quality
   evidence checks.
18. Current DPM PM operating-quality response extraction moves product-safe PM operating-quality
   response envelope assembly into `src/app/services/dpm_pm_operating_quality_response.py` while
   preserving the public `DpmPmOperatingQualityServiceMixin` route orchestration and Manage-owned
   upstream semantics. It reduces `src/app/services/dpm_pm_operating_quality_service.py` below the
   previous 383-line ceiling and ratchets the blocking threshold from 383/49 to 381/49 because
   `src/app/services/portfolio_workflow.py` is now the largest source file; threshold trials prove
   381 passes while 380 fails on that file. Focused validation includes DPM command-center service,
   service-boundary, refactor-threshold, and agent quality evidence checks.
19. Current portfolio workflow definitions extraction moves static workflow action specs and label
   policy into `src/app/services/portfolio_workflow_definitions.py` while preserving portfolio
   workflow response behavior and the single Gateway deployable boundary. It reduces
   `src/app/services/portfolio_workflow.py` below the previous 381-line ceiling and ratchets the
   blocking threshold from 381/49 to 379/49 because
   `src/app/contracts/risk_workspace_examples.py` is now the largest source file; threshold trials
   prove 379 passes while 378 fails on that file. Focused validation includes portfolio workflow,
   portfolio service, service-boundary, refactor-threshold, and agent quality evidence checks.
20. Current risk drawdown response-example extraction moves the drawdown OpenAPI/model example
   into `src/app/contracts/risk_workspace_drawdown_examples.py` while preserving the public
   `app.contracts.risk_workspace_examples` example names used by response model config. It reduces
   `src/app/contracts/risk_workspace_examples.py` below the previous 379-line ceiling and ratchets
   the blocking threshold from 379/49 to 378/49 because
   `src/app/services/upstream_envelope.py` is now the largest source file; threshold trials prove
   378 passes while 377 fails on that file. Focused validation includes risk workspace example
   model validation, contract-boundary, refactor-threshold, and agent quality evidence checks.
21. Current upstream error-policy extraction moves product-safe detail filtering, service-error
   status mapping, and service-error config types into
   `src/app/services/upstream_error_policy.py` while preserving existing
   `app.services.upstream_envelope` imports for callers. It reduces
   `src/app/services/upstream_envelope.py` below the previous 378-line ceiling and ratchets the
   blocking threshold from 378/49 to 376/49 because
   `src/app/contracts/workbench_sandbox.py` is now the largest source file; threshold trials prove
   376 passes while 375 fails on that file. Focused validation includes upstream envelope,
   service-boundary, refactor-threshold, and agent quality evidence checks.
22. Current Workbench analytics contract extraction moves analytics bucket, top-change, and
   response contracts into `src/app/contracts/workbench_analytics.py` while preserving the public
   `app.contracts.workbench` export surface. It reduces
   `src/app/contracts/workbench_sandbox.py` below the previous 376-line ceiling and ratchets the
   blocking threshold from 376/49 to 369/49 because
   `src/app/contracts/risk_workspace_drawdown.py` is now the largest source file; threshold trials
   prove 369 passes while 368 fails on that file. Focused validation includes Workbench contract,
   Workbench service analytics response, contract-boundary, refactor-threshold, and agent quality
   evidence checks.
23. Current risk drawdown payload schema example extraction moves the drawdown payload schema
   example into `src/app/contracts/risk_workspace_drawdown_examples.py` while preserving the
   `WorkbenchRiskDrawdownPayload` public contract. It reduces
   `src/app/contracts/risk_workspace_drawdown.py` below the previous 369-line ceiling and ratchets
   the blocking threshold from 369/49 to 366/49 because
   `src/app/services/advisor_brief_source.py` is now the largest source file; threshold trials
   prove 366 passes while 365 fails on that file. Focused validation includes risk drawdown
   contract, OpenAPI Workbench contract, contract-boundary, refactor-threshold, monetary-float,
   and agent quality evidence checks.
24. Current advisor brief source narrative extraction moves summary, talking-point, action, and
   risk narrative builders into `src/app/services/advisor_brief_source_narrative.py` while
   preserving the public advisor brief source context builder. It reduces
   `src/app/services/advisor_brief_source.py` below the previous 366-line ceiling and ratchets the
   blocking threshold from 366/49 to 363/49 because
   `src/app/clients/http_resilience.py` is the deterministic largest source file; threshold trials
   prove 363 passes while 362 fails on both `http_resilience.py` and
   `dpm_command_center_service.py`. Focused validation includes advisor brief source behavior,
   service-boundary, refactor-threshold, and agent quality evidence checks.
25. Current HTTP resilience retry-policy extraction moves retry attempt, backoff-delay, and
   retry-eligibility policy into `src/app/clients/http_retry_policy.py` while preserving the public
   JSON and binary retry request helpers. It reduces `src/app/clients/http_resilience.py` below the
   363-line ceiling tie and keeps the blocking threshold at 363/49 because
   `src/app/services/dpm_command_center_service.py` remains at 363 lines. Focused validation
   includes HTTP resilience behavior, retry-policy boundary, refactor-threshold, and agent quality
   evidence checks.
26. Previous DPM command center core extraction moves command-center and mandate pass-through route
   methods into `src/app/services/dpm_command_center_core_service.py` while preserving the public
   `DpmCommandCenterService` surface. It reduces
   `src/app/services/dpm_command_center_service.py` below the previous 363-line ceiling and
   ratchets the blocking threshold from 363/49 to 361/49 because
   `src/app/contracts/performance_attribution.py` is now the largest source file; threshold trials
   prove 361 passes while 360 fails on that file. Focused validation includes DPM command center
   behavior, service-boundary, refactor-threshold, and agent quality evidence checks.
27. Previous performance attribution trend contract extraction moves attribution trend row and
   response contracts into `src/app/contracts/performance_attribution_trend.py` while preserving
   `app.contracts.performance_attribution` compatibility imports. It reduces
   `src/app/contracts/performance_attribution.py` below the previous 361-line ceiling and ratchets
   the blocking threshold from 361/49 to 360/49 because `src/app/clients/reporting_client.py` is
   now the largest source file; threshold trials prove 360 passes while 359 fails on that file.
   Focused validation includes performance attribution contracts, Workbench OpenAPI contract,
   monetary-float guard, contract-boundary, refactor-threshold, and agent quality evidence checks.
28. Previous reporting batch client extraction moves report batch and schedule route-family methods
   into `src/app/clients/reporting_batch_client.py` while preserving the public `ReportingClient`
   surface. It reduces `src/app/clients/reporting_client.py` below the previous 360-line ceiling
   and ratchets the blocking threshold from 360/49 to 359/49 because
   `src/app/services/performance_workspace_benchmarks.py` is now the largest source file;
   threshold trials prove 359 passes while 358 fails on that file. Focused validation includes
   reporting client boundary, upstream reporting batch forwarding, refactor-threshold, mypy, and
   agent quality evidence checks.
29. Previous benchmark catalog parser extraction moves benchmark catalog parsing and product-safe
   failure mapping into `src/app/services/performance_workspace_benchmark_catalog.py` while
   preserving `app.services.performance_workspace_benchmarks.parse_benchmark_catalog_result` as a
   compatibility import. It reduces `src/app/services/performance_workspace_benchmarks.py` below
   the previous 359-line ceiling and ratchets the blocking threshold from 359/49 to 357/49 because
   `src/app/services/foundation_core_snapshot.py` and `src/app/contracts/dpm_outcome_review.py`
   are now the largest source files; threshold trials prove 357 passes while 356 fails on those
   files. Focused validation includes benchmark helper behavior, benchmark-boundary, mypy,
   refactor-threshold, and agent quality evidence checks.
30. Current DPM exception-summary contract extraction moves support-only exception-summary request
   and response DTOs into `src/app/contracts/dpm_exception_summary.py` while preserving
   compatibility re-exports from `app.contracts.dpm_outcome_review` and the public
   `app.contracts.dpm_command_center` facade. It reduces
   `src/app/contracts/dpm_outcome_review.py` from 357 to 250 lines while keeping the blocking
   threshold at 357/49 because `src/app/services/foundation_core_snapshot.py` remains the largest
   source file; focused validation includes DPM command-center contract shape, contract-boundary,
   mypy, refactor-threshold, and agent quality evidence checks.
31. Current Foundation core market-value extraction moves market-value key selection and
   quantized-money parsing into `src/app/services/foundation_core_market_value.py` while preserving
   the public `FoundationCoreSnapshotMapper.extract_market_value` method. It reduces
   `src/app/services/foundation_core_snapshot.py` from 357 to 333 lines and ratchets the blocking
   threshold from 357/49 to 356/49 because
   `src/app/services/dpm_pm_operating_quality_service.py` is now the largest source file; focused
   validation includes Foundation core snapshot tests, mypy, refactor-threshold, and agent quality
   evidence checks.
12. Current performance contribution payload mapping extraction moves contribution level, row,
   position, smoothing-evidence, and source-economics payload mapping into
   `src/app/services/performance_workspace_contribution_payloads.py` while preserving
   contribution summary/detail assembly and Lotus Performance source-truth payload handling. It
   reduces `src/app/services/performance_workspace_contribution.py` from 402 to 227 lines while
   keeping the blocking threshold at 402/49 because
   `src/app/services/risk_workspace_service.py` is now the sole 402-line hotspot; threshold trials
   prove 402 passes while 401 fails only on that file. Focused validation includes performance
   contribution, performance workspace service, service-boundary, refactor-threshold, and agent
   quality evidence checks.
13. Current platform capability feature and workflow flag extraction moves source capability
   feature-key and workflow-key interpretation into
   `src/app/services/platform_capabilities_feature_flags.py` while preserving normalized
   capability response behavior and shell bootstrap assembly. It reduces
   `src/app/services/platform_capabilities_normalization.py` from 404 to 192 lines, ratcheting the
   blocking threshold from 404/49 to 402/49 because
   `src/app/services/performance_workspace_contribution.py` and
   `src/app/services/risk_workspace_service.py` are now the tied 402-line hotspots; threshold
   trials prove 402 passes while 401 fails only on those two files. Focused validation includes
   platform capability normalization, platform capability service, service-boundary,
   refactor-threshold, quality-baseline artifact, and agent quality evidence checks.
14. Current proposal lifecycle contract and query-service extraction moves proposal lifecycle
   summary, workflow, lineage, and envelope DTOs into focused contract modules and moves
   workflow-events, approvals, and lineage query orchestration into
   `src/app/services/proposal_lifecycle_query_service.py` while preserving compatibility imports
   and proposal route behavior. It reduces `src/app/contracts/proposal_lifecycle.py` from 405 to
   21 lines and `src/app/services/proposal_service.py` from 405 to 324 lines, ratcheting the
   blocking threshold from 405/49 to 404/49 because
   `src/app/services/platform_capabilities_normalization.py` is now the sole 404-line hotspot;
   threshold trials prove 404 passes while 403 fails only on that file. Focused validation
   includes proposal contract, contract-boundary, service-boundary, refactor-threshold,
   quality-baseline artifact, and agent quality evidence checks.
13. Previous DPM wave AI payload extraction moved wave report-input supportability extraction,
   source-reference construction, request/task payload construction, supportability guardrail
   payloads, and gateway response assembly into `src/app/services/dpm_wave_ai_payloads.py` while
   preserving public `DpmWaveService` behavior. It reduces
   `src/app/services/dpm_wave_ai_handoff.py` from 411 to 195 lines and ratchets the blocking
   threshold from 411/49 to 408/49 because `src/app/services/risk_workspace_attribution.py` is now
   the sole 408-line hotspot; threshold trials prove 408 passes while 407 fails only on that file.
   Focused validation includes DPM wave service, DPM wave contract, service-boundary,
   refactor-threshold, and agent quality evidence checks.
10. Previous performance workspace attribution-trend service extraction moved attribution-trend
   request-context assembly, window construction, upstream fan-out, and response assembly into
   `src/app/services/performance_workspace_attribution_trend_service.py` while preserving public
   `PerformanceWorkspaceService.get_performance_attribution_trend` behavior. It reduces
   `src/app/services/performance_workspace_trend_service.py` from 415 to 223 lines and ratchets the
   blocking threshold from 415/49 to 411/49 because
   `src/app/services/dpm_wave_ai_handoff.py` is now the sole 411-line hotspot; threshold trials
   prove 411 passes while 410 fails only on that file. Focused validation includes performance
   workspace service, performance attribution, service-boundary, refactor-threshold, and agent
   quality evidence checks.
11. Current DPM wave AI contract extraction moves supportability and AI handoff DTOs into
   `src/app/contracts/dpm_wave_supportability.py` and `src/app/contracts/dpm_wave_ai.py` while
   preserving public `app.contracts.dpm_waves` imports and OpenAPI schema names. It reduces
   `src/app/contracts/dpm_waves.py` from 415 to 177 lines. The blocking threshold remains 415/49
   because `src/app/services/performance_workspace_trend_service.py` is now the sole 415-line
   hotspot; threshold trials prove 415 passes while 414 fails only on that file. Focused validation
   includes DPM wave contract, DPM wave service, contract-boundary, refactor-threshold, and agent
   quality evidence checks.
12. Current risk rolling payload-example extraction moves the large rolling OpenAPI payload example
   into `src/app/contracts/risk_workspace_rolling_examples.py` while preserving
   `WorkbenchRiskRollingPayload` schema behavior and the compatibility example alias. It reduces
   `src/app/contracts/risk_workspace_rolling.py` from 421 to 337 lines, moves the largest
   source-file hotspot to `src/app/contracts/dpm_waves.py` at 415 lines, and ratchets the blocking
   source-file threshold from 421 to 415. Focused validation includes risk rolling contract,
   contract-boundary, refactor-threshold, quality-baseline artifact, and agent quality evidence
   tests, with threshold trials proving 415 passes while 414 fails on
   `src/app/contracts/dpm_waves.py` and `src/app/services/performance_workspace_trend_service.py`.
13. Current platform capabilities source-result extraction moves upstream capability result
   classification into `src/app/services/platform_capabilities_sources.py` while preserving public
   `get_platform_capabilities` behavior. It reduces
   `src/app/services/platform_capabilities_service.py` from 427 to 326 lines, moves the largest
   source-file hotspot to `src/app/contracts/risk_workspace_rolling.py` at 421 lines, and ratchets
   the blocking source-file threshold from 427 to 421. Focused validation includes platform
   capability service, service-boundary, refactor-threshold, quality-baseline artifact, and agent
   quality evidence tests, with threshold trials proving 421 passes while 420 fails only on
   `src/app/contracts/risk_workspace_rolling.py`.
10. Current advisor-brief source metric extraction moves return-source metric construction into
   `src/app/services/advisor_brief_source_metrics.py` while preserving public
   `build_advisor_brief_source_metrics` behavior. It reduces
   `src/app/services/advisor_brief_source.py` from 429 to 366 lines, moves the largest
   source-file hotspot to `src/app/services/platform_capabilities_service.py` at 427 lines, and
   ratchets the blocking source-file threshold from 429 to 427. Focused validation includes
   advisor-brief source, service-boundary, refactor-threshold, quality-baseline artifact, and
   agent quality evidence tests, with threshold trials proving 427 passes while 426 fails only on
   `src/app/services/platform_capabilities_service.py`.
9. Current proposal generation contract extraction moves simulation request, response, and data
   contracts into `src/app/contracts/proposal_generation.py` while preserving public
   `app.contracts.proposals` imports. It reduces `src/app/contracts/proposals.py` from 431 to 314
   lines, moves the largest source-file hotspot to `src/app/services/advisor_brief_source.py` at
   429 lines, and ratchets the blocking source-file threshold from 431 to 429. Focused validation
   includes proposal contract, contract-module boundary, refactor-threshold,
   quality-baseline artifact, and agent quality evidence tests, with threshold trials proving 429
   passes while 428 fails only on `src/app/services/advisor_brief_source.py`.
9. Current risk workspace supportability extraction moves rolling supportability construction and
   shared source-calculation supportability into `risk_workspace_rolling_supportability.py` and
   `risk_workspace_source_supportability.py` while preserving rolling and attribution response
   behavior. It reduces `src/app/services/risk_workspace_rolling.py` from 432 to 342 lines and
   `src/app/services/risk_workspace_attribution.py` from 432 to 408 lines, moves the largest
   source-file hotspot to `src/app/contracts/proposals.py` at 431 lines, and ratchets the
   blocking source-file threshold from 432 to 431. Focused validation includes risk workspace
   service, rolling-window, rolling-supportability, service-boundary, refactor-threshold,
   quality-baseline artifact, and agent quality evidence tests, with threshold trials proving 431
   passes while 430 fails only on `src/app/contracts/proposals.py`.
9. Current performance workspace summary-view extraction moves summary fetch, parse, and detail-view
   fan-out orchestration into `src/app/services/performance_workspace_summary_views.py` while
   preserving the public `PerformanceWorkspaceService` response behavior. It reduces
   `src/app/services/performance_workspace_service.py` from 437 to 355 lines, moves the largest
   source-file hotspot to `src/app/services/risk_workspace_attribution.py` at 432 lines, and
   ratchets the blocking source-file threshold from 437 to 432. Focused validation includes
   performance workspace service, service-boundary, refactor-threshold, quality-baseline artifact,
   and agent quality evidence tests, with threshold trials proving 432 passes while 431 fails only
   on `src/app/services/risk_workspace_attribution.py` and
   `src/app/services/risk_workspace_rolling.py`.
9. Current advisor-brief runtime-context extraction moves runtime evidence loading into
   `src/app/services/advisor_brief_runtime_context.py` while preserving the public
   `AdvisorBriefService` response and review-action behavior. It reduces
   `src/app/services/advisor_brief_service.py` from 438 to 397 lines, moves the largest
   source-file hotspot to `src/app/services/performance_workspace_service.py` at 437 lines,
   and ratchets the blocking source-file threshold from 438 to 437. Focused validation includes
   advisor-brief service, service-boundary, refactor-threshold, quality-baseline artifact, and
   agent quality evidence tests, with threshold trials proving 437 passes while 436 fails only on
   `src/app/services/performance_workspace_service.py`.
8. Current performance attribution trend parser slice moves trend result parsing, period-payload
   selection, and row construction into `src/app/services/performance_workspace_attribution_trend.py`
   while preserving the public `performance_workspace_attribution` import surface. Focused
   validation passed with 22 performance attribution, refactor-threshold, quality-baseline
   artifact, and agent quality evidence tests, mypy over touched performance attribution modules,
   and refactor-threshold trials proving 465 passes while 464 fails only on
   `src/app/contracts/domain_products.py`. Full local `make check` passed with monetary-float
   governance at 152 findings/152 allowlisted, workflow governance, refactor thresholds, agent
   quality evidence, mypy over 595 source files, OpenAPI smoke, and 1,286 unit/contract tests.
9. Current domain-product trust contract slice moves live-trust certification DTOs into
   `src/app/contracts/domain_product_trust.py` while preserving the public
   `app.contracts.domain_products` import surface. Focused validation passed with 37
   domain-product contract, service, contract-boundary, refactor-threshold, and quality-baseline
   artifact tests, mypy over touched domain-product contract/service modules, and
   refactor-threshold trials proving 462 passes while 461 fails only on
   `src/app/services/portfolio_transaction_summary.py`. Full local `make check` passed with
   monetary-float governance at 152 findings/152 allowlisted, workflow governance, refactor
   thresholds, agent quality evidence, mypy over 596 source files, OpenAPI smoke, and 1,287
   unit/contract tests.
10. Current portfolio transaction income-summary slice moves income summary construction into
   `src/app/services/portfolio_transaction_income_summary.py` and shared transaction amount helpers
   into `src/app/services/portfolio_transaction_amounts.py` while preserving the public
   `portfolio_transaction_summary` import surface. It reduces
   `src/app/services/portfolio_transaction_summary.py` from 462 to 201 lines, moves the largest
   source-file hotspot to `src/app/services/workspace_client_protocols.py` at 458 lines, and
   ratchets the blocking threshold from 462 to 458. Focused validation passed with 21 portfolio
   transaction summary, refactor-threshold, quality-baseline artifact, and agent quality evidence
   tests, touched-module mypy, and refactor-threshold trials proving 458 passes while 457 fails
   only on the workspace client protocol hotspot; the agent quality evidence gate now tracks the
   executable 458/49 ratchet. Full local `make check` passed with monetary-float governance at
   152 findings/152 allowlisted, workflow governance, refactor thresholds, agent quality evidence,
   mypy over 598 source files, OpenAPI smoke, and 1,288 unit/contract tests.
11. Current portfolio client protocol-family slice moves `PortfolioCoreClient`,
   `PortfolioPerformanceClient`, and `PortfolioManageClient` into
   `src/app/services/portfolio_client_protocols.py` while preserving the public
   `workspace_client_protocols` compatibility surface. It reduces
   `src/app/services/workspace_client_protocols.py` from 458 to 329 lines, moves the largest
   source-file hotspot to `src/app/clients/dpm_client.py` at 452 lines, and ratchets the blocking
   threshold from 458 to 452. Focused validation passed with 99 portfolio service, portfolio
   catalog payload, service-boundary, refactor-threshold, quality-baseline artifact, and agent
   quality evidence tests, touched-module mypy, and refactor-threshold trials proving 452 passes
   while 451 fails only on the DPM client hotspot; the agent quality evidence gate now tracks the
   executable 452/49 ratchet. Full local `make check` passed with monetary-float governance at
   152 findings/152 allowlisted, workflow governance, refactor thresholds, agent quality evidence,
   mypy over 599 source files, OpenAPI smoke, and 1,290 unit/contract tests.
12. Current DPM outcome-review client route-family slice moves outcome-review upstream routes into
   `src/app/clients/dpm_outcome_review_client.py` while preserving the public `DpmClient` facade.
   It reduces `src/app/clients/dpm_client.py` below the blocking ceiling, moves the largest
   source-file hotspot to `src/app/services/risk_workspace_requests.py` at 448 lines, and ratchets
   the blocking threshold from 452 to 448. Focused validation includes DPM client boundary coverage,
   upstream-client route coverage, refactor-threshold, quality-baseline artifact, and agent quality
   evidence checks; the agent quality evidence gate now tracks the executable 448/49 ratchet.
13. Current risk workspace request-payload slice moves Lotus Risk stateful request payload
   construction and period/currency/detail-basis normalization into
   `src/app/services/risk_workspace_request_payloads.py` while preserving the public
   `risk_workspace_requests` compatibility surface. It reduces
   `src/app/services/risk_workspace_requests.py` from 448 to 254 lines, moves the largest
   source-file hotspot to `src/app/services/advisor_brief_narrative.py` at 444 lines, and ratchets
   the blocking threshold from 448 to 444. Focused validation includes risk workspace request,
   service, cache, attribution, refactor-threshold, quality-baseline artifact, and agent quality
   evidence checks; the agent quality evidence gate now tracks the executable 444/49 ratchet.
14. Current advisor-brief AI output parsing slice moves structured-output parsing, evidence-ref
   parsing, source-surface inference, and safe execution-detail extraction into
   `src/app/services/advisor_brief_ai_output.py` while preserving the public
   `advisor_brief_narrative` behavior. It reduces
   `src/app/services/advisor_brief_narrative.py` from 444 to 260 lines, moves the largest
   source-file hotspot to `src/app/services/performance_workspace_horizon.py` at 441 lines, and
   ratchets the blocking threshold from 444 to 441. Focused validation includes advisor-brief
   narrative/service, refactor-threshold, quality-baseline artifact, and agent quality evidence
   checks; the agent quality evidence gate now tracks the executable 441/49 ratchet.
15. Current performance horizon standard-window extraction moves MTD/QTD/YTD fetch and merge
   helpers into `src/app/services/performance_workspace_standard_horizon.py` while preserving the
   public horizon helper imports. It reduces `src/app/services/performance_workspace_horizon.py`
   from 441 to 220 lines, creates a focused 246-line standard-horizon helper, moves the largest
   source-file hotspot to `src/app/contracts/performance_attribution.py` at 440 lines, and ratchets
   the blocking threshold from 441 to 440. Focused validation includes horizon helper tests,
   touched-module mypy, refactor-threshold pass/fail trials, quality-baseline artifact tests, and
   agent quality evidence checks; full local `make check` passed with workflow governance,
   refactor thresholds, agent quality evidence, mypy over 603 source files, OpenAPI smoke, and
   1,293 unit/contract tests; the agent quality evidence gate now tracks the executable 440/49
   ratchet.
16. Current performance attribution supportability contract extraction moves source-owned reason,
   residual materiality, and evidence contracts into
   `src/app/contracts/performance_attribution_supportability.py` while preserving the public
   `app.contracts.performance_attribution` and `app.contracts.performance_workspace` import
   surfaces. It reduces `src/app/contracts/performance_attribution.py` from 440 to 361 lines,
   moves the largest source-file hotspot to `src/app/services/advisor_brief_service.py` at 438
   lines, and ratchets the blocking threshold from 440 to 438. Focused validation includes
   performance attribution contract tests, touched-module mypy, refactor-threshold pass/fail
   trials, quality-baseline artifact tests, and agent quality evidence checks; full local
   `make check` passed with workflow governance, refactor thresholds, agent quality evidence, mypy
   over 604 source files, OpenAPI smoke, and 1,294 unit/contract tests; the agent quality evidence
   gate now tracks the executable 438/49 ratchet.
17. All GitHub workflow jobs now declare explicit `timeout-minutes` values no higher than 60
   minutes, and `scripts/check_workflow_action_runtime.py` blocks missing or unbounded job
   timeouts in `make lint`.
11. Feature Lane and PR Merge Gate step names now call out `Lint and Refactor Quality Thresholds`
   so the promoted gate is visible in GitHub logs.
12. Current CI enforcement slice focused validation passed with 26 agent quality evidence,
   quality-baseline artifact, workflow-action runtime, and refactor-threshold tests. Full local
   `make check` passed with workflow governance, refactor thresholds, agent quality evidence, mypy
   over 579 source files, OpenAPI smoke, and 1,272 unit/contract tests.
13. Current advisor-brief contract-boundary branch moves Advisor Brief presentation/source item
   contracts into `src/app/contracts/advisor_brief_items.py` and source-supportability contracts
   into `src/app/contracts/advisor_brief_supportability.py`, preserving the public
   `app.contracts.advisor_brief` facade while reducing it from 646 to 398 script-counted lines.
   Focused validation passed with 39 Advisor Brief contract/service/supportability, threshold,
   and Workbench contract tests, mypy over 547 source files, and refactor-threshold trials proving
   `max_source_file_lines=639` passes while `638` fails on
   `src/app/services/performance_workspace_service.py`. Full local `make check` passed with 1,227
   unit/contract tests, and full local `make ci` passed with 209 integration tests, 1,436 combined
   coverage tests, 94.33% total coverage, and no known vulnerabilities after the governed
   `PYSEC-2026-161` exception.
11. Current performance workspace boundary branch moves detail-view orchestration into
   `src/app/services/performance_workspace_detail_views.py`, preserving the public
   `PerformanceWorkspaceService` surface while reducing
   `src/app/services/performance_workspace_service.py` below the previous top-file ceiling.
   Focused validation passed with 69 targeted performance workspace detail/service-boundary/threshold
   tests. Full local `make check` passed with ruff, format check over 769 files, monetary-float
   guard, refactor threshold gate, workflow action-runtime baseline, mypy over 548 source files,
   Workbench/OpenAPI contract smoke, and 1,231 unit/contract tests. Full local `make ci` passed with
   migration contract smoke, 209 integration tests, 1,440 combined coverage tests, 94.33% total
   coverage, and no known vulnerabilities after the governed `PYSEC-2026-161` exception.
   Refactor-threshold trials prove `max_source_file_lines=632` passes while `631` fails on
   `src/app/router_registry.py` and `src/app/services/risk_workspace_service.py`.
8. Current risk workspace cache-boundary branch moves cache-key construction and replay-time
   cache-status/correlation stamping into `src/app/services/risk_workspace_cache.py`, reducing
   `src/app/services/risk_workspace_service.py` below the current source-file ceiling while
   preserving risk workspace response behavior. Focused validation passed with ruff check, ruff
   format check, mypy over the touched risk workspace service modules, 54 risk workspace
   cache/service/boundary/threshold tests, and refactor-threshold trials proving
   `max_source_file_lines=630` passes while `629` fails only on
   `src/app/services/advisory_client_protocols.py`. Full local `make check` passed with ruff,
   format check over 772 files, monetary-float guard, refactor threshold gate, workflow
   action-runtime baseline, mypy over 550 source files, OpenAPI smoke, and 1,236 unit/contract
   tests. Full local `make ci` passed with migration contract smoke, 209 integration tests, 1,445
   combined coverage tests, 94.33% total coverage, and no known vulnerabilities after the governed
   `PYSEC-2026-161` exception. Branch-specific live canonical validation passed after rebuilding
   the Docker-backed Gateway and downstream stack:
   `lotus-workbench/output/playwright/live-canonical-risk-workspace-cache-boundary/live-validation-summary.json`
   records 94 API checks, 2 calculation checks, 29 screenshots, 25/25 ready panel classifications,
   28 supportability checks, 10 workflow-pack checks, no missing or non-ready panels, 9/9 RFC36-43
   features validated, and 0 RFC36-43 gaps. Companion observability evidence at
   `lotus-workbench/output/observability-live/risk-workspace-cache-boundary-20260619/observability-evidence-manifest.json`
   records 13/13 DNS checks, 13/13 representative API checks, 4/4 metric checks, 14 log artifacts,
   and 5/5 observability screenshots. GitHub checks and post-merge wiki publication remain pending
   for this branch.
9. Current advisory protocol-boundary branch splits the mixed advisory client protocol surface into
   focused bank-demo proof, copilot, workspace, cockpit, policy, and proposal protocol modules
   while preserving the public `app.services.advisory_client_protocols` facade. Focused validation
   passed with ruff check, mypy over `src`, 67 protocol/service-boundary tests, and
   refactor-threshold trials proving `max_source_file_lines=628` passes while `627` fails only on
   `src/app/clients/dpm_wave_client.py`. Full local `make check` passed with ruff, format check
   over 779 files, monetary-float guard, refactor threshold gate, workflow action-runtime baseline,
   mypy over 556 source files, OpenAPI smoke, and 1,239 unit/contract tests. Full local `make ci`
   passed with migration contract smoke, 209 integration tests, 1,448 combined coverage tests,
   94.30% total coverage, and no known vulnerabilities after the governed `PYSEC-2026-161`
   exception. Branch-specific live canonical validation passed after rebuilding the Docker-backed
   Gateway and downstream stack, then rerunning after performance lineage materialization completed:
   `lotus-workbench/output/playwright/live-canonical-advisory-protocol-boundaries-rerun/live-validation-summary.json`
   records 95 API checks, 2 calculation checks, 29 screenshots, 25/25 ready panel classifications,
   28 supportability checks, 10 workflow-pack checks, no missing or non-ready panels, 9/9 RFC36-43
   features validated, and 0 RFC36-43 gaps. Companion observability evidence at
   `lotus-workbench/output/observability-live/advisory-protocol-boundaries-rerun/observability-evidence-manifest.json`
   records 13/13 DNS checks, 13/13 representative API checks, 4/4 metric checks, 14 log artifacts,
   5/5 observability screenshots, Gateway correlation/request/trace IDs, 58 fan-out events, and 14
   audit events. Residual data-mesh limitation is not Gateway-owned: performance contribution source
   economics remains `SOURCE_LIMITED` for non-source-authored component P&L economics. GitHub checks
   and post-merge wiki publication remain pending for this branch.
7. Current DPM command-center exception-summary boundary branch focused validation passed with
   ruff check, ruff format check, mypy over four touched DPM command-center service modules,
   74 focused DPM command-center service/router/boundary tests, and refactor-threshold trials
   proving `max_source_file_lines=692` passes while `691` fails on
   `src/app/services/advisory_client_protocols.py`.
7. Current DPM command-center exception-summary boundary branch `make check` passed with ruff,
   format check over 743 files, monetary-float guard, refactor-threshold gate, workflow
   action-runtime gate, mypy over 527 source files, OpenAPI smoke, and 1,212 unit/contract tests.
8. Current DPM command-center exception-summary boundary branch `make ci` passed with migration
   contract smoke, 209 integration tests, 1,421 coverage tests, 94.29% total coverage, and no known
   vulnerabilities after the governed `PYSEC-2026-161` exception.
9. Current workbench enrichment boundary branch focused validation passed with ruff check, ruff
   format check, mypy over the touched Workbench service/enrichment modules, 114 focused
   Workbench/refactor tests, and refactor-threshold trials proving
   `max_source_file_lines=680` passes while `679` fails on
   `src/app/services/portfolio_service.py`.
10. Current workbench enrichment boundary branch `make check` passed with ruff, format check over
   748 files, monetary-float guard, refactor-threshold gate, workflow action-runtime gate, mypy
   over 530 source files, OpenAPI smoke, and 1,219 unit/contract tests.
11. Current workbench enrichment boundary branch `make ci` passed with migration contract smoke,
   209 integration tests, 1,428 combined coverage tests, 94.31% total coverage, and no known
   vulnerabilities after the governed `PYSEC-2026-161` exception.
12. Current workbench enrichment boundary branch live canonical validation passed after rebuilding
    the `lotus-gateway` container from this branch. Evidence:
    `lotus-workbench/output/playwright/live-canonical-gateway-workbench-boundaries/live-validation-summary.json`
    with 29 screenshots, 25 ready panel classifications, 2 calculation checks, 28 supportability
    checks, and 10 workflow-pack checks; companion observability evidence:
    `lotus-workbench/output/observability-live/20260618-194325/observability-evidence-manifest.json`
    with 13/13 API checks at HTTP 200, 4/4 metric checks at HTTP 200, 14 log artifacts, and 5/5
    observability screenshots at HTTP 200.
13. Previous portfolio insights response boundary branch focused validation passed with ruff check,
    ruff format, mypy over the touched portfolio service/response modules, 43 focused portfolio
    unit tests, and refactor-threshold trials proving `max_source_file_lines=667` passes while
    `666` fails on `src/app/services/performance_workspace_horizon.py`.
14. Previous portfolio insights response boundary branch `make check` passed with ruff, format
    check over 750 files, monetary-float guard, refactor-threshold gate, workflow action-runtime
    gate, mypy over 531 source files, Workbench contract smoke, and 1,220 unit/contract tests.
15. Previous portfolio insights response boundary branch `make ci` passed with migration contract
    smoke, 209 integration tests, 1,429 combined coverage tests, 94.31% total coverage, and no
    known vulnerabilities after the governed `PYSEC-2026-161` exception.
16. Previous portfolio insights response boundary branch live canonical validation passed after
    rebuilding the `lotus-gateway` container from this branch. Evidence:
    `lotus-workbench/output/playwright/live-canonical-gateway-portfolio-service-boundary/live-validation-summary.json`
    with 29 screenshots, 25 ready panel classifications, 2 calculation checks, 28 supportability
    checks, 10 workflow-pack checks, and 12 advisory journey checks; companion observability
    evidence:
    `lotus-workbench/output/observability-live/20260618-202754/observability-evidence-manifest.json`
    with 13/13 API checks at HTTP 200, 4/4 metric checks at HTTP 200, 14 log artifacts, and 5
    observability screenshots at HTTP 200.
17. Current performance horizon row-boundary branch focused validation passed with ruff check,
    ruff format, mypy over the touched performance horizon modules, 32 focused horizon and
    service-boundary unit tests, and refactor-threshold trials proving `max_source_file_lines=664`
    passes while `663` fails on `src/app/contracts/reporting_query.py`.
18. Current performance horizon row-boundary branch `make check` passed with ruff, format check
    over 751 files, monetary-float guard, refactor-threshold gate, workflow action-runtime gate,
    mypy over 532 source files, OpenAPI smoke, and 1,220 unit/contract tests.
19. Current performance horizon row-boundary branch `make ci` passed with migration contract smoke,
    209 integration tests, 1,429 combined coverage tests, 94.32% total coverage, and no known
    vulnerabilities after the governed `PYSEC-2026-161` exception.
20. Current performance horizon row-boundary branch live canonical validation passed after
    targeted-refresh rebuilt only `lotus-gateway` from this branch. Evidence:
    `lotus-workbench/output/playwright/live-canonical-gateway-performance-horizon-rows/live-validation-summary.json`
    with 94 API checks, 29 screenshots, 25 ready panel classifications, 2 calculation checks, 28
    supportability checks, 10 workflow-pack checks, 12 advisory journey checks, 0 non-demo
    screenshots, and 0 non-ready panels.
21. Current reporting query contract-boundary branch focused validation passed with 11 reporting
    query/threshold tests and refactor-threshold trials proving `max_source_file_lines=662`
    passes while `661` fails on `src/app/contracts/reporting_batches.py`. Full local
    `make check` passed with ruff, format check over 755 files, monetary-float guard,
    refactor-threshold gate, workflow action-runtime gate, mypy over 536 source files, Workbench
    contract smoke, and 1,220 unit/contract tests. Full local `make ci` passed with migration
    contract smoke, 209 integration tests, 1,429 combined coverage tests, 94.32% total coverage,
    and no known vulnerabilities after the governed `PYSEC-2026-161` exception. The slice
    preserves the existing `app.contracts.reporting_query` import surface while splitting
    status-event, job-search, snapshot-lineage, and example contract modules.
22. Current performance/reporting contract-boundary branch focused validation passed with 18
    reporting/performance contract and boundary tests, monetary-float allowlist refresh plus guard
    pass with 159 allowlisted findings, and refactor-threshold trials proving
    `max_source_file_lines=658` passes while `657` fails on
    `src/app/services/proposal_service.py`. The slice preserves the existing
    `app.contracts.performance_workspace` and `app.contracts.reporting_batches` import surfaces
    while splitting performance workspace common/summary/details contracts and report-batch
    examples, materialization, worker, and scheduler contracts. Full local `make check` passed
    with ruff, format check over 764 files, monetary-float guard, refactor-threshold gate,
    workflow action-runtime gate, mypy over 544 source files, OpenAPI smoke, and 1,225
    unit/contract tests. Full local `make ci` passed with migration contract smoke, 209
    integration tests, 1,434 combined coverage tests, 94.33% total coverage, and no known
    vulnerabilities after the governed `PYSEC-2026-161` exception.
    Canonical live validation then passed after rebuilding `lotus-gateway`, restoring the canonical
    `lotus-advise` runtime after an initial missing-container failure, and reseeding
    `PB_SG_GLOBAL_BAL_001`. `lotus-workbench/output/playwright/live-canonical/live-validation-summary.json`
    was generated at `2026-06-18T14:46:17.019Z` with 94 API checks, 29 screenshots, 25 ready
    panel classifications, 2 calculation checks, 28 supportability checks, 10 workflow-pack
    checks, and 12 advisory journey checks.
23. Current proposal service-boundary branch focused validation passed with 42 proposal-service,
    service-boundary, and threshold tests, and refactor-threshold trials proving
    `max_source_file_lines=646` passes while `645` fails on
    `src/app/contracts/advisor_brief.py`. The slice preserves the public `ProposalService`
    lifecycle transition method surface while moving submit/approval orchestration into
    `src/app/services/proposal_transition_service.py`, reducing
    `src/app/services/proposal_service.py` from 658 to 520 script-counted lines. Full local
    `make check` passed with ruff, format check over 765 files, monetary-float guard,
    refactor-threshold gate, workflow action-runtime gate, mypy over 545 source files, OpenAPI
    smoke, and 1,226 unit/contract tests. Full local `make ci` passed with migration contract
    smoke, 209 integration tests, 1,435 combined coverage tests, 94.32% total coverage, and no
    known vulnerabilities after the governed `PYSEC-2026-161` exception. GitHub gate evidence
    remains pending for this branch.
24. Previous analytics/catalog boundary branch `make check` passed with ruff, format check over
   746 files, monetary-float guard, refactor-threshold gate, workflow action-runtime gate, mypy
   over 529 source files, OpenAPI smoke, and 1,216 unit/contract tests.
25. Previous analytics/catalog boundary branch `make ci` passed with migration contract smoke, 209
   integration tests, 1,425 combined coverage tests, 94.29% total coverage, and no known
   vulnerabilities after the governed `PYSEC-2026-161` exception.
26. Previous analytics/catalog boundary branch live canonical validation passed after rebuilding the
    `lotus-gateway` container from this branch. Evidence:
    `lotus-workbench/output/playwright/live-canonical-gateway-client-catalog/live-validation-summary.json`
    with 29 screenshots, 25 ready panel classifications, 2 calculation checks, 28 supportability
    checks, and 10 workflow-pack checks; companion observability evidence:
    `lotus-workbench/output/observability-live/20260618-190935/observability-evidence-manifest.json`
    with 13/13 API checks at HTTP 200, 4/4 metric checks at HTTP 200, 14 log artifacts, and 5/5
    observability screenshots at HTTP 200.
20. Previous Advisor Brief client-protocol boundary branch `make check` passed with ruff, format
   check over 744 files, monetary-float guard, refactor-threshold gate, workflow action-runtime
   gate, mypy over 528 source files, OpenAPI smoke, and 1,213 unit/contract tests.
21. Previous Advisor Brief client-protocol boundary branch `make ci` passed with migration contract
   smoke, 209 integration tests, 1,422 coverage tests, 94.29% total coverage, and no known
   vulnerabilities after the governed `PYSEC-2026-161` exception.
22. Previous risk workspace example-boundary branch `make check` passed with ruff, format check
   over 739 files, monetary-float guard, refactor-threshold gate, workflow action-runtime gate,
   mypy over 524 source files, OpenAPI smoke, and 1,210 unit/contract tests.
23. Previous risk workspace example-boundary branch `make ci` passed with migration contract smoke,
   209 integration tests, 1,419 coverage tests, 94.29% total coverage, and no known
   vulnerabilities after the governed `PYSEC-2026-161` exception.
24. Prior source-file threshold ratchet branch focused validation passed with the then-current
   refactor threshold gate, 4 refactor-threshold unit tests, ruff check, and ruff format check over
   the touched threshold script and tests. The current blocking ceiling is recorded below.
10. Merged performance horizon contract branch focused validation passed with ruff check, ruff
    format, mypy over touched performance contract modules, 46 focused performance/workbench
    contract and integration tests, and refactor-threshold trials proving
    `max_source_file_lines=914` passes while `913` fails on `src/app/clients/advise_client.py`.
    Full local `make check` passed with 1,178 unit/contract tests. Full local `make ci` passed
    with 209 integration tests, 1,387 combined coverage tests, 94.18% total coverage, migration
    contract smoke, and no known vulnerabilities after the governed `PYSEC-2026-161` exception.
11. Merged Advise policy client-boundary branch focused validation passed with ruff check, ruff
    format, mypy over touched Advise client modules, 187 focused upstream/client-boundary/
    policy-router tests, and refactor-threshold trials proving `max_source_file_lines=872` passes
    while `871` fails on `src/app/router_registry.py`. Full local `make check` passed with 1,179
    unit/contract tests. Full local `make ci` passed with 209 integration tests, 1,388 combined
    coverage tests, 94.16% total coverage, migration contract smoke, and no known vulnerabilities
    after the governed `PYSEC-2026-161` exception.
12. Merged advisory router-group branch focused validation passed with ruff check, ruff format,
    touched-module mypy, 10 router-registry/refactor-threshold tests, and the refactor threshold
    gate at `max_source_file_lines=861`. The slice reduces `src/app/router_registry.py` from 872
    to 632 script-counted lines by moving Advise-owned router groups into
    `src/app/router_groups/advisory.py`.
13. Merged advisor brief narrative mapper branch focused validation passed with ruff check, ruff
    format, 24 advisor-brief source/narrative/service unit tests, and refactor-threshold trials
    proving `max_source_file_lines=854` passes while `853` fails on
    `src/app/services/proposal_service.py`. The slice reduces
    `src/app/services/advisor_brief_service.py` from 861 to 435 script-counted lines by moving AI
    task-request construction, AI narrative parsing, fallback audit normalization, and AI
    evidence-reference mapping into `src/app/services/advisor_brief_narrative.py`. Full local
    `make check` passed with ruff, format check over 719 files, monetary-float guard,
    refactor-threshold gate, workflow action-runtime gate, mypy over 507 source files,
    Workbench/OpenAPI contract smoke, and 1,184 unit/contract tests. Full local `make ci` passed
    with 209 integration tests, 1,393 combined coverage tests, 94.22% total coverage, migration
    contract smoke, and no known vulnerabilities after the governed `PYSEC-2026-161` exception.
14. Current proposal memo service branch focused validation passed with ruff check, ruff format,
    13 proposal-service unit tests, and refactor-threshold trials proving
    `max_source_file_lines=842` passes while `841` fails on
    `src/app/services/performance_workspace_service.py`. The slice reduces
    `src/app/services/proposal_service.py` from 854 to 658 script-counted lines by moving proposal
    memo create/read/projection/review, report-package event/request, AI-commentary request,
    lineage, and replay-evidence forwarding into `src/app/services/proposal_memo_service.py`.
    Full local `make check` passed with ruff, format check over 720 files, monetary-float guard,
    refactor-threshold gate, workflow action-runtime gate, mypy over 508 source files,
    Workbench/OpenAPI contract smoke, and 1,184 unit/contract tests. Full local `make ci` passed
    with 209 integration tests, 1,393 combined coverage tests, 94.21% total coverage, migration
    contract smoke, and no known vulnerabilities after the governed `PYSEC-2026-161` exception.
15. Current performance workspace context-service branch focused validation passed with ruff
    check, ruff format, mypy over 509 source files, 36 performance workspace service unit tests,
    and refactor-threshold trials proving `max_source_file_lines=841` passes while `840` fails on
    `src/app/contracts/dpm_command_center.py`. The slice reduces
    `src/app/services/performance_workspace_service.py` from 842 to 639 script-counted lines by
    moving cache-backed overview loading, report-window resolution, benchmark context assembly,
    and analytics-reference end-date fallback into
    `src/app/services/performance_workspace_context_service.py`. Full local `make check` passed
    with ruff, format check over 721 files, monetary-float guard, refactor-threshold gate,
    workflow action-runtime gate, mypy over 509 source files, Workbench/OpenAPI contract smoke,
    and 1,184 unit/contract tests. Full local `make ci` passed with 209 integration tests, 1,393
    combined coverage tests, 94.22% total coverage, migration contract smoke, and no known
    vulnerabilities after the governed `PYSEC-2026-161` exception.
16. Current DPM PM operating-quality contract branch focused validation passed with ruff check,
    ruff format, mypy over 510 source files, 17 focused contract/boundary/threshold tests, and
    refactor-threshold trials proving `max_source_file_lines=812` passes while `811` fails on
    `src/app/contracts/advisor_brief.py` and `src/app/contracts/proposals.py`. The slice reduces
    `src/app/contracts/dpm_command_center.py` from 841 to 593 script-counted lines by moving PM
    quality request, supportability, gateway response, and AI-summary handoff contracts into
    `src/app/contracts/dpm_pm_operating_quality.py`. Full local `make check` passed with ruff,
    format check over 722 files, monetary-float guard, refactor-threshold gate, workflow
    action-runtime gate, mypy over 510 source files, OpenAPI smoke, and 1,185 unit/contract tests.
    Full local `make ci` passed with migration contract smoke, 209 integration tests, 1,394
    combined coverage tests, 94.22% total coverage, and no known vulnerabilities after the
    governed `PYSEC-2026-161` exception.
17. Current advisor-brief/proposal contract-boundary branch focused validation passed with ruff
    check, ruff format, mypy over 512 source files, 61 advisor-brief/proposal
    contract/boundary/threshold tests, and refactor-threshold trials proving
    `max_source_file_lines=811` passes while `810` fails on `src/app/services/portfolio_service.py`.
    The slice reduces
    `src/app/contracts/advisor_brief.py` from 812 to 646 script-counted lines by moving
    workflow-pack and task-flow contracts into `src/app/contracts/advisor_brief_workflow.py`, and
    reduces `src/app/contracts/proposals.py` from 812 to 431 script-counted lines by moving
    lifecycle, version, workflow, approval, and lineage contracts into
    `src/app/contracts/proposal_lifecycle.py`. Full local `make check` passed with ruff, format
    check over 724 files, monetary-float guard, refactor-threshold gate, workflow action-runtime
    gate, mypy over 512 source files, OpenAPI smoke, and 1,187 unit/contract tests. Full local
    `make ci` passed with migration contract smoke, 209 integration tests, 1,396 combined coverage
    tests, 94.23% total coverage, and no known vulnerabilities after the governed
    `PYSEC-2026-161` exception.
18. Current portfolio workflow service-boundary branch focused validation passed with ruff check,
    ruff format, mypy over touched service files, 68 focused portfolio service/boundary/threshold
    tests, and
    refactor-threshold trials proving `max_source_file_lines=794` passes while `793` fails on
    `src/app/contracts/workbench.py`. The slice reduces `src/app/services/portfolio_service.py`
    from 811 to 768 script-counted lines by moving portfolio workflow orchestration and the
    latest-transaction probe into `src/app/services/portfolio_workflow_service.py` while preserving
    the public `PortfolioService` surface. Full local `make check` passed with ruff, format check
    over 725 files, monetary-float guard, refactor-threshold gate, workflow action-runtime gate,
    mypy over 513 source files, OpenAPI smoke, and 1,188 unit/contract tests. Full local `make ci`
    passed with migration contract smoke, 209 integration tests, 1,397 combined coverage tests,
    94.23% total coverage, and no known vulnerabilities after the governed `PYSEC-2026-161`
    exception.
19. Previous workbench contract-boundary branch moves common workbench view models, overview and
    portfolio-360 responses, and sandbox/analytics contracts into
    `src/app/contracts/workbench_common.py`, `src/app/contracts/workbench_overview.py`, and
    `src/app/contracts/workbench_sandbox.py`, reducing `src/app/contracts/workbench.py` from 794
    to 47 script-counted lines while preserving the public compatibility facade. Focused
    validation passed with ruff check, ruff format, mypy over the touched contract modules, 118
    workbench service/router/contract-boundary/threshold tests, and the refactor-threshold gate at
    `max_source_file_lines=771`. Full local `make check` passed with ruff, format check over 728
    files, monetary-float guard, refactor-threshold gate, workflow action-runtime gate, mypy over
    516 source files, OpenAPI smoke, and 1,189 unit/contract tests. Full local `make ci` passed
    with migration contract smoke, 209 integration tests, 1,398 combined coverage tests, 94.24%
    total coverage, and no known vulnerabilities after the governed `PYSEC-2026-161` exception.
13. Current portfolio holdings payload mapper branch focused validation passed with ruff format,
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
31. Prior DPM PM operating-quality client-boundary branch moves score-run, fairness-analysis,
    review-action, summary-invocation, and policy route methods into
    `dpm_pm_operating_quality_client.py` while preserving `DpmClient` as the public upstream
    client surface. Focused validation passed with ruff check, ruff format check, mypy over the
    touched clients, 182 upstream-client, boundary, and threshold unit tests, and trial refactor
    threshold gates proving `max_source_file_lines=1237` passes while `1236` fails. Local
    `make check` passed with mypy over 484 source files and 1,159 unit/contract tests. Local
    `make ci` passed with 207 integration tests, 1,366 combined coverage tests, 94.29% total
    coverage, migration contract smoke, and no known vulnerabilities after the governed
    `PYSEC-2026-161` exception.
32. Current DPM construction/proof-pack client-boundary branch moves construction-alternative and
    proof-pack route methods into `dpm_construction_client.py` and `dpm_proof_pack_client.py`
    while preserving `DpmClient` as the public upstream client surface, idempotency headers,
    route paths, operation names, observed fan-out transport, and Markdown binary response
    decoding. Focused validation passed with ruff check, ruff format check, touched-client mypy,
    180 upstream-client and boundary unit tests, and the refactor threshold gate. Local
    `make check` passed with mypy over 486 source files and 1,161 unit/contract tests. Local
    `make ci` passed with 207 integration tests, 1,368 combined coverage tests, 94.26% total
    coverage, migration contract smoke, and no known vulnerabilities after the governed
    `PYSEC-2026-161` exception.
33. Current portfolio upstream-access extraction branch moves cached Lotus Core, performance, and
    DPM upstream result acquisition into `portfolio_upstream_access.py`, reducing
    `portfolio_service.py` from 1,237 to 980 script-counted lines while preserving cache keys,
    optional-client behavior, source fan-out call shapes, and the public `PortfolioService` API.
    Focused validation passed with ruff check, touched-module mypy, 42 portfolio service tests,
    and trial refactor threshold gates proving `max_source_file_lines=1217` passes while `1216`
    fails. Local `make check` passed with ruff, format check, monetary-float guard, refactor
    threshold gate, workflow action-runtime gate, mypy over 487 source files, Workbench/OpenAPI
    contract smoke, and 1,161 unit/contract tests. Local `make ci` passed with 207 integration
    tests, 1,368 combined coverage tests, 94.26% total coverage, migration contract smoke, and no
    known vulnerabilities after the governed `PYSEC-2026-161` exception.
34. Current DPM PM operating-quality service-boundary branch moves PM operating-quality policy,
    score-run, fairness-analysis, review-action, summary-invocation, and AI summary workflow-pack
    service orchestration into `dpm_pm_operating_quality_service.py`, reducing
    `dpm_command_center_service.py` from 1,217 to 695 script-counted lines while preserving the
    public `DpmCommandCenterService` surface, manage-owned evidence boundaries, and `lotus-ai`
    workflow-pack execution behavior. Focused validation passed with ruff check, touched-module
    mypy, 48 DPM command-center service/contract tests, and trial refactor threshold gates proving
    `max_source_file_lines=1206` passes while `1205` fails. Local `make check` passed with ruff,
    format check, monetary-float guard, refactor threshold gate, workflow action-runtime gate, mypy
    over 488 source files, Workbench/OpenAPI contract smoke, and 1,161 unit/contract tests. Local
    `make ci` passed with 207 integration tests, 1,368 combined coverage tests, 94.27% total
    coverage, migration contract smoke, and no known vulnerabilities after the governed
    `PYSEC-2026-161` exception.
35. Current performance trend service-boundary branch moves performance horizon-comparison and
    attribution-trend service orchestration into `performance_workspace_trend_service.py`, reducing
    `performance_workspace_service.py` from 1,206 to 842 script-counted lines while preserving the
    public `PerformanceWorkspaceService` surface. Focused validation passed with ruff check,
    touched-module mypy, 67 performance workspace trend/horizon/attribution/context/control tests,
    and trial refactor threshold gates proving `max_source_file_lines=1098` passes while `1097`
    fails. Local `make check` passed with ruff, format check, monetary-float guard, refactor
    threshold gate, workflow action-runtime gate, mypy over 489 source files, Workbench/OpenAPI
    contract smoke, and 1,162 unit/contract tests. Local `make ci` passed with 207 integration
    tests, 1,369 combined coverage tests, 94.26% total coverage, migration contract smoke, and no
    known vulnerabilities after the governed `PYSEC-2026-161` exception.
36. Merged Advise bank-demo proof client-boundary branch moves RFC-0028 bank-demo proof upstream
    route methods into `advise_bank_demo_proof_client.py`, reducing `advise_client.py` from 1,098
    to 1,062 script-counted lines while preserving the public `AdviseClient` surface. Focused
    validation passed with ruff check, ruff format check, touched-client mypy, 14 Advise client
    boundary/factory, bank-demo proof router, Advise route-coverage, and refactor-threshold tests,
    and the refactor threshold gate at `max_source_file_lines=1093`. Full local `make check`
    passed with ruff, format check, monetary-float guard, refactor threshold gate, workflow
    action-runtime gate, mypy over 490 source files, Workbench/OpenAPI contract smoke, and 1,163
    unit/contract tests. Full local `make ci` passed with 207 integration tests, 1,370 combined
    coverage tests, 94.24% total coverage, migration contract smoke, and no known vulnerabilities
    after the governed `PYSEC-2026-161` exception.
37. Merged DPM wave AI handoff boundary branch moves PM memo and operations handoff summary
    workflow-pack orchestration into `dpm_wave_ai_handoff.py`, reducing `dpm_wave_service.py` from
    1,093 to 692 script-counted lines while preserving the public `DpmWaveService` surface.
    Focused validation passed with ruff check, ruff format check, touched-module mypy, 38 DPM wave
    service/boundary/contract/router tests, and trial refactor threshold gates proving
    `max_source_file_lines=1062` passes while `1061` fails. Full local `make check` passed with
    ruff, format check, monetary-float guard, refactor threshold gate, workflow action-runtime
    gate, mypy over 491 source files, Workbench/OpenAPI contract smoke, and 1,164 unit/contract
    tests. Full local `make ci` passed with 207 integration tests, 1,371 combined coverage tests,
    94.25% total coverage, migration contract smoke, and no known vulnerabilities after the
    governed `PYSEC-2026-161` exception.
38. Advise workspace client-boundary branch moves advisory-workspace upstream route methods
    into `advise_workspace_client.py`, reducing `advise_client.py` from 1,062 to 909
    script-counted lines while preserving the public `AdviseClient` surface. Focused validation
    passed with ruff check, ruff format check, touched-client mypy, 179 upstream-client/boundary
    tests, and the refactor threshold gate at `max_source_file_lines=1041`. Full local
    `make check` passed with ruff, format check, monetary-float guard, refactor threshold gate,
    workflow action-runtime gate, mypy over 492 source files, Workbench/OpenAPI contract smoke,
    and 1,165 unit/contract tests. Full local `make ci` passed with 207 integration tests, 1,372
    combined coverage tests, 94.23% total coverage, migration contract smoke, and no known
    vulnerabilities after the governed `PYSEC-2026-161` exception.
39. Previous DPM wave client-boundary branch moved rebalance-wave and campaign workflow upstream
    route methods into `dpm_wave_client.py`, reducing `dpm_client.py` from 1,041 to 452
    script-counted lines while preserving the public `DpmClient` surface. Focused validation
    passed with ruff check, ruff format check, 101 DPM upstream-client/boundary tests, and the
    refactor threshold gate at `max_source_file_lines=980`. Full local `make check` passed with
    ruff, format check, monetary-float guard, refactor threshold gate, workflow action-runtime
    gate, mypy over 493 source files, Workbench/OpenAPI contract smoke, and 1,166 unit/contract
    tests. Full local `make ci` passed with 207 integration tests, 1,373 combined coverage tests,
    94.21% total coverage, migration contract smoke, and no known vulnerabilities after the
    governed `PYSEC-2026-161` exception.
40. The previous portfolio transaction-boundary branch moved transaction ledger, income summary, and
    activity summary orchestration into `portfolio_transaction_service.py`, reducing
    `portfolio_service.py` from 980 script-counted lines to 811 physical lines while preserving
    the public `PortfolioService` surface. Focused validation passed with ruff check, ruff format
    check, touched-service mypy, 19 transaction/service-boundary tests, and refactor-threshold
    trials proving `max_source_file_lines=979` passes while `978` fails on
    `src/app/contracts/proposals.py`. Full local `make check` passed with ruff, format check,
    monetary-float guard, refactor threshold gate, workflow action-runtime gate, mypy over 494
    source files, Workbench/OpenAPI contract smoke, and 1,167 unit/contract tests. Full local
    `make ci` passed with 207 integration tests, 1,374 combined coverage tests, 94.22% total
    coverage, migration contract smoke, and no known vulnerabilities after the governed
    `PYSEC-2026-161` exception.
41. The previous proposal memo contract-boundary branch moved memo-specific proposal request and
    envelope contracts into `proposal_memos.py`, reducing `src/app/contracts/proposals.py` from
    979 to 828 script-counted lines while preserving the public `app.contracts.proposals` import
    surface. Focused validation passed with ruff check, ruff format check, 14 proposal
    contract/boundary/refactor-threshold tests, and refactor-threshold trials proving
    `max_source_file_lines=954` passes while `953` fails on `src/app/contracts/portfolio.py`.
    Full local `make check` passed with ruff, format check, monetary-float guard, refactor
    threshold gate, workflow action-runtime gate, mypy over 496 source files, Workbench/OpenAPI
    contract smoke, and 1,168 unit/contract tests. Full local `make ci` passed with 207
    integration tests, 1,375 combined coverage tests, 94.22% total coverage, migration contract
    smoke, and no known vulnerabilities after the governed `PYSEC-2026-161` exception.
42. Current portfolio liquidity contract-boundary branch moves liquidity and projected-cashflow
    contracts into `portfolio_liquidity.py`, reducing `src/app/contracts/portfolio.py` from 954
    to 754 script-counted lines while preserving the public `app.contracts.portfolio` import
    surface. Full local `make check` passed with 1,169 unit/contract tests, and full local
    `make ci` passed with 207 integration tests, 1,376 combined coverage tests, 94.22% total
    coverage, migration contract smoke, and no known vulnerabilities after the governed
    `PYSEC-2026-161` exception. Focused refactor-threshold trials prove
    `max_source_file_lines=951` passes while `950` fails on `src/app/services/foundation_service.py`.
43. Current Foundation core-snapshot mapper branch moves lotus-core snapshot parsing, defensive
    payload normalization, allocation bucketing, top-position mapping, and market-value extraction
    into `foundation_core_snapshot.py`, reducing `src/app/services/foundation_service.py` from
    951 to 618 script-counted lines while preserving Foundation workspace response behavior.
    Focused validation passed with ruff check, ruff format, mypy over touched service modules, and
    31 focused foundation/refactor unit, contract, and integration tests. Refactor-threshold trials prove
    `max_source_file_lines=930` passes while `929` fails on
    `src/app/contracts/performance_workspace.py`. Full local `make check` passed with ruff, format
    check, monetary-float guard, refactor threshold gate, workflow action-runtime gate, mypy over
    498 source files, Workbench/OpenAPI contract smoke, and 1,171 unit/contract tests. Full local
    `make ci` passed with 207 integration tests, 1,378 combined coverage tests, 94.23% total
    coverage, migration contract smoke, and no known vulnerabilities after the governed
    `PYSEC-2026-161` exception.
36. Current concrete-route registration fix expands registered gateway routers into concrete
    `APIRoute` entries so route enumeration, contract tests, and Prometheus route-name middleware
    do not see FastAPI lazy included-router placeholders. Focused validation passed with ruff
    check, ruff format check, mypy over `router_registry.py`, and 15 route/contract tests.
37. Current portfolio workspace component parser branch full local gates passed: `make check`
    passed with ruff, format check, monetary-float guard, refactor threshold gate, workflow
    action-runtime gate, mypy over 483 source files, Workbench/OpenAPI contract smoke, and 1,158
    unit/contract tests. `make ci` passed with 207 integration tests, 1,365 combined coverage
    tests, 94.31% total coverage, migration contract smoke, and no known vulnerabilities after
    the governed `PYSEC-2026-161` exception.
38. Merged advisory router-group branch moves Advise-owned route-family imports and group tuples
    into `src/app/router_groups/advisory.py`, reducing `src/app/router_registry.py` from 872 to
    632 script-counted lines while preserving concrete route registration. Focused validation
    passed with ruff check, ruff format check, touched-module mypy, 10 router-registry/refactor
    threshold tests, and the refactor threshold gate at `max_source_file_lines=861`. Full local
    `make check` passed with ruff, format check over 716 files, monetary-float guard,
    refactor-threshold gate, workflow action-runtime gate, mypy over 506 source files,
    Workbench/OpenAPI contract smoke, and 1,180 unit/contract tests. Full local `make ci` passed
    with 209 integration tests, 1,389 combined coverage tests, 94.17% total coverage, migration
    contract smoke, and no known vulnerabilities after the governed `PYSEC-2026-161` exception.

## Next Tightening Candidates

1. Keep the quality baseline's known tool findings visible as trend data while their absolute
   thresholds are classified; keep the no-new-regression ratchet, refactor-threshold,
   workflow-governance, artifact presence, and OpenAPI artifact validity enforced so evidence gaps
   and regressions are visible.
2. Refresh the Spectral warning artifact from the GitHub quality-baseline workflow and decide
   whether explicit operation IDs should replace generated IDs.
3. Promote import-linter contracts after false positives are classified.
4. Continue tightening the enforced source-file threshold downward as the remaining largest
   services, contracts, and clients are split; `src/app/clients/dpm_client.py` is now the largest
   file at 452 script-counted lines and defines the current blocking ceiling.
5. Extend static no-sensitive-observability checks beyond the new Prometheus metric-label gate to
   broader logs, trace attributes, and diagnostics fields.
