# API Surface

Current scope: this page summarizes the implemented Gateway route families and copy-paste API
examples for local operator and engineering validation. Evidence posture: route examples are
intended as operator smoke checks, while executable contract truth remains in the repo tests and
OpenAPI generation. Examples use `GATEWAY_BASE_URL` so the same commands work against local, Docker,
or governed ingress endpoints without embedding environment-specific hostnames in the wiki.

## Route families

- `GET /api/v1/foundation/portfolios`
- `GET /api/v1/foundation/portfolios/{portfolio_id}/workspace`
- `GET /api/v1/platform/capabilities`
- `GET /api/v1/domain-products/catalog`
- `GET /api/v1/domain-products/products/{producer_repository}/{product_name}/{product_version}`
- `GET /api/v1/domain-products/dependency-graph`
- `GET /api/v1/domain-products/trust-certification`
- `POST /api/v1/source-products/portfolios/{portfolio_id}/external-order-execution-acknowledgement`
- `POST /api/v1/proposals/*` and `GET /api/v1/proposals/*`
- `GET` and `POST /api/v1/advisory-copilot/*`
- `GET /api/v1/advisor-book/portfolios`
- `GET` and `POST /api/v1/advisory/bank-demo-proof/*`
- `POST /api/v1/intake/*`
- `GET /api/v1/lookups/*`
- `GET /api/v1/portfolio/*`
- `GET /api/v1/dpm/command-center`
- `GET` and `POST /api/v1/dpm/command-center/monitoring/*`
- `GET` and `POST /api/v1/dpm/command-center/exceptions*`
- `GET /api/v1/dpm/command-center/mandates*`
- `GET /api/v1/dpm/command-center/portfolios/{portfolio_id}/memory`
- `GET` and `POST /api/v1/dpm/command-center/outcome-reviews*`
- `GET`, `POST`, and `PUT /api/v1/dpm/command-center/pm-operating-quality/*`
- `POST /api/v1/dpm/command-center/exceptions/{exception_id}/ai-summary`
- `GET /api/v1/dpm/command-center/runs/{rebalance_run_id}/outcome-review`
- `GET` and `POST /api/v1/dpm/command-center/waves*`
- `GET` and `PUT /api/v1/dpm/command-center/waves/campaign-definitions*`
- `GET /api/v1/dpm/command-center/waves/campaign-operating-queue`
- `GET /api/v1/dpm/command-center/waves/campaign-approval-inbox`
- `GET /api/v1/dpm/command-center/waves/campaign-workflow-board`
- `GET /api/v1/dpm/command-center/waves/campaign-assignment-plan`
- `GET /api/v1/dpm/command-center/waves/campaign-workflow-automation`
- `GET /api/v1/dpm/command-center/waves/{wave_id}/outcome-reviews`
- `POST /api/v1/dpm/command-center/outcome-reviews/{outcome_review_id}/ai-narrative`
- `POST /api/v1/dpm/command-center/waves/{wave_id}/operations-handoff-summary`
- `GET` and `POST /api/v1/dpm/command-center/construction/alternative-sets*`
- `GET` and `POST /api/v1/dpm/command-center/proof-packs*`
- `POST /api/v1/dpm/command-center/proof-packs/{proof_pack_id}/ai-pm-memo`
- `GET` and `POST /api/v1/workbench/*`
- `GET /api/v1/report-ordering/options`
- `GET` and `POST /api/v1/reports/*`
- `POST /api/v1/reports/outcome-reviews`
- `GET /api/v1/report-jobs` and `GET`/`POST /api/v1/report-jobs/*`
- `POST /api/v1/report-batches`, `GET /api/v1/report-batches/{batch_id}`, and
  `POST /api/v1/report-batches/{batch_id}:*`
- `GET /api/v1/report-batch-schedules` and `POST /api/v1/report-batch-schedules:run-due`
- `GET /api/v1/documents/{document_id}`
- `GET /api/v1/documents/{document_id}/download`
- `GET /api/v1/ideas/review-queues/advisor`
- `GET /api/v1/ideas/candidates/{candidate_id}`
- `GET /api/v1/analytics-ui/diagnostics/{support_reference}`
- `/health`, `/health/live`, `/health/ready`, `/metrics`, `/docs`

## Current contract notes

- Portfolio workspace `as_of_date` is an optional review-date override. When it is omitted,
  Gateway lets lotus-core resolve the latest governed portfolio date first, then uses that same
  date for cashflow, cash balances, readiness, and performance composition. Gateway host time is
  not a portfolio business-date authority.
- advisor-book discovery requires camelCase `asOfDate` plus trusted actor, tenant, region, booking
  centre, role, and capability headers. The actor identifies the manager's own book; there is no
  advisor-id query override. Optional `clientId`, `mandateType`, `sortBy`, `sortOrder`, `offset`,
  and `limit` inputs only narrow or order the source cohort.
- platform capabilities uses camelCase query parameters `consumerSystem` and `tenantId`
- platform capabilities publishes `normalized.navigation.command_center=true` only when the
  `lotus_manage` source publishes governed Manage support capability such as
  `dpm.support.run_apis` or `lotus_manage.support.run_apis`
- domain-product discovery uses `consumerSystem` for caller identity and serves only
  platform-generated catalog, dependency-graph, and live trust certification artifacts
- domain-product detail requires the full governed identity:
  `producer_repository`, `product_name`, and `product_version`
- domain-product trust certification returns certified platform trust posture when the RFC-0087
  artifact exists and an explicit unavailable posture when it has not been generated
- source-product external order execution acknowledgement is a lotus-core pass-through that
  preserves fail-closed `UNAVAILABLE` supportability, missing data, blocked capabilities, and
  lineage without creating execution, OMS acknowledgement, fills, settlement, or best-execution
  truth
- reporting snapshot and reporting request payloads use `asOfDate`; portfolio review requests also
  support `benchmarkCode` for RFC-0002 performance and risk context
- report ordering options preserve Report-owned family, configuration, section, and output-format
  availability while applying trusted caller role and explicit portfolio, client, or advisor-book
  scope. The response publishes only implemented Gateway submission paths. Client/book scope does
  not expand portfolio membership, and ordering eligibility is not client-distribution approval or
  proof of document/archive completion
- reporting review preserves `client_sections`, `advisor_sections`, readiness, evidence, and
  partial/unavailable section states from `lotus-report`; advisor-only material must stay under
  `advisor_sections`
- portfolio review report job initiation uses canonical snake_case body fields and requires
  `Idempotency-Key`
