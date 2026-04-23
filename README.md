# lotus-gateway

Experience API and composition boundary for Lotus product clients, primarily
`lotus-workbench`.

Repository-local engineering context:
[REPOSITORY-ENGINEERING-CONTEXT.md](REPOSITORY-ENGINEERING-CONTEXT.md)

Experience-API blueprint:
[docs/documentation/experience-api-foundation-blueprint.md](docs/documentation/experience-api-foundation-blueprint.md)

Upstream contract-family map:
[docs/standards/RFC-0082-upstream-contract-family-map.md](docs/standards/RFC-0082-upstream-contract-family-map.md)

## Purpose And Scope

`lotus-gateway` owns product-facing API composition for Lotus.

It is responsible for:

- experience-oriented payload shaping for `lotus-workbench`
- partial-readiness-aware aggregation across upstream services
- gateway-level contract governance
- product-safe routing, evidence mediation, and degraded-state handling

It does not own portfolio domain truth, analytics methodology, reporting methodology, advisory
workflow truth, management workflow truth, or AI output truth. Those remain upstream.

## Ownership And Boundaries

`lotus-gateway` is the primary backend contract for `lotus-workbench`.

It depends on:

- `lotus-core`
  portfolio, booking, lookup, ingestion, simulation, and supportability inputs
- `lotus-performance`
  performance workspace analytics and evidence lineage
- `lotus-risk`
  stateful risk workspace analytics
- `lotus-advise`
  proposal and advisory workflow capability
- `lotus-manage`
  management workflow capability when split routing is enabled
- `lotus-report`
  reporting snapshot, summary, review payloads, and durable report job lifecycle
- `lotus-ai`
  evidence-grounded advisor-brief support through the explicit workflow-pack execution seam and shared run-ledger surfaces
- `lotus-platform`
  generated domain-product catalog, dependency-graph, and live trust certification artifacts for
  read-only product discovery

Boundary rules that matter:

1. gateway contracts should be product-oriented, not thin mirrors of every upstream route
2. domain authority stays upstream
3. partial-failure and supportability signals must survive composition when the UI depends on them
4. canonical local service identity for product and cross-app validation is `http://gateway.dev.lotus`

## Current Operational Posture

1. `lotus-gateway` is the primary experience API for `lotus-workbench`.
2. Foundation, platform capabilities, proposals, reporting, intake/lookups, portfolio, and workbench
   route families are active.
3. Domain-product catalog, product detail, dependency-graph, and trust-certification discovery
   routes are active as read-only facades over platform-generated artifacts.
4. The repository is still moving from thin pass-through behavior toward cleaner experience-API
   contracts.
5. Canonical local startup relies on `--app-dir src`; omitting it on Windows can start the wrong
   `app` package and yield a misleading health-only process.

## Architecture At A Glance

Main runtime surfaces come from [src/app/main.py](src/app/main.py):

- `foundation`
  `/api/v1/foundation/*`
- `platform`
  `/api/v1/platform/*`
- `domain-products`
  `/api/v1/domain-products/*`
- `proposals`
  `/api/v1/proposals/*`
- `intake` and `lookups`
  `/api/v1/intake/*`, `/api/v1/lookups/*`
- `portfolio`
  `/api/v1/portfolio/*`
- `workbench`
  `/api/v1/workbench/*`
- `reporting`
  `/api/v1/reports/*`
- `report-jobs`
  `/api/v1/report-jobs/*`
- platform surfaces
  `/health`, `/health/live`, `/health/ready`, `/metrics`, `/docs`

Key code areas:

- `src/app/routers/`
  public HTTP route families
- `src/app/services/`
  gateway composition, partial-readiness handling, and upstream orchestration
- `src/app/contracts/`
  workbench-facing gateway contracts
- `src/app/clients/`
  upstream client integrations
- `docs/documentation/`
  experience-API architecture and implementation guidance
- `docs/standards/`
  ownership, migration, durability, and RFC-0082 integration guidance

## Repository Layout

- `src/app/main.py`
  FastAPI entrypoint and router registration
- `src/app/routers/`
  gateway route families by product surface
- `src/app/services/`
  composition and orchestration logic
- `src/app/contracts/`
  workbench-facing response and request contracts
- `tests/contract/`
  contract proof for workbench-facing surfaces
- `tests/integration/`
  composed behavior checks
- `tests/e2e/`
  workflow and live integration checks
- `scripts/`
  quality gates, migration checks, and canonical startup helpers
- `wiki/`
  canonical authored source for GitHub wiki publication

## Quick Start

Install dependencies:

```bash
make install
```

Preferred direct local run:

```bash
make run-canonical
```

