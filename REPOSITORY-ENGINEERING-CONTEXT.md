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
3. performance, proposal, advisory-workspace, advisory-policy, advisory-copilot,
   advisor-cockpit, bank-demo proof, foundation, reporting, and capability aggregation
   routes are active, with proposal simulation/lifecycle/workflow/approval/lineage, typed
   selected-proposal risk-and-impact, implementation-status, and discussion-pack-review evidence,
   async operation support,
   idempotency lookup, replay evidence, reviewed narrative posture, execution
   handoff/status/update posture, memo report-package events, report-request, and delivery-posture
   routes routed to `lotus-advise` `/advisory/proposals/*`; advisory workspace create/draft/save,
   saved-version replay, resume, compare, rationale request/review, and handoff routes are routed
   to `lotus-advise` `/advisory/workspaces/*`; advisory policy-pack, policy-evaluation,
   review-queue, workflow, sign-off package, sign-off decision, report-package, lineage, replay,
   event, and AI-evidence routes are routed to `lotus-advise` `/advisory/policy-*` and
   `/advisory/proposals/*/policy-evaluations`; advisor-cockpit action, preparation-packet,
   single-action, snapshot, supportability, and acknowledgement routes are routed to `lotus-advise`
   `/advisory/cockpit/*`. Those Cockpit reads and acknowledgements derive advisor identity, role,
   capability, and portfolio scope from trusted server-side caller context: query `advisor_id` and
   `role` are rejected, advisor actors cannot project another advisor id, portfolio filters must
   match `X-Authorized-Portfolio-Id`, acknowledgement actors are bound to `X-Actor-Id`, and Gateway
   translates the result to the exact Advise principal headers. The tactical house-view cohort
   command remains a separate source-product route and does not receive an invented Cockpit
   capability. Advisory-copilot evidence-packet, action-run, review, supportability,
   and proposal-version run-lineage routes are routed to `lotus-advise`
   `/advisory/copilot/*` and `/advisory/proposals/*/copilot-runs`; bank-demo proof
   scenario-contract, supported-claim register, and
   proof-pack capture routes are routed to `lotus-advise`
   `/advisory/bank-demo-proof/*`. Gateway preserves source-hash, review,
   report-package, workspace replay, execution handoff, policy supportability, degraded/blocked
   posture, maker-checker state, sign-off posture, AI-evidence posture, cockpit action status,
   owner role, reason codes, preparation-packet posture, copilot action-run posture, evidence
   refs, lineage refs,
   acknowledgement state, supported-claim classifications, material-review conflicts, backend
   proof-pack posture, proposal allocation/risk/decision source authority, typed implementation
   handoff state/version/event/ownership posture, request-bound discussion narrative/memo/
   disclosure/package/consent evidence, and delivery event posture
   without generating narrative, evaluating policy rules, inferring client-ready publication,
   rendering reports, archiving documents, sourcing portfolio positions locally, calculating
   proposal risk or allocation deltas, claiming downstream order/fill/settlement authority, or
   recomputing advisory delivery truth, generating copilot
   recommendations, or turning support output into
   client-ready advice;
   `lotus-manage` consumption is through versioned `/api/v1` APIs for
   run lookup, supportability summary, capability posture, RFC-0038 mandate command-center
   summary/monitoring/exception/mandate drill-down route families, RFC-0040 proof-pack
   generate/read/Markdown/report-input/AI-evidence/AI PM memo route families,
   RFC-0040/RFC-0041/RFC-0042 portfolio-memory route family, RFC-0042 outcome-review
   preview/create/search/detail/source-refresh/supportability/report-input/AI-evidence and
   AI-narrative handoff route families, and Manage PM operating quality policy/score-run
   lifecycle route families,
4. source-backed report ordering configuration and selected-scope eligibility are active under
   `/api/v1/report-ordering/options`; `lotus-report` remains catalogue authority, Gateway publishes
   only implemented submission paths, and client/book scopes do not imply portfolio membership,