- outcome-review report job initiation uses manage-owned `DpmOutcomeReportInput` through
  `/api/v1/reports/outcome-reviews`; Gateway forwards the payload to `lotus-report` and does not
  recompute outcome truth, render artifacts, or archive documents
- report job search, status, append-only event history, and cancellation are gateway-first under
  `/api/v1/report-jobs` and `/api/v1/report-jobs/*`
- report batch materialization, status, pause, resume, cancel, retry-failed,
  recover-expired-leases, and bounded run-once operator actions are gateway-first under
  `/api/v1/report-batches`. Explicit creation accepts portfolio identifiers only and resolves the
  authenticated advisor's own-book membership, tenant, region, active state, and source provenance
  through trusted Gateway/Core contracts; caller-supplied candidate authority is rejected.
  `lotus-report` remains the batch lifecycle and execution authority
- report batch materialization, status, and bounded run-once responses preserve
  `supportability.feature_key=report.observability.evidence_surface_supportability` from
  `lotus-report` integration capabilities so Workbench can record report evidence-surface
  freshness and supportability without direct service coupling
- RFC-0098 proof-pack composition consumes `lotus-manage` RFC-0040 proof-pack APIs through
  `/api/v1/dpm/command-center/proof-packs*`. Gateway exposes generate, get, Markdown,
  report-input, AI-evidence-input, and AI PM memo routes for Workbench, preserving manage
  `proof_pack_id`, section states, reason codes, content hashes, source hashes, source refs,
  report refs, and AI refs. The AI PM memo action reads manage-owned
  `DpmProofPackAiEvidenceInput` and calls `lotus-ai` `dpm_pm_memo.pack@v1` as `lotus-gateway`.
  Gateway must not build proof-pack sections, recalculate hashes, infer source readiness, render
  reports, generate AI narrative or PM memos locally, score PMs, approve trades, contact clients,
  place orders, or treat `lotus-report` as proof-pack authority.
  `lotus-report` remains report materialization authority, not proof-pack authority.
- RFC40-WTBD-010 portfolio-memory Gateway composition consumes `lotus-manage`
  `/api/v1/rebalance/portfolio-memory/{portfolio_id}` and
  `/api/v1/rebalance/portfolio-memory/search` through
  `/api/v1/dpm/command-center/portfolios/{portfolio_id}/memory` and
  `/api/v1/dpm/command-center/portfolio-memory/search`. Gateway forwards portfolio, event,
  supportability, source-system, source-type, limit, offset, source-scan-limit, and correlation
  context, then preserves manage-owned event order, event types, event counts, source systems,
  source-system/source-type facets, source refs, artifact refs, applied filters, reason codes,
  supportability state, support boundary, bounded metadata, and content hash for Workbench.
  Gateway must not reconstruct timeline nodes, infer mandate exceptions, query source-owner
  stores, discover the global portfolio universe, calculate risk, performance, tax, cash, FX,
  OMS execution, fills, settlement, client communication, or source-owner methodology, or let
  Workbench bypass Gateway for portfolio memory.
- PM operating quality composition consumes `lotus-manage`
  `/api/v1/rebalance/pm-operating-quality/*` through
  `/api/v1/dpm/command-center/pm-operating-quality/*`. Gateway exposes policy list/get/upsert
  score-run preview/create/list/get routes, fairness-analysis preview/create/list/get,
  review-action preview/create/list/get, summary-invocation preview/create/list/get, and a
  score-run AI summary handoff that executes `lotus-ai` `pm_quality_summary.pack@v1` only after
  reading Manage-owned score-run evidence.
  Gateway preserves manage-owned policy configuration, score-run state, fairness-analysis state,
  review-action state, summary-invocation workflow lineage, bounded rationale, target content
  hashes, segment posture, governance evidence, source refs, reason codes, content hashes,
  supportability, summary-text boundary evidence, and forbidden-use posture.
  Gateway must not calculate scores, discover segments, calculate segment averages or fairness
  spread, infer protected classes, rank PMs, administer bank policy locally, reinterpret review
  rationale, store or expose generated summary text, reconstruct prompts or model responses, or
  create HR, compensation, conduct-enforcement, approval, client-contact, order, OMS, or execution
  decisions.
- RFC-0098 construction-alternative composition consumes `lotus-manage` RFC-0039 construction
  APIs through `/api/v1/dpm/command-center/construction/alternative-sets*`. Gateway exposes
  generate, get, and select routes for Workbench, preserving manage alternative-set ids, method
  identifiers, method statuses, objective traces, constraint traces, comparison metrics,
  diagnostics, supportability, selected-alternative state, and lineage. Gateway must not optimize,
  recompute construction metrics, infer source readiness, select alternatives, execute orders, or
  let Workbench bypass Gateway.
- RFC-0098 mandate command-center composition consumes `lotus-manage` RFC-0038 mandate health,
  monitoring run, exception queue, and mandate read APIs. Gateway now exposes
  `/api/v1/dpm/command-center`, `/api/v1/dpm/command-center/monitoring/*`,
  `/api/v1/dpm/command-center/exceptions*`, and `/api/v1/dpm/command-center/mandates*` for
  Workbench command-center consumers. These routes preserve manage-published health distribution,
  health dimensions, source readiness, supportability, latest monitoring run identity, active
  exceptions, reason codes, recommended actions, mandate source lineage, and version diffs.
  Gateway must not discover PM-book membership, calculate health scores, reconstruct source
  readiness, merge exceptions across monitoring runs, resolve exceptions locally, or let Workbench
  call `lotus-manage` directly.
  The exception-summary AI action
  `/api/v1/dpm/command-center/exceptions/{exception_id}/ai-summary` filters the manage
  exception queue, builds a bounded no-raw-payload evidence envelope for the selected exception,
  and calls `lotus-ai` `dpm_exception_summary.pack@v1` as `lotus-gateway`. Gateway preserves
  manage source refs, content hashes, and supportability boundaries; it must not generate local AI
  narrative, invent evidence, score PMs, approve trades, contact clients, route orders, or turn an
  exception summary into client-facing advice.
- RFC36-WTBD-003 portfolio-level DPM operations posture is exposed on Workbench overview and
  portfolio-360 `rebalance_snapshot`. Gateway reads manage rebalance runs through
  `/api/v1/rebalance/runs`, reads manage supportability summary through
  `/api/v1/rebalance/supportability/summary`, preserves manage action-register supportability, and
  includes a bounded recent-run list with run id, status, timestamp, workflow posture, and error
  code for Workbench operations dashboards. Gateway must not calculate supportability, workflow
  posture, or error semantics locally.
