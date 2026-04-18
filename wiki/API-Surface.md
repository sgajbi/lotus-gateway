# API Surface

## Route families

- `GET /api/v1/foundation/portfolios`
- `GET /api/v1/foundation/portfolios/{portfolio_id}/workspace`
- `GET /api/v1/platform/capabilities`
- `POST /api/v1/proposals/*` and `GET /api/v1/proposals/*`
- `POST /api/v1/intake/*`
- `GET /api/v1/lookups/*`
- `GET /api/v1/portfolio/*`
- `GET` and `POST /api/v1/workbench/*`
- `GET` and `POST /api/v1/reports/*`
- `/health`, `/health/live`, `/health/ready`, `/metrics`, `/docs`

## Current contract notes

- platform capabilities uses camelCase query parameters `consumerSystem` and `tenantId`
- reporting snapshot and reporting request payloads use `asOfDate`
- intake upload routes accept camelCase multipart aliases such as `entityType`, `sampleSize`, and
  `allowPartial`
- selected lookup filters remain snake_case, such as `cif_id`, `booking_center`, `product_type`,
  and `instrument_page_limit`
- proposal writes require `Idempotency-Key`

## Request examples

Platform capabilities:

```bash
curl "http://127.0.0.1:8111/api/v1/platform/capabilities?consumerSystem=lotus-workbench&tenantId=default"
```

Foundation workspace:

```bash
curl "http://127.0.0.1:8111/api/v1/foundation/portfolios/PF_1001/workspace"
```

Performance summary:

```bash
curl "http://127.0.0.1:8111/api/v1/workbench/DEMO_ADV_USD_001/performance/summary?period=YTD&chart_frequency=monthly&detail_basis=NET&contribution_dimension=asset_class&attribution_dimension=asset_class&benchmark_code=BMK_GLOBAL_BALANCED_60_40"
```

Reporting summary:

```bash
curl -X POST "http://127.0.0.1:8111/api/v1/reports/DEMO_DPM_EUR_001/summary" \
  -H "Content-Type: application/json" \
  -d "{\"asOfDate\":\"2026-02-24\",\"sections\":[\"WEALTH\",\"ALLOCATION\"],\"allocationDimensions\":[\"asset_class\"]}"
```

Proposal creation:

```bash
curl -X POST "http://127.0.0.1:8111/api/v1/proposals" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: idem-create-1" \
  -d @docs/demo/payloads/proposal-create.json
```

Use these examples to preserve the current gateway-facing parameter shapes until a contract is
intentionally changed.
