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

## Operating rule

Gateway must preserve platform product IDs, producer repositories, approved consumers, dependency edges, artifact provenance, and degraded trust states exactly. If platform evidence is unavailable or invalid, Gateway returns bounded product-safe reason text such as `live_trust_certification_unavailable` or a generic artifact-unavailable detail; configured filesystem paths remain operator diagnostics, not product-facing API payloads.