- RFC-0098 wave composition consumes `lotus-manage` RFC-0041 wave APIs for preview, create,
  search, detail, items, source-check, simulation, selection, approval, staging, handoff, cancel,
  proof-pack posture, supportability, report input, and campaign-definition discovery/upsert through
  `/api/v1/dpm/command-center/waves*`. Gateway now exposes the implementation-backed wave BFF
  route family, preserves manage `wave_id`, item states, aggregate metrics, selected alternative
  refs, proof-pack refs, handoff refs, report-input evidence, supportability issues, reason codes,
  campaign definition payloads, and the no-external-execution boundary. Gateway also exposes
  `GET /api/v1/dpm/command-center/waves/campaign-definitions`,
  `GET /api/v1/dpm/command-center/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}`,
  `GET /api/v1/dpm/command-center/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/lifecycle-events`,
  `GET /api/v1/dpm/command-center/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/preview-readiness`,
  `GET /api/v1/dpm/command-center/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/launch-history`,
  `GET /api/v1/dpm/command-center/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/launch-package`,
  `POST /api/v1/dpm/command-center/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/launch`,
  `POST /api/v1/dpm/command-center/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/retire`,
  `POST /api/v1/dpm/command-center/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/supersede`,
  `GET /api/v1/dpm/command-center/waves/campaign-discovery`,
  `GET /api/v1/dpm/command-center/waves/campaign-operating-queue`,
  `GET /api/v1/dpm/command-center/waves/campaign-approval-inbox`,
  `GET /api/v1/dpm/command-center/waves/campaign-workflow-board`,
  `GET /api/v1/dpm/command-center/waves/campaign-assignment-plan`,
  `GET /api/v1/dpm/command-center/waves/campaign-workflow-automation`,
  `GET` and `POST /api/v1/dpm/command-center/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/approval-decisions`,
  `GET` and `POST /api/v1/dpm/command-center/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/assignment-actions`,
  `GET` and `POST /api/v1/dpm/command-center/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/assignment-tasks`,
  `POST /api/v1/dpm/command-center/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/assignment-tasks/{task_ref}/transitions`,
  `GET` and `POST /api/v1/dpm/command-center/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/maker-checker-controls`,
  and `PUT /api/v1/dpm/command-center/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}`
  for manage-owned campaign/cohort definition discovery, lifecycle evidence, retire/supersede
  lifecycle commands, fail-closed
  `BulkReviewCampaignDefinitionPreviewReadiness:v1`, paged append-only
  `BulkReviewCampaignDefinitionLaunchHistory:v1` audit history, ready-only launch posture, and
  bounded campaign workflow/audit evidence.
  Campaign-definition list/get and campaign-discovery reads require `X-Tenant-Id`; requests
  without trusted tenant scope fail closed with `422`.
  For bounded Core-owned campaign candidate discovery, Gateway preserves
  `campaign_candidate_source=CORE_DPM_PORTFOLIO_UNIVERSE`,
  `model_portfolio_ids`, `include_inactive_mandates`, and `campaign_candidate_page_size` for
  lotus-manage, which consumes lotus-core `DpmPortfolioUniverseCandidate:v1`; Gateway rejects
  non-empty caller-supplied `portfolios`, `portfolio_ids`, or `source_candidates` in that mode and
  does not discover or rank a global portfolio universe.
  Gateway preserves preview-readiness supportability state, reason codes, blocked actions, source
  refs, requested as-of date, actor id, and operating boundaries exactly. Gateway also preserves
  launch-history campaign id/version, launch records, count, total count, limit, offset, and
  operating boundaries exactly. Gateway does not discover cohorts, calculate campaign membership,
  evaluate portfolio eligibility, infer campaign lifecycle state, recompute launch readiness or
  preview readiness, infer actor entitlement, or own maker-checker, staging, trade-approval, order
  generation, routing, fills, settlement, or OMS posture. Gateway also preserves workflow/audit
  count/page metadata, approval-decision evidence, assignment-action evidence, assignment-task
  evidence, task-transition evidence, maker-checker evidence, supportability, source refs, reason
  codes, operating boundaries, and content hashes without calculating task state, SLA, escalation,
  approval state, maker-checker state, workflow orchestration, client contact, orders, OMS
  execution, fills, or settlement.
  Gateway also exposes a governed handoff from
  manage-owned `DpmWaveReportInput` to `lotus-ai` `dpm_wave_pm_memo.pack@v1` for review-required
  PM/control support text. Gateway must not calculate affected portfolios, readiness,
  alternatives, proof-pack state, report evidence, AI narrative, PM scoring, trade approval,
  client contact, order placement, or external execution posture.
  The operations-handoff summary action reads manage-owned `DpmWaveReportInput` handoff evidence
  and calls `lotus-ai` `dpm_operations_handoff_summary.pack@v1` as `lotus-gateway`. Gateway
  preserves manage handoff refs, source refs, hashes, item posture, and the
  `external_execution_claimed=false` boundary; it must not generate handoff narrative locally,
  approve trades, contact clients, route orders, claim execution, or invent evidence.
- RFC-0098 outcome-review composition must consume `lotus-manage` RFC-0042 outcome-review APIs
  for preview, durable create, search, detail, source refresh, supportability, report input, AI
  evidence input, run lookup, and wave lookup. Gateway now exposes the first implementation-backed
  outcome-review BFF route family under `/api/v1/dpm/command-center/outcome-reviews*`,
  `/api/v1/dpm/command-center/runs/{rebalance_run_id}/outcome-review`, and
  `/api/v1/dpm/command-center/waves/{wave_id}/outcome-reviews`. These routes preserve manage
  `outcome_review_id`, state, dimension outcomes, expected values, realized values, variance,
  tolerances, source refs, source hashes, freshness, applied source-lineage filters,
  source-owner counts, source-type counts, support boundaries, report-input posture,
  AI-evidence posture, remediation routes, supportability, and Manage-owned
  `client_communication_boundary` posture when present. Gateway also exposes a governed AI
  narrative handoff action that reads
  manage-owned `DpmOutcomeAiEvidenceInput` and calls `lotus-ai`
  `outcome_review_narrative.pack@v1` as `lotus-gateway`; Gateway must not recompute outcome
  truth, synthesize client communication truth, query source-owner stores, discover the global
  portfolio universe, generate reports, generate AI narrative locally, infer PM quality, approve
  trades, contact clients, or let Workbench bypass Gateway.
  In short: Gateway must not recompute outcome truth.
