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
- `GET /api/v1/dpm/command-center`
- `GET` and `POST /api/v1/dpm/command-center/monitoring/*`
- `GET` and `POST /api/v1/dpm/command-center/exceptions*`
- `GET /api/v1/dpm/command-center/mandates*`
- `GET` and `POST /api/v1/dpm/command-center/outcome-reviews*`
- `GET /api/v1/dpm/command-center/runs/{rebalance_run_id}/outcome-review`
- `GET /api/v1/dpm/command-center/waves/{wave_id}/outcome-reviews`
- `POST /api/v1/dpm/command-center/outcome-reviews/{outcome_review_id}/ai-narrative`
- `GET` and `POST /api/v1/dpm/command-center/construction/alternative-sets*`
- `GET` and `POST /api/v1/dpm/command-center/proof-packs*`
- `GET` and `POST /api/v1/workbench/*`
- `GET` and `POST /api/v1/reports/*`
- `POST /api/v1/reports/outcome-reviews`
- `GET /api/v1/report-jobs` and `GET`/`POST /api/v1/report-jobs/*`
- `POST /api/v1/report-batches`, `GET /api/v1/report-batches/{batch_id}`, and
  `POST /api/v1/report-batches/{batch_id}:*`
- `GET /api/v1/report-batch-schedules` and `POST /api/v1/report-batch-schedules:run-due`
- `GET /api/v1/documents/{document_id}`
- `GET /api/v1/documents/{document_id}/download`
- `GET /api/v1/analytics-ui/diagnostics/{support_reference}`
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
- portfolio review report job initiation uses canonical snake_case body fields and requires
  `Idempotency-Key`
- outcome-review report job initiation uses manage-owned `DpmOutcomeReportInput` through
  `/api/v1/reports/outcome-reviews`; Gateway forwards the payload to `lotus-report` and does not
  recompute outcome truth, render artifacts, or archive documents
- report job search, status, append-only event history, and cancellation are gateway-first under
  `/api/v1/report-jobs` and `/api/v1/report-jobs/*`
- report batch materialization, status, pause, resume, cancel, retry-failed,
  recover-expired-leases, and bounded run-once operator actions are gateway-first under
  `/api/v1/report-batches`; `lotus-report` remains the batch lifecycle and execution authority
- report batch materialization, status, and bounded run-once responses preserve
  `supportability.feature_key=report.observability.evidence_surface_supportability` from
  `lotus-report` integration capabilities so Workbench can record report evidence-surface
  freshness and supportability without direct service coupling
- RFC-0098 proof-pack composition consumes `lotus-manage` RFC-0040 proof-pack APIs through
  `/api/v1/dpm/command-center/proof-packs*`. Gateway exposes generate, get, Markdown,
  report-input, and AI-evidence-input routes for Workbench, preserving manage `proof_pack_id`,
  section states, reason codes, content hashes, source hashes, source refs, report refs, and AI
  refs. Gateway must not build proof-pack sections, recalculate hashes, infer source readiness,
  render reports, generate AI narrative, or treat `lotus-report` as proof-pack authority.
  `lotus-report` remains report materialization authority, not proof-pack authority.
- RFC-0098 construction-alternative composition consumes `lotus-manage` RFC-0039 construction
  APIs through `/api/v1/dpm/command-center/construction/alternative-sets*`. Gateway exposes
  generate, get, and select routes for Workbench, preserving manage alternative-set ids, method
  identifiers, method statuses, objective traces, constraint traces, comparison metrics,
  diagnostics, supportability, selected-alternative state, and lineage. Gateway must not optimize,
  recompute construction metrics, infer source readiness, select alternatives, execute orders, or
  let Workbench bypass Gateway.
- RFC-0098 mandate command-center composition consumes `lotus-manage` RFC-0038 mandate health,
  monitoring run, exception queue, and mandate read APIs. Gateway now exposes
  `/api/v1/dpm/command-center`, `/api/v1/dpm/command-center/monitoring/*`,
  `/api/v1/dpm/command-center/exceptions*`, and `/api/v1/dpm/command-center/mandates*` for
  Workbench command-center consumers. These routes preserve manage-published health distribution,
  health dimensions, source readiness, supportability, latest monitoring run identity, active
  exceptions, reason codes, recommended actions, mandate source lineage, and version diffs.
  Gateway must not discover PM-book membership, calculate health scores, reconstruct source
  readiness, merge exceptions across monitoring runs, resolve exceptions locally, or let Workbench
  call `lotus-manage` directly.
