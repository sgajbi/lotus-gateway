# lotus-gateway

Experience API and composition boundary for Lotus product clients, primarily
`lotus-workbench`.

`lotus-gateway` is the place where product-facing API contracts are composed, stabilized, and made
safe for front-office use. It is not a portfolio book, performance engine, risk engine, advisory
workflow system, reporting engine, archive, or AI authority.

Repository-local engineering context:
[REPOSITORY-ENGINEERING-CONTEXT.md](REPOSITORY-ENGINEERING-CONTEXT.md)

Architecture guide:
[docs/architecture.md](docs/architecture.md)

Upstream contract-family map:
[docs/standards/RFC-0082-upstream-contract-family-map.md](docs/standards/RFC-0082-upstream-contract-family-map.md)

Quality and enterprise-readiness baseline:
[quality/baseline_report.md](quality/baseline_report.md),
[quality/quality_scorecard.md](quality/quality_scorecard.md),
[docs/architecture.md](docs/architecture.md),
[docs/api-governance.md](docs/api-governance.md),
[docs/observability.md](docs/observability.md),
[docs/security.md](docs/security.md), and
[docs/operations-runbook.md](docs/operations-runbook.md)

The duplicate-code quality gate runs the pinned jscpd detector twice with the same production
source scope and fails when normalized candidate identities or aggregate metrics drift between
the invocations. `make duplicate-code` provides the same local check when the pinned Node runtime
is available; Ubuntu/Node 20 in the protected Quality Baseline remains authoritative for reviewed
baseline updates. This repeated-run check detects same-environment nondeterminism and does not
claim unverified cross-operating-system equivalence. `make duplicate-code-protected` provides the
repository-native fallback for hosts whose local runtime selects different candidates: it runs the
same scan and ratchet in the pinned Linux/Node 20 image, uses a checkout-specific Compose project,
and cleans up that project without touching the canonical Gateway runtime. It mounts the checkout
read-only and places npm dependencies and scan output in project-scoped volumes removed by teardown,
so native-Linux runs cannot leave root-owned ignored artifacts in the developer checkout.

## Purpose And Scope

`lotus-gateway` owns product-facing API composition for Lotus.

It is responsible for:

- experience-oriented payload shaping for `lotus-workbench`
- partial-readiness-aware aggregation across upstream services
- gateway-level contract governance
- product-safe routing, evidence mediation, and degraded-state handling

It does not own portfolio domain truth, analytics methodology, reporting methodology, advisory
workflow truth, management workflow truth, or AI output truth. Those remain upstream.

## Current Implementation-Backed Story

For demos, onboarding, and buyer-facing technical review, describe the current Gateway posture this
way:

1. Gateway is the governed API boundary consumed by Workbench.
2. Gateway preserves upstream authority and supportability rather than recomputing domain truth.
3. Gateway has implementation-backed route families for Workbench, platform
   capabilities, domain-product discovery, portfolio, performance/risk workbench reads, proposals,
   advisory policy, advisor cockpit, bank-demo proof, DPM command center, reporting, report
   batches, archive metadata/download, idea review/candidate reads, and analytics diagnostics.
4. Gateway exposes bounded degraded, partial, unavailable, and permission-blocked states where the
   UI and operators need them.
5. Gateway does not by itself certify full product demo readiness. Populated Workbench proof,
   screenshots, and end-to-end demo claims still require the governed Workbench canonical runtime
   and platform QA evidence.

Use [docs/demo/README.md](docs/demo/README.md) and [wiki/Supported-Features.md](wiki/Supported-Features.md)
as the claim-controlled demo entrypoints.

## Audience Guide

- Business, demo, and client-facing reviewers:
  start with [wiki/Supported-Features.md](wiki/Supported-Features.md),
  [wiki/Overview.md](wiki/Overview.md), and [docs/demo/README.md](docs/demo/README.md).
- Engineers changing routes or contracts:
  start with this README, [REPOSITORY-ENGINEERING-CONTEXT.md](REPOSITORY-ENGINEERING-CONTEXT.md),
  [wiki/API-Surface.md](wiki/API-Surface.md), and
  [docs/standards/RFC-0082-upstream-contract-family-map.md](docs/standards/RFC-0082-upstream-contract-family-map.md).
- Operators and support teams:
  start with [wiki/Operations-Runbook.md](wiki/Operations-Runbook.md),
  [wiki/Troubleshooting.md](wiki/Troubleshooting.md), and [docs/operations-runbook.md](docs/operations-runbook.md).
