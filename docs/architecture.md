# Architecture

`lotus-gateway` is the Lotus experience API and composition boundary. It is consumed primarily by
`lotus-workbench` and mediates product-facing access to domain-authoritative services.

## Role

Gateway owns:

1. product-facing API composition,
2. partial-readiness-aware aggregation,
3. route contract governance,
4. product-safe response shaping,
5. correlation, supportability, degraded-state, and evidence mediation.

Gateway does not own portfolio source truth, performance methodology, risk methodology, advisory
workflow truth, management workflow truth, reporting truth, archive truth, or AI output truth.

## Runtime Layers

1. `src/app/routers/`
   FastAPI route handlers. Routers should validate request shape, call services, and return typed
   contracts. They should not construct concrete downstream clients.
2. `src/app/services/`
   Experience orchestration, upstream composition, supportability mapping, partial-failure mapping,
   and product response shaping.
3. `src/app/clients/`
   Concrete upstream HTTP client implementations.
4. `src/app/contracts/`
   Product-facing DTOs for Workbench and external consumers.
5. `src/app/middleware/`
   Cross-cutting middleware for correlation and HTTP behavior.

## Integration Boundaries

Gateway integrates with:

1. `lotus-core` for portfolio, booking, lookup, ingestion, supportability, and source-owned AUM
   reporting inputs,
2. `lotus-performance` for performance analytics and evidence,
3. `lotus-risk` for risk workspace analytics,
4. `lotus-advise` for proposals, advisory policy, advisor cockpit, and bank-demo proof,
5. `lotus-manage` for DPM command-center and discretionary management workflows,
6. `lotus-report` for reporting and report-batch workflows,
7. `lotus-archive` for generated-document metadata and controlled download,
8. `lotus-ai` for governed workflow-pack execution seams,
9. `lotus-platform` for generated data-product catalog and trust evidence.

## Boundary Rules

1. Domain authority remains upstream.
2. Gateway preserves upstream supportability and lineage instead of recomputing truth.
3. Gateway routes should expose product-oriented contracts, not uncontrolled upstream mirrors.
4. Concrete clients are constructed in service factory modules.
5. Service modules should depend on typed protocols where possible.
6. Public API behavior must be pinned by contract or integration tests.

## Stateful Risk Tenant Scope

All five Workbench Risk routes (summary, concentration, drawdown, rolling, and attribution)
require one nonblank `X-Tenant-Id`. Gateway admits it before upstream I/O, forwards that tenant
to `lotus-risk` on the request-bound client, and partitions cached Risk answers by tenant.
Summary and concentration use the same tenant when composing `lotus-manage` mandate evidence.
The shared analytics client carries no ambient tenant and must never acquire a seeded default:
other upstreams have different admission rules. This is caller-asserted scope, not an IAM grant.
Risk retains calculation and supportability authority; Gateway does not recreate its figures.

Drawdown episode timing preserves Risk's undated opening-wealth baseline: `peak_date`,
`days_to_trough`, and `total_days` are required nullable fields. An opening loss can therefore
retain its real episode identity, depth, trough and recovery evidence without an invented peak
date or zero duration. The existing mapper validates those facts and retains depth ordering;
null timing does not downgrade otherwise valid source calculations. Existing source quality,
benchmark availability, tenant admission and cache qualification still determine response posture.
Consumers must admit null timing and show it as unavailable rather than discard the episode or
reconstruct chronology. Registered-route replay of retained actual Risk responses is bounded
contract proof, not live Risk, browser, IAM or banking certification.

## Performance Caller Authority

### Composite Fact Selectors

The existing `POST /api/v1/performance/composites/twr` and `/inspect` routes preserve
`restatement_sequence`, `return_view` and `reporting_currency` through the registered DTO,
service and concrete Performance HTTP client. Both request DTOs reject unknown fields before
source I/O; body returns, fee rates, publication assertions and selector aliases are not accepted.

An explicit positive `restatement_sequence` selects that immutable source generation. Omission
or null leaves latest qualified numeric-sequence selection to Performance. `return_view` accepts
only `GROSS`, `NET_ACTUAL` or `NET_MODEL_FEE`; omission leaves the source default `NET_ACTUAL`,
while explicit null is invalid. `reporting_currency` accepts three ASCII letters and normalizes
case to uppercase without trimming; omission or null delegates to the source definition currency.
Gateway does not derive a currency from fact rows, perform FX conversion or calculate fees.

Source failures retain the existing product-safe error mapping: a source selection conflict is
Gateway `502`, with `upstream_status=409` and bounded detail `COMPOSITE_FACT_SELECTION_INCOMPLETE`.
Gateway does not fall back to a different generation, view or currency after source refusal.

The named `test_registered_composite_replays_complete_persisted_producer_selection` controls
retain complete actual registered Performance responses at
`4ffad93e7c57789d3521ace5205bf682a6513995` in
`tests/fixtures/composite-selector-source-responses.json`. In the isolated synthetic fixture,
sequence 1 returns 1%; latest returns 9%; gross USD returns 3%; net EUR returns 5%.
Inspection retains the corresponding member inputs, weights, returns and tenant-bound lineage
artifacts. These are independent fixed expected figures over persisted synthetic publications,
not evidence of live Core/Manage materialization, production IAM or Workbench presentation.
`NET_MODEL_FEE` selection transport is not model-fee producer implementation or certification.

