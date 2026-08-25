# Mesh Data Products

## Mesh role

`lotus-gateway` is the read-only API publication face for Lotus mesh discovery and trust posture.

## Governed API surface

- `GET /api/v1/domain-products/catalog`
- `GET /api/v1/domain-products/products/{producer_repository}/{product_name}/{product_version}`
- `GET /api/v1/domain-products/dependency-graph`
- `GET /api/v1/domain-products/trust-certification`

## Platform relationship

Gateway reads platform-generated catalog, dependency graph, and live trust certification artifacts.
It owns only its repo-native consumer declarations, including direct Core dependencies for
`PortfolioManagerBookMembership:v1`, `PortfolioAnalyticsReference:v1`, `BenchmarkAssignment:v1`,
`BenchmarkDefinition:v1`, and `ExternalOrderExecutionAcknowledgement:v1`. These declarations cover
implemented Gateway reads and preserve Core ownership of portfolio state, benchmark definitions,
and external OMS supportability. Gateway does not own producer declarations, trust telemetry,
access policy, SLO policy, evidence policy, maturity matrix, or operating reports.

Catalog responses preserve platform provenance fields including `governedByRfcs`, `sourceManifestPath`, and `sourceDeclarationDirectory`. Dependency-graph responses preserve `governedByRfcs` and the source catalog reference. These fields are sourced from the generated platform artifacts; Gateway does not derive replacement provenance locally.

Performance composition preserves the Core benchmark-assignment boundary: a valid unassigned
portfolio remains distinct from an assignment lookup failure, which is surfaced as the sanitized
`BENCHMARK_ASSIGNMENT_UNAVAILABLE` warning and Core partial-failure evidence.

The RFC-0084 contract gate checks completeness in both directions: the five declared Core
domain-product routes must exist in the client source, and `/integration/` route arguments passed
as `path=` or `url=` in async or sync functions in `lotus_core*.py` (including local and module-level
route assignments, normalized f-string and `.format(...)` templates) must be represented in the
route inventory. The comparison includes route identity as well as client method, so an existing
inventoried method cannot hide an additional endpoint; unresolved public route construction fails
closed. Every Core client module must expose a statically resolvable transport route; the explicit
`lotus_core_transaction_params.py` exemption is a parameter/DTO-only module with no transport
surface. Core capabilities, effective policy, and core-snapshot calls are explicitly classified as
non-domain-product control-plane operations. An unclassified new Core integration route fails the
gate rather than silently escaping the mesh declaration.

## Operating rule

Gateway must preserve platform product IDs, producer repositories, approved consumers, dependency edges, artifact provenance, and degraded trust states exactly. If platform evidence is unavailable or invalid, Gateway returns bounded product-safe reason text such as `live_trust_certification_unavailable` or a generic artifact-unavailable detail; configured filesystem paths remain operator diagnostics, not product-facing API payloads.
