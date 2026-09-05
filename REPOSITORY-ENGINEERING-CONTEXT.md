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
3. proposal, advisory-workspace, advisory-policy, advisor-cockpit, advisory-copilot, bank-demo
   proof, proposal-memo, and Manage-consumption route families are active, each preserving
   source authority (performance, reporting, and capability-aggregation families are recorded
   in their own items below, capability aggregation in the final item):
   - proposal routes, with proposal simulation/lifecycle/workflow/approval/lineage, typed
   selected-proposal risk-and-impact, implementation-status, and discussion-pack-review evidence,
   async operation support,
   idempotency lookup, replay evidence, reviewed narrative posture, execution
   handoff/status/update posture, memo report-package events, report-request, and delivery-posture
   routes routed to `lotus-advise` `/advisory/proposals/*`;
   - advisory workspace create/draft/save,
   saved-version replay, resume, compare, rationale request/review, and handoff routes are routed
   to `lotus-advise` `/advisory/workspaces/*`;
   - advisory policy-pack, policy-evaluation,
   review-queue, workflow, sign-off package, sign-off decision, report-package, lineage, replay,
   event, and AI-evidence routes are routed to `lotus-advise` `/advisory/policy-*` and
   `/advisory/proposals/*/policy-evaluations`;
   - advisor-cockpit action, preparation-packet,
   single-action, snapshot, supportability, and acknowledgement routes are routed to `lotus-advise`
   `/advisory/cockpit/*`. Those Cockpit reads and acknowledgements derive advisor identity, role,
   capability, and portfolio scope from trusted server-side caller context: query `advisor_id` and
   `role` are rejected, advisor actors cannot project another advisor id, portfolio filters must
   match `X-Authorized-Portfolio-Id`, acknowledgement actors are bound to `X-Actor-Id`, and Gateway
   translates the result to the exact Advise principal headers. The tactical house-view cohort
   command remains a separate source-product route and does not receive an invented Cockpit
   capability. Action list and single-action reads are exposed through typed, closed Gateway
   contracts that validate source shape and fail closed on successful payload drift; Gateway does
   not derive action posture or apply this contract to the other Cockpit response families.
   - advisory-copilot evidence-packet, action-run, review, supportability,
   and proposal-version run-lineage routes are routed to `lotus-advise`
   `/advisory/copilot/*` and `/advisory/proposals/*/copilot-runs`;
   - bank-demo proof scenario-contract, supported-claim register, and
   proof-pack capture routes are routed to `lotus-advise`
   `/advisory/bank-demo-proof/*`;
   - across all of these, Gateway preserves source-hash, review,
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
   - proposal memo detail, audience projection, review, report-package event/request, AI commentary,
   lineage, and replay-evidence routes publish typed source-faithful response envelopes. The typed
   boundary preserves Advise memo identity, immutable version, hashes, append-only events,
   replay posture, report handles, archive refs, and non-authoritative commentary without moving
   memo lifecycle or publication rules into Gateway. Memo evidence, projection, posture, replay,
   commentary, and report-explanation structures are closed typed models; only bounded scalar
   metadata maps remain source-owned pass-through evidence. Stale illustrative response nesting,
   legacy string commentary sections, incomplete commentary objects,
   audit-count contradictions, and malformed successful source payloads fail closed: typed
   contract construction maps the latter to a product-safe `502` identifying `lotus-advise`.
   Commentary posture, action, audit, lineage, and replay paths reuse one closed section contract
   carrying Advise-owned section key, title, text, and review state. Recorded commentary posture
   retains source memo/input hashes, idempotency evidence, requested section keys, and reason so
   Workbench can verify the refreshed action before confirming it. Recorded or available
   commentary without its idempotency and memo/source hashes fails closed. Those hashes must match
   the enclosing memo, lineage item, or replay evidence, and the commentary action result must
   match the submitted memo hash and idempotency key; non-recorded posture may omit that action
   lineage;
   Memo lineage also requires item/count/latest identity consistency before publication. Contract
   tests and generated OpenAPI expose named nested properties and recursively closed response
   references rather than an opaque memo-family `data` object. The OpenAPI fitness gate also
   rejects recursively reachable `additionalProperties: true` objects while allowing bounded
   scalar maps;
   - `lotus-manage` consumption is through versioned `/api/v1` APIs for
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
5. authenticated advisor own-book discovery, bounded own-book value summary, Advise-backed
   own-book action items, and the primary own-book workspace composition are active under
   `/api/v1/advisor-book/portfolios`, `/api/v1/advisor-book/summary`,
   `/api/v1/advisor-book/action-items`, and `/api/v1/advisor-book/workspace`; Gateway derives the
   manager only from trusted caller context, consumes Core `PortfolioManagerBookMembership:v1`,
   preserves assignment basis and provenance, and rejects cross-scope evidence. The summary makes
   an explicit as-of date and reporting currency mandatory and reads Core's
   `portfolio-summary-bulk-v1` contract once for the trusted cohort: per member it preserves the
   source-owned coverage state and reason (MEASURED_ZERO is a supported zero — a business fact;
   CARRY_FORWARD is supported with its snapshot date visible), publishes total, cash, and invested
   value only from member totals the source states as trustworthy, and takes book totals from
   Core's fail-closed cohort aggregate — Gateway never sums rows, substitutes zero, or infers
   coverage. The action-items route intersects two independently admitted scopes on
   portfolio identity only: the Core membership cohort (resolved for the requested business
   date) and the caller's advisor-scoped Advise cockpit action feed (cockpit read capability
   enforced; a portfolio-scoped Advise entitlement is rejected because it cannot state coverage
   for the whole book). Gateway counts the items the source returns, whatever their source
   status — actionable meaning stays with lotus-advise — with their own reason codes, reports
   unassigned and outside-book items as explicit counts, runs membership and every action page
   under one elapsed composition deadline, and surfaces a stopped read, page budget, stated-total
   contradiction, or self-contradicting pagination as explicit partial coverage; action evidence
   is current-state (a historical membership date never implies historical action evidence), and
   an empty book does not read the feed and says so (`not_read`). The workspace route is the
   primary Advisor Book composition for the Workbench landing experience: membership is resolved
   exactly once, the cohort and its provenance are frozen, and the bulk value read plus the
   action-feed read are composed concurrently against exactly that cohort under one elapsed
   composition deadline; every cohort member is a row with per-fact truth, a degraded enrichment
   degrades only its own typed fact block (`value_facts`/`action_facts`) with a bounded reason
   and never removes a row or substitutes zero, the Advise scope is optional there (absent,
   invalid, portfolio-scoped, or unscoped context leaves the action fact explicitly unavailable
   while value facts still stand), and only an unresolvable membership cohort is fatal. All
   three fact-bearing routes share single-owner fact builders (`advisor_book_value_facts`,
   `advisor_book_action_items_read`) so their semantics cannot drift. Gateway does not fall back
   to the global portfolio catalogue or infer team, delegate, supervisor, household, performance,
   risk, suitability, communication, or execution truth, and does not reinterpret Advise action
   status, priority, or business meaning.