- report batch schedule list and run-due actions are gateway-first under
  `/api/v1/report-batch-schedules`; schedules remain config-backed in `lotus-report`, and gateway
  does not expose schedule CRUD or scheduler registry management
- report batch materialization requires `Idempotency-Key`; all report batch routes require
  `X-Actor-Id`, `X-Tenant-Id`, and `X-Region`, with optional `X-Caller-Application`,
  `X-Booking-Center-Code`, and `X-Role` forwarded as caller context
- archived generated-document metadata and download are gateway-first under `/api/v1/documents/*`;
  `lotus-workbench` must not call `lotus-archive` directly
- archived document routes require `X-Actor-Id`, `X-Tenant-Id`, and `X-Region`; optional
  `X-Booking-Center-Code` and `X-Role` are forwarded as caller context
- archived document metadata and download enforce tenant and region parity against archive
  metadata before returning metadata or streaming binary content. Broader portfolio, client, and
  advisor entitlement remains upstream authorization truth; Gateway must not claim fuller document
  entitlement enforcement until that source is wired and tested.
- idea review queue/detail reads and candidate review-action, feedback, and conversion-intent
  recordings are gateway-first under `/api/v1/ideas/*`;
  Gateway forwards `X-Caller-Subject`, `X-Caller-Roles`, `X-Caller-Capabilities`,
  `X-Caller-Tenant-Ids`, `X-Caller-Book-Ids`, `X-Caller-Portfolio-Ids`,
  `X-Caller-Client-Ids`, optional `X-Lotus-Trusted-Caller-Context`, and correlation/trace context
  to `lotus-idea` for entitlement-scope enforcement. Mutation requests require `Idempotency-Key`
  and may carry `X-Causation-Id`; Gateway preserves source-owned ranking, source signal identifiers,
  source refs, durable-storage posture, accepted/replayed outcomes, and
  `supportedFeaturePromoted=false`. It does not generate, rank, enrich, certify, or promote Idea
  candidates, grant downstream authority, or create downstream delivery/execution records locally
- Workbench performance summary, risk summary, advisor-brief read, and advisor-brief review-action
  routes require `X-Actor-Id`, `X-Tenant-Id`, and `X-Region`; optional
  `X-Caller-Application`, `X-Booking-Center-Code`, and `X-Role` preserve entitlement and audit
  posture for RFC-0108 front-office analytics reads and workflow actions
- Workbench advisor-brief reads emit bounded analytics read audit records with
  `operation=advisor_brief.summary` and `panel=advisor-brief`; upstream authorization denials are
  recorded as permission-blocked without restricted identifiers or raw entitlement text
- legal-hold summary is returned as metadata for support posture; gateway retrieval does not expose
  legal-hold mutation, purge, retention mutation, or access-event routes
- intake upload routes accept camelCase multipart aliases such as `entityType`, `sampleSize`, and
  `allowPartial`
- selected lookup filters remain snake_case, such as `cif_id`, `booking_center`, `product_type`,
  and `instrument_page_limit`
- proposal writes require `Idempotency-Key`
- proposal simulation, create, list, detail, version, workflow-event, approval, lineage, reviewed
  narrative, report-request, delivery-summary, and delivery-event routes call `lotus-advise`
  `/advisory/proposals/*`; they do not call `lotus-manage`
- reviewed narrative Gateway routes preserve `lotus-advise` review state, source-hash,
  policy/guardrail/disclosure posture, report narrative-package posture, and append-only delivery
  events. Gateway does not generate narrative, infer client-ready publication, render reports,
  archive documents, contact clients, or recompute advisory delivery truth
- advisory policy routes call `lotus-advise` policy-pack and policy-evaluation endpoints:
  `/api/v1/advisory-policy-packs/*`,
  `/api/v1/proposals/{proposal_id}/versions/{proposal_version_id}/policy-evaluations`, and
  `/api/v1/advisory-policy-evaluations/*`. Gateway preserves Advise-owned policy-pack,
  evaluation, review-queue, workflow, sign-off package, sign-off decision, lineage, replay,
  event, report-package, AI-evidence, degraded, and blocked posture. Gateway does not evaluate
  suitability or best-interest rules, infer supportability, approve sign-off, override
  client-ready blockers, generate AI evidence, or promote blocked/degraded evaluations to client
  output.
- advisor cockpit routes call `lotus-advise` `/advisory/cockpit/*` through
  `/api/v1/advisor-cockpit/actions`, `/api/v1/advisor-cockpit/preparation-packets`,
  `/api/v1/advisor-cockpit/snapshot`, `/api/v1/advisor-cockpit/supportability`, and
  `/api/v1/advisor-cockpit/actions/{action_item_id}/acknowledgements`, plus
  `/api/v1/advisor-cockpit/house-view-cohorts/evaluate` for source-backed tactical house-view
  cohort publication. Cockpit reads and acknowledgements reject caller-selected `advisor_id` and
  `role`; Gateway derives authority from trusted caller headers, authorizes portfolio filters,
  binds acknowledgements to the authenticated actor, and forwards the exact Advise principal
  contract. The tactical house-view command remains outside that Cockpit capability boundary.
  Gateway preserves
  Advise-owned action status, priority, owner role, reason codes, SLA, source refs, evidence refs,
  lineage refs, unsupported capabilities, supportability, preparation-packet posture,
  tactical house-view cohort membership, and acknowledgement state.
  Gateway does not reconstruct advisory policy, memo blockers, cockpit action or preparation semantics, tactical house-view membership,
  client-ready publication, external client communication, OMS/order/fill/settlement posture, or
  demo-readiness claims.
- advisory-copilot routes call `lotus-advise` `/advisory/copilot/*` and
  `/advisory/proposals/{proposal_id}/versions/{version_id}/copilot-runs` through
  `/api/v1/advisory-copilot/evidence-packets`,
  `/api/v1/advisory-copilot/evidence-packets/from-proposal-version`,
  `/api/v1/advisory-copilot/evidence-packets/{evidence_packet_id}`,
  `/api/v1/advisory-copilot/actions`,
  `/api/v1/advisory-copilot/actions/{run_id}`,
  `/api/v1/advisory-copilot/actions/{run_id}/reviews`,
  `/api/v1/advisory-copilot/supportability`, and
  `/api/v1/advisory-copilot/proposals/{proposal_id}/versions/{version_id}/runs`.
  Gateway unwraps Workbench command envelopes where needed, preserves Advise-owned evidence
  packet identity, action-run posture, supportability, lineage, blocked capabilities, and review
  state, and does not generate recommendations, score suitability, infer client-ready advice,
  approve reviews, expose prompts/model output, contact clients, or claim OMS/order/fill/
  settlement posture.
