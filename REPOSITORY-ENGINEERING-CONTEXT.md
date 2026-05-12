# Repository Engineering Context

This file provides repository-local engineering context for `lotus-gateway`.

For platform-wide truth, read:

1. `../lotus-platform/context/LOTUS-QUICKSTART-CONTEXT.md`
2. `../lotus-platform/context/LOTUS-ENGINEERING-CONTEXT.md`
3. `../lotus-platform/context/CONTEXT-REFERENCE-MAP.md`

## Repository Role

`lotus-gateway` is the Lotus experience API and composition boundary.

It provides the governed client contract for `lotus-workbench` and related product consumers.

## Business And Domain Responsibility

This repository owns:

1. product-facing API composition,
2. partial-readiness-aware aggregation,
3. gateway-level routing and contract governance,
4. experience-oriented payload shaping across domain services.

It does not replace domain authority in upstream services.

## Current-State Summary

Current repository posture:

1. `lotus-gateway` is the primary backend contract for `lotus-workbench`,
2. the repository is moving from thin pass-through behavior to a cleaner experience-API posture,
3. performance, proposal, foundation, reporting, and capability aggregation routes are active,
   with proposal simulation/lifecycle/workflow/approval/lineage routed to `lotus-advise`
   `/advisory/proposals/*`; `lotus-manage` consumption is through versioned `/api/v1` APIs for
   run lookup, supportability summary, capability posture, RFC-0038 mandate command-center
   summary/monitoring/exception/mandate drill-down route families, RFC-0040 proof-pack
   generate/read/Markdown/report-input/AI-evidence/AI PM memo route families,
   RFC-0040/RFC-0041/RFC-0042 portfolio-memory route family, and RFC-0042 outcome-review
   preview/create/search/detail/source-refresh/supportability/report-input/AI-evidence and
   AI-narrative handoff route families,
4. report job initiation/search/status/event-history/cancellation routes are active for
   gateway-first portfolio review report job workflows under `/api/v1/reports/portfolio-reviews`,
   `/api/v1/report-jobs`, and `/api/v1/report-jobs/*`,
5. RFC-0104 report batch materialization/status/control/retry/recovery/bounded operator-run routes
   are active under `/api/v1/report-batches` and `/api/v1/report-batches/*`; config-backed
   scheduler list/run-due routes are active under `/api/v1/report-batch-schedules`; lifecycle,
   scheduler configuration, and execution truth remain in `lotus-report`,
6. archived generated-document metadata and controlled download routes are active under
   `/api/v1/documents/{document_id}` and `/api/v1/documents/{document_id}/download` as the
   product-facing boundary over `lotus-archive`,
7. domain-product catalog, dependency-graph, and live trust certification discovery routes are
   active under `/api/v1/domain-products`,
8. upstream service consumption is classified under RFC-0082 in `docs/standards/RFC-0082-upstream-contract-family-map.md`,
9. the advisor-brief path now calls the explicit `lotus-ai` workflow-pack execution seam and consumes the returned run identity directly instead of inferring it from task audit request ids; it also preserves bounded RFC-0097 task-flow posture and replacement lineage from `lotus-ai` without making gateway the task-flow authority,
10. RFC-0042 outcome-review AI narrative handoff now reads manage-owned
    `DpmOutcomeAiEvidenceInput` and executes `lotus-ai` `outcome_review_narrative.pack@v1` as
    `lotus-gateway`; manage remains outcome evidence and workflow authority, and Gateway does not
    generate narrative locally,
11. RFC-0038 DPM exception-summary AI handoff now reads manage-owned monitoring-exception evidence
    from the command-center exception queue and executes `lotus-ai`
    `dpm_exception_summary.pack@v1` as `lotus-gateway`; manage remains exception evidence
    authority, `lotus-ai` remains workflow-pack execution authority, and Gateway does not generate
    exception summaries locally, score PMs, approve trades, contact clients, route orders, or
    invent evidence,
12. RFC-0041 operations-handoff summary now reads manage-owned `DpmWaveReportInput` handoff
    evidence and executes `lotus-ai` `dpm_operations_handoff_summary.pack@v1` as
    `lotus-gateway`; manage remains wave and handoff evidence authority, `lotus-ai` remains
    workflow-pack execution authority, and Gateway does not generate handoff summaries locally,
    score PMs, approve trades, contact clients, route orders, claim external execution, or invent
    evidence,