6. Current source-backed portfolio position tax-lot drill-down is active at
   `/api/v1/portfolio/portfolios/{portfolio_id}/positions/{security_id}/lots`; Gateway publishes
   only Core's current BUY-lot identity, acquisition, quantity, cost, and lineage fields. It does
   not invent as-of valuation, holding-period, unrealized-P&L, disposal, or reporting-currency
semantics. Core follow-up evidence for those semantics is tracked by #1033, with valuation and
disposal ownership remaining in Core issues #788 and #481; Gateway delivery is tracked by #630
under parent issue #586.
7. Current source-backed allocation reads are active at
   `/api/v1/portfolio/portfolios/{portfolio_id}/allocations`. Core owns allocation calculation,
   classification, look-through eligibility, contributor ordering, source lineage, bucket totals,
   and bounded residuals. Gateway validates the Core contributor contract and publishes typed
   direct-position/look-through-component rows, preserving booked/component identity, source
   snapshot and component-record lineage, reporting-currency contribution values, effective
   look-through posture, and explicit truncation. Gateway does not recalculate allocation, join
   direct positions to infer components, or invent target, benchmark, drift, suitability,
   recommendation, order, execution, or settlement truth. The route accepts only canonical
   `direct_only` and `prefer_look_through` modes and bounds contributor detail to 1–250 rows per
   bucket, default 50; malformed successful Core payloads fail closed with
   `PORTFOLIO_ALLOCATION_CONTRACT_INVALID`. This is the bounded Gateway delivery for #496; Core
   source-contract history remains tracked by lotus-core#801 and is not closed by Gateway. The
   Gateway-owned `PortfolioAllocation*` response graph is closed in OpenAPI and recursively
   fitness-checked; Core source-reader models remain tolerant of additive fields.
