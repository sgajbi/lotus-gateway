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

## Performance Caller Authority

The Workbench Performance summary, details, horizon comparison, attribution trend, Advisor Brief
and evidence-download routes, plus the portfolio performance snapshot, admit the trusted actor,
tenant and region before source I/O. Missing/blank context returns `400 missing_caller_context`;
repeated identity headers return `400 ambiguous_caller_context`. Served OpenAPI declares the
required trio once. These development/trusted-service headers are not production IAM grants.

Routes bind the admitted context through `with_caller_headers` on request-specific service/client
views. The shared provider is never mutated. The bound Performance adapter snapshots the admitted
headers for submission, result polling, execution, lineage and artifacts, including late completions.
Redirect following is disabled for bound calls, and a foreign result origin is refused. Origin
comparison uses normalized hostname and effective HTTP port, accepting equivalent default-port
spellings while refusing different ports and user-info. Refused
JSON submission, polling and evidence redirects become explicit `502` source failures; a `3xx`
payload cannot masquerade as available evidence or a successful result. The generic
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

## Quality Baseline

The current architecture baseline is documented in:

1. `quality/baseline_report.md`,
2. `quality/architecture_rules.md`,
3. `.importlinter`,
4. `tests/unit/test_service_layer_boundaries.py`,
5. `tests/unit/test_router_layer_boundaries.py`.
