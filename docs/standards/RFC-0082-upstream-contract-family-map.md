# RFC-0082 Upstream Contract Family Map

This document records how `lotus-gateway` consumes upstream Lotus services under
`lotus-platform` RFC-0082.

`lotus-gateway` is an experience API. It may compose, filter, reshape, and annotate product-facing
payloads for `lotus-workbench`, but it must not become the domain authority for portfolio source
data, performance analytics, risk analytics, advisory workflow, management workflow, reporting, or AI
outputs.

## Current Integration Posture

1. REST/OpenAPI remains the governed integration contract for current `lotus-gateway` upstream calls.
2. No current `lotus-gateway` integration requires or justifies gRPC.
3. Domain calculations stay in their authoritative upstream services.
4. Gateway services preserve upstream supportability, readiness, and partial-failure state rather than
   hiding it behind synthetic success.

## `lotus-core` Contract Family Map

| Gateway client surface | Upstream route family | RFC-0082 family | Gateway use | Boundary rule |
| --- | --- | --- | --- | --- |
| `get_capabilities` | `GET /integration/capabilities` | Control-plane and policy | expose supported upstream capability posture | do not infer unsupported capabilities locally |
| `get_effective_policy` | `GET /integration/policy/effective` | Control-plane and policy | expose effective policy context | preserve policy provenance |
| `list_portfolios`, `get_portfolio`, `get_portfolio_positions`, `get_portfolio_transactions` | `/portfolios`, `/portfolios/{portfolio_id}`, `/positions`, `/transactions` | Operational Read | product-facing portfolio and activity views | do not convert convenience reads into analytics source truth |
| `list_instruments`, lookup calls | `/instruments`, `/lookups/*` | Operational Read | selector and reference-data payloads | maintain source-service attribution |
| reporting query calls | `/reporting/*/query` | Operational Read watchlist | reporting-oriented workspace summaries | keep as read-model consumption; do not define new reporting semantics in gateway |
| `get_cashflow_projection` | `/portfolios/{portfolio_id}/cashflow-projection` | Operational Read watchlist | front-office cashflow projection panel | preserve upstream methodology and supportability |
| `get_core_snapshot` | `/integration/portfolios/{portfolio_id}/core-snapshot` | Snapshot and simulation | simulation and workspace state bundle | do not add performance or risk analytics sections locally |
| simulation session calls | `/simulation-sessions/*` | Snapshot and simulation | create and mutate projected state | gateway only brokers product flow; simulation semantics remain upstream |
| projected-state calls | `/simulation-sessions/*/projected-*` | Snapshot and simulation watchlist | projected position and summary views | watch for semantics that should move to a governed analytics service |
| `get_portfolio_analytics_reference` | `/integration/portfolios/{portfolio_id}/analytics/reference` | Analytics Input | upstream source context for analytics consumers | do not compute analytics conclusions in gateway |
| `get_benchmark_assignment` | `/integration/portfolios/{portfolio_id}/benchmark-assignment` | Analytics Input | benchmark context for workspace composition | benchmark meaning remains core-governed input |
| `get_benchmark_catalog` | `/integration/benchmarks/catalog` | Analytics Input watchlist | selector and catalog composition | keep catalog interpretation out of gateway |
| support overview and readiness calls | `/support/portfolios/{portfolio_id}/*` | Control-plane and support metadata | show supportability and readiness | preserve partial readiness and gap details |

## Domain Analytics Upstream Map

| Upstream service | Consumed surface | Gateway use | Boundary rule |
| --- | --- | --- | --- |
| `lotus-performance` | performance summary, TWR, MWR, contribution, attribution, workspace summary, benchmark exposure context, execution polling, lineage artifact inventory | performance workspace, first-paint modules, and gateway-owned evidence posture | performance calculations, execution state, and lineage provenance remain in `lotus-performance`; gateway may reshape them for UI-safe evidence review but must not invent or replace source truth |
| `lotus-risk` | calculate risk, concentration, drawdown, rolling metrics, historical attribution | risk workspace modules and risk panels | risk methodology, concentration, drawdown, and attribution semantics remain in `lotus-risk` |
| `lotus-advise` | proposal lifecycle and advisory workflow surfaces | proposal workflow composition | advisory decision workflow remains in `lotus-advise` |
| `lotus-manage` | versioned `/api/v1` rebalance run lookup, supportability summary, capability posture, construction alternatives, proof packs, portfolio memory, outcome reviews, report input, AI evidence input, and PM operating quality policy/score-run/fairness-analysis/review-action/summary-invocation lifecycle APIs | management workflow composition | discretionary management operations, proof-pack evidence, portfolio-memory timeline lineage, outcome-review truth, and PM operating quality policy/score-run/fairness-analysis/review-action/summary-invocation truth remain in `lotus-manage`; gateway must not reintroduce retired unversioned aliases, monolithic `dpm-execution-context` assumptions, local timeline reconstruction, PM scoring logic, fairness recomputation, review-rationale reinterpretation, generated-summary text/prompt/model-response exposure, PM ranking, or HR/compensation/conduct decision semantics |
| `lotus-report` | report snapshot rows, summary/review payloads, report job status/search/event/cancellation APIs, report batch materialization/status/control/operator-run APIs | report-ready experience payloads, durable report-job support posture, and RFC-0104 batch operator boundary | report generation, request semantics, job lifecycle truth, batch lifecycle truth, and batch execution truth remain in `lotus-report` |
| `lotus-archive` | archived document metadata, current-document resolution, and binary download APIs | gateway-controlled generated-document retrieval for product clients | archive metadata, retention, legal-hold, purge, lifecycle, checksum, storage, and access-audit truth remain in `lotus-archive`; gateway exposes metadata and controlled download only |
| `lotus-ai` | advisor-brief, DPM workflow-pack execution surfaces, workflow-pack run-ledger, and RFC-0097 task-flow posture surfaces | evidence-grounded narrative/support text plus bounded run/task-flow posture for Workbench | gateway must not invent unsupported evidence, model outputs, review states, replacement lineage, task-flow authority, trade approval, client messaging, PM scoring, or order-routing instructions |