8. Repo-native RFC-0084 consumer declaration records five direct Core dependencies with required
   trust metadata and protected validation lanes: `PortfolioManagerBookMembership:v1` is
   fail-closed for entitlement, `PortfolioAnalyticsReference:v1` is fail-closed by default with
   bounded partial overrides for ordinary reference loss and fail-closed typed since-inception
   window errors, `BenchmarkAssignment:v1` degrades to partial composition with sanitized
   `BENCHMARK_ASSIGNMENT_UNAVAILABLE` evidence on lookup failure, `BenchmarkDefinition:v1`
   degrades to partial composition, and `ExternalOrderExecutionAcknowledgement:v1` is fail-closed
   for OMS supportability. The source-backed route inventory is maintained in
   `contracts/domain-data-products/lotus-gateway-core-route-inventory.v1.json`; the AUM route
   remains an RFC-0082 operational-read dependency rather than a new domain-product declaration,
   and the RFC-0084 unit gate statically checks Core client route arguments in async or sync methods
   under `lotus_core*.py` against that inventory in both directions, including `path=`/`url=` shapes,
   normalized route identity for every discovered integration path, and module-level route
   visibility with an explicit DTO-only exemption. Unresolved routes fail closed by default,
   including private helpers that happen to accept a caller-supplied path. The only exceptions
   are the small, named module/method allowlist for generic Core transport helpers, with a reason
   recorded beside each entry; new generic helpers must be added explicitly. Opaque f-string
   interpolations are unresolved. A route-leading unencoded caller parameter is opaque regardless
   of its name; a caller parameter after a stable concrete route prefix (a route boundary or an
   already-known `/integration/` marker) is retained as a normalized placeholder. Only the explicit
   Core base-URL attributes are trusted as host prefixes; arbitrary instance attributes and
   incomplete route prefixes fail closed. Opaque `.format()` replacements also fail closed.
   Statically resolved route-bearing constants are retained in the route template, while aliases
   with multiple assignments are ambiguous and fail closed. Parameter rebindings are collected
   across plain, destructured, augmented, loop, and named-expression targets; writes to trusted
   base-URL attributes also invalidate the transport exemption. The seven generic transport
   exemptions apply only to their documented caller-path, caller-URL, or base-URL-plus-path AST shape. Only a non-rebound direct
   `from urllib.parse import quote` binding with `quote(..., safe="")` is known safe for a
   caller-supplied segment; aliases, other imports, local definitions, and rebindings fail closed.
   Capabilities, effective policy, and core-snapshot
   remain explicitly classified control-plane/snapshot operations,
9. report job initiation/search/status/event-history/cancellation routes are active for
   gateway-first portfolio review report job workflows under `/api/v1/reports/portfolio-reviews`,
   `/api/v1/report-jobs`, and `/api/v1/report-jobs/*`,
10. RFC-0104 report batch materialization/status/control/retry/recovery/bounded operator-run routes
   are active under `/api/v1/report-batches` and `/api/v1/report-batches/*`; config-backed
   scheduler list/run-due routes are active under `/api/v1/report-batch-schedules`. Explicit batch
   creation accepts portfolio identifiers only, derives the advisor's own-book authority from
   trusted caller context, resolves membership through Core `PortfolioManagerBookMembership:v1`,
   and constructs Report candidate tenant, region, active-state, and source provenance server-side;
   browser-supplied candidate authority is rejected. Lifecycle, scheduler configuration, and
   execution truth remain in `lotus-report`. Batch status now preserves the directly linked
   source report-job state and publishes archive document identity only after caller-scoped
   Archive confirms access; Gateway projects explicit available,
   pending, and unavailable archive posture and emits metadata/download links only for a confirmed
   archived source document. Before publishing those links, Gateway sends one bounded
   caller-scoped Archive access-preflight request for unique eligible identities. That advisory
   request uses one HTTP attempt within the configured three-second maximum and never retries a
   timeout; denied, missing, unavailable, malformed, and timeout postures remain linkless and
   indistinguishable to the consumer. The
   final metadata/download routes still re-check tenant/region, and Gateway never exposes raw
   storage locations or substitutes a newer correction document. The read-only
   `/api/v1/report-batches/preflight` route now evaluates the same
   validated batch setup against Core's `PortfolioManagerBookMembership:v1` once and Report's
   ordering catalogue once, returning ordered per-portfolio `ready`, `partial`, `stale`,
   `permission_blocked`, or `unavailable` posture plus separate membership/configuration
   supportability. It is non-authoritative and never creates a batch or report job; mutation
   repeats all scope and configuration checks,
11. archived generated-document metadata and controlled download routes are active under
   `/api/v1/documents/{document_id}` and `/api/v1/documents/{document_id}/download` as the
   product-facing boundary over `lotus-archive`,
12. domain-product catalog, dependency-graph, and live trust certification discovery routes are
   active under `/api/v1/domain-products`,
13. idea review queue/detail reads, candidate review-action, feedback, conversion-intent, and
   visible-render presentation-receipt recordings, plus governed AI-explanation generation
   passthrough and readiness reads (transport-only over the Lotus Idea generation surface:
   the explicit `EXPLANATION_UNAVAILABLE` degraded shape passes through verbatim, and a served
   explanation contradicted by its own proof — a disposition other than executed, an
   unaccepted verdict, an unconfirmed runtime execution or missing run id, a posture other
   than ready-for-advisor-review, an unpassed verifier, fallback use or a populated fallback
   reason, a fallback-only execution provenance, unrecorded AI lineage, blank text, mismatched
   evidence identity, or transit authority escalation — fails closed as a bounded 502) are active under `/api/v1/ideas/*`; Gateway forwards caller entitlement scope, optional
   trusted context, correlation/trace context, and for mutations `Idempotency-Key` plus optional
   causation. It preserves `lotus-idea` ranking, source refs, durable-storage posture, accepted or
   replayed source outcomes, and `supportedFeaturePromoted=false`. Review and conversion requests
   use the closed `IdeaReasonCode` vocabulary reconciled through
   `contracts/upstream/lotus-idea-reason-codes.v1.json`; feedback uses the separate governed
   `idea-feedback-taxonomy-v1` contract with no legacy aliases. Queue candidates require
   Idea-owned material/evidence versions so Workbench can bind visible-render receipts without
   reconstructing source state. Presentation receipt transport preserves Idea `201` accepted,
   `200` replayed, and allowlisted product-safe failure codes. It preserves Idea global rank
   independently from Workbench visible-set count and never derives, compares, or rewrites rank,
   count, digest, policy, version, or presentation time; queue reads never synthesize receipts.
   Gateway does not generate, rank, enrich, certify, authorize, or promote
   ideas locally. These BFF routes do not claim
   Workbench completion, data-product certification, downstream realization, execution, or client
   communication readiness,
