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

## Quality Baseline

The current architecture baseline is documented in:

1. `quality/baseline_report.md`,
2. `quality/architecture_rules.md`,
3. `.importlinter`,
4. `tests/unit/test_service_layer_boundaries.py`,
5. `tests/unit/test_router_layer_boundaries.py`.