5. authenticated advisor own-book discovery is active under
   `/api/v1/advisor-book/portfolios`; Gateway derives the manager only from trusted caller context,
   consumes Core `PortfolioManagerBookMembership:v1`, preserves assignment basis and provenance,
   rejects cross-scope evidence, reports null Core tenant scope as degraded, and does not fall back
   to the global portfolio catalogue or infer team, delegate, supervisor, household,
   assets-under-management, attention, suitability, communication, or execution truth. Its
   repo-native RFC-0084 consumer declaration records the direct Core dependency, required trust
   metadata, protected lanes, and fail-closed posture; Gateway remains an experience API rather
   than the assignment authority,
5. report job initiation/search/status/event-history/cancellation routes are active for
   gateway-first portfolio review report job workflows under `/api/v1/reports/portfolio-reviews`,
   `/api/v1/report-jobs`, and `/api/v1/report-jobs/*`,
6. RFC-0104 report batch materialization/status/control/retry/recovery/bounded operator-run routes
   are active under `/api/v1/report-batches` and `/api/v1/report-batches/*`; config-backed
   scheduler list/run-due routes are active under `/api/v1/report-batch-schedules`. Explicit batch
   creation accepts portfolio identifiers only, derives the advisor's own-book authority from
   trusted caller context, resolves membership through Core `PortfolioManagerBookMembership:v1`,
   and constructs Report candidate tenant, region, active-state, and source provenance server-side;
   browser-supplied candidate authority is rejected. Lifecycle, scheduler configuration, and
   execution truth remain in `lotus-report`,
7. archived generated-document metadata and controlled download routes are active under
   `/api/v1/documents/{document_id}` and `/api/v1/documents/{document_id}/download` as the
   product-facing boundary over `lotus-archive`,
8. domain-product catalog, dependency-graph, and live trust certification discovery routes are
   active under `/api/v1/domain-products`,
9. idea review queue/detail reads and candidate review-action, feedback, and conversion-intent
   recordings are active under `/api/v1/ideas/*`; Gateway forwards caller entitlement scope, optional
   trusted context, correlation/trace context, and for mutations `Idempotency-Key` plus optional
   causation. It preserves `lotus-idea` ranking, source refs, durable-storage posture, accepted or
   replayed source outcomes, and `supportedFeaturePromoted=false`. Candidate action requests use
   the closed `IdeaReasonCode` vocabulary reconciled through
   `contracts/upstream/lotus-idea-reason-codes.v1.json`; unknown values fail at Gateway validation
   before source fan-out. Gateway does not generate, rank, enrich, certify, authorize, or promote
   ideas locally. These BFF routes do not claim
   Workbench completion, data-product certification, downstream realization, execution, or client
   communication readiness,
10. upstream service consumption is classified under RFC-0082 in `docs/standards/RFC-0082-upstream-contract-family-map.md`,
9. the advisor-brief path now calls the explicit `lotus-ai` workflow-pack execution seam and consumes the returned run identity directly instead of inferring it from task audit request ids; it also preserves bounded RFC-0097 task-flow posture and replacement lineage from `lotus-ai` without making gateway the task-flow authority,
10. RFC-0042 outcome-review AI narrative handoff now reads manage-owned
    `DpmOutcomeAiEvidenceInput` and executes `lotus-ai` `outcome_review_narrative.pack@v1` as
    `lotus-gateway`; manage remains outcome evidence and workflow authority, Gateway preserves
    Manage-owned `client_communication_boundary` posture when present, and Gateway does not
    generate narrative or client communication truth locally,
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
14. the six DPM AI handoff families publish one typed, product-safe
    `DpmAiWorkflowExecution` boundary. Gateway validates lotus-ai service, pack, version, caller,
    correlation, workflow-surface, authorization, eligibility, task, run, provider, and authority
    identities before returning source-owned runtime, review, supportability, evidence, artifact,
    freshness, replacement, and recovery posture. Contract drift fails closed with
    `AI_WORKFLOW_EXECUTION_CONTRACT_INVALID`; raw prompts, free-text model output, evidence
    attributes, storage locations, and unbounded provider telemetry are not exposed. Gateway does
    not infer that an accepted request has produced an available, reviewed, current, or
    client-usable output. Request construction and response validation share the immutable
    `explain.v1` / `EXPLANATION_ONLY` task contract, so internally consistent task or output-label
    drift also fails closed,