14. upstream service consumption is classified under RFC-0082 in `docs/standards/RFC-0082-upstream-contract-family-map.md`,
15. lotus-core enforces fail-closed tenant admission at ingress: every protected Core call
   must carry `X-Tenant-Id` or Core rejects it 401 `TENANT_CONTEXT_REQUIRED`. Gateway
   satisfies this through one request-scoped mechanism: the correlation middleware captures
   the caller-presented `X-Tenant-Id` (only that header — never actor, role, application,
   entitlement claims, or credentials), and `build_core_upstream_headers` in
   `app/clients/upstream_headers.py` merges it EXCLUSIVELY on lotus-core query (READ)
   client calls. Core WRITES (the ingestion client behind the intake routes) never take
   the ambient fence — a caller-selected tenant must not scope a mutation into another
   tenant's partition. The intake routes admit the governed core.intake.write capability claim
   (403 intake_write_capability_required otherwise; services/intake_access_policy.py) plus
   the trusted caller context explicitly (routers/trusted_caller_context.py requires
   X-Actor-Id, X-Tenant-Id, X-Region; 400 missing_caller_context) and thread it as
   explicitly admitted caller_headers
   through the intake service into the ingestion client, so Core writes carry admitted —
   never ambient — tenant authority. The generic `build_upstream_headers` propagates nothing
   ambiently, deliberately: other upstream boundaries (for example the DPM/Manage
   read-authority forwarding) classify `X-Tenant-Id` itself as trusted authority, so an
   ambient merge there would turn an unadmitted request header into upstream scope. Never
   move the ambient tenant into the generic builder or a non-Core client; a route that
   resolves tenant scope through its own contract (platform capabilities) re-admits the
   resolved value via `admit_caller_tenant` so its Core calls and its response label carry
   one identical scope. A route's explicitly admitted `caller_headers` always override the
   ambient tenant,
16. the advisor-brief path now calls the explicit `lotus-ai` workflow-pack execution seam and consumes the returned run identity directly instead of inferring it from task audit request ids; it also preserves bounded RFC-0097 task-flow posture and replacement lineage from `lotus-ai` without making gateway the task-flow authority. When a deployment's lotus-ai runs `verified_service_jwt` caller trust, operators provision the ops-issued platform credential through `LOTUS_AI_CALLER_CREDENTIAL` (a secret; passed through `docker-compose.yml`, empty in header-trust environments) and Gateway attaches it as a Bearer token on every lotus-ai request — Gateway mints nothing and lotus-ai owns verification. The credential is read once at process start with no runtime refetch: rotation is platform-managed secret rotation plus a governed rolling Gateway restart before expiry, a rejected or expired credential fails closed at lotus-ai on exactly one request, and Gateway never downgrades from verified identity to bare caller headers,
17. RFC-0042 outcome-review AI narrative handoff now reads manage-owned
    `DpmOutcomeAiEvidenceInput` and executes `lotus-ai` `outcome_review_narrative.pack@v1` as
    `lotus-gateway`; manage remains outcome evidence and workflow authority, Gateway preserves
    Manage-owned `client_communication_boundary` posture when present, and Gateway does not
    generate narrative or client communication truth locally,
18. RFC-0038 DPM exception-summary AI handoff now reads manage-owned monitoring-exception evidence
    from the command-center exception queue and executes `lotus-ai`
    `dpm_exception_summary.pack@v1` as `lotus-gateway`; manage remains exception evidence
    authority, `lotus-ai` remains workflow-pack execution authority, and Gateway does not generate
    exception summaries locally, score PMs, approve trades, contact clients, route orders, or
    invent evidence,
19. RFC-0041 operations-handoff summary now reads manage-owned `DpmWaveReportInput` handoff
    evidence and executes `lotus-ai` `dpm_operations_handoff_summary.pack@v1` as
    `lotus-gateway`; manage remains wave and handoff evidence authority, `lotus-ai` remains
    workflow-pack execution authority, and Gateway does not generate handoff summaries locally,
    score PMs, approve trades, contact clients, route orders, claim external execution, or invent
    evidence,
20. RFC-0040 proof-pack AI PM memo handoff now reads manage-owned
    `DpmProofPackAiEvidenceInput` and executes `lotus-ai` `dpm_pm_memo.pack@v1` as
    `lotus-gateway`; manage remains proof-pack evidence authority, `lotus-ai` remains workflow-pack
    execution authority, and Gateway does not generate memos, score PMs, approve trades, contact
    clients, place orders, or invent evidence,
