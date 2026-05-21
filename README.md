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
  proposal simulation, persisted proposal lifecycle, workflow, approval, and lineage capability
- `lotus-manage`
  discretionary management run lookup, supportability summary, platform capability posture, and
  RFC-0039 construction alternative-set authority, RFC-0040 proof-pack authority, and RFC-0042
  post-trade outcome-review authority through the DPM command-center BFF routes
- `lotus-report`
  reporting snapshot, summary, review payloads, portfolio-review and outcome-review durable report
  job initiation/lifecycle/search, and RFC-0104 batch materialization/status/control/operator-run APIs
- `lotus-archive`
  archived generated-document metadata and controlled binary retrieval
- `lotus-ai`
  evidence-grounded advisor-brief support, outcome-review narrative support, DPM exception-summary
  support, proof-pack PM memo support, wave PM memo support, and operations handoff support through
  explicit workflow-pack execution seams and shared run-ledger surfaces
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
- `source-products`
  `/api/v1/source-products/portfolios/{portfolio_id}/external-order-execution-acknowledgement`
- `proposals`
  `/api/v1/proposals/*`
- `intake` and `lookups`
  `/api/v1/intake/*`, `/api/v1/lookups/*`
- `portfolio`
  `/api/v1/portfolio/*`
- `dpm-command-center`
  `/api/v1/dpm/command-center/construction/alternative-sets/generate`,
  `/api/v1/dpm/command-center/construction/alternative-sets/{alternative_set_id}`,
  `/api/v1/dpm/command-center/construction/alternative-sets/{alternative_set_id}/selections`,
  `/api/v1/dpm/command-center/proof-packs`,
  `/api/v1/dpm/command-center/proof-packs/{proof_pack_id}`,
  `/api/v1/dpm/command-center/proof-packs/{proof_pack_id}/summary.md`,
  `/api/v1/dpm/command-center/proof-packs/{proof_pack_id}/report-input`,
  `/api/v1/dpm/command-center/proof-packs/{proof_pack_id}/ai-evidence-input`,
  `/api/v1/dpm/command-center/proof-packs/{proof_pack_id}/ai-pm-memo`,
  `/api/v1/dpm/command-center/portfolios/{portfolio_id}/memory`,
  `/api/v1/dpm/command-center/pm-operating-quality/policies*`,
  `/api/v1/dpm/command-center/pm-operating-quality/score-runs*`,
  `/api/v1/dpm/command-center/pm-operating-quality/score-runs/{score_run_id}/ai-summary`,
  `/api/v1/dpm/command-center/pm-operating-quality/fairness-analyses/preview`,
  `/api/v1/dpm/command-center/pm-operating-quality/review-actions*`,
  `/api/v1/dpm/command-center/waves/campaign-definitions*`,
  `/api/v1/dpm/command-center/waves/campaign-operating-queue`,
  `/api/v1/dpm/command-center/waves/campaign-approval-inbox`,
  `/api/v1/dpm/command-center/waves/campaign-workflow-board`,
  `/api/v1/dpm/command-center/waves/campaign-assignment-plan`,
  `/api/v1/dpm/command-center/waves/campaign-workflow-automation`,
  `/api/v1/dpm/command-center/waves*`,
  `/api/v1/dpm/command-center/waves/{wave_id}/report-input`,
  `/api/v1/dpm/command-center/waves/{wave_id}/ai-pm-memo`,
  `/api/v1/dpm/command-center/waves/{wave_id}/operations-handoff-summary`,
  `/api/v1/dpm/command-center/outcome-reviews*`,
  `/api/v1/dpm/command-center/exceptions/{exception_id}/ai-summary`,
  `/api/v1/dpm/command-center/runs/{rebalance_run_id}/outcome-review`,
  `/api/v1/dpm/command-center/waves/{wave_id}/outcome-reviews`
- `workbench`
  `/api/v1/workbench/*`
- `reporting`
  `/api/v1/reports/*`
- `report-jobs`
  `/api/v1/report-jobs`, `/api/v1/report-jobs/*`
- `report-batches`
  `/api/v1/report-batches`, `/api/v1/report-batches/*`
- `report-batch-schedules`
  `/api/v1/report-batch-schedules`, `/api/v1/report-batch-schedules:run-due`
- `archived documents`
  `/api/v1/documents/{document_id}`, `/api/v1/documents/{document_id}/download`
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
5. reporting snapshot and reporting portfolio requests use `asOfDate`; portfolio review requests
   also document `benchmarkCode` for RFC-0002 performance and risk context
6. intake upload routes accept camelCase multipart aliases such as `entityType`, `sampleSize`, and
   `allowPartial`
7. some lookup filters intentionally remain snake_case, such as `cif_id`, `booking_center`,
   `product_type`, and `instrument_page_limit`
8. proposal write routes require `Idempotency-Key`
9. report batch materialization uses canonical snake_case body fields and requires
   `Idempotency-Key`; report batch status/control/operator-run routes require caller context
   headers and forward the operation to `lotus-report` as the lifecycle authority
10. archived document metadata and download routes require caller context headers:
   `X-Actor-Id`, `X-Tenant-Id`, and `X-Region`; the gateway calls `lotus-archive` as
   `lotus-gateway` and does not expose archive storage locations
11. Workbench performance summary, risk summary, advisor-brief read, and advisor-brief review
   action routes require caller context headers:
   `X-Actor-Id`, `X-Tenant-Id`, and `X-Region`; optional `X-Caller-Application`,
   `X-Booking-Center-Code`, and `X-Role` preserve entitlement and audit posture for
   front-office analytics reads and bounded advisor workflow actions