- bank-demo proof routes call `lotus-advise` `/advisory/bank-demo-proof/*` through
  `/api/v1/advisory/bank-demo-proof/scenario-contract`,
  `/api/v1/advisory/bank-demo-proof/supported-claim-register`, and
  `/api/v1/advisory/bank-demo-proof/proof-packs`. Gateway preserves Advise-owned scenario
  identity, supported-claim classifications, material-review posture, proof markers, source refs,
  lineage refs, blocked/supportability posture, and sanitized proof-pack payloads.
  Gateway does not reconstruct bank-demo proof, infer Workbench browser proof, promote screenshot
  readiness, claim RFP/security evidence completion, infer client-ready publication, contact
  clients, or claim OMS/order/fill/settlement posture.
- gateway calls `lotus-manage` only through versioned `/api/v1/*` paths for discretionary
  management run lookup, supportability summary, capability posture, RFC-0038 mandate
  command-center authority APIs, RFC-0039 construction alternative-set authority APIs, RFC-0040
  proof-pack and portfolio-memory authority APIs, RFC-0041 rebalance-wave authority APIs, and
  RFC-0042 outcome-review authority APIs
- `/metrics` includes RFC-0108 gateway analytics fan-out metrics for selected Workbench analytics
  operations plus the central `lotus-advise`, `lotus-manage`, `lotus-report`, `lotus-archive`,
  `lotus-ai`, direct `lotus-core` query/control-plane, and `lotus-core` ingestion client seams:
  `lotus_gateway_analytics_fanout_duration_seconds` and
  `lotus_gateway_analytics_degraded_total`. Labels are bounded to operation/service/status class
  and degraded reason; portfolio, client, document, transaction, session, upload, trace,
  correlation, request, response, raw prompt, and model output content are not metric labels.
  Performance and risk upstream `metadata.calculation_supportability` is folded into Gateway
  fan-out state and degraded reason labels using the same bounded label contract.
- Workbench risk concentration remains a `lotus-risk` source-owned calculation. Gateway preserves
  `ConcentrationRiskReport:v1` top-position weights and current/proposed driver identities for
  Workbench, including `top_position_weight_current`, `top_position_weight_proposed`,
  `top_position_weight_delta`, `top_position_current`, and `top_position_proposed`; Gateway does
  not recompute `TOP_POSITION_WEIGHT`.
- analytics UI protected diagnostics lookup is gateway-first under
  `/api/v1/analytics-ui/diagnostics/{support_reference}`. It requires `X-Actor-Id`,
  `X-Tenant-Id`, `X-Region`, and an operator support role in `X-Role`; it returns only safe panel,
  operation, service, state, reason, forbidden-field, and operator-guidance posture and emits
  `gateway.analytics.audit.protected_diagnostics_lookup`.

## Request examples

Set the target gateway once:

```bash
export GATEWAY_BASE_URL="<gateway-base-url>"
```

Platform capabilities:

```bash
curl "$GATEWAY_BASE_URL/api/v1/platform/capabilities?consumerSystem=lotus-workbench&tenantId=default"
```

Domain-product catalog:

```bash
curl "$GATEWAY_BASE_URL/api/v1/domain-products/catalog?consumerSystem=lotus-workbench"
```

The catalog response includes platform provenance such as `governedByRfcs`,
`sourceManifestPath`, and `sourceDeclarationDirectory`; missing or invalid artifact failures use
bounded product-safe detail text rather than configured filesystem paths.

Domain-product detail:

```bash
curl "$GATEWAY_BASE_URL/api/v1/domain-products/products/lotus-core/PortfolioStateSnapshot/v1?consumerSystem=lotus-workbench"
```

Domain-product dependency graph:

```bash
curl "$GATEWAY_BASE_URL/api/v1/domain-products/dependency-graph?consumerSystem=lotus-workbench"
```

The dependency graph preserves platform `governedByRfcs` and source catalog provenance from the
generated artifact.

Domain-product trust certification:

```bash
curl "$GATEWAY_BASE_URL/api/v1/domain-products/trust-certification?consumerSystem=lotus-workbench"
```

Foundation workspace:

```bash
curl "$GATEWAY_BASE_URL/api/v1/foundation/portfolios/PF_1001/workspace"
```

The Foundation workspace uses `lotus-core` portfolio identity and core-snapshot sections for
first-paint holdings context, then resolves `PortfolioAnalyticsReference.performance_end_date`
before requesting YTD TWR from `lotus-performance`. This keeps the displayed return, supportability
state, and fan-out logs aligned to the latest complete calculable performance horizon instead of a
raw calendar date.

Performance summary:

```bash
curl "$GATEWAY_BASE_URL/api/v1/workbench/DEMO_ADV_USD_001/performance/summary?period=YTD&chart_frequency=monthly&detail_basis=NET&contribution_dimension=asset_class&attribution_dimension=asset_class&benchmark_code=BMK_PB_GLOBAL_BALANCED_60_40" \
  -H "X-Actor-Id: advisor-123" \
  -H "X-Caller-Application: lotus-workbench" \
  -H "X-Tenant-Id: tenant-sg" \
  -H "X-Region: APAC" \
  -H "X-Booking-Center-Code: SG" \
  -H "X-Role: advisor"
```

Risk summary:

```bash
curl "$GATEWAY_BASE_URL/api/v1/workbench/DEMO_ADV_USD_001/risk/summary?period=YTD&detail_basis=NET&benchmark_code=BMK_PB_GLOBAL_BALANCED_60_40&reporting_currency=USD" \
  -H "X-Actor-Id: advisor-123" \
  -H "X-Caller-Application: lotus-workbench" \
  -H "X-Tenant-Id: tenant-sg" \
  -H "X-Region: APAC" \
  -H "X-Booking-Center-Code: SG" \
  -H "X-Role: advisor"
```

Advisor brief:

```bash
curl "$GATEWAY_BASE_URL/api/v1/workbench/DEMO_ADV_USD_001/performance/advisor-brief?period=YTD&chart_frequency=monthly&detail_basis=NET&contribution_dimension=asset_class&attribution_dimension=asset_class&benchmark_code=BMK_PB_GLOBAL_BALANCED_60_40" \
  -H "X-Actor-Id: advisor-123" \
  -H "X-Caller-Application: lotus-workbench" \
  -H "X-Tenant-Id: tenant-sg" \
  -H "X-Region: APAC" \
  -H "X-Booking-Center-Code: SG" \
  -H "X-Role: advisor"
```