13. RFC-0040 proof-pack AI PM memo handoff now reads manage-owned
    `DpmProofPackAiEvidenceInput` and executes `lotus-ai` `dpm_pm_memo.pack@v1` as
    `lotus-gateway`; manage remains proof-pack evidence authority, `lotus-ai` remains workflow-pack
    execution authority, and Gateway does not generate memos, score PMs, approve trades, contact
    clients, place orders, or invent evidence,
14. canonical local startup now depends on environment-scoped service identity and `--app-dir src` to avoid misleading Windows import-path failures.
15. RFC-0108 analytics UI observability is active for selected Workbench performance summary,
    risk summary, advisor-brief read, and advisor-brief review-action paths, and has expanded
    fan-out coverage for central `lotus-advise`, `lotus-manage`,
    `lotus-report`, `lotus-archive`, `lotus-ai`, direct `lotus-core` query/control-plane, and
    `lotus-core` ingestion client seams. Gateway owns product-safe
    structured fan-out logs, bounded fan-out metrics, degraded-source counters, selected analytics
    read audit logs, and a protected operator diagnostics lookup under
    `/api/v1/analytics-ui/diagnostics/{support_reference}`. Successful upstream reads emit bounded
    `analytics_read_allowed` audit records, upstream `401`/`403` responses emit bounded
    `analytics_read_denied` audit records, and protected diagnostics lookups emit bounded
    `protected_diagnostics_lookup` audit records. Advisor-brief read audit records use
    `operation=advisor_brief.summary` and `panel=advisor-brief` without portfolio, client, prompt,
    response-body, trace, or raw entitlement fields. Gateway analytics metrics are limited to
    `operation`, `service`, `status_class`, and degraded `reason` labels; audit fields must stay
    limited to route, panel, operation, state, reason, status class, region, and environment;
    portfolio, client, holding, transaction, session, upload, trace, correlation, document,
    request/response body, screen content, raw prompt, model output, and raw entitlement-failure
    fields remain forbidden. Gateway preserves upstream `metadata.calculation_supportability`
    from `lotus-performance` and `lotus-risk` as product-safe source calculation posture for
    evidence views, risk module supportability, fan-out state, and bounded degraded metrics without
    recomputing domain calculation truth.

## Architecture And Module Map

Primary areas:

1. `src/app/`
   FastAPI application, routing, and service logic.
2. `tests/contract/`
   Contract tests for workbench-facing behavior.
3. `tests/integration/`
   Integration behavior across composed flows.
4. `tests/e2e/`
   Live or stack-backed behavior checks where applicable.
5. `docs/`
   Experience-API architecture and standards documentation.
6. `scripts/`
   quality gates, migration checks, and canonical startup helpers.
7. `wiki/`
   canonical authored source for GitHub wiki publication and operator-facing gateway summaries.

## Runtime And Integration Boundaries

Runtime model:

1. FastAPI experience API,
2. consumed primarily by `lotus-workbench`,
3. depends on `lotus-core`, `lotus-performance`, `lotus-risk`, `lotus-advise`, `lotus-manage`,
   `lotus-report`, `lotus-archive`, and `lotus-ai`.

Boundary rules:

1. gateway payloads should be product-oriented and governed,
2. domain ownership must remain upstream,
3. route contracts should prefer replacement and cleanup over versioned clutter while pre-live,
4. gateway must not become the authority for portfolio source data, performance analytics, risk analytics, advisory workflow, management workflow, reporting, or AI outputs,
5. REST/OpenAPI remains the canonical integration contract; gRPC is not justified for current gateway upstream calls,
6. canonical service identity is part of the operational contract,
7. domain-product discovery must preserve platform artifact provenance, approved consumers, trust metadata, dependency posture, and certified trust posture without duplicating platform validation logic inside gateway.

## Repo-Native Commands

Use these commands as the primary local contract:

1. install
   `make install`
2. lint and formatting guard
   `make lint`
3. typecheck
   `make typecheck`
4. contract and unit gate
   `make check`
5. PR-grade local gate
   `make ci`
6. Docker parity
   `make ci-local-docker`
7. canonical local runtime
   `make run-canonical`

## Validation And CI Expectations

`lotus-gateway` uses explicit CI lanes:

1. `Remote Feature Lane`
2. `Pull Request Merge Gate`
3. `Main Releasability Gate`
4. platform-facing validation when cross-app experience contracts are affected

Important validation expectations:

1. OpenAPI and workbench contract quality are part of the gate,
2. migration smoke remains required,
3. security audit and monetary-float governance remain active,
4. Docker parity matters because the gateway is a live integration boundary,
5. README and wiki updates should preserve truthful endpoint-specific parameter conventions, and
   mixed query, body, or multipart shapes should be backed by executable examples in the wiki.

## Standards And RFCs That Govern This Repository

Most relevant current governance:

1. `../lotus-platform/rfcs/RFC-0007-bff-integration-contract-for-ui-platform.md`
2. `../lotus-platform/rfcs/RFC-0041-platform-integration-architecture-bible-governance.md`
3. `../lotus-platform/rfcs/RFC-0067-centralized-api-vocabulary-inventory-and-openapi-documentation-governance.md`
4. `../lotus-platform/rfcs/RFC-0071-centralized-environment-scoped-service-addressing-and-ingress-governance.md`
5. `../lotus-platform/rfcs/RFC-0072-platform-wide-multi-lane-ci-validation-and-release-governance.md`
6. `../lotus-platform/rfcs/RFC-0073-lotus-ecosystem-engineering-context-and-agent-guidance-system.md`
7. `../lotus-platform/rfcs/RFC-0082-lotus-core-domain-authority-and-analytics-serving-boundary-hardening.md`
8. `docs/standards/RFC-0082-upstream-contract-family-map.md`

## Known Constraints And Implementation Notes

1. Windows startup can serve a misleading health-only process if `--app-dir src` is omitted,
2. stale thin-pass-through routes should be retired as better experience contracts replace them,
3. gateway fixes should not smuggle domain logic out of authoritative upstream services,
4. reporting query, cashflow projection, projected summary, and benchmark catalog upstream calls remain RFC-0082 watchlist surfaces,
5. integration drift is most dangerous here because it directly affects the product UI,
6. repo-local `wiki/` content should summarize route families and operator flows without duplicating
   the full `docs/` tree.
7. archive retrieval uses `ARCHIVE_SERVICE_BASE_URL` and forwards archive-specific caller context
   as `lotus-gateway`; direct Workbench-to-archive access is not part of the supported product
   boundary,
8. domain-product discovery defaults to platform-generated catalog and dependency-graph artifacts
   under the sibling `lotus-platform/generated/` directory, and live trust certification defaults to
   `lotus-platform/output/trust-certification/domain-product-live-trust-certification.json`;
   deployment-specific paths should use `DOMAIN_PRODUCT_CATALOG_PATH`,
   `DOMAIN_PRODUCT_DEPENDENCY_GRAPH_PATH`, and `DOMAIN_PRODUCT_LIVE_TRUST_CERTIFICATION_PATH`.
9. report batch gateway routes are an RFC-0104 API/operator boundary only; Workbench batch UI,
   RFC-0105 replay/dashboard operations, and RFC-0106 entitlement certification remain separate
   implementation scopes until explicitly delivered and proven.
10. RFC-0042 outcome-review Gateway routes are active under
    `/api/v1/dpm/command-center/outcome-reviews*`,
    `/api/v1/dpm/command-center/runs/{rebalance_run_id}/outcome-review`, and
    `/api/v1/dpm/command-center/waves/{wave_id}/outcome-reviews`. Gateway composes a BFF envelope
    and supportability summary over manage truth, but it must not recompute outcome dimensions,
    generate reports, generate AI narrative, infer PM quality, or let Workbench call manage
    directly.
11. RFC-0038 mandate command-center Gateway routes are active under
    `/api/v1/dpm/command-center`, `/api/v1/dpm/command-center/monitoring/*`,
    `/api/v1/dpm/command-center/exceptions*`, and
    `/api/v1/dpm/command-center/mandates*`. Gateway composes a BFF envelope and supportability
    summary over manage truth, but it must not discover PM books, calculate health scores,
    reconstruct health dimensions, infer source readiness, merge exceptions across monitoring
    runs, or close exceptions locally.