15. canonical local startup now depends on environment-scoped service identity and `--app-dir src`
    to avoid misleading Windows import-path failures.
16. RFC-0108 analytics UI observability is active for selected Workbench performance summary,
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
    recomputing domain calculation truth. For `ConcentrationRiskReport:v1`, Gateway validates and
    forwards source-owned single-position concentration fields, including
    `top_position_weight_current`, `top_position_weight_proposed`, `top_position_weight_delta`,
    `top_position_current`, and `top_position_proposed`; `TOP_POSITION_WEIGHT` methodology truth
    remains owned by `lotus-risk`.
    Advisor-brief workflow-pack mapping preserves Lotus AI's source-recorded latest review actor,
    latest review event time, transition count, and history flag. Consumers must fail closed when
    that evidence is absent or malformed; terminal `review_state` is not sufficient evidence of a
    recorded human decision.
17. performance workspace-summary orchestration uses
    `PERFORMANCE_SUMMARY_DEADLINE_SECONDS=30` as an end-to-end monotonic budget across submission
    and polling, while `PERFORMANCE_ANALYTICS_TIMEOUT_SECONDS=15` remains a per-call ceiling.
    Submission and result reads are limited to the remaining budget both through HTTPX
    per-operation timeouts and a complete-await cancellation guard. Typed transient transport
    failures continue through the outer elapsed-time polling loop while actual upstream HTTP
    failures remain terminal. Polling waits for the accepted response's minimum source cadence
    before the first read, preserves one calculation identity and caller context after acceptance,
    and emits bounded `async_poll_deadline_exhausted` telemetry. When submission acceptance is
    unknown, the deadline response omits calculation identity and result path. Deadline exhaustion
    becomes the specific Workbench `PERFORMANCE_WORKSPACE_SUMMARY_DEADLINE_EXHAUSTED`
    partial-readiness response and suppresses follow-on execution or lineage evidence reads; it is
    not masked by a replacement calculation or treated as successful because a later warm retry
    completes.
18. performance `evidence_view` responses carry the inclusive `report_start_date` and
    `report_end_date` from the same Gateway-resolved workspace request context used for analytics.
    These boundaries are required across supported, partial, and unavailable evidence postures so
    Workbench can fail closed when calculation evidence does not match the advisor's review window;
    Workbench must not infer or reconstruct them.

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
   `lotus-report`, `lotus-archive`, `lotus-idea`, and `lotus-ai`.

Boundary rules:

1. gateway payloads should be product-oriented and governed,
2. domain ownership must remain upstream,
3. route contracts should prefer replacement and cleanup over versioned clutter while pre-live,
4. gateway must not become the authority for portfolio source data, performance analytics, risk analytics, advisory workflow, management workflow, reporting, or AI outputs,
5. REST/OpenAPI remains the canonical integration contract; gRPC is not justified for current gateway upstream calls,
6. canonical service identity is part of the operational contract,
7. domain-product discovery must preserve platform artifact provenance, approved consumers, trust metadata, dependency posture, and certified trust posture without duplicating platform validation logic inside gateway,
8. service modules must depend on typed protocol surfaces instead of concrete upstream client
   classes; only client factory modules under `src/app/services/*_client_factory.py` should import
   `app.clients.*` constructors. Protocol modules such as `ai_client_protocols.py`,
   `dpm_client_protocols.py`, `reporting_client_protocols.py`, `advisory_client_protocols.py`,
   `workspace_client_protocols.py`, and `domain_client_protocols.py` own broad protocol families,
   and `tests/unit/test_service_layer_boundaries.py` enforces the factory-only concrete-client rule.

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
4. workflow action-runtime governance is part of `make lint` and enforces the platform baseline
   for governed core GitHub Actions majors plus the workflow-level Node 24 JavaScript action opt-in,
