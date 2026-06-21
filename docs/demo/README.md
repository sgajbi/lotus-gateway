# Advisor Experience API Demo Pack

This pack helps presenters and engineers demonstrate the Gateway experience API without
overclaiming ownership or product readiness.

## Goal

Run deterministic lotus-gateway demos for:

1. the split benchmark-aware performance workstation contracts, and
2. proposal creation plus approval-chain actions.

## Demo-Safe Positioning

Use this concise talk track:

1. `lotus-gateway` is the governed Workbench-facing API boundary.
2. It composes product-ready payloads while preserving upstream source authority.
3. It exposes supportability, partial-readiness, degraded, unavailable, and permission-blocked
   states instead of hiding upstream posture.
4. It can certify deterministic Gateway route behavior through `make demo-certification`.
5. Full populated Workbench demo readiness, screenshots, and buyer-facing evidence packs require
   the canonical Workbench runtime and platform QA evidence after the Gateway route checks pass.

Do not claim that Gateway alone owns portfolio source data, performance/risk calculations,
advisory policy truth, DPM workflow state, report rendering, archive retention, or AI model output.

## Prerequisites

- lotus-advise running at `http://advise.dev.lotus`
- lotus-manage running at `http://manage.dev.lotus` for run/supportability enrichment
- lotus-gateway running at `http://gateway.dev.lotus`
- lotus-core query running at `http://core-query.dev.lotus`
- lotus-core ingestion running at `http://core-ingestion.dev.lotus`
- lotus-performance running at `http://performance.dev.lotus`

## Gateway Demo Certification

Run the app-level Gateway certification command before relying on the demo pack:

```bash
make demo-certification
```

The command writes machine-readable evidence to:

```text
output/demo-certification/gateway-demo-certification.json
```

Current scope is intentionally report-only in CI. It uses deterministic synthetic upstream fixtures
through real Gateway FastAPI routes and asserts canonical product figures for
`PB_SG_GLOBAL_BAL_001`:

1. readiness returns `ready`,
2. Workbench overview returns market value `1,250,000.0`, cash weight `8.0`, three positions,
   YTD return `4.2`, benchmark return `3.6`, and healthy DPM supportability,
3. portfolio-360 returns one projected position and net delta quantity `50.0`,
4. sandbox create/apply returns session versions `1` and `2`,
5. sandbox policy feedback returns `PASS`.

Do not treat this command as full live front-office certification. Full populated Workbench proof
still uses the governed `lotus-workbench` canonical runtime and platform QA evidence.

## Evidence To Keep

For a demo rehearsal or PR evidence package, keep:

1. the `make demo-certification` command output,
2. `output/demo-certification/gateway-demo-certification.json`,
3. any local or GitHub `make check` / `make ci` evidence used for the slice,
4. Workbench canonical runtime evidence when the demo includes UI screenshots or populated panels.

Do not paste raw client, account, holding, prompt, model-output, document, entitlement, trace, or
correlation payloads into demo notes.

## Performance Contract Demo

Use the seeded flagship mandate:

- portfolio: `DEMO_ADV_USD_001`
- assigned benchmark: `BMK_PB_GLOBAL_BALANCED_60_40`
- alternate benchmark: `BMK_GLOBAL_GROWTH_80_20`

Probe the split contracts:

```bash
curl "http://gateway.dev.lotus/api/v1/workbench/DEMO_ADV_USD_001/performance/summary?period=YTD&chart_frequency=monthly&detail_basis=NET&contribution_dimension=asset_class&attribution_dimension=asset_class&benchmark_code=BMK_PB_GLOBAL_BALANCED_60_40" \
  -H "X-Actor-Id: advisor-123" \
  -H "X-Caller-Application: lotus-workbench" \
  -H "X-Tenant-Id: tenant-sg" \
  -H "X-Region: APAC" \
  -H "X-Booking-Center-Code: SG" \
  -H "X-Role: advisor"

curl "http://gateway.dev.lotus/api/v1/workbench/DEMO_ADV_USD_001/performance/details?period=YTD&chart_frequency=monthly&detail_basis=NET&contribution_dimension=asset_class&attribution_dimension=asset_class&benchmark_code=BMK_PB_GLOBAL_BALANCED_60_40"

curl "http://gateway.dev.lotus/api/v1/workbench/DEMO_ADV_USD_001/performance/horizon-comparison?detail_basis=NET&chart_frequency=monthly&benchmark_code=BMK_PB_GLOBAL_BALANCED_60_40"

curl "http://gateway.dev.lotus/api/v1/workbench/DEMO_ADV_USD_001/performance/attribution-trend?period=YTD&chart_frequency=monthly&detail_basis=NET&attribution_dimension=asset_class&benchmark_code=BMK_PB_GLOBAL_BALANCED_60_40"
```

Verify:

1. summary returns both benchmark options
2. details returns chart, contribution, and attribution blocks
3. horizon comparison returns `MTD`, `QTD`, and `YTD`
4. attribution trend returns benchmark-relative effect rows when available

## Proposal Flow Run

```bash
bash docs/demo/scripts/demo-approval-chain.sh
```

The proposal script will:

1. Create proposal draft via lotus-gateway.
2. Submit for risk review.
3. Approve risk.
4. Record client consent.
5. Fetch workflow events and approvals.
