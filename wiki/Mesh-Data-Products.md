# Mesh Data Products

## Mesh role

`lotus-gateway` is the read-only API publication face for Lotus mesh discovery and trust posture.

## Governed API surface

- `GET /api/v1/domain-products/catalog`
- `GET /api/v1/domain-products/products/{producer_repository}/{product_name}/{product_version}`
- `GET /api/v1/domain-products/dependency-graph`
- `GET /api/v1/domain-products/trust-certification`

## Platform relationship

Gateway reads platform-generated catalog, dependency graph, and live trust certification artifacts. It does not own domain-product declarations, trust telemetry, access policy, SLO policy, evidence policy, maturity matrix, or operating reports.

## Operating rule

Gateway must preserve platform product IDs, producer repositories, approved consumers, dependency edges, and degraded trust states exactly. If platform evidence is unavailable, gateway should return explicit unavailable/degraded posture rather than inventing trust.