21. the six DPM AI handoff families publish one typed, product-safe
    `DpmAiWorkflowExecution` boundary. Gateway validates lotus-ai service, pack, version, caller,
    correlation, workflow-surface, authorization, eligibility, task, run, provider, and authority
    identities before returning source-owned runtime, review, supportability, evidence, artifact,
    freshness, replacement, and recovery posture. Contract drift fails closed with
    `AI_WORKFLOW_EXECUTION_CONTRACT_INVALID`; raw prompts, free-text model output, evidence
    attributes, storage locations, and unbounded provider telemetry are not exposed. Gateway does
    not infer that an accepted request has produced an available, reviewed, current, or
    client-usable output. Request construction and response validation share the immutable
    `explain.v1` / `EXPLANATION_ONLY` task contract, so internally consistent task or output-label
    drift also fails closed. Provider provenance is a closed `disabled|stub|openai|
    local_openai_compatible` vocabulary with deterministic modes requiring `stubbed=true` and
    live modes requiring `stubbed=false`; missing, unknown, or contradictory posture fails closed
    at the typed DPM boundary. Advisor Brief applies the same policy before publishing completed
    AI narrative output and downgrades unverifiable completion to source-backed partial posture
    without returning the unverified AI payload,
22. canonical local startup now depends on environment-scoped service identity and `--app-dir src`
    to avoid misleading Windows import-path failures.
23. RFC-0108 analytics UI observability is active for selected Workbench performance summary,
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
24. performance workspace-summary orchestration uses
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
25. performance `evidence_view` responses carry the inclusive `report_start_date` and
    `report_end_date` from the same Gateway-resolved workspace request context used for analytics.
    These boundaries are required across supported, partial, and unavailable evidence postures so
    Workbench can fail closed when calculation evidence does not match the advisor's review window;
    Workbench must not infer or reconstruct them.
26. the portfolio performance-snapshot route uses `report_start_date` and `report_end_date` as
    its canonical explicit-window query names, matching the summary, details, attribution-trend,
    and advisor-brief family. It retains `explicit_start_date` and `explicit_end_date` as
    deprecated one-release aliases; for each boundary, the canonical name wins when both are
    supplied.
27. selected proposal Risk and Impact evidence is a typed anti-corruption projection over one
    Advise detail read. Gateway centrally validates decision-status/top-level/action relationships,
    the gate-to-next-step matrix, compatible decision/workflow gates, and blocking-evidence
    posture. Contradictions fail closed; partial decision evidence cannot publish an executable
    workflow gate as ready, and incomplete blocking-gate reason evidence remains partial rather than
    being invented. The runtime pairing policy is loaded from the packaged Advise
    `proposal-decision-vocabulary.v1` snapshot under `src/app/contracts/upstream`; protected and
    scheduled CI reconcile it with the current producer artifact and report the producer Git blob
    revision. The source artifact governs pairings, while the stricter Gateway reason-evidence rule
    remains separate. Gateway does not invent progression or approval truth.
28. multi-source platform capability aggregation is active under `/api/v1/platform/capabilities`:
    Gateway aggregates lotus-core, lotus-performance, lotus-risk, lotus-advise, lotus-manage, and
    lotus-report integration capabilities into one contract for UI feature control, shell
    bootstrap, and workflow negotiation, fanning out concurrently with a bounded per-source
    timeout and returning partial-failure diagnostics instead of serially blocking the shell.
    The route admits exactly one tenant scope — the `tenantId` query selector and the
    `X-Tenant-Id` caller context must agree when both are presented, the governed default tenant
    applies only when neither is given, and the resolved scope is re-admitted via
    `admit_caller_tenant` so the response label and every tenant-aware source call carry one
    identical tenant (see the tenant-admission item above): Core-backed reads take the ambient
    Core-read fence and the analytics capability read receives the tenant selector its contract
    declares, while lotus-risk's `/integration/capabilities` route publishes service-level,
    tenant-agnostic capability truth and is deliberately called without tenant scope rather than
    inventing a selector its contract does not declare.

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
7. protected duplicate-code fallback when host selection differs
   `make duplicate-code-protected`
8. canonical local runtime
   `make run-canonical`
9. PR issue-lifecycle text guard (before creating or editing a PR)
   `$env:LOTUS_PR_TITLE='<title>'; $env:LOTUS_PR_BODY='<body>'; make pr-issue-lifecycle`

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
   `scripts/check_agent_quality_evidence.py`; it keeps the executable 315/49 refactor ratchet, the
    current evidence-selected `src/app/contracts/dpm_pm_operating_quality.py`
   hotspot, and durable
   scorecard/context guidance synchronized for future agent work,
6. proposal decision vocabulary governance is part of `make lint` through
   `scripts/check_proposal_decision_vocabulary.py`; the blocking target requires a current producer
   source and never falls back to self-comparison. Unit/contract and Docker parity validate the
   packaged artifact, while Remote Feature, PR Merge, Main Releasability, and scheduled drift lanes
   compare it with the current Advise source artifact. The explicit offline snapshot target is not
   producer-drift evidence,