12. Workbench advisor-brief reads emit product-safe RFC-0108 analytics read audit events with
   `panel=advisor-brief` and `operation=advisor_brief.summary`; upstream `401` and `403` outcomes
   are recorded as permission-blocked denials without portfolio, client, prompt, response-body,
   trace, or raw entitlement fields
13. DPM command-center outcome-review routes under
   `/api/v1/dpm/command-center/outcome-reviews*` consume `lotus-manage` RFC-0042 APIs and preserve
   manage-owned `outcome_review_id`, state, supportability, lineage, hashes, report-input payloads,
   and AI-evidence payloads without recomputing expected-versus-realized outcome truth
14. DPM command-center construction routes under
   `/api/v1/dpm/command-center/construction/alternative-sets*` consume `lotus-manage` RFC-0039
   construction authority APIs and preserve manage-owned alternative-set ids, method ids, method
   statuses, objective traces, constraint traces, comparison metrics, diagnostics, supportability,
   selected-alternative state, and lineage without optimizing, recomputing, or selecting
   alternatives locally
15. DPM command-center wave routes under `/api/v1/dpm/command-center/waves*` consume
   `lotus-manage` RFC-0041 rebalance-wave APIs and preserve manage-owned `wave_id`, lifecycle
   state, item states, aggregate metrics, selected alternative refs, proof-pack refs, handoff refs,
   supportability, report-input evidence, and reason codes without calculating affected portfolios,
   source readiness, alternatives, proof-pack state, report evidence, or execution posture locally.
   Gateway also exposes campaign-definition list, get, lifecycle-events, launch-package, launch,
   upsert, operating queue, approval inbox, workflow board, assignment plan, workflow automation,
   approval-decision, assignment-action, assignment-task, task-transition, and maker-checker
   evidence routes under
   `/api/v1/dpm/command-center/waves/campaign-definitions*` so Workbench can discover and preserve
   manage-owned campaign/cohort definitions, launch posture, workflow/audit posture, count/page
   metadata, supportability, source refs, reason codes, operating boundaries, and content hashes
   without recomputing cohort facts, portfolio eligibility, readiness, task state, approval state,
   maker-checker posture, workflow orchestration, durable replay state, or membership locally.
   Gateway also exposes a governed `dpm_wave_pm_memo.pack@v1` handoff to `lotus-ai` from
   manage-owned wave report input; it does not generate memo narrative, score PMs, approve trades,
   contact clients, place orders, or invent missing evidence.
   Gateway also exposes a governed `dpm_operations_handoff_summary.pack@v1` handoff to `lotus-ai`
   from the same manage-owned wave report input and internal handoff refs; it does not route
   orders, claim external execution, approve trades, contact clients, or invent missing evidence.
16. DPM portfolio-memory route
   `/api/v1/dpm/command-center/portfolios/{portfolio_id}/memory` consumes `lotus-manage`
   RFC-0040/RFC-0041/RFC-0042 portfolio-memory truth and preserves event order, event type
   counts, source systems, source refs, artifact refs, reason codes, supportability state, and
   content hash without reconstructing timeline nodes or calculating risk, performance, tax, cash,
   FX, or execution truth locally
17. DPM exception-summary AI handoff
   `/api/v1/dpm/command-center/exceptions/{exception_id}/ai-summary` reads manage-owned
   monitoring-exception evidence from the command-center exception queue, builds a bounded
   no-raw-payload evidence envelope, and calls `lotus-ai` `dpm_exception_summary.pack@v1` as
   `lotus-gateway`. Gateway preserves manage evidence authority and lotus-ai workflow-pack posture;
   it does not generate exception narrative locally, score PMs, approve trades, contact clients,
   route orders, or invent missing evidence.
18. DPM PM operating quality routes under
   `/api/v1/dpm/command-center/pm-operating-quality/*` consume `lotus-manage`
   PM operating quality policy, score-run lifecycle, fairness-analysis lifecycle, and
   review-action lifecycle APIs. Gateway also reads Manage-owned score-run evidence before invoking
   `lotus-ai`
   `pm_quality_summary.pack@v1` for review-gated support-only summaries. Gateway preserves Manage
   policy configuration, score-run state, fairness-analysis state, review-action state, bounded
   rationale, target content hashes, segment posture, governance evidence, source refs, reason
   codes, content hashes, and forbidden-use posture without calculating scores, discovering
   segments, calculating fairness spread, inferring protected classes, ranking PMs, administering
   bank policy locally, reinterpreting review rationale, or creating HR, compensation,
   conduct-enforcement, approval, client-contact, trade, order-routing, OMS, or execution
   decisions.

Copy-paste request examples live in [wiki/API-Surface.md](wiki/API-Surface.md).

## Integration Boundaries

- primary downstream consumer:
  `lotus-workbench`
- key upstreams:
  `lotus-core`, `lotus-performance`, `lotus-risk`, `lotus-advise`, `lotus-manage`, `lotus-report`,
  `lotus-archive`, `lotus-ai`
- downstream ownership rule:
  proposal routes call `lotus-advise` `/advisory/proposals/*`; `lotus-manage` calls are limited to
  certified `/api/v1` discretionary management APIs, including run lookup, supportability summary,
  platform capabilities, RFC-0039 construction alternative-set generate/get/select APIs,
  RFC-0040/RFC-0041/RFC-0042 portfolio-memory read APIs,
  RFC-0041 rebalance-wave preview/create/search/detail/items/source-check/simulate/select/approve/
  stage/handoff/cancel/proof-pack/supportability/report-input APIs, and RFC-0042 outcome-review
  preview/create/search/detail/source-refresh, supportability, report-input, AI-evidence, run
  lookup, wave lookup, PM operating quality policy/score-run lifecycle APIs, and command-center
  exception queue reads for bounded exception-summary AI handoff
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