## Conformance Rules

1. Gateway routes should be product-oriented contracts, not one-to-one mirrors of every upstream route.
2. Thin pass-through routes are tolerated only while a replacement-first product contract is being
   prepared.
3. Gateway services must not perform authoritative portfolio valuation, performance attribution, risk
   concentration, advisory suitability, or reporting methodology calculations.
4. `source_service`, supportability, readiness, and partial-failure metadata must survive composition
   when the product surface depends on it. Gateway preserves upstream
   `metadata.calculation_supportability` from performance and risk calculations as product-safe
   source calculation posture, but it does not recompute or override source-owned supportability.
   For `ConcentrationRiskReport:v1`, Gateway preserves the source-owned
   `single_position_concentration.top_position_weight_current`,
   `single_position_concentration.top_position_weight_proposed`,
   `single_position_concentration.top_position_weight_delta`,
   `single_position_concentration.top_position_current`, and
   `single_position_concentration.top_position_proposed` fields; it does not recompute
   `TOP_POSITION_WEIGHT`.
5. Any new upstream dependency must be classified into an RFC-0082 family before becoming a stable
   Workbench-facing contract.
6. Transport optimization discussions start with query shape, payload shape, caching, export semantics,
   and contract boundaries. gRPC is not a default answer for gateway integration.

## Current Evidence

Existing tests that cover this posture include:

1. `tests/unit/test_upstream_clients.py`
   Includes `test_dpm_client_uses_only_canonical_manage_api_v1_contracts`, which exercises every
   manage-facing DPM client method and rejects retired unversioned route families and monolithic
   execution-context assumptions.
2. `tests/unit/test_workbench_service.py`
3. `tests/unit/test_workbench_service_additional.py`
4. `tests/unit/test_performance_workspace_service.py`
5. `tests/unit/test_risk_workspace_service.py`
6. `tests/unit/test_foundation_service.py`
7. `tests/unit/test_portfolio_service.py`
8. `tests/contract/test_platform_capabilities_contract.py`
9. `tests/contract/test_lookup_contract.py`
10. `tests/integration/test_workbench_router.py`
11. `tests/integration/test_portfolio_router.py`
12. `tests/integration/test_foundation_router.py`
13. `tests/integration/test_platform_capabilities_router.py`
14. `tests/e2e/test_workflow_journeys.py`

This RFC-0082 documentation slice reflects current runtime behavior:

1. `workbench/performance/summary` and `workbench/performance/details` expose a gateway-owned
   `evidence_view` sourced from lotus-performance execution polling and lineage inventory.
2. the performance `evidence_view` includes RFC-0108/RFC-0079-facing product context for as-of date,
   period, basis, benchmark, calculation scope, source services, freshness posture, methodology
   references, calculation versions, source calculation supportability, coverage, fallbacks, and
   limitations. Gateway derives only UI-safe evidence context from upstream payloads; it does not
   become the calculation or methodology authority.
3. lineage artifact links presented to downstream clients are rewritten to a gateway-owned download
   route rather than exposing direct lotus-performance URLs.
4. archived generated-document metadata and binary links are exposed through gateway-owned document
   routes rather than exposing direct lotus-archive URLs.
5. RFC-0104 report batch materialization, status, control, recovery, retry, and bounded run-once
   operator actions are exposed through gateway-owned `/api/v1/report-batches` routes while
   preserving `lotus-report` as the lifecycle and execution authority.
6. RFC-0104 config-backed scheduler list and run-due actions are exposed through gateway-owned
   `/api/v1/report-batch-schedules` routes while preserving `lotus-report` as the scheduler
   configuration and materialization authority.

## Gap Register

1. Reporting query and cashflow projection consumption remain watchlist surfaces because they can drift
   into hidden methodology ownership if gateway starts interpreting the payloads.
2. Projected-summary consumption should stay aligned with governed simulation semantics and should not
   become a gateway-owned analytics summary.
3. Thin pass-through routes should continue to be replaced by product-oriented experience contracts
   before first production release.
4. If Workbench performance or risk panels become latency-constrained, the first hardening step is
   contract and retrieval-shape optimization in the authoritative upstream service, not a gateway-local
   gRPC path.
5. Gateway archive retrieval currently has no product-owned entitlement engine beyond caller-context
   propagation and upstream archive authorization; if client-level document entitlements are required,
   the policy source must be defined before expanding UI access.
6. Gateway report batch routes are an operator/API boundary only. Workbench batch UI, RFC-0105
   replay/dashboard operations, and RFC-0106 entitlement certification must not be inferred from
   these routes until those slices are implemented and proven.

## Validation Lane

This document is governed as Feature Lane documentation and contract proof. Escalate to PR Merge Gate
only when a future slice changes gateway runtime behavior, public API contracts, or upstream coupling.
