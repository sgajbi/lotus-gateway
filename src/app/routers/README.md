# Routers Guide

## Responsibility

`src/app/routers/` owns product-facing HTTP route handlers. Keep handlers small: accept typed
request inputs, call private request/response helpers when needed, delegate to application services,
and return contract-shaped responses.

## Boundary Rules

| Area | Rule | Evidence |
| --- | --- | --- |
| HTTP boundary | Route handlers should be single-statement delegators. | `tests/unit/test_router_layer_boundaries.py` |
| Mapping | Build filters, request DTOs, and correlation inputs in private helpers, not inline handler blocks. | `tests/unit/test_router_layer_boundaries.py` |
| Upstream access | Do not import concrete clients or service factories directly from routers. | `tests/unit/test_router_layer_boundaries.py` |
| Contract truth | Update OpenAPI and contract tests when a route payload or error changes. | `tests/contract/test_workbench_contract.py` |

## Validation

Run `python -m pytest tests/unit/test_router_layer_boundaries.py -q` for router-only changes and
`make openapi-gate` when public routes, schemas, status codes, or examples change.

## Update Triggers

Update this guide, `README.md`, `wiki/API-Surface.md`, and relevant RFC/standard docs when route
families, request mapping rules, idempotency behavior, or public API ownership changes.
