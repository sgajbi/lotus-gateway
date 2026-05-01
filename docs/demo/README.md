# Advisor Experience API Demo Pack

## Goal

Run deterministic lotus-gateway demos for:

1. the split benchmark-aware performance workstation contracts, and
2. proposal creation plus approval-chain actions.

## Prerequisites

- lotus-advise running at `http://advise.dev.lotus`
- lotus-manage running at `http://manage.dev.lotus` for run/supportability enrichment
- lotus-gateway running at `http://gateway.dev.lotus`
- lotus-core query running at `http://core-query.dev.lotus`
- lotus-core ingestion running at `http://core-ingestion.dev.lotus`
- lotus-performance running at `http://performance.dev.lotus`

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
