# Release note — duplicate foundation route retirement

Date: 2026-08-24

The pre-live duplicate Gateway route family under `/api/v1/foundation/*` has been removed after
the Workbench validator migrated to the canonical product-owned portfolio workspace routes.

There is no redirect or compatibility alias. Clients must use:

- `GET /api/v1/portfolio/portfolios`
- `GET /api/v1/portfolio/portfolios/{portfolio_id}/workspace`
- the remaining `/api/v1/portfolio/portfolios/{portfolio_id}/*` module routes

The product workspace contract is unchanged. Gateway OpenAPI no longer publishes the retired
foundation operations or schemas. The historical RFC-0014 and RFC-0015 files remain available for
decision history and are marked retired.