5. agent quality evidence governance is part of `make lint` through
   `scripts/check_agent_quality_evidence.py`; it keeps the executable 316/49 refactor ratchet, the
   current evidence-selected `src/app/services/platform_capabilities_workspace_descriptors.py`
   hotspot, and durable
   scorecard/context guidance synchronized for future agent work,
6. PR auto-merge is rebase-only for linear history; `.github/workflows/pr-auto-merge.yml` uses
   `LOTUS_AUTOMERGE_TOKEN` and `gh pr merge --auto --rebase --delete-branch`, and skips cleanly
   with a warning when the token is absent so an authorized human or release actor can perform the
   rebase merge without leaving a false red helper check,
7. `.github/workflows/merged-pr-main-releasability.yml` dispatches `main-releasability.yml` after
   a pull request is merged into `main`, preserving exact-main release evidence for authorized
   human or release-actor merges as well as token-backed auto-merge; `main-releasability.yml` is
   intentionally `workflow_dispatch`-only so this dispatcher remains the single automatic
   post-merge path and does not duplicate a push-triggered release run,
8. `make demo-certification` is the current app-level Gateway demo-readiness command; it calls real
   FastAPI routes with deterministic synthetic upstream fixtures, writes
   `output/demo-certification/gateway-demo-certification.json`, and remains report-only in Quality
   Baseline until repeated low-noise evidence and exception policy justify blocking promotion,
9. Docker parity matters because the gateway is a live integration boundary,
10. Gateway Docker images are tagged with the Git SHA, stamped with non-secret build-time OCI
   labels, scanned with Trivy before any main-lane push, inventoried with an SBOM, and recorded in a
   release manifest. Main Releasability is the only lane that pushes to GHCR; it captures the
   digest after push, signs the digest-pinned image, creates provenance attestation evidence, and
   requires Kubernetes deployment by digest while preserving the same image for environment
   promotion,
11. `/version` exposes the same non-secret build and deployment metadata expected in release
    manifests: Git commit SHA, branch, build timestamp, repo URL, image digest, CI run ID, and
    version. Image digest is deployment/runtime metadata captured after push and must not be baked
    into Docker build args, ENV, or OCI labels as `unknown`,
12. README and wiki updates should preserve truthful endpoint-specific parameter conventions, and
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

Portfolio transaction settlement applicability is a joint source contract: `component_type`
identifies canonical FX cash-settlement components and nullable `settlement_status` carries their
source-owned lifecycle state. Keep both meanings explicit in Gateway OpenAPI, preserve explicit
`null` serialization for rows without a reported applicable lifecycle, and leave business presentation to Workbench without
reclassifying arbitrary source codes in the BFF.

1. Windows startup can serve a misleading health-only process if `--app-dir src` is omitted,
2. stale thin-pass-through routes should be retired as better experience contracts replace them,
3. gateway fixes should not smuggle domain logic out of authoritative upstream services,
4. reporting query, cashflow projection, projected summary, and benchmark catalog upstream calls remain RFC-0082 watchlist surfaces,
5. integration drift is most dangerous here because it directly affects the product UI,
6. an omitted optional portfolio workspace `as_of_date` must remain omitted for the initial
   lotus-core AUM request; Gateway then aligns the remaining workspace sources and analytics to
   the source-resolved date rather than substituting its host wall clock,
7. repo-local `wiki/` content should summarize route families and operator flows without duplicating
   the full `docs/` tree.