The source reader owns publication completeness and default/latest semantics. Manage remains
definition/membership/policy authority; Core and registered external producers own source facts;
Performance owns admitted member facts and calculations. Neither Gateway nor Workbench acquires
financial, eligibility or publication authority. The full composite programme remains under
Platform #923/#924; annual dispersion and model fees are distinct Performance #608/#609 scopes.

The Workbench Performance summary, details, horizon comparison, attribution trend, Advisor Brief
and evidence-download routes, the portfolio performance snapshot, and the composite TWR and
inspection routes admit the trusted actor, tenant and region before source I/O. Missing/blank
context returns `400 missing_caller_context`; repeated identity headers return
`400 ambiguous_caller_context`. Served OpenAPI declares the required trio once. These
development/trusted-service headers are not production IAM grants.

Routes bind the admitted context through `with_caller_headers` on request-specific service/client
views. Composite operations create an equivalently bound client view for each call. The shared
provider is never mutated. The bound Performance adapter snapshots the admitted headers for
submission, result polling, execution, lineage and artifacts, including late completions.
Redirect following is disabled for bound calls, and a foreign result origin is refused. Origin
comparison uses normalized hostname and effective HTTP port, accepting equivalent default-port
spellings while refusing different ports and user-info. Refused
JSON submission, polling and evidence redirects become explicit `502` source failures; a `3xx`
payload cannot masquerade as available evidence or a successful result. Rejected result admission
also emits the normalized failure through the existing fanout log/metrics path; an earlier `202`
submission is not the only observed outcome. No raw result URL or caller identity is logged. The generic
upstream header builder still has no ambient authority; the Core-only read fence is unchanged.

`AsyncTtlCache.scoped` supplies an ownership namespace over the existing store, lock and in-flight
tasks, not a second cache. Workspace and Advisor Brief views partition results by the full admitted
context. Equal contexts reuse results; different tenants or actors cannot join another context's
fill. Scoped invalidation preserves other callers and fences late fills using the existing task
generation rule. Correlation IDs remain observability data, not authority or cache identity.

Performance continues to own durable calculation registration, tenant-bound replay and authorized
Core reads. Gateway does not manufacture a tenant when a source refuses a request. Repository
transport tests do not certify the assembled canonical journey; that requires the separately pinned
Core/Performance/Workbench runtime receipt tracked by issue #692.

## Performance Input Evidence-Date Alignment

Summary and details expose independent `evidence_view.input_freshness` entries. Performance uses
the producer's `portfolio_timeseries` and `position_timeseries` snapshots; an assigned benchmark
requires `benchmark_return_series` or `benchmark_market_series`, with any supplied benchmark
definition/composition snapshots also checked. Reference-only or unknown endpoint families do
not establish series freshness. Every included calculation must supply its required series family.
All matching snapshots must have coherent source identity, recorded HTTP `200` retrieval and
canonical ISO business dates. Registered responses bind portfolio identity to the requested
portfolio and benchmark identity to the resolved benchmark code. Internal projections without
request identity prove coherence only, not entitlement or requested-portfolio admission.

`fresh` means all required recorded dates equal the resolved evidence business date. Any valid
different date, including mixed current/older/future dates, yields `stale`; missing, invalid,
failed or conflicting identity evidence yields `unknown`. No benchmark assignment omits the
benchmark entry rather than inventing benchmark evidence. Neither a ready peer, complete
execution/lineage nor current portfolio evidence can promote another family's missing or stale
evidence. Execution posture, source supportability and history coverage remain separate fields.

Examples bound by unit and registered summary/detail tests:

| Recorded series evidence | Performance | Benchmark |
| --- | --- | --- |
| No snapshots, assigned benchmark | unknown | unknown |
| Current portfolio, older benchmark | fresh | stale |
| Older portfolio, current benchmark | stale | fresh |
| All required series current / all older | fresh / stale | fresh / stale |

These labels are evidence-date alignment, not producer correction/revision completeness, venue
calendar coverage, independently measured source freshness, financial-calculation certification,
joined live runtime or Workbench presentation proof. Numbers and source history remain unchanged.

## Performance History Qualification

Summary and detail preserve Performance's named history contract at
`evidence_view.source_supportability[].history_coverage`, alongside calculation role/id,
actual result period keys and the selected metric basis. Requested, covered and effective
dates, calculation/calendar basis, missing count/sample and bounded reasons remain source-owned.
The current workspace source qualifies its aggregate calculation window, not each period
independently; Gateway does not manufacture finer period coverage or venue-calendar attestation.

Partial available-window returns remain numeric. For example, the retained one-year control
has a 5.0% return over January 5–9, 2026, with 360 missing observations and `available_window`.
These controls are source-derived synthetic fixtures, not a fresh live Performance run.
Complete execution, freshness or a ready peer cannot make partial/unknown history complete.
Distinct peer calculations retain their own qualification rather than merging on posture alone.

Absent/null history is optional for legacy and analytics families that do not publish it,
and never means complete history. Present malformed history uses the existing missing/invalid
source-qualification boundary: partial/unverified evidence with no invented coverage. Gateway
does not calculate performance, fill observation gaps or certify downstream presentation.

## Quality Baseline

The current architecture baseline is documented in:

1. `quality/baseline_report.md`,
2. `quality/architecture_rules.md`,
3. `.importlinter`,
4. `tests/unit/test_service_layer_boundaries.py`,
5. `tests/unit/test_router_layer_boundaries.py`.