- Security, governance, and procurement reviewers:
  start with [wiki/Security-and-Governance.md](wiki/Security-and-Governance.md),
  [quality/quality_scorecard.md](quality/quality_scorecard.md), and
  [docs/security.md](docs/security.md).

## Ownership And Boundaries

`lotus-gateway` is the primary backend contract for `lotus-workbench`.

It depends on:

- `lotus-core`
  portfolio, authenticated portfolio-manager book membership, booking, lookup, ingestion,
  simulation, and supportability inputs
- `lotus-performance`
  performance workspace analytics and evidence lineage
- `lotus-risk`
  stateful risk workspace analytics
- `lotus-advise`
  proposal simulation, persisted proposal lifecycle, workflow, approval, lineage, reviewed
  narrative posture, report-request, delivery-posture, advisory policy, and advisor cockpit
  capability, plus RFC-0028 bank-demo proof scenario, supported-claim, material-review, and
  backend proof-pack authority
- `lotus-manage`
  discretionary management run lookup, supportability summary, platform capability posture, and
  RFC-0039 construction alternative-set authority, RFC-0040 proof-pack authority, and RFC-0042
  post-trade outcome-review authority through the DPM command-center BFF routes
- `lotus-report`
  reporting snapshot, summary, review payloads, source-owned report ordering catalogue,
  portfolio-review and outcome-review durable report job initiation/lifecycle/search, and RFC-0104
  batch materialization/status/control/operator-run APIs
- `lotus-archive`
  archived generated-document metadata and controlled binary retrieval
- `lotus-idea`
  opportunity intelligence review queues, source-safe candidate detail, and source-owned candidate
  review, feedback, and conversion-intent recording
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
2. Platform capabilities, proposals, advisory policy, advisor cockpit, bank-demo proof,
   reporting, intake/lookups, portfolio, and workbench route families are active.
3. Domain-product catalog, product detail, dependency-graph, and trust-certification discovery
   routes are active as read-only facades over platform-generated artifacts.
4. Idea queue/detail reads and bounded candidate review, feedback, and conversion-intent routes are
   active as source-preserving BFF facades over `lotus-idea`; Gateway does not rank, generate,
   enrich, authorize, or promote ideas locally.
5. The repository is still moving from thin pass-through behavior toward cleaner experience-API
   contracts.
6. Canonical local startup relies on `--app-dir src`; omitting it on Windows can start the wrong
   `app` package and yield a misleading health-only process.

## Architecture At A Glance

Main runtime surfaces come from [src/app/main.py](src/app/main.py):

- `platform`
  `/api/v1/platform/*`
- `domain-products`
  `/api/v1/domain-products/*`
- `source-products`
  `/api/v1/source-products/portfolios/{portfolio_id}/external-order-execution-acknowledgement`
- `proposals`
  `/api/v1/proposals/*`, including the typed selected-record
  `/api/v1/proposals/{proposal_id}/risk-impact` experience contract
- `advisory-policy`
  `/api/v1/advisory-policy-packs/*`,
  `/api/v1/advisory-policy-evaluations/*`,
  `/api/v1/proposals/{proposal_id}/versions/{proposal_version_id}/policy-evaluations`
- `advisor-cockpit`
  `/api/v1/advisor-cockpit/actions`,
  `/api/v1/advisor-cockpit/preparation-packets`,
  `/api/v1/advisor-cockpit/actions/{action_item_id}`,
  `/api/v1/advisor-cockpit/snapshot`,
  `/api/v1/advisor-cockpit/supportability`,
  `/api/v1/advisor-cockpit/actions/{action_item_id}/acknowledgements`,
  `/api/v1/advisor-cockpit/house-view-cohorts/evaluate`
- `bank-demo-proof`
  `/api/v1/advisory/bank-demo-proof/scenario-contract`,
  `/api/v1/advisory/bank-demo-proof/supported-claim-register`,
  `/api/v1/advisory/bank-demo-proof/proof-packs`
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
  `/api/v1/dpm/command-center/pm-operating-quality/summary-invocations*`,
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
- `report-ordering`
  `/api/v1/report-ordering/options`
- `report-jobs`
  `/api/v1/report-jobs`, `/api/v1/report-jobs/*`
- `report-batches`
  `/api/v1/report-batches`, `/api/v1/report-batches/*`
- `report-batch-schedules`
  `/api/v1/report-batch-schedules`, `/api/v1/report-batch-schedules:run-due`
- `archived documents`
  `/api/v1/documents/{document_id}`, `/api/v1/documents/{document_id}/download`
- `ideas`
  `/api/v1/ideas/review-queues/advisor`,
  `/api/v1/ideas/candidates/{candidate_id}`
