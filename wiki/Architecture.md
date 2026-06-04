# Architecture

## Runtime model

- FastAPI experience API
- route families under `src/app/routers/`
- composition logic under `src/app/services/`
- upstream integrations under `src/app/clients/`
- workbench-facing contracts under `src/app/contracts/`
- consolidated architecture and quality-baseline docs under
  [docs/architecture.md](../docs/architecture.md) and
  [quality/architecture_rules.md](../quality/architecture_rules.md)
- current enterprise-hardening evidence records `portfolio_service.py` at 3,155 lines after the
  portfolio workspace, insight-rule, workflow-action, typed response-component,
  transaction-summary, transaction-page, and book response extractions, with the repository
  longest-function baseline reduced to 62 lines

## Route-family map

- `foundation`
  first-paint workspace entry and selector-ready catalog
- `platform`
  aggregated capability posture for shell bootstrap and gating
- `proposals`
  advisory proposal lifecycle, approvals, lineage, reviewed narrative posture, report-request
  posture, and delivery-posture inspection over `lotus-advise`
- `advisor-cockpit`
  advisor operating actions, preparation packets, tactical house-view cohort publication,
  snapshot, supportability, and idempotent acknowledgement boundary over `lotus-advise` RFC-0026
- `bank-demo-proof`
  bank-demo scenario contract, supported-claim register, and backend proof-pack publication over
  `lotus-advise` RFC-0028 authority
- `intake` and `lookups`
  ingress handoff and selector catalog surfaces
- `portfolio`
  portfolio page workspace, readiness, book, liquidity, activity, and transactions
- `workbench`
  overview, portfolio-360, sandbox, performance, risk, and advisor brief surfaces
- `reporting`
  report snapshot, summary, and review payloads
- `report-jobs`
  report generation job initiation, search, status, event history, and cancellation
- `report-batches`
  batch materialization, status, control, and bounded operator-run boundary over `lotus-report`
- `report-batch-schedules`
  config-backed scheduler inspection and bounded run-due boundary over `lotus-report`
- `archived documents`
  generated-document metadata and controlled download boundary over `lotus-archive`
- `dpm-command-center construction`
  Workbench-facing construction alternative generation, retrieval, and selection over
  `lotus-manage` RFC-0039 authority

## Boundary notes

1. product composition belongs here
2. domain calculations stay upstream
3. gateway must preserve supportability, readiness, and partial-failure state
4. RFC-0082 classification governs how new upstream dependencies are justified
5. generated-document retrieval is product-facing through gateway; archive storage, retention,
   purge, legal-hold mutation, and access-event ownership stay in `lotus-archive`
6. report batch lifecycle, scheduler configuration, and execution truth stay in `lotus-report`;
   gateway exposes the governed operator boundary and rewrites only gateway-relative status URLs
7. construction alternatives stay in `lotus-manage`; gateway exposes the Workbench contract and
   preserves manage-owned alternatives, statuses, diagnostics, supportability, and selections
8. proposal narrative review and delivery posture stay in `lotus-advise`; gateway preserves
   source hashes, review state, narrative-package posture, and delivery events without generating
   narrative or recomputing advisory delivery truth
9. advisor cockpit action construction, preparation packets, SLA, supportability, evidence,
   lineage, and acknowledgement truth stay in `lotus-advise`; gateway publishes the
   product-facing route family and preserves Advise-owned posture without reconstructing advisory
   or meeting preparation semantics
10. bank-demo scenario-contract, supported-claim classification, material-review, and backend
    proof-pack truth stay in `lotus-advise`; gateway publishes the product-facing route family and
    preserves Advise-owned posture without inferring client-ready, screenshot, Workbench browser,
    RFP/security, external communication, OMS, order, fill, or settlement readiness
11. service modules depend on typed protocol surfaces rather than concrete upstream client classes.
    Only client factory modules construct `app.clients.*` clients; protocol modules own broad AI,
    DPM, reporting, advisory, workspace/composition, and domain-support protocol families, and
    boundary tests enforce this factory-only construction rule.
12. portfolio exception-summary payload construction is isolated in
    `src/app/services/portfolio_exception_summaries.py`; `PortfolioService` keeps readiness
    orchestration while the compact exception-summary contract remains separately testable.
13. performance workspace capability state derivation is isolated behind
    `PerformanceCapabilityInputs` and `resolve_history_date_range`; capability payload assembly
    remains in `src/app/services/performance_workspace_capabilities.py`.
14. portfolio workspace source/analytics assembly, response-component assembly, and position
    parsing, foundation workspace assembly and response composition, performance workspace
    summary/detail, horizon, attribution-trend, request contexts, and summary route dependencies,
    risk drawdown/rolling/attribution orchestration and attribution supportability, risk
    attribution route queries, shell workspace descriptor specs and descriptor state, DPM PM
    quality summary orchestration, advisor-brief route dependencies, rebalance supportability
    failure recording, portfolio transaction query contracts, portfolio transaction-summary
    context loading, transaction page loading, portfolio book response assembly, and shared
    analytics async polling now sit behind focused helpers so public route/service methods stay
    orchestration-oriented.