8. archive retrieval uses `ARCHIVE_SERVICE_BASE_URL` and forwards archive-specific caller context
   as `lotus-gateway`; direct Workbench-to-archive access is not part of the supported product
   boundary,
9. idea publication uses `IDEA_SERVICE_BASE_URL`, forwards `X-Caller-Subject`,
   `X-Caller-Roles`, `X-Caller-Capabilities`, entitlement-scope headers for published idea reads,
   and correlation context to `lotus-idea`, and maps unsafe upstream failures to product-safe
   Gateway errors,
10. domain-product discovery defaults to platform-generated catalog and dependency-graph artifacts
   under the sibling `lotus-platform/generated/` directory, and live trust certification defaults to
   `lotus-platform/output/trust-certification/domain-product-live-trust-certification.json`;
   deployment-specific paths should use `DOMAIN_PRODUCT_CATALOG_PATH`,
   `DOMAIN_PRODUCT_DEPENDENCY_GRAPH_PATH`, and `DOMAIN_PRODUCT_LIVE_TRUST_CERTIFICATION_PATH`.
10. report batch gateway routes are an RFC-0104 trusted own-book/API/operator boundary only;
    Workbench batch UI,
   RFC-0105 replay/dashboard operations, and RFC-0106 entitlement certification remain separate
   implementation scopes until explicitly delivered and proven.
10. RFC-0042 outcome-review Gateway routes are active under
    `/api/v1/dpm/command-center/outcome-reviews*`,
    `/api/v1/dpm/command-center/runs/{rebalance_run_id}/outcome-review`, and
    `/api/v1/dpm/command-center/waves/{wave_id}/outcome-reviews`. Gateway composes a BFF envelope
    and supportability summary over manage truth, but it must not recompute outcome dimensions,
    synthesize `client_communication_boundary`, generate reports, generate AI narrative, infer PM
    quality, or let Workbench call manage directly.
    All registered DPM routes require trusted `X-Actor-Id`, `X-Tenant-Id`, and `X-Role` caller audit
    identity; `X-Region` is preserved when supplied and remains required where a route-specific
    contract declares it. Reads forward only validated caller audit identity and correlation.
    Mutations replace any caller-supplied workload authority with the request-scoped
    `X-Service-Identity: lotus-gateway` and exact `X-Capabilities: manage.write` contract before
    calling Manage. Missing or malformed caller identity fails closed before the upstream call.
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
14. RFC-0040/RFC-0041/RFC-0042 portfolio-memory Gateway routes are active under
    `/api/v1/dpm/command-center/portfolios/{portfolio_id}/memory` and
    `/api/v1/dpm/command-center/portfolio-memory/search`. Gateway forwards portfolio, event,
    supportability, source-system, source-type, pagination, and scan-limit filters to
    `lotus-manage` portfolio-memory APIs, preserves manage-owned event order, event types, source
    systems, source-system/type facets, source refs, artifact refs, applied filters, reason codes,
    supportability state, support boundary, content hash, and bounded metadata, and must not
    reconstruct timeline nodes, infer mandate exceptions, query source-owner stores, discover the
    global portfolio universe, calculate risk, performance, tax, cash, FX, OMS execution, fills,
    settlement, client communication, or source-owner methodology locally.