7. `make pr-issue-lifecycle` is a fail-closed pre-PR guard and the Pull Request Merge Gate runs the
   same command against event title/body values held in environment variables. Intended automatic
   closure must be a standalone body line such as `Closes #123`; partial work uses `Keep #123 open`.
   Negated close/fix/resolve wording with an issue reference and malformed closing references are
   rejected, including GitHub issue URLs, because GitHub may still auto-close the issue. Opening,
   synchronizing, reopening, or
   editing a PR title/body starts a fresh merge-gate event, so lifecycle evidence cannot survive a
   later metadata change. A draft PR's initial `opened` event already supplies this evidence, so
   changing only draft state does not redundantly restart the heavy merge lane. A manual workflow
   dispatch has no PR text and receives a distinct `manual metadata unavailable` check name, so it
   cannot satisfy the protected lifecycle context,
8. PR auto-merge is rebase-only for linear history; `.github/workflows/pr-auto-merge.yml` uses
   `LOTUS_AUTOMERGE_TOKEN` and `gh pr merge --auto --rebase --delete-branch`, and skips cleanly
   with a warning when the token is absent so an authorized human or release actor can perform the
   rebase merge without leaving a false red helper check,
9. `.github/workflows/merged-pr-main-releasability.yml` dispatches `main-releasability.yml` after
   a pull request is merged into `main`, preserving exact-main release evidence for authorized
   human or release-actor merges as well as token-backed auto-merge; `main-releasability.yml` is
   intentionally `workflow_dispatch`-only so this dispatcher remains the single automatic
   post-merge path and does not duplicate a push-triggered release run; its concurrency identity is
   always the checked-out `github.sha`, while caller-supplied `expected_sha` remains validation-only,
   so malformed input and newer merges cannot cancel another revision's evidence,
10. `make demo-certification` is the current app-level Gateway demo-readiness command; it calls real
   FastAPI routes with deterministic synthetic upstream fixtures, writes
   `output/demo-certification/gateway-demo-certification.json`, and remains report-only in Quality
   Baseline until repeated low-noise evidence and exception policy justify blocking promotion,
11. `scripts/check_quality_baseline_ratchet.py` enforces no-new-regression thresholds from
   `quality/quality_ratchet.json`; every Quality Baseline run must publish current value, baseline,
   delta, threshold, and remediation evidence. Baseline updates auto-tighten only; any loosening
   requires per-metric `--allow-regression METRIC=VALUE --reason "..."` in a reviewed change.
   The current dependency-findings baseline is 21, banked from the measured post-#645 deptry
   improvement; a later run above 21 must fail the quality gate.
   The pinned `quality/package-lock.json` jscpd scan also ratchets production duplicate-code
   clone count, duplicated lines, duplicated percentage, and stable source-pair/normalised-
   fragment occurrence fingerprints with Python-version-independent AST scope context,
   canonical-source-side selection with reported column boundaries, literal-preserving
   normalization, stable f-string token-span normalization, and stable occurrence
   ordering; adjacent source edits and non-local scope-body edits must not invalidate unrelated
   clones, while same-scope relocation is an explicit identity trade-off. The checked-in baseline
   is generated and enforced for pull requests on the required Ubuntu/Node 20 Quality Baseline
   lane; that lane runs the detector twice and fails on normalized candidate-identity-set or
   aggregate-metric drift. Main Releasability independently runs the same blocking
   `make duplicate-code` target after exact-revision assertion and retains
   `main-duplicate-code-evidence`, so the reviewed baseline is proved again at the exact merged
   SHA. The image build, registry push, signing, and provenance job depends on this result, so a
   failing ratchet cannot publish release artifacts for the rejected revision. Cross-operating-
   system equivalence remains intentionally unclaimed rather than being hidden in a union baseline;
   a new clone, stale baseline fingerprint, or detector failure is a protected quality failure;
   reviewed baseline updates must bank removals before the improvement can be spent again. Hosts
   with different candidate selection use `make duplicate-code-protected`, which runs the pinned
   Linux/Node 20 image under a checkout-specific Compose project and removes only that project;
   it does not disturb the canonical Gateway runtime. The fallback mounts the checkout read-only at
   a dedicated source root; its writable dependency and output volumes are sibling roots rather
   than nested mounts below that read-only bind, which keeps Docker Desktop and Linux Compose
   topology valid. It keeps npm dependencies in a project-scoped volume and copies its scan report
   before teardown into a run-unique caller-created `output/duplicate-code-protected/` directory. This preserves
   diagnostics without leaving root-owned checkout artifacts. The checker reports `--update-baseline` as
   blocked when unexpected findings, metric regressions, or detector failures remain.
   Every report-producing quality log must also carry exactly one numeric
   `QUALITY_COMMAND_STATUS` marker from the producer exit status; missing, malformed, or duplicate
   markers are measurement failures, while non-zero status with reviewed baseline findings remains
   explicit debt evidence,
