# API Governance

`lotus-gateway` exposes the governed product API contract for Lotus front-office and operating
surfaces.

## API Shape

Public APIs should:

1. live under `/api/v1` unless a governed version change is approved,
2. use typed request and response contracts,
3. include summaries, descriptions, tags, operation IDs, examples, and standard errors,
4. preserve correlation IDs,
5. document degraded and partial-readiness behavior,
6. avoid leaking upstream-only DTOs when a product contract is required.

## OpenAPI Baseline

Current generated OpenAPI baseline:

1. 233 paths,
2. 247 operations,
3. 0 missing summaries,
4. 0 missing descriptions,
5. 0 missing generated operation IDs,
6. 0 missing tags,
7. 0 missing documented 4xx/5xx responses,
8. 0 operation tags missing a global description,
9. 186 Spectral warnings and 0 Spectral errors in the first report-only smoke; Spectral was not
   rerun locally for the latest tag-catalog update because the command is not installed locally.

`.spectral.yaml` captures report-only rules for operation ID, summary, description, tags, and
standard error responses. A contract test now fails if any generated public operation is missing a
description, tags, a documented 4xx/5xx response, or a global tag declaration with description.

## Error Governance

Gateway should converge on RFC 7807/problem-details for platform errors where applicable. Existing
unhandled exceptions return `application/problem+json`. Reporting job and report-batch upstream
errors now use explicit code-owned mapping rules for preserved validation/not-found/conflict errors
and safe fallback `502` responses. The shared generic service-error mapper now uses explicit
code-owned status rules for preserved validation/not-found errors and safe fallback `502`
responses. Product-safe service-error defaults are now also available through a typed immutable
configuration seam used by advisory-facing policy, workspace, cockpit, and bank-demo-proof
composition services; broader route-specific upstream error mapping remains a baseline improvement
area.

## Versioning And Deprecation

1. Current public APIs use `/api/v1`.
2. Breaking changes require docs, tests, and migration posture.
3. Deprecated routes must be marked in OpenAPI and referenced in supported-features material.

## Pagination, Filtering, Sorting

Collection routes should use explicit, bounded query parameters. New collection routes should
document pagination, filtering, sorting, and default ordering behavior in OpenAPI descriptions.