Advisor brief review action:

```bash
curl -X POST "$GATEWAY_BASE_URL/api/v1/workbench/DEMO_ADV_USD_001/performance/advisor-brief/review-actions?period=YTD" \
  -H "Content-Type: application/json" \
  -H "X-Actor-Id: advisor-123" \
  -H "X-Caller-Application: lotus-workbench" \
  -H "X-Tenant-Id: tenant-sg" \
  -H "X-Region: APAC" \
  -H "X-Booking-Center-Code: SG" \
  -H "X-Role: advisor" \
  -d "{\"action_type\":\"ACCEPT\",\"reviewed_by\":\"advisor-123\",\"reason\":\"Approved for client discussion.\"}"
```

Authenticated advisor own-book discovery:

```bash
curl "$GATEWAY_BASE_URL/api/v1/advisor-book/portfolios?asOfDate=2026-04-10&sortBy=client_id&limit=25" \
  -H "X-Actor-Id: PM_SG_001" \
  -H "X-Caller-Application: lotus-workbench" \
  -H "X-Tenant-Id: tenant-sg" \
  -H "X-Region: APAC" \
  -H "X-Booking-Center-Code: Singapore" \
  -H "X-Role: ADVISOR" \
  -H "X-Caller-Capabilities: advisor.book.read"
```

The response contains only the source-backed own-book cohort for the trusted actor and booking
centre. Treat `trusted_context_only`, `legacy_advisor_projection`, and other limitations as
operating boundaries; do not promote them to tenant certification or authoritative role coverage.

Report ordering options for a selected portfolio:

```bash
curl "$GATEWAY_BASE_URL/api/v1/report-ordering/options?scopeType=portfolio&scopeId=PB_SG_GLOBAL_BAL_001" \
  -H "X-Actor-Id: advisor-123" \
  -H "X-Caller-Application: lotus-workbench" \
  -H "X-Tenant-Id: tenant-sg" \
  -H "X-Region: APAC" \
  -H "X-Booking-Center-Code: SG" \
  -H "X-Role: client_advisor" \
  -H "X-Caller-Portfolio-Ids: PB_SG_GLOBAL_BAL_001"
```

The response separates source catalogue availability from caller-scope eligibility. JSON may be
ready while PDF remains unavailable with a Report-owned reason code. Use the returned submission
path for an eligible ordering mode; do not infer distribution or document completion from this
discovery response.

Reporting summary:

```bash
curl -X POST "$GATEWAY_BASE_URL/api/v1/reports/DEMO_DPM_EUR_001/summary" \
  -H "Content-Type: application/json" \
  -d "{\"asOfDate\":\"2026-02-24\",\"sections\":[\"WEALTH\",\"ALLOCATION\"],\"allocationDimensions\":[\"asset_class\"]}"
```

Reporting portfolio review:

```bash
curl -X POST "$GATEWAY_BASE_URL/api/v1/reports/DEMO_DPM_EUR_001/review" \
  -H "Content-Type: application/json" \
  -d "{\"asOfDate\":\"2026-02-24\",\"sections\":[\"OVERVIEW\",\"PERFORMANCE\",\"RISK_ANALYTICS\"],\"allocationDimensions\":[\"asset_class\"],\"lookThroughMode\":\"full\",\"benchmarkCode\":\"BMK_PB_GLOBAL_BALANCED_60_40\"}"
```

Portfolio review report job:

```bash
curl -X POST "$GATEWAY_BASE_URL/api/v1/reports/portfolio-reviews" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: portfolio-review-PB_SG_GLOBAL_BAL_001-2026-04-22" \
  -H "X-Actor-Id: advisor-123" \
  -H "X-Caller-Application: lotus-workbench" \
  -H "X-Tenant-Id: tenant-sg" \
  -H "X-Region: APAC" \
  -H "X-Booking-Center-Code: SG" \
  -H "X-Role: advisor" \
  -d "{\"portfolio_scope\":{\"portfolio_ids\":[\"PB_SG_GLOBAL_BAL_001\"]},\"as_of_date\":\"2026-04-22\",\"requested_output_formats\":[\"json\"],\"reporting_currency\":\"USD\",\"options\":{\"sections\":[\"OVERVIEW\",\"PERFORMANCE\",\"RISK_ANALYTICS\"],\"benchmark_code\":\"BMK_PB_GLOBAL_BALANCED_60_40\"}}"
```

Outcome-review report job:

```bash
curl -X POST "$GATEWAY_BASE_URL/api/v1/reports/outcome-reviews" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: outcome-review-dor_001-pdf" \
  -H "X-Actor-Id: advisor-123" \
  -H "X-Caller-Application: lotus-workbench" \
  -H "X-Tenant-Id: tenant-sg" \
  -H "X-Region: APAC" \
  -d "{\"outcome_report_input\":{\"outcome_review_id\":\"dor_001\",\"portfolio_id\":\"PB_SG_GLOBAL_BAL_001\",\"review_window\":{\"end_date\":\"2026-04-23\"},\"content_hash\":\"sha256:report-input\"},\"requested_output_formats\":[\"pdf\"]}"
```

All registered DPM routes require trusted caller audit headers `X-Actor-Id`, `X-Tenant-Id`, and
`X-Role`; send `X-Region` when available. Reads forward only that validated business caller context
and correlation. Product callers must not select Gateway workload authority. Gateway replaces any
supplied service identity or capability and derives exactly `X-Service-Identity: lotus-gateway`
plus `X-Capabilities: manage.write` only for outbound Manage mutations.

DPM outcome-review create:

```bash
curl -X POST "$GATEWAY_BASE_URL/api/v1/dpm/command-center/outcome-reviews" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: outcome-review-or_20260415_001" \
  -H "X-Correlation-Id: corr-rfc42-outcome-review-1" \
  -H "X-Actor-Id: platform-seed-automation" \
  -H "X-Tenant-Id: tenant-sg" \
  -H "X-Region: APAC" \
  -H "X-Role: platform-automation" \
  -d "{\"body\":{\"portfolio_id\":\"PB_SG_GLOBAL_BAL_001\",\"rebalance_run_id\":\"rr_20260415_001\",\"proof_pack_id\":\"ppack_20260415_001\",\"requested_by\":\"dpm_sg_1\"}}"
```

DPM outcome-review supportability:

```bash
curl "$GATEWAY_BASE_URL/api/v1/dpm/command-center/outcome-reviews/or_20260415_001/supportability" \
  -H "X-Correlation-Id: corr-rfc42-supportability-1"
```