11. Quality Baseline uses the `pull_request` event targeting `main` as its sole authoritative
   automated feature-revision trigger; feature-branch pushes do not start a duplicate run. Its
   concurrency group uses the pull-request number to cancel stale synchronized revisions while
   manual dispatch uses a unique run ID, and the event matrix is documented in
   `docs/quality-baseline-event-matrix.md`,
12. Docker parity matters because the gateway is a live integration boundary,
13. Gateway Docker images are tagged with the Git SHA, stamped with non-secret build-time OCI
   labels, scanned with Trivy before any main-lane push, inventoried with an SBOM, and recorded in a
   release manifest. Main Releasability is the only lane that pushes to GHCR; it captures the
   digest after push, signs the digest-pinned image, creates provenance attestation evidence, and
   requires Kubernetes deployment by digest while preserving the same image for environment
   promotion,
14. `/version` exposes the same non-secret build and deployment metadata expected in release
    manifests: Git commit SHA, branch, build timestamp, repo URL, image digest, CI run ID, and
    version. Image digest is deployment/runtime metadata captured after push and must not be baked
    into Docker build args, ENV, or OCI labels as `unknown`,
15. README and wiki updates should preserve truthful endpoint-specific parameter conventions, and
   mixed query, body, or multipart shapes should be backed by executable examples in the wiki.
16. the Starlette TestClient dependency is test-only: the `dev` extra provides
    `httpx2>=2.12.0,<3.0.0`, and `scripts/check_testclient_dependency.py` is a hard gate against
    missing/outdated HTTPX2 or Starlette's legacy `httpx` fallback warning. The production-only
    `requirements-audit.txt` intentionally excludes HTTPX2 because the application image does not
    import TestClient.

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

Transaction temporal semantics are also source-owned and explicit at the Gateway boundary:
`transaction_date` is Core's transaction event timestamp for event-date filtering and ordering;
`settlement_date` is the separate optional settlement timestamp. Gateway normalizes both to UTC
and requires an ISO-8601 timezone-aware date-time, does not invent `booking_date`, and applies
inclusive UTC calendar-day windows as a Gateway-owned reporting convention. Core's current published
transaction contract defines the event/trade meaning and inclusive date-filter shape, but does not
establish UTC or a booking-centre-local timezone convention. Gateway therefore does not claim that
its UTC windows reproduce a Core source-local business date; valid non-UTC offsets can shift a row
across a Gateway reporting-period boundary. Missing, date-only, naive, malformed, or impossible
source timestamps fail closed with `502` code
`portfolio_transaction_source_contract_invalid`; Gateway does not emit partial malformed rows or
silently discard them. Valid timezone-aware source timestamps remain compatible. Workbench display,
consumer migration, and source-policy follow-up remain under parent issue #569 and child issue
#642. No database migration is required because this slice changes documentation and regression
coverage only.

Performance attribution level totals are also source-owned. Gateway preserves explicit numeric
zero, positive, and negative `levels[].totals.total_effect` values and publishes `null` when
`lotus-performance` omits the aggregate; it does not reconstruct the total from attribution rows.

Workbench risk summary and concentration responses include a typed `mandate_comparison` composed
from Manage-owned mandate, health, review-policy, and lineage evidence; Risk-owned tracking-error
and concentration measures; and the Core-owned cash measure already resolved by the Workbench
snapshot. Gateway may normalize percentage points to ratios and calculate signed presentation
headroom only from date- and basis-aligned source facts. Cash-band headroom is the distance to the
nearest approved boundary. Largest-position and largest-issuer constraints belong only to the
concentration response; issuer verdicts require complete source coverage. An omitted review cadence
remains absent rather than becoming a Gateway default. Gateway must not calculate mandate health,
invent a limit or cadence, blend source dates, accept cross-portfolio evidence, or publish a
conflicting verdict as within/breach. Manage's historical mandate/health selection contract is
tracked by `lotus-manage#639`; until it lands, historical risk reads preserve latest source dates
and report explicit mismatch posture.