- platform surfaces
  `/health`, `/health/live`, `/health/ready`, `/metrics`, `/docs`

Key code areas:

- `src/app/routers/`
  public HTTP route families; see [src/app/routers/README.md](src/app/routers/README.md)
- `src/app/services/`
  gateway composition, partial-readiness handling, and upstream orchestration; see
  [src/app/services/README.md](src/app/services/README.md)
- `src/app/contracts/`
  workbench-facing gateway contracts; see [src/app/contracts/README.md](src/app/contracts/README.md)
- `src/app/clients/`
  upstream client integrations; see [src/app/clients/README.md](src/app/clients/README.md)
- `docs/documentation/`
  experience-API architecture and implementation guidance; see [docs/README.md](docs/README.md)
- `docs/standards/`
  ownership, migration, durability, and RFC-0082 integration guidance

## Repository Layout

- `src/app/main.py`
  FastAPI entrypoint and router registration
- `src/app/`
  application package boundary; see [src/app/README.md](src/app/README.md)
- `src/app/routers/`
  gateway route families by product surface
- `src/app/services/`
  composition and orchestration logic
- `src/app/contracts/`
  workbench-facing response and request contracts
- `tests/contract/`
  contract proof for workbench-facing surfaces; see [tests/README.md](tests/README.md)
- `tests/integration/`
  composed behavior checks
- `tests/e2e/`
  workflow and live integration checks
- `scripts/`
  quality gates, migration checks, and canonical startup helpers; see [scripts/README.md](scripts/README.md)
- `quality/`
  quality baseline and enterprise-readiness scorecards; see [quality/README.md](quality/README.md)
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
  lint, format, monetary-float, refactor, workflow, agent-quality, folder, TestClient dependency,
  and proposal decision-vocabulary governance
- `make typecheck`
  mypy on `src/`
- `make check`
  contract and unit gate
- `make ci`
  PR-grade local proof with migration smoke, integration, coverage, and security audit
- `make ci-local-docker`
  dockerized parity check
- `make proposal-decision-vocabulary-gate`
  reconcile the packaged Advise proposal decision policy with a required source contract; set the
  governed producer URL locally, while protected CI supplies it and records the blob revision
- `make proposal-decision-vocabulary-snapshot-check`
  explicitly validate only the packaged snapshot for offline package-integrity diagnosis; this is
  not a producer-drift proof and is never used by protected CI
- `make run-canonical`
  canonical local gateway runtime on port `8111`
- `make clean`
  remove disposable local generated artifacts and caches, including `output/`, `.codex-logs/`,
  coverage reports, Python bytecode caches, package metadata, and `gateway-*.log`; publish or
  preserve any required evidence before cleanup

## Validation And CI Lanes

`lotus-gateway` follows the Lotus multi-lane model:

1. `Remote Feature Lane`
2. `Pull Request Merge Gate`
3. `Main Releasability Gate`
4. platform-facing validation when cross-app experience contracts change
5. scheduled `Upstream Contract Drift` reconciliation for the Advise proposal decision vocabulary

Repo-native gate mapping:

- `make check`
  lint, typecheck, OpenAPI contract proof, unit tests
- `make ci`
  migration smoke, integration tests, coverage, and security audit
- `make ci-local`
  local feature-lane style validation
- `make ci-local-docker`
  Docker parity for the live integration boundary

PR auto-merge is rebase-only for linear history. The `Queue Auto Merge` helper uses
`LOTUS_AUTOMERGE_TOKEN` with `gh pr merge --auto --rebase --delete-branch`; when that token is not
available, the helper emits a warning and exits successfully so an authorized human or release actor
can perform the rebase merge without leaving a false red CI check.
Merged PRs into `main` also trigger `Merged PR Main Releasability Dispatch`, a bounded
`pull_request_target` closed-event workflow that dispatches `main-releasability.yml` through an
immutable `main-releasability-<sha>` tag for the exact merged pull request SHA while stamping
`main` as the release source branch in build metadata, provenance, manifests, and `/version`. This
preserves exact-main release evidence when a PR is merged by an authorized human or release actor
rather than the auto-merge helper without mislabelling release artifacts as tag-origin builds.
The lane's concurrency identity always uses GitHub's checked-out SHA. The caller-supplied expected
SHA remains an assertion only, so an invalid manual input cannot cancel validation evidence for a
different revision and a newer merge cannot cancel evidence for an earlier revision.
The main releasability workflow is intentionally `workflow_dispatch`-only; the merged-PR
dispatcher owns the automatic post-merge path so human or release-actor merges do not start both a
push-triggered run and a dispatched run for the same main SHA. Manual dispatches intentionally have
no `source_branch` default; release metadata inherits the selected workflow ref unless an operator
explicitly provides a source branch override.

