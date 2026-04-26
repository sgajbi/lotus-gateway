# Architecture

## Runtime model

- FastAPI experience API
- route families under `src/app/routers/`
- composition logic under `src/app/services/`
- upstream integrations under `src/app/clients/`
- workbench-facing contracts under `src/app/contracts/`

## Route-family map

- `foundation`
  first-paint workspace entry and selector-ready catalog
- `platform`
  aggregated capability posture for shell bootstrap and gating
- `proposals`
  advisory proposal lifecycle and approvals
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

## Boundary notes

1. product composition belongs here
2. domain calculations stay upstream
3. gateway must preserve supportability, readiness, and partial-failure state
4. RFC-0082 classification governs how new upstream dependencies are justified
5. generated-document retrieval is product-facing through gateway; archive storage, retention,
   purge, legal-hold mutation, and access-event ownership stay in `lotus-archive`
6. report batch lifecycle, scheduler configuration, and execution truth stay in `lotus-report`;
   gateway exposes the governed operator boundary and rewrites only gateway-relative status URLs