The Workbench performance summary, details, attribution-trend, and advisor-brief routes accept
optional `as_of_date` and `reporting_currency` controls. Gateway forwards the selected reporting
currency to `lotus-performance`, uses the requested as-of date as the report-window end when an
explicit end date is absent, and publishes an effective top-level `as_of_date` separately from
the caller's `requested_as_of_date`, alongside requested versus effective currency fields plus
typed currency state. Advisor-brief read and review-action routes reuse the shared performance
workspace context and preserve selected controls in source links. This does not promote workspace
capabilities, claim source-applied currency evidence, or add lookup-backed currency validation;
those remain separate follow-up slices under GitHub issue #572.
When the summary source rejects a requested currency, the Gateway publishes a typed
lotus-performance partial failure, resolves effective currency back to the portfolio base, and
publishes `reporting_currency_state="rejected"` only when the source returns a typed
`VALIDATION_ERROR` whose validation location names a currency control. Exceptions, timeouts,
unrelated validation failures, and other HTTP failures use the base currency with
`reporting_currency_state="unavailable"`; human-readable error text is not a classification
signal. A successful summary currently uses `accepted_unverified` until lotus-performance
publishes applied-currency evidence (tracked by lotus-performance#470). Internal summary and
benchmark pipeline parameters use `reporting_currency` to distinguish the requested/source
reporting unit from portfolio base currency.

1. Windows startup can serve a misleading health-only process if `--app-dir src` is omitted,
2. stale thin-pass-through routes should be retired as better experience contracts replace them,
3. gateway fixes should not smuggle domain logic out of authoritative upstream services,
4. reporting query, cashflow projection, projected summary, and benchmark catalog upstream calls remain RFC-0082 watchlist surfaces,
5. integration drift is most dangerous here because it directly affects the product UI,
6. an omitted optional Workbench `as_of_date` remains omitted from caller context; Gateway first
   asks lotus-core support overview for the latest governed business date, uses that date for the
   required snapshot query, and aligns date-dependent enrichment to the snapshot-confirmed date.
   A host-date fallback may satisfy Core's required query shape but is never published as business
   truth,
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
    validates launch, retirement, supersession, approval-decision, assignment-action,
    assignment-task, task-transition, and maker-checker request shape and bounded vocabulary with
    distinct closed OpenAPI schemas before forwarding, while leaving command eligibility and state
    transition rules to `lotus-manage`;
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

Scope, admission, cache, and retry invariants delivered by the 2026-09-05 completion campaign
(gateway PRs #724–#728). Preserve these when touching their owners:

1. Report-job search is fenced by the admitted caller scope in
   `services/reporting_search_scope.py`: the admitted `X-Tenant-Id`/`X-Region` are always sent
   upstream, a conflicting supplied `tenantId`/`region` filter is a bounded `400` before any
   source call, and the applied-filter echo plus every returned row is validated before
   publication (`502` on violation). Cross-tenant reads need a separately authorized contract,
   never a filter value. The producer-side half is lotus-report#292; gateway#718 tracks it.
2. Reporting source successes are admitted semantically by
   `services/reporting_response_admission.py`: each query and submission consumer binds exactly
   the identities its source contract exposes — requested job or snapshot, per-row event and
   lineage identities, echoed submission idempotency key, and the handle↔status-URL job
   relationship. A well-shaped answer for a different identity is
   `502 report_job_source_identity_mismatch`; a malformed success is
   `502 report_job_source_contract_invalid`, never an escaping validation error.
3. `services/async_ttl_cache.py` fills own their completion through a synchronous done-callback:
   waiters await a shielded view, so one waiter's cancellation never cancels shared work; a
   failed or cancelled fill leaves its key recoverable; `clear`/`discard`/`set` detach in-flight
   fills so a stale fill can never refill an invalidated generation or overwrite a newer value.
4. AI mutations obey producer replay contracts (`clients/http_retry_policy.py`): ambiguous
   response losses (read/write/close failures, remote-protocol errors, read/write timeouts) are
   never retried automatically without a replay identity. `execute_workflow_pack` mints one
   `idempotency_key` per logical execution and reuses it across transport attempts; review
   actions stop on ambiguous loss and do not follow redirects. Correlation ids are tracing,
   never replay identity. The inbound seam — a consumer retrying the Gateway request mints a new
   key — is recorded on gateway#726 and stays open pending an inbound idempotency contract.
5. Advisor Book value evidence must be internally consistent
   (`services/advisor_book_value_facts.py`): a member resolved off the cohort as-of basis, or a
   `COMPLETE` aggregate over an untrustworthy member, degrades the value block through the typed
   contract-invalid refusal while rows and action facts survive; carry-forward `snapshot_date`
   and `MEASURED_ZERO` facts are preserved, and Gateway never recomputes Core's totals.
6. Mutation idempotency and caller-context admission are route-declared, never universal: a
   retry replays only when the request carries the replay identity its route declares — the
   `Idempotency-Key` header on most mutation families (required on some, accepted optionally on
   others: execution handoff/update, memo review and AI commentary, report-package
   request/event, narrative review), the nonstandard optional `X-Idempotency-Key` header on the
   intake portfolio-bundle route, a required `idempotency_key` request-body field on the DPM
   construction, proof-pack, and wave creation mutations (their other lifecycle mutations, such
   as alternative-set selection, declare none and are not replay-safe to retry), and none at all
   on a few (proposal report requests take no key and are not replay-safe to retry). Read the
   generated OpenAPI together with each route's declared error responses: the reporting
   portfolio-review and outcome-review submissions mark the header optional in the schema yet
   enforce it in the service with the declared 400 missing_idempotency_key, so the schema alone
   understates a requirement the error contract declares.
7. Canonical `gateway.dev.lotus` addressing exists only while the optional platform ingress is
   active; `make run-canonical` binds Uvicorn to `0.0.0.0:8111` (reachable on all local
   interfaces — `127.0.0.1:8111` is the conventional debugging URL, not the bind scope) and
   does not provision that hostname.

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
