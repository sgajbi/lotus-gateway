# API Governance Rules

`lotus-gateway` is the product-facing experience API for Lotus. API governance focuses on
truthful contracts, stable documentation, consistent error behavior, and gateway-first
consumption by product clients.

## Required Operation Shape

Every public operation should define:

1. route-family tags,
2. summary,
3. description,
4. stable operation ID,
5. request model or typed query parameters,
6. response model,
7. examples where the route is non-trivial,
8. standard error responses.

`.spectral.yaml` records these expectations as warning-level baseline checks. The current FastAPI
OpenAPI export contains 233 paths and 247 operations. Current generated OpenAPI has no missing
summaries, descriptions, operation IDs, tags, documented 4xx/5xx responses, or operation tags
missing global descriptions. The operation-level checks are now pinned by a contract test. The
last Spectral smoke using `.spectral.yaml` plus the inherited `spectral:oas` rules reported 186
warnings and no errors; Spectral was not available in the local shell for the latest tag-catalog
update, so the warning count should be refreshed from the GitHub quality-baseline workflow.

## Error Model

Gateway errors should converge on RFC 7807/problem-details where applicable. The current app has a
`ProblemDetails` model and an unhandled-exception handler that returns
`application/problem+json`; route-specific upstream error mapping remains mixed and should be
normalized incrementally.

## Pagination, Filtering, Sorting, Versioning

1. New collection endpoints should use consistent pagination naming and explicit limit bounds.
2. Filtering and sorting parameters should be enumerated and documented in OpenAPI descriptions.
3. Public routes remain under `/api/v1` until a governed version change is approved.
4. Deprecation must be explicit in OpenAPI and documented in the API catalog or supported-features
   material.

## Gateway Authority Boundary

Gateway may compose and shape product payloads. It must not recompute domain-source truth or
invent readiness, entitlement, advisory, report, archive, or AI posture that belongs upstream.