DPM outcome-review AI narrative handoff:

```bash
curl -X POST "$GATEWAY_BASE_URL/api/v1/dpm/command-center/outcome-reviews/or_20260415_001/ai-narrative" \
  -H "Content-Type: application/json" \
  -H "X-Correlation-Id: corr-rfc42-outcome-review-ai-narrative" \
  -H "X-Actor-Id: pm_sg_1" \
  -H "X-Tenant-Id: tenant-sg" \
  -H "X-Region: APAC" \
  -H "X-Role: PORTFOLIO_MANAGER" \
  -d "{\"requested_outputs\":[\"pm_summary\",\"cio_summary\",\"control_summary\",\"evidence_gaps\"],\"audience\":[\"portfolio_manager\",\"cio_office\",\"investment_control\"]}"
```

DPM proof-pack AI PM memo handoff:

```bash
curl -X POST "$GATEWAY_BASE_URL/api/v1/dpm/command-center/proof-packs/dpp_rr_001/ai-pm-memo" \
  -H "Content-Type: application/json" \
  -H "X-Correlation-Id: corr-rfc40-proof-pack-ai-pm-memo" \
  -H "X-Actor-Id: pm_sg_1" \
  -H "X-Tenant-Id: tenant-sg" \
  -H "X-Region: APAC" \
  -H "X-Role: PORTFOLIO_MANAGER" \
  -d "{\"requested_outputs\":[\"pm_memo\",\"rationale_summary\",\"evidence_gaps\"],\"audience\":[\"portfolio_manager\",\"investment_control\"]}"
```

DPM rebalance-wave create:

```bash
curl -X POST "$GATEWAY_BASE_URL/api/v1/dpm/command-center/waves" \
  -H "Content-Type: application/json" \
  -H "X-Correlation-Id: corr-rfc41-wave-create" \
  -H "X-Actor-Id: pm_sg_1" \
  -H "X-Tenant-Id: tenant-sg" \
  -H "X-Region: APAC" \
  -H "X-Role: PORTFOLIO_MANAGER" \
  -d "{\"idempotency_key\":\"wave-idem-001\",\"body\":{\"trigger_type\":\"EXPLICIT_PORTFOLIO_LIST\",\"trigger_id\":\"manual-wave-20260503-001\",\"rationale\":\"CIO model update for the Singapore balanced DPM book.\",\"as_of_date\":\"2026-05-03\",\"actor_id\":\"pm_sg_1\",\"portfolios\":[{\"portfolio_id\":\"PB_SG_GLOBAL_BAL_001\"}]}}"
```

DPM rebalance-wave supportability:

```bash
curl "$GATEWAY_BASE_URL/api/v1/dpm/command-center/waves/dwv_001/supportability" \
  -H "X-Correlation-Id: corr-rfc41-wave-supportability"
```

DPM rebalance-wave report input:

```bash
curl "$GATEWAY_BASE_URL/api/v1/dpm/command-center/waves/dwv_001/report-input" \
  -H "X-Correlation-Id: corr-rfc41-wave-report-input"
```

DPM rebalance-wave AI PM memo:

```bash
curl -X POST "$GATEWAY_BASE_URL/api/v1/dpm/command-center/waves/dwv_001/ai-pm-memo" \
  -H "Content-Type: application/json" \
  -H "X-Correlation-Id: corr-rfc41-wave-ai-pm-memo" \
  -H "X-Actor-Id: pm_sg_1" \
  -H "X-Tenant-Id: tenant-sg" \
  -H "X-Region: APAC" \
  -H "X-Role: PORTFOLIO_MANAGER" \
  -d "{\"requested_outputs\":[\"wave_pm_memo\",\"approval_checklist\",\"evidence_gaps\"],\"audience\":[\"portfolio_manager\",\"investment_control\",\"operations\"]}"
```

DPM rebalance-wave selection with proof-pack generation:

```bash
curl -X POST "$GATEWAY_BASE_URL/api/v1/dpm/command-center/waves/dwv_001/items/dwi_001/select" \
  -H "Content-Type: application/json" \
  -H "X-Correlation-Id: corr-rfc41-wave-select" \
  -H "X-Actor-Id: pm_sg_1" \
  -H "X-Tenant-Id: tenant-sg" \
  -H "X-Region: APAC" \
  -H "X-Role: PORTFOLIO_MANAGER" \
  -d "{\"body\":{\"alternative_id\":\"alt_001\",\"actor_id\":\"pm_sg_1\",\"reason_code\":\"PM_SELECTED\",\"generate_proof_pack\":true}}"
```

Report job status:

```bash
curl "$GATEWAY_BASE_URL/api/v1/report-jobs/rjob_example"
```

Report job operational search:

```bash
curl "$GATEWAY_BASE_URL/api/v1/report-jobs?tenantId=tenant-sg&region=APAC&portfolioId=PB_SG_GLOBAL_BAL_001&status=accepted&limit=25" \
  -H "X-Actor-Id: support-operator-1" \
  -H "X-Tenant-Id: tenant-sg" \
  -H "X-Region: APAC"
```

Report job event history:

```bash
curl "$GATEWAY_BASE_URL/api/v1/report-jobs/rjob_example/events"
```

Report batch materialization:

```bash
curl -X POST "$GATEWAY_BASE_URL/api/v1/report-batches" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: batch-PB_SG_GLOBAL_BAL_001-2026-04-22" \
  -H "X-Actor-Id: advisor-123" \
  -H "X-Tenant-Id: tenant-sg" \
  -H "X-Region: APAC" \
  -H "X-Booking-Center-Code: SG" \
  -H "X-Role: ADVISOR" \
  -H "X-Caller-Capabilities: advisor.book.read" \
  -d "{\"selector_mode\":\"explicit_portfolio_list\",\"portfolio_ids\":[\"PB_SG_GLOBAL_BAL_001\"],\"as_of_date\":\"2026-04-22\",\"requested_output_formats\":[\"pdf\"],\"reporting_currency\":\"USD\",\"options\":{\"sections\":[\"OVERVIEW\",\"PERFORMANCE\"]},\"max_batch_size\":250}"
```

Report batch status:

```bash
curl "$GATEWAY_BASE_URL/api/v1/report-batches/rbch_example" \
  -H "X-Actor-Id: support-operator-1" \
  -H "X-Tenant-Id: tenant-sg" \
  -H "X-Region: APAC"
```

Report batch bounded operator run:

```bash
curl -X POST "$GATEWAY_BASE_URL/api/v1/report-batches/rbch_example:run-once" \
  -H "Content-Type: application/json" \
  -H "X-Actor-Id: support-operator-1" \
  -H "X-Tenant-Id: tenant-sg" \
  -H "X-Region: APAC" \
  -d "{\"worker_id\":\"lotus-report-batch-worker-1\",\"recover_expired_leases\":true,\"dispatch_policy\":{\"max_active_batches\":1,\"max_active_items\":5,\"max_active_upstream_jobs\":3,\"max_active_render_jobs\":2,\"max_active_archive_jobs\":2,\"lease_seconds\":300},\"runtime_load\":{\"active_batches\":0,\"active_items\":0,\"active_upstream_jobs\":0,\"active_render_jobs\":0,\"active_archive_jobs\":0}}"
```

Archived document metadata:

```bash
curl "$GATEWAY_BASE_URL/api/v1/documents/doc_example" \
  -H "X-Actor-Id: advisor-123" \
  -H "X-Caller-Application: lotus-workbench" \
  -H "X-Tenant-Id: tenant-sg" \
  -H "X-Region: APAC" \
  -H "X-Booking-Center-Code: SG" \
  -H "X-Role: advisor"
```

Archived document download:

```bash
curl "$GATEWAY_BASE_URL/api/v1/documents/doc_example/download" \
  -H "X-Actor-Id: advisor-123" \
  -H "X-Caller-Application: lotus-workbench" \
  -H "X-Tenant-Id: tenant-sg" \
  -H "X-Region: APAC" \
  -H "X-Booking-Center-Code: SG" \
  -H "X-Role: advisor" \
  --output portfolio-review.pdf
```

Advisor idea review queue:

```bash
curl "$GATEWAY_BASE_URL/api/v1/ideas/review-queues/advisor?evaluatedAtUtc=2026-06-21T10:10:00Z" \
  -H "X-Caller-Subject: advisor-123" \
  -H "X-Caller-Roles: advisor" \
  -H "X-Caller-Capabilities: idea.review.queue.read" \
  -H "X-Caller-Tenant-Ids: tenant-private-bank-sg" \
  -H "X-Caller-Book-Ids: book-advisor-001" \
  -H "X-Caller-Portfolio-Ids: PB_SG_GLOBAL_BAL_001" \
  -H "X-Caller-Client-Ids: client-001"
```

Idea candidate detail:

```bash
curl "$GATEWAY_BASE_URL/api/v1/ideas/candidates/idea_high_cash_8d57adbf52f7f5a7" \
  -H "X-Caller-Subject: advisor-123" \
  -H "X-Caller-Roles: advisor" \
  -H "X-Caller-Capabilities: idea.candidate.detail.read" \
  -H "X-Caller-Tenant-Ids: tenant-private-bank-sg" \
  -H "X-Caller-Book-Ids: book-advisor-001" \
  -H "X-Caller-Portfolio-Ids: PB_SG_GLOBAL_BAL_001" \
  -H "X-Caller-Client-Ids: client-001"
```

Idea candidate review action:

```bash
curl -X POST "$GATEWAY_BASE_URL/api/v1/ideas/candidates/idea_high_cash_8d57adbf52f7f5a7/review-actions" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: idea-review-001" \
  -H "X-Caller-Subject: advisor-123" \
  -H "X-Caller-Roles: advisor" \
  -H "X-Caller-Capabilities: idea.review.record" \
  -H "X-Caller-Tenant-Ids: tenant-private-bank-sg" \
  -H "X-Caller-Portfolio-Ids: PB_SG_GLOBAL_BAL_001" \
  -d "{\"reviewId\":\"review-001\",\"action\":\"approve_for_conversion\",\"reasonCodes\":[\"review_required\"],\"decidedAtUtc\":\"2026-06-21T10:15:00Z\"}"
```

The `feedback` and `conversion-intents` routes use the same caller-context and idempotency posture.
They record only Lotus Idea-owned workflow facts; a conversion intent does not initiate downstream
submission, rebalance, execution, suitability approval, or client communication.

Analytics diagnostics protected lookup:

```bash
curl "$GATEWAY_BASE_URL/api/v1/analytics-ui/diagnostics/gdiag-risk-summary-permission-blocked" \
  -H "X-Actor-Id: support-operator-1" \
  -H "X-Tenant-Id: tenant-sg" \
  -H "X-Region: APAC" \
  -H "X-Role: support-operator"
```

Proposal creation:

```bash
curl -X POST "$GATEWAY_BASE_URL/api/v1/proposals" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: idem-create-1" \
  -d @docs/demo/payloads/proposal-create.json
```

Proposal narrative review:

```bash
curl -X POST "$GATEWAY_BASE_URL/api/v1/proposals/pp_1/versions/2/narrative/review" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: proposal-narrative-review-idem-001" \
  -H "X-Correlation-Id: corr-rfc23-narrative-review" \
  -d "{\"action\":\"APPROVE\",\"reviewed_by\":\"compliance_reviewer_001\",\"reason\":\"Evidence-grounded and suitable for advisor use.\"}"
```

Proposal report request with reviewed narrative package:

```bash
curl -X POST "$GATEWAY_BASE_URL/api/v1/proposals/pp_1/report-requests" \
  -H "Content-Type: application/json" \
  -H "X-Correlation-Id: corr-rfc23-report-request" \
  -d "{\"report_type\":\"PORTFOLIO_REVIEW\",\"requested_by\":\"advisor_1\",\"related_version_no\":2,\"include_reviewed_narrative\":true}"
```

Proposal delivery posture:

```bash
curl "$GATEWAY_BASE_URL/api/v1/proposals/pp_1/delivery-summary" \
  -H "X-Correlation-Id: corr-rfc23-delivery-summary"

curl "$GATEWAY_BASE_URL/api/v1/proposals/pp_1/delivery-events" \
  -H "X-Correlation-Id: corr-rfc23-delivery-events"
```

Bank-demo proof supported-claim register:

```bash
curl "$GATEWAY_BASE_URL/api/v1/advisory/bank-demo-proof/supported-claim-register" \
  -H "X-Correlation-Id: corr-rfc0028-claims"
```

Bank-demo proof-pack capture is automation-oriented. The `POST
/api/v1/advisory/bank-demo-proof/proof-packs` body should be the governed evidence envelope
produced by the canonical runtime proof flow, including `live_runtime_payload` and sanitized
`runtime_posture`; do not hand-build demo proof payloads in UI code.

Use these examples to preserve the current gateway-facing parameter shapes until a contract is
intentionally changed.