Canonical local identities:

- cross-app and product validation: `http://gateway.dev.lotus`
- direct process debugging: `http://127.0.0.1:8111`

Quick probes:

```bash
curl http://127.0.0.1:8111/health
curl "http://127.0.0.1:8111/api/v1/platform/capabilities?consumerSystem=lotus-workbench&tenantId=default"
curl "http://127.0.0.1:8111/api/v1/domain-products/catalog?consumerSystem=lotus-workbench"
curl "http://127.0.0.1:8111/api/v1/domain-products/trust-certification?consumerSystem=lotus-workbench"
```

## Common Commands

- `make install`
  install dependencies
- `make lint`
  lint, format check, and monetary-float guard
- `make typecheck`
  mypy on `src/`
- `make check`
  contract and unit gate
- `make ci`
  PR-grade local proof with migration smoke, integration, coverage, and security audit
- `make ci-local-docker`
  dockerized parity check
- `make run-canonical`
  canonical local gateway runtime on port `8111`

## Validation And CI Lanes

`lotus-gateway` follows the Lotus multi-lane model:

1. `Remote Feature Lane`
2. `Pull Request Merge Gate`
3. `Main Releasability Gate`
4. platform-facing validation when cross-app experience contracts change

Repo-native gate mapping:

- `make check`
  lint, typecheck, OpenAPI contract proof, unit tests
- `make ci`
  migration smoke, integration tests, coverage, and security audit
- `make ci-local`
  local feature-lane style validation
- `make ci-local-docker`
  Docker parity for the live integration boundary

## API Contract Notes

Important current parameter conventions:

1. `GET /api/v1/platform/capabilities` uses camelCase query parameters `consumerSystem` and
   `tenantId`
2. `GET /api/v1/domain-products/catalog` and
   `GET /api/v1/domain-products/dependency-graph` use `consumerSystem` for caller identity and
   preserve platform artifact provenance
3. `GET /api/v1/domain-products/products/{producer_repository}/{product_name}/{product_version}`
   requires the full governed product identity and does not fabricate missing products
4. `GET /api/v1/domain-products/trust-certification` publishes RFC-0087 platform live trust
   certification when present and returns an explicit unavailable posture when the generated
   artifact is absent
5. reporting snapshot and reporting portfolio requests use `asOfDate`
6. intake upload routes accept camelCase multipart aliases such as `entityType`, `sampleSize`, and
   `allowPartial`
7. some lookup filters intentionally remain snake_case, such as `cif_id`, `booking_center`,
   `product_type`, and `instrument_page_limit`
8. proposal write routes require `Idempotency-Key`

Copy-paste request examples live in [wiki/API-Surface.md](wiki/API-Surface.md).

## Integration Boundaries

- primary downstream consumer:
  `lotus-workbench`
- key upstreams:
  `lotus-core`, `lotus-performance`, `lotus-risk`, `lotus-advise`, `lotus-manage`, `lotus-report`,
  `lotus-ai`
- contract rule:
  gateway may reshape, aggregate, and annotate upstream data for product use, but must not assume
  upstream business authority
- discovery rule:
  gateway may expose the platform-generated domain-product catalog and dependency graph, but the
  producer and consumer declarations remain governed outside gateway

## Operations And Runtime Posture

- use `gateway.dev.lotus` for canonical product and cross-app validation
- use `127.0.0.1:8111` for direct local debugging only
- if startup appears healthy but product routes 404 on Windows, verify `--app-dir src`
- if domain-product discovery returns `503`, verify `DOMAIN_PRODUCT_CATALOG_PATH`,
  `DOMAIN_PRODUCT_DEPENDENCY_GRAPH_PATH`, and the sibling `lotus-platform/generated/` artifacts
- treat degraded responses as composition issues first: inspect upstream supportability, readiness,
  and parameter shape before changing the gateway response contract

## Documentation Map

- architecture direction:
  [docs/documentation/experience-api-foundation-blueprint.md](docs/documentation/experience-api-foundation-blueprint.md)
- upstream integration governance:
  [docs/standards/RFC-0082-upstream-contract-family-map.md](docs/standards/RFC-0082-upstream-contract-family-map.md)
- demo material:
  [docs/demo/README.md](docs/demo/README.md)
- RFC inventory:
  [docs/rfcs/README.md](docs/rfcs/README.md)
- wiki home:
  [wiki/Home.md](wiki/Home.md)

## Wiki Source

Repository-authored wiki pages live under [wiki/](wiki). If the GitHub wiki is published later,
keep `wiki/` as the canonical source and treat any separate `*.wiki.git` clone as publication
plumbing only.
