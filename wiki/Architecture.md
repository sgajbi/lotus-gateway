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

## Boundary notes

1. product composition belongs here
2. domain calculations stay upstream
3. gateway must preserve supportability, readiness, and partial-failure state
4. RFC-0082 classification governs how new upstream dependencies are justified