- RFC36-WTBD-003 portfolio-level DPM operations posture is exposed on Workbench overview and
  portfolio-360 `rebalance_snapshot`. Gateway reads manage rebalance runs through
  `/api/v1/rebalance/runs`, reads manage supportability summary through
  `/api/v1/rebalance/supportability/summary`, preserves manage action-register supportability, and
  includes a bounded recent-run list with run id, status, timestamp, workflow posture, and error
  code for Workbench operations dashboards. Gateway must not calculate supportability, workflow
  posture, or error semantics locally.
- RFC-0098 wave composition must consume `lotus-manage` RFC-0041 wave APIs for preview, create,
  source-check, simulation, selection, approval, staging, handoff, and supportability. Target
  Gateway routes belong under `/api/v1/dpm/command-center/waves*`, preserve manage `wave_id`,
  item states, aggregate metrics, selected alternative refs, proof-pack refs, handoff refs, and
  supportability refs, and must not calculate affected portfolios, readiness, alternatives,
  proof-pack state, or external execution posture.
- RFC-0098 outcome-review composition must consume `lotus-manage` RFC-0042 outcome-review APIs
  for preview, durable create, search, detail, source refresh, supportability, report input, AI
  evidence input, run lookup, and wave lookup. Gateway now exposes the first implementation-backed
  outcome-review BFF route family under `/api/v1/dpm/command-center/outcome-reviews*`,
  `/api/v1/dpm/command-center/runs/{rebalance_run_id}/outcome-review`, and
  `/api/v1/dpm/command-center/waves/{wave_id}/outcome-reviews`. These routes preserve manage
  `outcome_review_id`, state, dimension outcomes, expected values, realized values, variance,
  tolerances, source refs, source hashes, freshness, report-input posture, AI-evidence posture,
  remediation routes, and supportability. Gateway also exposes a governed AI narrative handoff
  action that reads manage-owned `DpmOutcomeAiEvidenceInput` and calls `lotus-ai`
  `outcome_review_narrative.pack@v1` as `lotus-gateway`; Gateway must not recompute outcome
  truth, generate reports, generate AI narrative locally, infer PM quality, approve trades, contact
  clients, or let Workbench bypass Gateway.
  In short: Gateway must not recompute outcome truth.
- report batch schedule list and run-due actions are gateway-first under
  `/api/v1/report-batch-schedules`; schedules remain config-backed in `lotus-report`, and gateway
  does not expose schedule CRUD or scheduler registry management
- report batch materialization requires `Idempotency-Key`; all report batch routes require
  `X-Actor-Id`, `X-Tenant-Id`, and `X-Region`, with optional `X-Caller-Application`,
  `X-Booking-Center-Code`, and `X-Role` forwarded as caller context
- archived generated-document metadata and download are gateway-first under `/api/v1/documents/*`;
  `lotus-workbench` must not call `lotus-archive` directly
- archived document routes require `X-Actor-Id`, `X-Tenant-Id`, and `X-Region`; optional
  `X-Booking-Center-Code` and `X-Role` are forwarded as caller context
- Workbench performance summary, risk summary, advisor-brief read, and advisor-brief review-action
  routes require `X-Actor-Id`, `X-Tenant-Id`, and `X-Region`; optional
  `X-Caller-Application`, `X-Booking-Center-Code`, and `X-Role` preserve entitlement and audit
  posture for RFC-0108 front-office analytics reads and workflow actions
- Workbench advisor-brief reads emit bounded analytics read audit records with
  `operation=advisor_brief.summary` and `panel=advisor-brief`; upstream authorization denials are
  recorded as permission-blocked without restricted identifiers or raw entitlement text