15. RFC-0041 rebalance-wave Gateway routes are active under
    `/api/v1/dpm/command-center/waves*`. Gateway forwards preview, durable create, search, detail,
    item list, source-check, simulation, item selection, approval, staging, internal handoff,
    cancellation, proof-pack posture, supportability, report-input, campaign-definition list,
    get, lifecycle-events, preview-readiness, upsert, bounded campaign-discovery, campaign
    operating queue, approval inbox, workflow board, assignment plan, workflow automation,
    approval-decision, assignment-action, assignment-task, task-transition, and maker-checker
    evidence requests to `lotus-manage`;
    campaign-definition list/get and campaign-discovery reads require trusted `X-Tenant-Id`
    scope and fail closed at request validation when it is missing;
    preserves the bounded `campaign_candidate_source=CORE_DPM_PORTFOLIO_UNIVERSE` request shape
    for Manage/Core `DpmPortfolioUniverseCandidate:v1` consumption while rejecting non-empty
    caller-supplied candidate portfolio fields at the BFF boundary;
    preserves manage-owned `wave_id`, lifecycle state, item states, reason codes, aggregate
    metrics, selected alternative refs, proof-pack refs, handoff refs, campaign definition payloads,
    campaign workflow/audit payloads, count/page metadata, supportability issues, source refs,
    content hashes, report-input evidence, and `external_execution_claimed=false`; and must not
    calculate affected portfolios, classify source readiness, discover cohorts, recompute campaign
    membership, discover global campaign cohorts, calculate task state, approval state,
    maker-checker state, SLA posture, workflow orchestration, generate alternatives, select
    alternatives, approve items, stage items, create handoff evidence, rebuild proof packs,
    generate report evidence, or claim external execution locally. Gateway can request `lotus-ai`
    `dpm_wave_pm_memo.pack@v1` from manage-owned wave report input as a review-required PM/control
    support artifact, but it must not generate AI narrative locally, score PMs, approve trades,
    contact clients, place orders, or invent missing evidence.
16. PM operating quality Gateway routes are active under
    `/api/v1/dpm/command-center/pm-operating-quality/*`. Gateway forwards policy list/get/upsert,
    score-run preview/create/list/get, fairness-analysis preview/create/list/get,
    review-action preview/create/list/get, and summary-invocation preview/create/list/get
    requests to `lotus-manage`, and exposes a governed
    `/score-runs/{score_run_id}/ai-summary` route that reads Manage score-run evidence before
    executing `lotus-ai` `pm_quality_summary.pack@v1` as `lotus-gateway`. Gateway preserves Manage
    policy configuration, score-run state, fairness-analysis state, review-action state, bounded
    rationale, target content hashes, source-defined segment posture, summary-invocation workflow
    refs, summary-text boundary evidence, governance evidence, source refs, reason codes, content
    hashes, supportability, and forbidden-use posture, and must not calculate scores, discover
    segments, calculate segment averages or fairness spread, infer protected classes, rank PMs,
    administer bank policy locally, reinterpret review rationale, store or expose generated
    summary text, reconstruct prompts or model responses, create HR or compensation decisions,
    perform conduct enforcement, approve trades, contact clients, route orders, claim
    OMS/execution, or invent missing evidence.
17. Gateway Manage clients must never trust browser-supplied service identity, capability, service
    actor, tenant, role, or resource-scope authority. Registered DPM routes validate actor, tenant,
    role, and optional region once in request scope. Reads forward only that caller audit context;
    mutations additionally derive Gateway's own `lotus-gateway` workload identity and exact
    `manage.write` capability. Missing request scope fails closed before DPM transport.
18. The Workbench overview and portfolio-360 `rebalance_snapshot` now carry bounded
    portfolio-level DPM operations posture for RFC36-WTBD-003: latest rebalance status, last run,
    manage action-register supportability from `/api/v1/rebalance/supportability/summary`, and up
    to five recent manage runs from `/api/v1/rebalance/runs` with bounded status, timestamp,
    workflow posture, and error code. Gateway remains the product-facing composition boundary and
    does not calculate supportability, workflow state, or error semantics locally.
19. RFC-0028 bank-demo proof Gateway routes are active under
    `/api/v1/advisory/bank-demo-proof/*`. Gateway forwards scenario-contract, supported-claim
    register, and proof-pack capture requests to `lotus-advise`, preserves Advise-owned
    classifications, material-review posture, source refs, lineage refs, proof markers, and
    blocked/supportability posture, and must not infer demo readiness, client-ready publication,
    Workbench browser proof, screenshot readiness, RFP/security completion, external client
    communication, OMS/order/fill/settlement posture, or proof semantics locally.

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
