# API Surface

## Route families

- `GET /api/v1/foundation/portfolios`
- `GET /api/v1/foundation/portfolios/{portfolio_id}/workspace`
- `GET /api/v1/platform/capabilities`
- `GET /api/v1/domain-products/catalog`
- `GET /api/v1/domain-products/products/{producer_repository}/{product_name}/{product_version}`
- `GET /api/v1/domain-products/dependency-graph`
- `GET /api/v1/domain-products/trust-certification`
- `POST /api/v1/proposals/*` and `GET /api/v1/proposals/*`
- `POST /api/v1/intake/*`
- `GET /api/v1/lookups/*`
- `GET /api/v1/portfolio/*`
- `GET` and `POST /api/v1/workbench/*`
- `GET` and `POST /api/v1/reports/*`
- `/health`, `/health/live`, `/health/ready`, `/metrics`, `/docs`

## Current contract notes

- platform capabilities uses camelCase query parameters `consumerSystem` and `tenantId`
- domain-product discovery uses `consumerSystem` for caller identity and serves only
  platform-generated catalog, dependency-graph, and live trust certification artifacts
- domain-product detail requires the full governed identity:
  `producer_repository`, `product_name`, and `product_version`
- domain-product trust certification returns certified platform trust posture when the RFC-0087
  artifact exists and an explicit unavailable posture when it has not been generated
- reporting snapshot and reporting request payloads use `asOfDate`; portfolio review requests also
  support `benchmarkCode` for RFC-0002 performance and risk context
- reporting review preserves `client_sections`, `advisor_sections`, readiness, evidence, and
  partial/unavailable section states from `lotus-report`; advisor-only material must stay under
  `advisor_sections`
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

Domain-product catalog:

```bash
curl "http://127.0.0.1:8111/api/v1/domain-products/catalog?consumerSystem=lotus-workbench"
```

Domain-product detail:

```bash
curl "http://127.0.0.1:8111/api/v1/domain-products/products/lotus-core/PortfolioStateSnapshot/v1?consumerSystem=lotus-workbench"
```

Domain-product dependency graph:

```bash
curl "http://127.0.0.1:8111/api/v1/domain-products/dependency-graph?consumerSystem=lotus-workbench"
```

Domain-product trust certification:

```bash
curl "http://127.0.0.1:8111/api/v1/domain-products/trust-certification?consumerSystem=lotus-workbench"
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

Reporting portfolio review:

```bash
curl -X POST "http://127.0.0.1:8111/api/v1/reports/DEMO_DPM_EUR_001/review" \
  -H "Content-Type: application/json" \
  -d "{\"asOfDate\":\"2026-02-24\",\"sections\":[\"OVERVIEW\",\"PERFORMANCE\",\"RISK_ANALYTICS\"],\"allocationDimensions\":[\"asset_class\"],\"lookThroughMode\":\"full\",\"benchmarkCode\":\"BMK_GLOBAL_BALANCED_60_40\"}"
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