- legal-hold summary is returned as metadata for support posture; gateway retrieval does not expose
  legal-hold mutation, purge, retention mutation, or access-event routes
- intake upload routes accept camelCase multipart aliases such as `entityType`, `sampleSize`, and
  `allowPartial`
- selected lookup filters remain snake_case, such as `cif_id`, `booking_center`, `product_type`,
  and `instrument_page_limit`
- proposal writes require `Idempotency-Key`
- proposal simulation, create, list, detail, version, workflow-event, approval, and lineage routes
  call `lotus-advise` `/advisory/proposals/*`; they do not call `lotus-manage`
- gateway calls `lotus-manage` only through versioned `/api/v1/*` paths for discretionary
  management run lookup, supportability summary, capability posture, RFC-0038 mandate
  command-center authority APIs, RFC-0039 construction alternative-set authority APIs, and
  RFC-0042 outcome-review authority APIs
- `/metrics` includes RFC-0108 gateway analytics fan-out metrics for selected Workbench analytics
  operations plus the central `lotus-advise`, `lotus-manage`, `lotus-report`, `lotus-archive`,
  `lotus-ai`, direct `lotus-core` query/control-plane, and `lotus-core` ingestion client seams:
  `lotus_gateway_analytics_fanout_duration_seconds` and
  `lotus_gateway_analytics_degraded_total`. Labels are bounded to operation/service/status class
  and degraded reason; portfolio, client, document, transaction, session, upload, trace,
  correlation, request, response, raw prompt, and model output content are not metric labels.
  Performance and risk upstream `metadata.calculation_supportability` is folded into Gateway
  fan-out state and degraded reason labels using the same bounded label contract.
- analytics UI protected diagnostics lookup is gateway-first under
  `/api/v1/analytics-ui/diagnostics/{support_reference}`. It requires `X-Actor-Id`,
  `X-Tenant-Id`, `X-Region`, and an operator support role in `X-Role`; it returns only safe panel,
  operation, service, state, reason, forbidden-field, and operator-guidance posture and emits
  `gateway.analytics.audit.protected_diagnostics_lookup`.

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
curl "http://127.0.0.1:8111/api/v1/workbench/DEMO_ADV_USD_001/performance/summary?period=YTD&chart_frequency=monthly&detail_basis=NET&contribution_dimension=asset_class&attribution_dimension=asset_class&benchmark_code=BMK_PB_GLOBAL_BALANCED_60_40" \
  -H "X-Actor-Id: advisor-123" \
  -H "X-Caller-Application: lotus-workbench" \
  -H "X-Tenant-Id: tenant-sg" \
  -H "X-Region: APAC" \
  -H "X-Booking-Center-Code: SG" \
  -H "X-Role: advisor"
```

Risk summary:

```bash
curl "http://127.0.0.1:8111/api/v1/workbench/DEMO_ADV_USD_001/risk/summary?period=YTD&detail_basis=NET&benchmark_code=BMK_PB_GLOBAL_BALANCED_60_40&reporting_currency=USD" \
  -H "X-Actor-Id: advisor-123" \
  -H "X-Caller-Application: lotus-workbench" \
  -H "X-Tenant-Id: tenant-sg" \
  -H "X-Region: APAC" \
  -H "X-Booking-Center-Code: SG" \
  -H "X-Role: advisor"
```

Advisor brief:

```bash
curl "http://127.0.0.1:8111/api/v1/workbench/DEMO_ADV_USD_001/performance/advisor-brief?period=YTD&chart_frequency=monthly&detail_basis=NET&contribution_dimension=asset_class&attribution_dimension=asset_class&benchmark_code=BMK_PB_GLOBAL_BALANCED_60_40" \
  -H "X-Actor-Id: advisor-123" \
  -H "X-Caller-Application: lotus-workbench" \
  -H "X-Tenant-Id: tenant-sg" \
  -H "X-Region: APAC" \
  -H "X-Booking-Center-Code: SG" \
  -H "X-Role: advisor"
