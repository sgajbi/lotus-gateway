# lotus-gateway

FastAPI experience API for `lotus-workbench`, evolving from proposal-first aggregation and
pass-through routes into the primary BFF layer for Lotus workspace applications.

## Contribution Standards

- Contribution process: `CONTRIBUTING.md`
- Docs-with-code standard: `docs/documentation/implementation-documentation-standard.md`
- PR checklist template: `.github/pull_request_template.md`
- Platform-wide architecture governance source: `https://github.com/sgajbi/lotus-platform`

## Architecture Direction

- Experience API foundation blueprint:
  `docs/documentation/experience-api-foundation-blueprint.md`
- Current RFC history:
  `docs/rfcs/README.md`

## Quickstart

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -e ".[dev]"
make run
```

API docs: `http://gateway.dev.lotus/docs`

Preferred environment-scoped service identity:

- Gateway: `http://gateway.dev.lotus`

Public-entry repos should depend on the stable service identity above. Raw port mappings remain an
internal local-runtime detail until the full RFC-0071 rollout is complete.

## Current endpoints

- `GET /api/v1/foundation/portfolios` (selector-ready Foundation portfolio catalog)
- `GET /api/v1/foundation/portfolios/{portfolio_id}/workspace` (Foundation workspace entry payload with readiness and partial-failure-aware upstream context)
- `GET /api/v1/workbench/{portfolio_id}/performance/summary` (first-paint benchmark-aware performance summary)
- `GET /api/v1/workbench/{portfolio_id}/performance/details` (lower-canvas analytical detail contract)
- `GET /api/v1/workbench/{portfolio_id}/performance/horizon-comparison` (compact multi-horizon comparison module)
- `GET /api/v1/workbench/{portfolio_id}/performance/attribution-trend` (benchmark-relative attribution-over-time module)
- `GET /api/v1/workbench/{portfolio_id}/performance/advisor-brief` (source-grounded advisor brief with evidence refs and supportability)
- `GET /api/v1/workbench/{portfolio_id}/performance` (legacy compatibility endpoint; deprecated in favor of split Performance contracts)
- `POST /api/v1/proposals/simulate` (proxies to lotus-manage `/rebalance/proposals/simulate`)
- `POST /api/v1/proposals` (create draft proposal via lotus-manage lifecycle create)
- `GET /api/v1/proposals` (list proposals)
- `GET /api/v1/proposals/{proposal_id}` (proposal detail)
- `GET /api/v1/proposals/{proposal_id}/versions/{version_no}` (immutable proposal version detail)
- `POST /api/v1/proposals/{proposal_id}/versions` (create proposal version `N+1`)
- `POST /api/v1/proposals/{proposal_id}/submit` (submit draft for review via lotus-manage transition)
- `POST /api/v1/proposals/{proposal_id}/approve-risk` (risk approval action)
- `POST /api/v1/proposals/{proposal_id}/approve-compliance` (compliance approval action)
- `POST /api/v1/proposals/{proposal_id}/record-client-consent` (client consent action)
- `GET /api/v1/proposals/{proposal_id}/workflow-events` (workflow timeline)
- `GET /api/v1/proposals/{proposal_id}/approvals` (approval records)
- `GET /api/v1/platform/capabilities` (aggregated lotus-core+lotus-performance+lotus-manage capability contract for UI)
- `GET /api/v1/workbench/{portfolio_id}/overview` (aggregated lotus-core+lotus-performance+lotus-manage decision-console overview)
- `GET /api/v1/reports/{portfolio_id}/snapshot` (report-ready aggregation rows from lotus-report)
- `POST /api/v1/intake/portfolio-bundle` (lotus-core ingestion bundle pass-through)
- `POST /api/v1/intake/uploads/preview` (lotus-core upload preview pass-through)
- `POST /api/v1/intake/uploads/commit` (lotus-core upload commit pass-through)
- `GET /api/v1/lookups/portfolios` (lotus-core-backed portfolio selector values)
- `GET /api/v1/lookups/instruments` (lotus-core-backed instrument selector values)
- `GET /api/v1/lookups/currencies` (lotus-core-backed currency selector values)