The Quality Baseline workflow publishes complexity, maintainability, dead-code, dependency,
security, import-boundary, documentation, coverage, and OpenAPI governance evidence. Its checked-in
ratchet fails new measured regressions while preserving known findings as explicit trend data;
individual clean checks can be promoted after their findings are classified and remediated.

Remote Feature, PR Merge, and Main Releasability run the proposal decision-vocabulary gate against
the current public Advise artifact. A daily and operator-dispatched drift workflow repeats that
check even when no Gateway branch is active, so changed producer pairings become CI evidence before
the next Gateway release.

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
6. report ordering options use camelCase `scopeType` and `scopeId`, require trusted actor, tenant,
   and region context, and accept trusted role plus portfolio, client, or advisor-book entitlement
   headers. The response preserves Report-owned configuration and output availability while Gateway
   publishes only implemented submission paths; ordering eligibility is not distribution approval
   or document-completion evidence
7. advisor-book discovery uses camelCase `asOfDate`, `clientId`, `mandateType`, `sortBy`, and
   `sortOrder`; requires trusted actor, tenant, region, booking centre, exact supported role, and
   `advisor.book.read`; and exposes no browser-authored advisor-id override
8. intake upload routes accept camelCase multipart aliases such as `entityType`, `sampleSize`, and
   `allowPartial`
8. some lookup filters intentionally remain snake_case, such as `cif_id`, `booking_center`,
   `product_type`, and `instrument_page_limit`
9. proposal lifecycle write routes require `Idempotency-Key`; narrative review accepts an optional
   `Idempotency-Key` and preserves the reviewed narrative posture returned by `lotus-advise`
10. explicit report batch materialization accepts portfolio identifiers and report configuration,
   requires `Idempotency-Key` plus trusted own-book caller context, resolves portfolio membership
   and candidate provenance through Core before mutation, and rejects caller-supplied candidate
   authority; status/control/operator-run routes preserve `lotus-report` as lifecycle authority
11. archived document metadata and download routes require caller context headers:
   `X-Actor-Id`, `X-Tenant-Id`, and `X-Region`; the gateway calls `lotus-archive` as
   `lotus-gateway` and does not expose archive storage locations
12. Idea queue/detail and candidate action routes forward `X-Caller-Subject`, `X-Caller-Roles`,
   `X-Caller-Capabilities`, `X-Caller-Tenant-Ids`, `X-Caller-Book-Ids`,
   `X-Caller-Portfolio-Ids`, `X-Caller-Client-Ids`, and optional
   `X-Lotus-Trusted-Caller-Context` to `lotus-idea` for entitlement-scope enforcement. Candidate
   mutations require `Idempotency-Key` and forward correlation/trace context and optional
   `X-Causation-Id`. Gateway preserves
   `supportedFeaturePromoted=false` and does not rank, score, enrich, or certify idea candidates
   locally, grant downstream authority, or create downstream execution records
13. Workbench performance summary, risk summary, advisor-brief read, and advisor-brief review
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
   AI-evidence payloads, applied source-lineage filters, source-owner counts, source-type counts,
   and support boundaries without recomputing expected-versus-realized outcome truth or querying
   source-owner stores
   Every registered DPM route fails closed unless callers supply trusted `X-Actor-Id`,
   `X-Tenant-Id`, and `X-Role` audit identity; `X-Region` is preserved when present and remains
   required where the route contract declares it. Reads forward only that validated caller context
   and correlation. Gateway does not trust browser workload authority: it derives
   `X-Service-Identity: lotus-gateway` and the exact `X-Capabilities: manage.write` scope only for
   outbound Manage mutations.
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
   retire, supersede, upsert, operating queue, approval inbox, workflow board, assignment plan,
   workflow automation, approval-decision, assignment-action, assignment-task, task-transition,
   and maker-checker evidence routes under
   `/api/v1/dpm/command-center/waves/campaign-definitions*` so Workbench can discover and preserve
   manage-owned campaign/cohort definitions, launch posture, lifecycle lineage, workflow/audit
   posture, count/page metadata, supportability, source refs, reason codes, operating boundaries,
   replacement version/hash evidence, and content hashes
   without recomputing cohort facts, portfolio eligibility, readiness, task state, approval state,
   maker-checker posture, workflow orchestration, durable replay state, lifecycle state, or
   membership locally.
   Campaign-definition list/get and campaign-discovery reads require `X-Tenant-Id` and fail
   closed with request validation errors when trusted tenant scope is absent.
   Gateway also exposes a governed `dpm_wave_pm_memo.pack@v1` handoff to `lotus-ai` from
   manage-owned wave report input; it does not generate memo narrative, score PMs, approve trades,
   contact clients, place orders, or invent missing evidence.
   Gateway also exposes a governed `dpm_operations_handoff_summary.pack@v1` handoff to `lotus-ai`
   from the same manage-owned wave report input and internal handoff refs; it does not route
   orders, claim external execution, approve trades, contact clients, or invent missing evidence.