```

Advisor brief review action:

```bash
curl -X POST "http://127.0.0.1:8111/api/v1/workbench/DEMO_ADV_USD_001/performance/advisor-brief/review-actions?period=YTD" \
  -H "Content-Type: application/json" \
  -H "X-Actor-Id: advisor-123" \
  -H "X-Caller-Application: lotus-workbench" \
  -H "X-Tenant-Id: tenant-sg" \
  -H "X-Region: APAC" \
  -H "X-Booking-Center-Code: SG" \
  -H "X-Role: advisor" \
  -d "{\"action_type\":\"ACCEPT\",\"reviewed_by\":\"advisor-123\",\"reason\":\"Approved for client discussion.\"}"
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
  -d "{\"asOfDate\":\"2026-02-24\",\"sections\":[\"OVERVIEW\",\"PERFORMANCE\",\"RISK_ANALYTICS\"],\"allocationDimensions\":[\"asset_class\"],\"lookThroughMode\":\"full\",\"benchmarkCode\":\"BMK_PB_GLOBAL_BALANCED_60_40\"}"
```

Portfolio review report job:

```bash
curl -X POST "http://127.0.0.1:8111/api/v1/reports/portfolio-reviews" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: portfolio-review-PB_SG_GLOBAL_BAL_001-2026-04-22" \
  -H "X-Actor-Id: advisor-123" \
  -H "X-Caller-Application: lotus-workbench" \
  -H "X-Tenant-Id: tenant-sg" \
  -H "X-Region: APAC" \
  -H "X-Booking-Center-Code: SG" \
  -H "X-Role: advisor" \
  -d "{\"portfolio_scope\":{\"portfolio_ids\":[\"PB_SG_GLOBAL_BAL_001\"]},\"as_of_date\":\"2026-04-22\",\"requested_output_formats\":[\"json\"],\"reporting_currency\":\"USD\",\"options\":{\"sections\":[\"OVERVIEW\",\"PERFORMANCE\",\"RISK_ANALYTICS\"],\"benchmark_code\":\"BMK_PB_GLOBAL_BALANCED_60_40\"}}"
```

Outcome-review report job:

```bash
curl -X POST "http://127.0.0.1:8111/api/v1/reports/outcome-reviews" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: outcome-review-dor_001-pdf" \
  -H "X-Actor-Id: advisor-123" \
  -H "X-Caller-Application: lotus-workbench" \
  -H "X-Tenant-Id: tenant-sg" \
  -H "X-Region: APAC" \
  -d "{\"outcome_report_input\":{\"outcome_review_id\":\"dor_001\",\"portfolio_id\":\"PB_SG_GLOBAL_BAL_001\",\"review_window\":{\"end_date\":\"2026-04-23\"},\"content_hash\":\"sha256:report-input\"},\"requested_output_formats\":[\"pdf\"]}"
```

DPM outcome-review create:

```bash
curl -X POST "http://127.0.0.1:8111/api/v1/dpm/command-center/outcome-reviews" \
  -H "Content-Type: application/json" \
  -H "X-Correlation-Id: corr-rfc42-outcome-review-1" \
  -d "{\"body\":{\"portfolio_id\":\"PB_SG_GLOBAL_BAL_001\",\"rebalance_run_id\":\"rr_20260415_001\",\"proof_pack_id\":\"ppack_20260415_001\",\"requested_by\":\"dpm_sg_1\"}}"
```

DPM outcome-review supportability:

```bash
curl "http://127.0.0.1:8111/api/v1/dpm/command-center/outcome-reviews/or_20260415_001/supportability" \
  -H "X-Correlation-Id: corr-rfc42-supportability-1"
```

DPM outcome-review AI narrative handoff:

```bash
curl -X POST "http://127.0.0.1:8111/api/v1/dpm/command-center/outcome-reviews/or_20260415_001/ai-narrative" \
  -H "Content-Type: application/json" \
  -H "X-Correlation-Id: corr-rfc42-outcome-review-ai-narrative" \
  -d "{\"requested_outputs\":[\"pm_summary\",\"cio_summary\",\"control_summary\",\"evidence_gaps\"],\"audience\":[\"portfolio_manager\",\"cio_office\",\"investment_control\"]}"
```

Report job status:

```bash
curl "http://127.0.0.1:8111/api/v1/report-jobs/rjob_example"
```

Report job operational search:

```bash
curl "http://127.0.0.1:8111/api/v1/report-jobs?tenantId=tenant-sg&region=APAC&portfolioId=PB_SG_GLOBAL_BAL_001&status=accepted&limit=25" \
  -H "X-Actor-Id: support-operator-1" \
  -H "X-Tenant-Id: tenant-sg" \
  -H "X-Region: APAC"
```

Report job event history:

```bash
curl "http://127.0.0.1:8111/api/v1/report-jobs/rjob_example/events"
```

Report batch materialization:

```bash
curl -X POST "http://127.0.0.1:8111/api/v1/report-batches" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: batch-PB_SG_GLOBAL_BAL_001-2026-04-22" \
  -H "X-Actor-Id: support-operator-1" \
  -H "X-Caller-Application: lotus-workbench" \
  -H "X-Tenant-Id: tenant-sg" \
  -H "X-Region: APAC" \
  -d "{\"selector_mode\":\"explicit_portfolio_list\",\"portfolio_ids\":[\"PB_SG_GLOBAL_BAL_001\"],\"source_candidates\":[{\"portfolio_id\":\"PB_SG_GLOBAL_BAL_001\",\"tenant_id\":\"tenant-sg\",\"region\":\"APAC\",\"active\":true,\"selected\":true,\"source_system\":\"lotus-core\",\"source_object\":\"PortfolioScope\"}],\"as_of_date\":\"2026-04-22\",\"requested_output_formats\":[\"pdf\"],\"reporting_currency\":\"USD\",\"options\":{\"sections\":[\"OVERVIEW\",\"PERFORMANCE\"]},\"max_batch_size\":250}"
```

Report batch status:

```bash
curl "http://127.0.0.1:8111/api/v1/report-batches/rbch_example" \
  -H "X-Actor-Id: support-operator-1" \
  -H "X-Tenant-Id: tenant-sg" \
  -H "X-Region: APAC"
```

Report batch bounded operator run:

```bash
curl -X POST "http://127.0.0.1:8111/api/v1/report-batches/rbch_example:run-once" \
  -H "Content-Type: application/json" \
  -H "X-Actor-Id: support-operator-1" \
  -H "X-Tenant-Id: tenant-sg" \
  -H "X-Region: APAC" \
  -d "{\"worker_id\":\"lotus-report-batch-worker-1\",\"recover_expired_leases\":true,\"dispatch_policy\":{\"max_active_batches\":1,\"max_active_items\":5,\"max_active_upstream_jobs\":3,\"max_active_render_jobs\":2,\"max_active_archive_jobs\":2,\"lease_seconds\":300},\"runtime_load\":{\"active_batches\":0,\"active_items\":0,\"active_upstream_jobs\":0,\"active_render_jobs\":0,\"active_archive_jobs\":0}}"
```

Archived document metadata:

```bash
curl "http://127.0.0.1:8111/api/v1/documents/doc_example" \
  -H "X-Actor-Id: advisor-123" \
  -H "X-Caller-Application: lotus-workbench" \
  -H "X-Tenant-Id: tenant-sg" \
  -H "X-Region: APAC" \
  -H "X-Booking-Center-Code: SG" \
  -H "X-Role: advisor"
```

Archived document download:

```bash
curl "http://127.0.0.1:8111/api/v1/documents/doc_example/download" \
  -H "X-Actor-Id: advisor-123" \
  -H "X-Caller-Application: lotus-workbench" \
  -H "X-Tenant-Id: tenant-sg" \
  -H "X-Region: APAC" \
  -H "X-Booking-Center-Code: SG" \
  -H "X-Role: advisor" \
  --output portfolio-review.pdf
```

Analytics diagnostics protected lookup:

```bash
curl "http://127.0.0.1:8111/api/v1/analytics-ui/diagnostics/gdiag-risk-summary-permission-blocked" \
  -H "X-Actor-Id: support-operator-1" \
  -H "X-Tenant-Id: tenant-sg" \
  -H "X-Region: APAC" \
  -H "X-Role: support-operator"
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