These are the current endpoints. Because the project is pre-live, the target future direction is a
clean replacement-first experience-API model organized around workspace journeys rather than thin
upstream parity. Stale routes should be replaced and removed instead of being preserved by default
under versioned duplication, as described in
`docs/documentation/experience-api-foundation-blueprint.md`.

## Docker

```bash
make docker-up
make docker-down

make ci-local-docker
make ci-local-docker-down
```

Live platform-capabilities E2E (lotus-gateway + lotus-core + lotus-performance + lotus-manage):

```bash
export ADVISE_REPO_PATH=/c/Users/sande/dev/lotus-advise
export LOTUS_MANAGE_REPO_PATH=/c/Users/sande/dev/lotus-manage
export LOTUS_CORE_REPO_PATH=/c/Users/sande/dev/lotus-core
export LOTUS_PERFORMANCE_REPO_PATH=/c/Users/sande/dev/lotus-performance
make e2e-up
make test-e2e-live
make e2e-down
```

Coverage gate (local parity with CI threshold):

```bash
make test-coverage
```

## Live Performance Demo Contracts

The current flagship performance workstation integration is served from `lotus-gateway`.

Required upstreams:

- `lotus-core` query: `http://core-query.dev.lotus`
- `lotus-core` control plane: `http://core-control.dev.lotus`
- `lotus-core` ingestion: `http://core-ingestion.dev.lotus`
- `lotus-performance`: `http://performance.dev.lotus`
- `lotus-ai`: `http://ai.dev.lotus`

Example live probes:

```bash
curl "http://gateway.dev.lotus/api/v1/workbench/DEMO_ADV_USD_001/performance/summary?period=YTD&chart_frequency=monthly&detail_basis=NET&contribution_dimension=asset_class&attribution_dimension=asset_class&benchmark_code=BMK_GLOBAL_BALANCED_60_40"

curl "http://gateway.dev.lotus/api/v1/workbench/DEMO_ADV_USD_001/performance/details?period=YTD&chart_frequency=monthly&detail_basis=NET&contribution_dimension=asset_class&attribution_dimension=asset_class&benchmark_code=BMK_GLOBAL_BALANCED_60_40"

curl "http://gateway.dev.lotus/api/v1/workbench/DEMO_ADV_USD_001/performance/horizon-comparison?detail_basis=NET&chart_frequency=monthly&benchmark_code=BMK_GLOBAL_BALANCED_60_40"

curl "http://gateway.dev.lotus/api/v1/workbench/DEMO_ADV_USD_001/performance/attribution-trend?period=YTD&chart_frequency=monthly&detail_basis=NET&attribution_dimension=asset_class&benchmark_code=BMK_GLOBAL_BALANCED_60_40"

curl "http://gateway.dev.lotus/api/v1/workbench/DEMO_ADV_USD_001/performance/advisor-brief?period=YTD&chart_frequency=monthly&detail_basis=NET&contribution_dimension=asset_class&attribution_dimension=asset_class&benchmark_code=BMK_GLOBAL_BALANCED_60_40"
```

Expected benchmark catalog for the seeded flagship mandate:

- `BMK_GLOBAL_BALANCED_60_40` (`Global Balanced 60/40`)
- `BMK_GLOBAL_GROWTH_80_20` (`Global Growth 80/20`)

## Demo Pack

- `docs/demo/README.md`
- `docs/demo/payloads/proposal-create.json`
- `docs/demo/scripts/demo-approval-chain.sh`

## Platform Foundation Commands

- `make migration-smoke`
- `make migration-apply`
- `make security-audit`

Standards documentation:

- `docs/standards/migration-contract.md`
- `docs/standards/data-model-ownership.md`



Split routing notes:
- Advisory lifecycle APIs (/api/v1/proposals/*) use DECISIONING_SERVICE_BASE_URL (lotus-advise).
- lotus-manage/workbench APIs use MANAGEMENT_SERVICE_BASE_URL (lotus-manage) when MANAGE_SPLIT_ENABLED=true.