16. DPM portfolio-memory routes
   `/api/v1/dpm/command-center/portfolios/{portfolio_id}/memory` and
   `/api/v1/dpm/command-center/portfolio-memory/search` consume `lotus-manage`
   RFC-0040/RFC-0041/RFC-0042 portfolio-memory truth and preserve event order, event type
   counts, source systems, source-system/source-type facets, source refs, artifact refs, applied
   filters, reason codes, supportability state, support boundaries, and content hash without
   reconstructing timeline nodes, querying source-owner stores, discovering the global portfolio
   universe, or calculating risk, performance, tax, cash, FX, OMS, fill, settlement, client
   communication, or execution truth locally
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
   review-action and summary-invocation lifecycle APIs. Gateway also reads Manage-owned score-run
   evidence before invoking `lotus-ai`
   `pm_quality_summary.pack@v1` for review-gated support-only summaries. Gateway preserves Manage
   policy configuration, score-run state, fairness-analysis state, review-action state,
   summary-invocation workflow lineage, bounded rationale, target content hashes, segment posture,
   governance evidence, source refs, reason codes, content hashes, summary-text boundary evidence,
   and forbidden-use posture without calculating scores, discovering segments, calculating fairness
   spread, inferring protected classes, ranking PMs, administering bank policy locally,
   reinterpreting review rationale, storing or exposing generated summary text, reconstructing
   prompts or model responses, or creating HR, compensation, conduct-enforcement, approval,
   client-contact, trade, order-routing, OMS, or execution decisions.

Copy-paste request examples live in [wiki/API-Surface.md](wiki/API-Surface.md).

## Integration Boundaries

- primary downstream consumer:
  `lotus-workbench`
- key upstreams:
  `lotus-core`, `lotus-performance`, `lotus-risk`, `lotus-advise`, `lotus-manage`, `lotus-report`,
  `lotus-archive`, `lotus-idea`, `lotus-ai`
- downstream ownership rule:
  proposal routes call `lotus-advise` `/advisory/proposals/*`, including typed risk-and-impact,
  reviewed narrative posture, report-request, and delivery-posture routes; Gateway validates and
  reshapes source evidence but does not calculate risk, infer approval, generate narrative, infer
  client-ready publication, render reports, archive documents, or recompute advisory delivery
  truth. `lotus-manage` calls are limited to
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
- idea publication rule:
  gateway may expose product-facing reads over `lotus-idea`, but `lotus-idea` remains the
  opportunity intelligence, queue ranking, candidate lifecycle, evidence, conversion, and
  supported-feature authority

## Operations And Runtime Posture

- use `gateway.dev.lotus` for canonical product and cross-app validation
- use `127.0.0.1:8111` for direct local debugging only
- if startup appears healthy but product routes 404 on Windows, verify `--app-dir src`
- if domain-product discovery returns `503`, verify `DOMAIN_PRODUCT_CATALOG_PATH`,
  `DOMAIN_PRODUCT_DEPENDENCY_GRAPH_PATH`, and the sibling `lotus-platform/generated/` artifacts
- treat degraded responses as composition issues first: inspect upstream supportability, readiness,
  and parameter shape before changing the gateway response contract

## Documentation Map

- claim-controlled demo pack:
  [docs/demo/README.md](docs/demo/README.md)
- current implementation-backed feature matrix:
  [wiki/Supported-Features.md](wiki/Supported-Features.md)
- copy-paste API examples:
  [wiki/API-Surface.md](wiki/API-Surface.md)
- architecture guide:
  [docs/architecture.md](docs/architecture.md)
- upstream integration governance:
  [docs/standards/RFC-0082-upstream-contract-family-map.md](docs/standards/RFC-0082-upstream-contract-family-map.md)
- RFC inventory:
  [docs/rfcs/README.md](docs/rfcs/README.md)
- wiki home:
  [wiki/Home.md](wiki/Home.md)

## Wiki Source

Repository-authored wiki pages live under [wiki/](wiki). If the GitHub wiki is published later,
keep `wiki/` as the canonical source and treat any separate `*.wiki.git` clone as publication
plumbing only.
