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
| `lotus-performance` | performance summary, TWR, MWR, contribution, attribution, workspace summary, benchmark exposure context | performance workspace and first-paint modules | performance calculations and benchmark-relative interpretation remain in `lotus-performance` |
| `lotus-risk` | calculate risk, concentration, drawdown, rolling metrics, historical attribution | risk workspace modules and risk panels | risk methodology, concentration, drawdown, and attribution semantics remain in `lotus-risk` |
| `lotus-advise` | proposal lifecycle and advisory workflow surfaces | proposal workflow composition | advisory decision workflow remains in `lotus-advise` |
| `lotus-manage` | management workflow surfaces where split routing still applies | management workflow composition | discretionary management operations remain in `lotus-manage` |
| `lotus-report` | report snapshot rows | report-ready experience payloads | report generation and report row semantics remain in `lotus-report` |
| `lotus-ai` | advisor-brief and AI-supported surfaces | evidence-grounded narrative support | gateway must not invent unsupported evidence or model outputs |

## Conformance Rules

1. Gateway routes should be product-oriented contracts, not one-to-one mirrors of every upstream route.
2. Thin pass-through routes are tolerated only while a replacement-first product contract is being
   prepared.
3. Gateway services must not perform authoritative portfolio valuation, performance attribution, risk
   concentration, advisory suitability, or reporting methodology calculations.
4. `source_service`, supportability, readiness, and partial-failure metadata must survive composition
   when the product surface depends on it.
5. Any new upstream dependency must be classified into an RFC-0082 family before becoming a stable
   Workbench-facing contract.
6. Transport optimization discussions start with query shape, payload shape, caching, export semantics,
   and contract boundaries. gRPC is not a default answer for gateway integration.

## Current Evidence

Existing tests that cover this posture include:

1. `tests/unit/test_upstream_clients.py`
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

This RFC-0082 documentation slice did not change runtime behavior, OpenAPI output, or upstream
request/response contracts.

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

## Validation Lane

This document is governed as Feature Lane documentation and contract proof. Escalate to PR Merge Gate
only when a future slice changes gateway runtime behavior, public API contracts, or upstream coupling.