12. RFC-0039 construction-alternative Gateway routes are active under
    `/api/v1/dpm/command-center/construction/alternative-sets*`. Gateway forwards generation,
    retrieval, and selection requests to `lotus-manage`, preserves manage-owned alternatives,
    method status, diagnostics, comparison metrics, selected-alternative state, and supportability,
    and must not optimize portfolios, recompute construction metrics, infer source readiness, or
    choose alternatives locally.
13. RFC-0040 proof-pack Gateway routes are active under
    `/api/v1/dpm/command-center/proof-packs*`. Gateway forwards generation, lookup, Markdown,
    report-input, AI-evidence-input, and AI PM memo requests, preserves manage-owned
    `proof_pack_id`, section states, reason codes, content hashes, source hashes, source refs,
    report refs, and AI refs, and executes `lotus-ai` `dpm_pm_memo.pack@v1` only after reading
    manage-owned AI evidence input. Gateway must not build proof-pack sections, recalculate hashes,
    infer source readiness, render reports, generate AI narrative or PM memos locally, score PMs,
    approve trades, contact clients, place orders, or invent missing evidence.
14. RFC-0040/RFC-0041/RFC-0042 portfolio-memory Gateway route is active under
    `/api/v1/dpm/command-center/portfolios/{portfolio_id}/memory`. Gateway forwards portfolio id
    and limit to `lotus-manage` `/api/v1/rebalance/portfolio-memory/{portfolio_id}`, preserves
    manage-owned event order, event types, source systems, source refs, artifact refs, reason
    codes, supportability state, content hash, and bounded metadata, and must not reconstruct
    timeline nodes, infer mandate exceptions, calculate risk, performance, tax, cash, FX,
    execution, or source-owner methodology locally.
15. RFC-0041 rebalance-wave Gateway routes are active under
    `/api/v1/dpm/command-center/waves*`. Gateway forwards preview, durable create, search, detail,
    item list, source-check, simulation, item selection, approval, staging, internal handoff,
    cancellation, proof-pack posture, supportability, and report-input requests to `lotus-manage`;
    preserves manage-owned `wave_id`, lifecycle state, item states, reason codes, aggregate
    metrics, selected alternative refs, proof-pack refs, handoff refs, supportability issues,
    report-input evidence, and `external_execution_claimed=false`; and must not calculate affected
    portfolios, classify source readiness, generate alternatives, select alternatives, approve
    items, stage items, create handoff evidence, rebuild proof packs, generate report evidence, or
    claim external execution locally. Gateway can request `lotus-ai`
    `dpm_wave_pm_memo.pack@v1` from manage-owned wave report input as a review-required PM/control
    support artifact, but it must not generate AI narrative locally, score PMs, approve trades,
    contact clients, place orders, or invent missing evidence.
16. The Workbench overview and portfolio-360 `rebalance_snapshot` now carry bounded
    portfolio-level DPM operations posture for RFC36-WTBD-003: latest rebalance status, last run,
    manage action-register supportability from `/api/v1/rebalance/supportability/summary`, and up
    to five recent manage runs from `/api/v1/rebalance/runs` with bounded status, timestamp,
    workflow posture, and error code. Gateway remains the product-facing composition boundary and
    does not calculate supportability, workflow state, or error semantics locally.

## Context Maintenance Rule

Update this document when:

1. major route families or product-facing responsibilities change,
2. canonical startup commands or CI expectations change,
3. upstream dependency boundaries change,
4. gateway composition patterns or partial-readiness behavior change materially,
5. RFC-0082 contract-family classification changes,
6. current endpoint-specific parameter conventions or canonical startup guidance changes,
7. current-state architectural direction changes,
8. domain-product discovery endpoints, platform artifact paths, or catalog/graph/trust
   consumption posture changes.

## Cross-Links

1. `../lotus-platform/context/LOTUS-QUICKSTART-CONTEXT.md`
2. `../lotus-platform/context/LOTUS-ENGINEERING-CONTEXT.md`
3. `../lotus-platform/context/CONTEXT-REFERENCE-MAP.md`
4. `../lotus-platform/context/Repository-Engineering-Context-Contract.md`
5. [Lotus Developer Onboarding](../lotus-platform/docs/onboarding/LOTUS-DEVELOPER-ONBOARDING.md)
6. [Lotus Agent Ramp-Up](../lotus-platform/docs/onboarding/LOTUS-AGENT-RAMP-UP.md)
