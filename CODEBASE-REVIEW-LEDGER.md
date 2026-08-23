# Codebase Review Ledger

Last updated: 2026-08-23
Repository: `lotus-gateway`
Reference branch: `origin/main`

### Batch 3B — latest source-confirmed Workbench date for omitted queries (#595)

- Objective: make no-query Workbench overview and portfolio-360 requests resolve the latest
  source-owned business date instead of querying Core with the Gateway host date as if it were
  portfolio truth.
- Change: when the caller omits `as_of_date`, Gateway reads Core support overview `business_date`
  as the candidate, uses it for Core's required snapshot request, and publishes the date only
  when the snapshot returns matching top-level `freshness_status=CURRENT` evidence. A failed,
  missing, invalid, conflicting, or non-current result remains `unavailable`; date-dependent
  enrichment is withheld. Explicit requested dates retain their existing query and response
  semantics.
- Regression proof: context tests prove no-query support-date discovery, exact snapshot propagation,
  and fail-closed support failure; router integration proves the canonical no-query 360 path
  confirms `2026-04-10` with `requested_as_of_date=null`; existing explicit-date and downstream
  Workbench suites remain covered.
- Compatibility: the optional query remains optional and response fields remain additive. The
  internal host-date fallback exists only because Core's snapshot request currently requires a
  date and is never published or used for enrichment. No Core schema, migration, or Workbench UI
  change is included.
- Documentation decision: supported-features, API-surface wiki, repository context, RFC-0082
  upstream mapping, and this ledger change because no-query date resolution is now implementation
  backed. Wiki publication and strict parity are required after merge.
- Deferred boundary: latest-date discovery remains Gateway orchestration over Core's support
  contract; Core snapshot freshness remains business-date authority. Workbench rendering remains
  downstream work tracked by `lotus-workbench#814`.

### Batch 3A — source-confirmed Workbench snapshot dates (#592)

- Objective: stop Workbench overview and portfolio-360 from publishing the Core request-bound
  date or Gateway host date as an effective portfolio business date.
- Change: the shared Core snapshot mapping now uses top-level `freshness_status=CURRENT` and the
  valid top-level `as_of_date` as business-date authority for an explicit request. It preserves
  requested and effective dates separately and publishes the typed `as_of_state` values
  `confirmed`, `accepted_unverified`, or `unavailable`. Nested `freshness.snapshot_timestamp` and
  `snapshot_epoch` remain lineage only. The legacy top-level `as_of_date` is now the effective date
  or `null`; when no date is requested and Core cannot resolve a latest business date, Gateway
  reports `unavailable` and withholds date-dependent enrichment. Both Workbench snapshot routes
  accept the same optional requested date control.
- Regression proof: context and portfolio-360 tests cover the canonical Core pair: requested
  `2026-04-10` with top-level `CURRENT` and requested `2026-08-23` with top-level `UNAVAILABLE`,
  while both rows carry the same nested snapshot timestamp. Tests also prove omitted-date requests
  cannot turn a host-date query bound into `confirmed`, and unavailable dates withhold embedded
  performance and rebalance snapshots. Router integration covers query propagation and the
  additive response fields; OpenAPI contract tests pin both route parameters and response
  metadata; composed performance workspace coverage proves downstream consumers fail closed when
  no usable date exists.
- Compatibility: query names and existing financial fields remain available. New temporal fields
  are additive. The legacy `as_of_date` meaning is intentionally corrected and is nullable when
  source evidence is unavailable; consumers must inspect `as_of_state` before presenting a date as
  confirmed. Legacy incomplete Core payloads remain usable only as `accepted_unverified`. Composed
  performance workspace consumers no longer fabricate a reference date when this evidence is
  unavailable; they return typed `WORKBENCH_AS_OF_DATE_UNAVAILABLE` unless an explicit report end
  was supplied.
- Documentation decision: supported-features, API-surface wiki, and this ledger change because
  the public date contract changed. No migration, central context, skill, or demo-pack change is
  required. Wiki publication and strict parity are required after merge.
- Deferred boundary: Workbench rendering of unavailable dates remains #814; mandate identity and
  display-name enrichment remains #591; performance date semantics remains #572. No upstream Core
  schema change is included.

## Performance Summary Review Controls

- Scope: bounded Batches 2A and 2B of GitHub issue #572, limited to the Workbench performance summary
  route and its existing Gateway-to-`lotus-performance` request path.
- Objective: expose optional `as_of_date` and `reporting_currency` controls without allowing the
  summary route to pin currency to portfolio base or echo the service clock as review truth.
- Change: the route validates ISO-shaped query inputs, normalizes currency codes to uppercase,
  forwards the effective currency through the existing summary cache/client boundary, uses the
  requested as-of date as the report-window end when no explicit end is supplied, and publishes
  requested/effective date and currency fields. Explicit report windows remain authoritative.
- Regression proof: service tests cover forwarding and response publication plus explicit-window
  precedence; router integration coverage proves query parsing and uppercase normalization; the
  existing summary, context, response, projection, dependency, and Workbench suites remain green.
- Compatibility: omitted controls preserve the existing base-currency/default-window request
  path, while the summary `as_of_date` now reflects the resolved report-window date rather than
  the Workbench overview service clock. Details, attribution trend, advisor brief, currency
  lookup validation, capability promotion, and downstream Workbench enablement are explicitly
  deferred follow-ups under #572.
- Documentation decision: repository context, API-surface wiki, supported-features wiki, and
  this ledger change because the summary contract and support boundary changed. No central
  platform context or skill change is required.
- Follow-up: complete the remaining #572 route family only after the summary slice is merged and
  its exact-mainline/live evidence is recorded; do not promote workspace capabilities from this
  bounded slice alone.

### Batch 2D — details review controls and single summary classification (#572)

- Objective: make the Workbench performance details route publish truthful review-date and
  reporting-currency context using the same bounded semantics as summary.
- Change: details accepts and forwards optional `as_of_date` and `reporting_currency` controls,
  publishes requested/effective date and currency fields plus `reporting_currency_state`, and
  preserves portfolio-base fallback for rejected, unavailable, empty, or malformed summaries.
  Reporting-currency outcome classification now belongs to the summary parser as reusable
  `classify_reporting_currency_outcome(result, requested_period)`; the response assembler projects
  the parser's state rather than evaluating the raw result again.
- Regression proof: parser coverage proves empty requested-period summaries are `unavailable`;
  response tests prove precomputed-state projection; service and router tests prove forwarding,
  uppercase normalization, explicit-window precedence, additive details fields, and fallback;
  OpenAPI coverage proves the new query and response contract fields.
- Compatibility: existing details fields, query names, omitted-parameter behavior, and capability
  posture remain unchanged. The new controls and response fields are additive. This slice does
  not claim source-applied currency evidence or promote trend, advisor-brief, currency-lookup,
  as-of-after-last-observation, or workspace-wide capabilities.
- Documentation decision: `docs/supported-features.md`, `wiki/Supported-Features.md`,
  `wiki/API-Surface.md`, and this ledger change because details support and classifier ownership
  changed. No central platform context or skill change is required.

### Batch 2F — terminal HTTPX request-error taxonomy (#538)

- Objective: stop permanent HTTPX request/protocol errors from being retried as transient transport
  failures until the analytics result deadline.
- Change: the shared retry-policy owner now allow-lists timeouts (when enabled), network errors,
  and remote protocol disconnects. `TooManyRedirects`, `UnsupportedProtocol`,
  `LocalProtocolError`, and unclassified `RequestError` values are terminal; typed JSON outcomes
  publish `TERMINAL_REQUEST_ERROR`, so the analytics polling boundary returns the communication
  failure immediately. The binary transport inherits the same shared policy rather than retaining
  a divergent permanent-error retry path.
- Regression proof: HTTPX policy tests cover allow-listed network/remote-protocol errors and
  terminal redirect, unsupported-protocol, local-protocol, and unclassified request errors;
  analytics polling proves terminal failure does not become deadline exhaustion. Existing timeout,
  status-retry, JSON, binary, and remote-protocol tests remain green.
- Compatibility: public response shapes and API routes are unchanged. Timeout and genuinely
  transient network behavior remain bounded; only permanent request-construction/protocol errors
  stop retrying. No migration, central context, or skill change is required.
- Documentation decision: `docs/standards/scalability-availability.md` and
  `wiki/Validation-and-CI.md` now state the explicit retry taxonomy; wiki publication and strict
  parity are required after merge.

### Batch 2G — attribution-trend review controls (#572)

- Objective: make the Workbench attribution-trend route participate in the same review-date and
  reporting-currency context already supported by summary and details.
- Change: attribution-trend accepts optional `as_of_date` and `reporting_currency`, preserves
  explicit `report_end_date` precedence, forwards requested currency to each bounded
  `lotus-performance` attribution request, and publishes requested/effective date and currency
  fields plus `reporting_currency_state`. A shared currency-rejection predicate and a trend-specific
  usable-period classifier prevent request echoes from claiming source evidence; typed rejection and
  no-usable-period outcomes fall back to the portfolio base currency.
- Regression proof: focused parser/service/router/client tests cover successful forwarding,
  uppercase query normalization, explicit-window precedence, typed currency rejection, unavailable
  periods, response context, OpenAPI fields, and omission-preserving upstream payloads.
- Compatibility: omitted parameters keep the prior attribution payload; new response fields are
  additive. Partial period failures remain visible. No capability promotion, advisor-brief,
  currency-catalog validation, or as-of-after-last-observation mapping is included.
- Documentation decision: supported-features, demo, API-surface wiki, and this ledger change because
  the route's supported controls and response contract changed. No migration or central context/skill
  change is needed.

### Batch 2E — authoritative performance horizon windows (#551)

- Objective: remove silent January-1/YTD fallback from accepted performance horizon resolution and
  make the Gateway, source request, response, and evidence windows describe the same inclusive
  observations.
- Change: the shared performance-window resolver now validates the closed Gateway vocabulary
  (`MTD`, `QTD`, `YTD`, `1Y`, `2Y`, `3Y`, `5Y`, `10Y`, `SI`, `EXPLICIT`), resolves `2Y` and `10Y`
  with the existing trailing-year boundary rule, and resolves `SI` from Core's
  `PortfolioAnalyticsReference.portfolio_open_date`. Long and since-inception workspace requests
  are sent as explicit windows so the Gateway boundary is the one reused by summary, details,
  composed contribution/attribution requests, response context, and evidence. Unknown periods,
  malformed dates, missing/invalid inception evidence, and `EXPLICIT` without a start fail closed
  with typed 422 errors. Compact horizon comparison rejects long periods rather than returning
  standard rows under a mismatched top-level window.
- Regression proof: focused controls/reference/service tests cover long-horizon boundaries, leap
  semantics, source-owned SI resolution, missing/invalid inception, unknown/malformed requests,
  summary/detail/evidence/upstream alignment, and horizon-comparison rejection. Workbench OpenAPI
  contract assertions pin the published period vocabulary and 422 behavior; 105 focused unit,
  contract, and router tests pass.
- Compatibility: canonical supported periods remain available. Values that previously fell through
  to fabricated YTD semantics now return a typed 422; this is an intentional correctness boundary.
  Performance calculation methodology and upstream ownership remain unchanged. No migration,
  central context, or skill change is required. No Workbench UI code changed; the canonical demo
  continues to use YTD and existing runtime proof remains applicable.
- Documentation decision: `docs/supported-features.md`, `wiki/Supported-Features.md`,
  `wiki/API-Surface.md`, and this ledger change because the accepted period contract and failure
  behavior changed. Wiki publication and strict parity are required after merge.
- Deferred boundary: source end-after-last-observation classification remains owned by
  `lotus-performance#469`; applied currency evidence remains `lotus-performance#470`; neither is
  conflated with this start-window fix.

### Batch 2B — upstream rejection truth and currency naming

- Objective: prevent a rejected reporting-currency request from being published as an effective
  currency, and remove the overloaded `portfolio_currency` name from the summary/benchmark
  pipeline.
- Change: summary response assembly initially fell back to the portfolio base currency only when
  the upstream error payload explicitly identified an unsupported currency; Batch 2C below
  narrows that classifier to typed validation locations and makes all failed-summary currency
  posture explicit. Declared response-context attributes replace defensive `getattr` calls, and
  summary, horizon, attribution-trend, benchmark, and cache request parameters use
  `reporting_currency` internally without changing public API fields.
- Regression proof: focused performance workspace tests include a 422 unsupported-currency case
  asserting requested `SGD`, effective base `USD`, and `HTTP_422` lotus-performance failure;
  65 focused tests pass, plus MyPy on 9 changed source modules.
- Compatibility: public query fields remain unchanged. Batch 2C adds the response field
  `reporting_currency_state` with a default and keeps `effective_reporting_currency` string-valued;
  failed summaries use portfolio base rather than publishing a requested currency. Deferred
  details, attribution trend, advisor brief, lookup validation, capability promotion, and
  as-of-after-last-observation mapping remain under #572.
- Documentation decision: repository context, this ledger, API-surface wiki, and supported-
  features wiki require updates; no central platform context or skill change is required.

### Batch 2C — typed summary currency failure state (#579)

- Objective: prevent a missing performance summary from publishing the requested reporting currency
  as effective, while distinguishing typed currency rejection from other unavailable outcomes.
- Change: summary response assembly now publishes additive `reporting_currency_state` values:
  `accepted_unverified` for a structurally successful summary, `rejected` only for a 4xx
  `VALIDATION_ERROR` with a `validation_errors[].loc` entry naming `report_ccy`, `currency_mode`,
  `fx`, or `reporting_currency`, and `unavailable` for exceptions, timeouts, unrelated validation
  failures, malformed results, and other HTTP failures. All non-success states use portfolio base
  currency for the existing string-valued effective field. No human-readable payload text is
  searched.
- Regression proof: table-driven unit coverage covers success, typed currency rejection, unrelated
  validation, 503, exception, and text-only rejection; OpenAPI integration coverage asserts the
  state enum. Focused response/router tests and contract tests pass.
- Compatibility: query fields and the existing string-valued effective currency remain present;
  the new state field is additive with a safe default. `accepted_unverified` remains deliberate
  until lotus-performance#470 publishes applied-currency evidence.
- Documentation decision: repository context, this ledger, API-surface wiki, and supported-features
  wiki record the state vocabulary; no central platform context or skill change was needed.
- Quality-bar follow-forward: the currency assessment now lives in a dedicated service module and
  requires parser-aligned portfolio TWR or money-weighted figures before publishing
  `accepted_unverified`; a nonempty but malformed period payload remains `unavailable`. A route
  integration regression covers `/performance/summary?reporting_currency=SGD` with a stubbed 503,
  asserting base-currency fallback and the typed `HTTP_503` partial failure. No public contract or
  wiki truth changed, so no additional wiki update is required for this follow-forward slice.
- CI audit: the broader quality baseline remains a separately tracked governance gap in #581;
  duplicate Quality Baseline execution remains separately tracked in #523. Neither is mixed into
  this bounded currency fix.

### CI quality ratchet slice — #581

- Objective: preserve the fast PR/Main gates while making the broader Quality Baseline fail on
  measurable regression rather than treating every report as advisory output.
- Change: `scripts/check_quality_baseline_ratchet.py` reads checked-in metric policies and the
  deterministic baseline logs, reports current value, baseline, delta, threshold, and remediation,
  and fails on a new complexity, architecture, dead-code, dependency, security, documentation,
  OpenAPI, or coverage regression. `--update-baseline` is explicit and intended only for a reviewed
  baseline change; CI never updates the baseline automatically.
- Current ratchet: coverage 94.77% minimum; architecture import failures <=11; Xenon blocks <=2;
  Vulture findings <=24; Deptry findings <=48; security severity counts at Undefined 0, Low <=2,
  Medium <=1, and High 0; Interrogate >=1.6%; and Spectral problems <=4. Existing known findings
  remain visible and are not hidden or weakened.
- Compatibility: application runtime, public API, schemas, migrations, and upstream contracts are
  unchanged. The change tightens CI behavior: a quality-baseline metric regression blocks that
  workflow and reports the violating metric and remediation command.
- Tests: deterministic unit coverage proves threshold pass, regression failure, and explicit
  baseline-update behavior; quality artifact validation requires the ratchet evidence log. Baseline
  updates auto-tighten only; loosening requires named `--allow-regression METRIC=VALUE` and a
  non-empty `--reason`.
- Follow-up: #523 remains the independent duplicate-run/concurrency slice. Promotion of individual
  advisory findings to clean gates remains a future bounded slice after their baseline issues are
  remediated; this ratchet prevents those findings from increasing meanwhile.

### Quality Baseline event deduplication slice — #523

- Objective: retain every Quality Baseline quality step and protected PR check while ensuring a
  feature revision is analyzed by one authoritative automated event.
- Change: removed the non-main `push` trigger from `.github/workflows/quality-baseline.yml`; the
  `pull_request` event targeting `main` owns feature-revision evidence, and `workflow_dispatch`
  remains available for explicit operator revalidation. Concurrency now keys pull-request runs by
  PR number to cancel stale synchronized revisions; manual runs use a unique run ID.
- Measurable improvement: a feature push before PR creation no longer launches a duplicate quality
  run; PR creation/synchronization produces one run per head SHA, and a new commit produces one run
  for the new SHA. The event matrix is durable in `docs/quality-baseline-event-matrix.md`.
- Compatibility: application runtime, public API, schemas, migrations, thresholds, artifacts, and
  ratchet behavior are unchanged. Only CI scheduling changes; manual dispatch and the protected
  `Quality Baseline / Ratcheted Trend Gate` remain available.
- Regression proof: workflow tests pin the authoritative event set, protected job name, stable
  pull-request concurrency, isolated manual dispatch, and stale-run cancellation. Focused
  validation also covers the complete artifact and ratchet contract.
- Documentation decision: repository context, CI quality gates, operations guidance, authored wiki,
  and the event-matrix runbook change because CI trigger semantics and operator expectations changed.

### CI-local Compose isolation slice — #521

- Objective: prevent repository-native CI-local cleanup from stopping a Gateway container owned by
  the active product Compose runtime.
- Finding: product and CI-local Compose files inherited the same directory project identity, so
  `down -v --remove-orphans` could classify the product service as an orphan and remove it.
- Change: `make ci-local-docker` and `make ci-local-docker-down` now use the same stable,
  checkout-specific project identity derived by `scripts/ci_local_compose_project.py`.
  `CI_LOCAL_COMPOSE_PROJECT` supports a caller-supplied unique override. Product Compose remains on
  its default identity; CI-local cleanup is scoped to CI-owned resources without cross-checkout
  collisions.
- Compatibility: no application/API/schema/migration or runtime service behavior changes. The
  operational compatibility improvement is that shared Gateway runtime containers remain outside
  CI-local cleanup scope while CI-local volumes, networks, and containers remain removable.
- Regression proof: the Docker Compose Makefile contract tests pin symmetric project-name use,
  stable same-checkout naming, distinct checkout naming, and rejection of the unscoped cleanup
  command. The PR/main Docker parity lane remains the runtime validation path; operator guidance
  requires verifying the shared Gateway health after cleanup.
- Documentation decision: operations runbook, authored wiki, and this ledger change because the
  Compose ownership and cleanup safety contract changed.

## Attribution Level Aggregate Source Authority

- Scope: GitHub issue #506, the performance attribution level mapper and its Workbench-facing
  contract.
- Finding: `_build_attribution_levels` converted an omitted or null source
  `levels[].totals.total_effect` into numeric `0.0`, conflating absent evidence with a legitimate
  zero and violating the Gateway source-authority boundary.
- Change: `AttributionLevelView.total_effect_pct` is nullable and the mapper preserves the
  quantized source value directly. The sibling attribution-trend cumulative mapper becomes
  unavailable when a contributing source total is missing. Gateway does not sum rows or otherwise
  reconstruct an absent aggregate.
- Regression proof: table-driven unit tests cover missing, null, explicit zero, positive, and
  negative totals and include a row whose value differs from the level total to prove no fallback
  reconstruction. Trend tests prove a missing period total does not become a numeric cumulative
  value. OpenAPI integration coverage proves the response properties are nullable and documents
  the missing-source behavior.
- Compatibility: explicit numeric totals are unchanged; only a previously fabricated zero becomes
  `null` when the source aggregate is absent.
- Documentation decision: repository context, API-surface wiki, supported-features wiki, and this
  ledger change because the public nullable contract and source-authority failure posture changed.
  No central platform context or skill change is required.
- Follow-up: Workbench consumer compatibility and canonical populated proof remain downstream
  validation concerns owned by their existing issues; this slice does not change attribution
  methodology or UI behavior.

## DPM Mutation And AI Response Trust Boundaries

- Scope: GitHub issues #524 and #525, discovered while producing canonical live evidence for
  Workbench issue `sgajbi/lotus-workbench#528` and reviewing the late comment on Gateway PR #522.
- Source authority: authenticated product callers own their actor, tenant, role, and optional
  operating-region audit identity. Gateway owns its service identity and the exact `manage.write`
  workload capability. `lotus-ai` owns workflow execution, while Gateway owns the bounded
  request/response contract that permits a DPM explanation result to reach Workbench.
- Findings: Gateway-to-Manage mutations did not carry a Gateway-owned workload identity after
  Manage enabled enterprise write authorization, so canonical DPM actions failed with `403`.
  Separately, the DPM AI validator checked internal task/label consistency but accepted a
  consistently wrong task identity or output-use label.
- Change: one request-scoped mutation-authority dependency now covers every DPM `POST`, `PUT`,
  `PATCH`, and `DELETE` route. It validates caller audit identity, strips caller-supplied authority,
  and derives only `X-Service-Identity: lotus-gateway` plus `X-Capabilities: manage.write` for the
  Manage call; reads remain unprivileged. One immutable DPM explanation task contract now drives
  both lotus-ai request construction and response validation, pinning `explain.v1` and
  `EXPLANATION_ONLY` across all six handoff families.
- Failure posture: missing or malformed DPM mutation caller identity fails before Manage with a
  stable product-safe error. A mutation outside the request authority scope fails closed inside
  the client. Consistent lotus-ai task or output-label drift returns
  `AI_WORKFLOW_EXECUTION_CONTRACT_INVALID` without structured-output leakage.
- Regression proof: 234 focused authority/client/router tests cover every registered DPM mutation,
  OpenAPI caller-header publication, exact upstream workload authority, hostile header
  replacement, missing/invalid context, request-scope cleanup, and least-privilege reads. Another
  53 focused AI contract tests cover every workflow family and consistent task/label drift. Ruff,
  formatting, and touched-source MyPy are green; full and container/live evidence is recorded on
  the issues before merge.
- Repeatable rule: service-to-service authority must be derived at the closest trusted outbound
  boundary, remain request-scoped, and preserve the human caller separately. A response validator
  must bind internally consistent source fields to the contract actually requested, not merely to
  one another.
- Documentation decision: README, RFC implementation evidence, repository context, API examples,
  operations guidance, security guidance, and authored wiki truth change because the public caller
  contract and operator failure posture changed. No central platform architecture or skill routing
  changed.
- Independent follow-up: #523 owns duplicate Quality Baseline execution and is not claimed here.

## Typed DPM AI Workflow Execution Boundary

- Scope: GitHub issue #520, discovered while preparing Workbench issue #528 to extend governed AI
  disclosure across six DPM workflow outputs.
- Source authority: `lotus-ai` owns workflow-pack eligibility, execution, run, review,
  supportability, provider, evidence, artifact, freshness, supersession, replacement, and recovery
  truth; `lotus-manage` owns consequence-bearing DPM workflow and source evidence. Gateway owns a
  bounded product-facing validation and projection boundary only.
- Finding: all six response contracts promised workflow execution and review evidence but exposed
  `data` as `dict[str, object]`; reduced and inconsistent fixtures allowed source-contract drift and
  left Workbench unable to distinguish request acceptance from output, evidence, review,
  supportability, freshness, or client-use posture.
- Change: introduced reusable `DpmAiWorkflowExecution` models and one expectation-driven validator
  for proof-pack memo, wave memo, operations handoff, exception summary, outcome-review narrative,
  and PM-quality summary routes. The validator binds service, pack, version, registration, caller,
  authenticated identity, correlation, workflow surface, authority owner, task, run, provider, and
  eligibility identities before returning the typed projection.
- Measured modularity: the contract is separated into audit/evidence (115 lines), run/lineage (171
  lines), and execution-envelope (135 lines) modules. The proof-pack facade is reduced from the
  gate-rejected 325 lines to 178 lines by extracting its AI handoff; all production files remain
  below the enforced 316-line file and 49-line function ceilings.
- Projection safety: governed structured task output, runtime/review/supportability posture,
  bounded evidence descriptors, safe artifact metadata, timestamps, and replacement/recovery
  lineage are retained. Raw prompt selection, generated message/output preview, evidence
  attributes, storage locations, creator fields, and unbounded control/provider narratives are
  stripped. Invalid source output returns product-safe
  `AI_WORKFLOW_EXECUTION_CONTRACT_INVALID` without payload or validation-detail leakage.
- Regression proof: one versioned complete lotus-ai fixture builder serves all six families; unit,
  contract, and integration tests cover six success paths, live and stub execution,
  review-required, historical/superseded/replacement, recovery lineage, raw-field stripping,
  identity mismatch, missing fields, authorization failure, and route-level product-safe `502`
  behavior. The execution-envelope and validator modules have 100% line and branch coverage.
- Repeatable rule: a source-published generated-output envelope must be consumer-typed, identity
  bound, and allowlist-projected at the Gateway boundary. A generic dictionary, HTTP success, or
  request id is not evidence that generated output is safe, available, reviewed, current, or fit
  for client use.
- Documentation decision: repository context and the authored supported-features wiki are updated
  because the public Gateway contract and operator-visible failure posture changed. Central skill
  routing and platform architecture did not change, so no central context or skill edit is needed.
- Follow-up: containerized validation exposed that the CI-local cleanup target can remove the
  active product Gateway container because both compose files share a default project identity.
  The runtime was restored healthy immediately and independent operability hardening is durable in
  #521; it is not claimed by #520.

## Authenticated Advisor Own-Book Experience Contract

- Scope: GitHub issue #500, raised from Workbench portfolio-selector discovery because the global
  portfolio catalogue cannot prove an authenticated advisor's book of business.
- Source authority: `lotus-core` owns `PortfolioManagerBookMembership:v1`, effective portfolio
  membership, assignment basis, source record evidence, freshness, content identity, and lineage.
  Gateway owns the bounded product-facing own-book projection and caller-context enforcement.
- Change: added a path-safe Core control-plane client call, strict source model, focused
  client protocol, own-book mapping service, cached factory/provider, executable response example,
  and `GET /api/v1/advisor-book/portfolios` with explicit business date, exact filters,
  deterministic sort, and bounded paging.
- Security and truth boundary: manager identity comes only from trusted `X-Actor-Id`; exact
  supported role plus `advisor.book.read`, tenant, region, and booking centre are required. A
  manager, date, booking-centre, non-null tenant, count, duplicate-row, or source-contract mismatch
  fails closed. Null Core tenant scope and legacy advisor projection remain explicit degraded
  posture. The route never falls back to the global portfolio catalogue.
- Measured signal: the feature remains bounded to dedicated `advisor_book` modules. The mapping
  service is 241 lines, supportability policy is 93 lines, router is 104 lines, and request-input
  module is 114 lines, all below the current 316-line source-file quality ceiling; every function
  is within the 49-line ceiling. Existing client, service, router, and provider ownership guards
  remain green.
- Proof: focused client, source-contract, access-policy, service, provider, integration-router,
  OpenAPI, and layer-boundary tests cover path encoding, exact caller capability, missing context,
  cross-scope rejection, cross-tenant denial, duplicate evidence, explicit empty, filter-empty,
  tenant degradation, legacy projection, upstream failure, deterministic paging, and no
  browser-owned advisor identity. Repository-wide gates are recorded on issue #500 before PR
  review.
- Durable documentation: supported-feature source, wiki supported features/API examples,
  RFC-0082 upstream-family classification, README parameter conventions, and repository context
  are updated in the same slice.
- Existing follow-up owners: Gateway/Workbench #436 owns production authenticated principal
  resolution; Core #513 owns richer effective-dated relationship roles until its local work is
  packaged, reviewed, merged, and exact-main validated. No duplicate downstream issue was opened.
- No-claim boundary: team, delegated, supervisory, household, assets-under-management, attention,
  suitability, recommendation, client communication, order, and execution coverage remain out of
  scope unless separately sourced and proven.

## Capability Contract Issue Triage

- Scope: GitHub issue triage for open Gateway integration-contract findings affecting platform
  capability composition, reporting capabilities, proposal upstream ownership, and foundation
  cash totals.
- Existing owner pattern: Gateway owns the BFF composition contract and public camelCase
  `/api/v1/platform/capabilities` API; source services own their direct integration capability
  contracts. Gateway must call source-owned capability endpoints with source-owned query
  vocabulary while preserving the public BFF shape for Workbench consumers.
- Change: updated `ReportingClient.get_capabilities()` and direct e2e source-service healthchecks
  to use canonical `consumer_system` and `tenant_id` query parameters; refreshed Manage and Report
  platform-capability fixtures from retired `pas_ref` terminology to current `portfolio_id`
  input-mode terminology.
- Measured signal: stale camelCase direct source-service capability calls are removed from
  `ReportingClient` and `docker-compose.e2e.yml`; Manage and Report capability fixtures now
  preserve current downstream vocabulary while Core, Performance, and Risk legacy compatibility
  coverage remains explicit.
- Tests: `python -m pytest tests/unit/test_upstream_clients.py
  tests/unit/test_platform_capabilities_service.py
  tests/integration/test_platform_capabilities_router.py tests/e2e/test_workflow_journeys.py
  tests/contract/test_platform_capabilities_contract.py -q` passed with 209 tests;
  `python -m pytest tests/unit/test_foundation_service.py tests/integration/test_foundation_router.py
  tests/contract/test_foundation_contract.py -q` passed with 23 tests; `python -m ruff check` on
  touched Python files and `python -m mypy src\app\clients\reporting_client.py` passed.
- Issue disposition evidence: #129 is valid and fixed in this slice; #130 and #131 are valid
  fixture-drift issues fixed in this slice; #128, #132, and #134 are resolved in current code with
  existing tests and search evidence; #182 remains open until current canonical QA proves whether a
  Gateway-owned or downstream-owned defect still exists.
- Integration review: no current downstream issue is warranted for the fixed capability contract
  drift because Gateway now sends the source-owned vocabulary and preserves downstream
  `portfolio_id` capability terminology; open downstream issues should be created only from fresh
  failing integration evidence.
- Follow-up: after merge, close resolved issues with the PR/test evidence and leave #182 open or
  file a downstream issue only if current canonical QA reproduces a non-Gateway defect.

## DPM Proof-Pack Supportability Mapping Extraction

- Scope: behavior-preserving DPM proof-pack service modularity and CI ratchet enforcement.
- Existing owner pattern: `DpmProofPackService` remains the product-facing Gateway facade for
  Manage-owned RFC-0040 proof-pack routes; `lotus-manage` remains source truth for proof-pack
  identifiers, section states, reason codes, content hashes, report input, and AI evidence input;
  `lotus-ai` remains the governed workflow-pack execution authority for PM memo support output.
- Change: moved Manage proof-pack supportability derivation into
  `src/app/services/dpm_proof_pack_supportability.py`; preserved proof-pack generation, lookup,
  Markdown, report-input, AI-evidence-input, product-safe Manage error mapping, and Lotus AI PM
  memo handoff behavior.
- Measured signal: `src/app/services/dpm_proof_pack_service.py` is reduced from 399 to 315 lines
  and the extracted supportability module is 90 lines. The blocking source-file threshold ratchets
  from `399/49` to `398/49` because the current largest source file is now
  `src/app/contracts/advisor_brief.py`; longest function remains 49 lines.
- CI enforcement: `398` passes and `397` fails only on
  `src/app/contracts/advisor_brief.py`; no allowlist or exception is introduced.
- Tests: `tests/unit/test_dpm_proof_pack_service.py` preserves Manage payload passthrough,
  supportability, Markdown, handoff input, Lotus AI memo, and product-safe upstream error
  behavior; `tests/unit/test_service_layer_boundaries.py` pins supportability mapping ownership
  outside the public proof-pack facade; refactor-threshold and agent-quality evidence gates pin
  the 398/49 ratchet.
- Integration review: no upstream or downstream Lotus defect was identified; Gateway still calls
  the same Manage and Lotus AI APIs and preserves source-owned proof-pack and memo-support
  semantics.
- Follow-up: next measured modularity slice should inspect
  `src/app/contracts/advisor_brief.py` before changing code.

## Risk Workspace Response Loading Extraction

- Scope: behavior-preserving risk workspace service modularity and CI ratchet enforcement.
- Existing owner pattern: `RiskWorkspaceService` remains the public Workbench risk facade and owns
  cache, correlation, and cache-status stamping; request construction, response mapping,
  unavailable envelopes, cache keys, source supportability, and attribution orchestration are
  already delegated to focused modules.
- Change: moved summary, concentration, drawdown, rolling, and rolling-Sharpe fallback upstream
  response loading into `src/app/services/risk_workspace_response_loading.py`; preserved Lotus
  Risk source-truth methodology handling, unavailable envelope mapping, cache keys, and public
  service behavior.
- Measured signal: `src/app/services/risk_workspace_service.py` is reduced from 402 to 222 lines
  and the extracted response-loading module is 222 lines. The blocking source-file threshold
  ratchets from `402/49` to `399/49` because the current largest source file is now
  `src/app/services/dpm_proof_pack_service.py`; longest function remains 49 lines.
- CI enforcement: `399` passes and `398` fails only on
  `src/app/services/dpm_proof_pack_service.py`; no allowlist or exception is introduced.
- Tests: `tests/unit/test_risk_workspace_service.py` preserves summary, concentration, drawdown,
  rolling, cache, supportability, malformed-success, unavailable, and Sharpe fallback behavior;
  `tests/unit/test_service_layer_boundaries.py` pins response-loading ownership outside the public
  risk service facade; refactor-threshold and agent-quality evidence gates pin the 399/49 ratchet.
- Integration review: no upstream or downstream Lotus defect was identified; Gateway still calls
  the same Lotus Risk APIs and preserves source-owned calculation/supportability semantics.
- Follow-up: next measured modularity slice should inspect
  `src/app/services/dpm_proof_pack_service.py` before changing code.

## Performance Contribution Payload Mapping Extraction

- Scope: behavior-preserving performance contribution payload modularity and quality evidence
  synchronization.
- Existing owner pattern: `PerformanceWorkspaceService` orchestrates Workbench performance reads
  through typed client protocols; `performance_workspace_contribution.py` remains the
  contribution summary facade; `lotus-performance` remains source truth for contribution,
  smoothing, and source-economics evidence.
- Change: moved contribution level, row, position, smoothing-evidence, and source-economics
  payload mapping into `src/app/services/performance_workspace_contribution_payloads.py`;
  preserved summary/detail contribution assembly, merge behavior, and upstream error handling.
- Measured signal: `src/app/services/performance_workspace_contribution.py` is reduced from 402
  to 227 lines and the extracted payload module is 190 lines. The current largest source-file
  ceiling remains 402 lines, now reported by the agent quality evidence gate as
  `src/app/services/risk_workspace_service.py`; longest function remains 49 lines.
- CI enforcement: blocking refactor threshold remains `402/49`; `402` passes and `401` fails
  only on `src/app/services/risk_workspace_service.py`, so this slice updates durable
  agent-quality evidence instead of claiming an artificial ratchet.
- Tests: `tests/unit/test_performance_workspace_contribution.py` preserves contribution payload
  shape, smoothing evidence, source-economics evidence, and merge semantics;
  `tests/unit/test_performance_workspace_service.py` preserves service orchestration;
  `tests/unit/test_service_layer_boundaries.py` pins payload mapping ownership outside the
  contribution facade.
- Integration review: no upstream or downstream Lotus defect was identified; Gateway still
  consumes and preserves the same Lotus Performance contribution payloads without recomputing
  methodology truth.
- Follow-up: next measured modularity slice should inspect
  `src/app/services/risk_workspace_service.py` before changing code.

## Platform Capability Feature And Workflow Flag Extraction

- Scope: behavior-preserving platform capability normalization modularity and CI ratchet
  enforcement.
- Existing owner pattern: `PlatformCapabilitiesService` remains the upstream capability fan-out
  orchestrator; `platform_capabilities_sources.py` parses upstream result envelopes;
  `platform_capabilities_normalization.py` assembles the normalized BFF response; Gateway preserves
  upstream capability and partial-readiness truth without becoming the domain source of truth.
- Change: moved source capability feature-key and workflow-key interpretation into
  `src/app/services/platform_capabilities_feature_flags.py`; preserved normalized response shape,
  shell bootstrap construction, and service helper behavior.
- Measured signal: `src/app/services/platform_capabilities_normalization.py` is reduced from 404
  to 192 lines. The current largest source-file ceiling is now 402 lines, first reported by the
  agent quality evidence gate as `src/app/services/performance_workspace_contribution.py`; longest
  function remains 49 lines.
- CI enforcement: blocking refactor threshold ratcheted from `404/49` to `402/49`; `402` passes
  and `401` fails only on `src/app/services/performance_workspace_contribution.py` and
  `src/app/services/risk_workspace_service.py`.
- Tests: `tests/unit/test_platform_capabilities_normalization.py` preserves source-backed
  normalized capability behavior and malformed upstream-shape handling;
  `tests/unit/test_platform_capabilities_service.py` preserves service behavior;
  `tests/unit/test_service_layer_boundaries.py` pins feature/workflow flag ownership outside the
  normalized response assembler.
- Integration review: no upstream or downstream Lotus defect was identified; Gateway still
  consumes and preserves the same upstream capability payloads.
- Follow-up: next measured modularity slice should inspect
  `src/app/services/performance_workspace_contribution.py` and
  `src/app/services/risk_workspace_service.py` before changing code.

## Proposal Lifecycle Contract And Query-Service Extraction

- Scope: behavior-preserving proposal lifecycle contract/service modularity and CI ratchet
  enforcement.
- Existing owner pattern: `app.contracts.proposals` remains the Workbench-facing compatibility
  facade; `proposal_lifecycle.py` remains a compatibility import surface; `ProposalService`
  composes focused mixins for lifecycle transitions, lifecycle queries, memo, and delivery
  posture; `lotus-advise` remains source truth for proposal lifecycle, workflow event, approval,
  lineage, and immutable-version semantics.
- Change: split proposal lifecycle DTOs into focused summary, workflow, lineage, and envelope
  modules; moved workflow-events, approvals, and lineage query orchestration into
  `src/app/services/proposal_lifecycle_query_service.py`; preserved existing imports, OpenAPI
  component names, router behavior, and typed envelope mapping.
- Measured signal: `src/app/contracts/proposal_lifecycle.py` is reduced from 405 to 21 lines and
  `src/app/services/proposal_service.py` is reduced from 405 to 324 lines. Current largest source
  file is `src/app/services/platform_capabilities_normalization.py` at 404 lines; longest function
  remains 49 lines.
- CI enforcement: blocking refactor threshold ratcheted from `405/49` to `404/49`; `404` passes
  and `403` fails only on `src/app/services/platform_capabilities_normalization.py`.
- Tests: `tests/unit/test_contract_module_boundaries.py` pins focused lifecycle contract ownership;
  `tests/unit/test_service_layer_boundaries.py` pins lifecycle query ownership outside
  `ProposalService`; proposal contract tests preserve schema shape and compatibility imports.
- Follow-up: next measured modularity slice should inspect
  `src/app/services/platform_capabilities_normalization.py` before changing code.

## Advise Proposal Delivery Client Extraction

- Scope: behavior-preserving Advise proposal upstream-client modularity and CI ratchet
  enforcement.
- Existing owner pattern: `AdviseClient` remains the concrete Lotus Advise HTTP client and public
  service-facing surface; proposal route-family methods live in focused mixins under
  `src/app/clients/advise_*_client.py`; `lotus-advise` remains source truth for proposal delivery,
  report-request, execution handoff, execution status, and delivery-event semantics.
- Change: moved report-request, delivery-summary, delivery-event, execution-handoff,
  execution-status, and execution-update route forwarding into
  `src/app/clients/advise_proposal_delivery_client.py`; `AdviseProposalClientMixin` now inherits
  that focused mixin, preserving the public `AdviseClient` method surface.
- Measured signal: `src/app/clients/advise_proposal_client.py` is reduced below the prior
  406-line ceiling; largest current source-file hotspots are now
  `src/app/contracts/proposal_lifecycle.py` and `src/app/services/proposal_service.py` at 405
  lines; longest function remains 49 lines.
- CI enforcement: blocking refactor threshold ratcheted from `406/49` to `405/49`; `405` passes
  and `404` fails only on `src/app/contracts/proposal_lifecycle.py` and
  `src/app/services/proposal_service.py`.
- Tests: `tests/unit/test_advise_client_boundaries.py` pins proposal delivery route-family
  ownership outside the core proposal client mixin while preserving the inherited `AdviseClient`
  surface; refactor-threshold, quality-baseline artifact, and agent-quality evidence tests pin the
  ratchet.
- Follow-up: next measured modularity slice should inspect `src/app/contracts/proposal_lifecycle.py`
  and `src/app/services/proposal_service.py` before changing code.

## Gateway Demo Certification Report-Only Command

- Scope: app-level demo-readiness evidence command and report-only CI wiring.
- Existing owner pattern: Gateway owns product-facing FastAPI route composition; Lotus Core,
  Performance, Manage, and Advise remain source truth for portfolio data, performance figures,
  DPM supportability, and policy feedback.
- Change: added `scripts/certify_demo_readiness.py` and `make demo-certification`; the command
  uses deterministic synthetic upstream fixtures through real Gateway routes and writes
  `output/demo-certification/gateway-demo-certification.json`.
- Measured signal: current local command passed 24 assertions across five Gateway API calls:
  readiness, Workbench overview, portfolio-360 projected state, sandbox create, and sandbox apply
  policy feedback for `PB_SG_GLOBAL_BAL_001`.
- CI posture: Quality Baseline now runs the command with `continue-on-error: true`, captures
  `output/quality-baseline/demo-certification.txt`, and uploads `output/demo-certification/` as
  report-only evidence. It is not a blocking gate until repeated runs prove deterministic,
  low-noise behavior and an exception policy.
- Tests: `tests/unit/test_demo_readiness_certification.py` validates machine-readable evidence,
  canonical figures, endpoint count, and report-only posture; quality-baseline artifact tests pin
  CI wiring.
- Follow-up: review repeated Quality Baseline artifacts before considering Feature Lane or PR Merge
  Gate promotion.

## Risk Workspace Attribution Mapping Extraction

- Scope: behavior-preserving risk workspace attribution mapping modularity and CI ratchet
  enforcement.
- Existing owner pattern: `RiskWorkspaceAttributionServiceMixin` owns request context, caching, and
  upstream Lotus Risk calls; `risk_workspace_attribution.py` owns product response state,
  controls, supportability, metadata, and failure envelopes.
- Change: moved upstream attribution period, set, contributor, quality-flag, and numeric coercion
  mapping into `src/app/services/risk_workspace_attribution_mapping.py`; response assembly remains
  in `src/app/services/risk_workspace_attribution.py`.
- Measured signal: `src/app/services/risk_workspace_attribution.py` reduced from 408 to 274 lines;
  the extracted mapping module is 142 lines; largest source file is now
  `src/app/clients/advise_proposal_client.py` at 406 lines; longest function remains 49 lines.
- CI enforcement: blocking refactor threshold ratcheted from `408/49` to `406/49`; `406` passes
  and `405` fails only on `src/app/clients/advise_proposal_client.py`.
- Tests: `tests/unit/test_risk_workspace_attribution.py` preserves upstream methodology, period
  error, numeric coercion, blocked, and unavailable behavior; `tests/unit/test_risk_workspace_service.py`
  preserves service orchestration; `tests/unit/test_service_layer_boundaries.py` pins the new
  attribution mapping module boundary.
- Follow-up: next measured modularity slice should inspect
  `src/app/clients/advise_proposal_client.py` before changing code.

## DPM Wave AI Payload Extraction

- Scope: behavior-preserving DPM wave AI handoff modularity and CI ratchet enforcement.
- Existing owner pattern: `DpmWaveService` composes focused mixins; `dpm_wave_ai_handoff.py`
  owns Manage report-input loading and Lotus AI workflow-pack orchestration for PM memo and
  operations handoff summary requests.
- Change: moved wave report-input supportability extraction, source-reference construction,
  request/task payload construction, supportability guardrail payloads, and gateway response
  assembly into `src/app/services/dpm_wave_ai_payloads.py`; the handoff mixin remains the owner of
  workflow-pack execution and product-safe upstream error mapping.
- Measured signal: `src/app/services/dpm_wave_ai_handoff.py` reduced from 411 to 195 lines; the
  extracted payload module is 235 lines; largest source file is now
  `src/app/services/risk_workspace_attribution.py` at 408 lines; longest function remains 49 lines.
- CI enforcement: blocking refactor threshold ratcheted from `411/49` to `408/49`; `408` passes
  and `407` fails only on `src/app/services/risk_workspace_attribution.py`.
- Tests: `tests/unit/test_dpm_wave_service.py` preserves Manage report-input and Lotus AI
  workflow-pack behavior; `tests/contract/test_dpm_wave_contract.py` preserves contract shape;
  `tests/unit/test_dpm_wave_service_boundaries.py` pins the new payload/helper module boundary.
- Follow-up: next measured modularity slice should inspect
  `src/app/services/risk_workspace_attribution.py` before changing code.

## Performance Workspace Attribution-Trend Service Extraction

- Scope: behavior-preserving performance workspace trend-service modularity and CI ratchet
  enforcement.
- Existing owner pattern: `PerformanceWorkspaceService` composes focused mixins; horizon
  comparison orchestration and attribution-trend orchestration previously shared
  `performance_workspace_trend_service.py`, while context construction and attribution payload
  parsing already lived in focused modules.
- Change: moved attribution-trend request-context assembly, window construction, upstream
  fan-out, and response assembly into
  `src/app/services/performance_workspace_attribution_trend_service.py`; the existing
  `PerformanceWorkspaceTrendServiceMixin` remains the compatibility mixin used by
  `PerformanceWorkspaceService`.
- Measured signal: `src/app/services/performance_workspace_trend_service.py` reduced from 415 to
  223 lines; the extracted attribution-trend service mixin is 243 lines; largest source file is
  now `src/app/services/dpm_wave_ai_handoff.py` at 411 lines; longest function remains 49 lines.
- CI enforcement: blocking refactor threshold ratcheted from `415/49` to `411/49`; `411` passes
  and `410` fails only on `src/app/services/dpm_wave_ai_handoff.py`.
- Tests: `tests/unit/test_performance_workspace_service.py` preserves horizon and attribution
  trend response behavior; `tests/unit/test_performance_workspace_attribution.py` preserves
  attribution trend payload parsing; `tests/unit/test_service_layer_boundaries.py` pins the new
  attribution-trend orchestration module boundary.
- Follow-up: next measured modularity slice should inspect
  `src/app/services/dpm_wave_ai_handoff.py` before changing code.

## DPM Wave AI Contract Extraction

- Scope: behavior-preserving DPM wave contract modularity and CI evidence synchronization.
- Existing owner pattern: `dpm_waves.py` remains the compatibility import surface for DPM wave
  route contracts; campaign definition and workflow DTOs already live in focused modules.
- Change: moved DPM wave supportability and AI handoff request/response DTOs into
  `src/app/contracts/dpm_wave_supportability.py` and `src/app/contracts/dpm_wave_ai.py` while
  preserving public `app.contracts.dpm_waves` imports and OpenAPI schema names.
- Measured signal: `src/app/contracts/dpm_waves.py` reduced from 415 to 177 lines; largest source
  file is now `src/app/services/performance_workspace_trend_service.py` at 415 lines; longest
  function remains 49 lines.
- CI enforcement: blocking refactor threshold remains `415/49`; `415` passes and `414` fails only
  on `src/app/services/performance_workspace_trend_service.py`, so this slice updates durable
  agent-quality evidence instead of claiming an artificial ratchet.
- Tests: `tests/contract/test_dpm_wave_contract.py`, `tests/unit/test_dpm_wave_service.py`, and
  `tests/unit/test_contract_module_boundaries.py` preserve schema/import behavior and pin focused
  contract-module ownership.
- Follow-up: next measured modularity slice should inspect
  `src/app/services/performance_workspace_trend_service.py` before changing code.

## Risk Rolling Payload Example Extraction

- Scope: behavior-preserving risk rolling contract modularity and CI ratchet enforcement.
- Existing owner pattern: `risk_workspace_rolling.py` owns Workbench-facing risk rolling DTOs;
  `risk_workspace.py` remains the compatibility facade and `risk_workspace_examples.py` composes
  response examples for OpenAPI.
- Change: moved the large rolling payload example into
  `src/app/contracts/risk_workspace_rolling_examples.py` while preserving
  `WorkbenchRiskRollingPayload` schema behavior and the private compatibility example alias.
- Measured signal: `src/app/contracts/risk_workspace_rolling.py` reduced from 421 to 337 lines;
  largest source file is now `src/app/contracts/dpm_waves.py` at 415 lines; longest function
  remains 49 lines.
- CI enforcement: blocking refactor threshold ratcheted from `421/49` to `415/49`; `415` passes
  and `414` fails on `src/app/contracts/dpm_waves.py` and
  `src/app/services/performance_workspace_trend_service.py`.
- Tests: `tests/unit/test_risk_workspace_rolling_contracts.py` preserves compatibility and schema
  behavior; `tests/unit/test_contract_module_boundaries.py` pins risk rolling example ownership.
- Follow-up: next measured modularity slice should inspect `src/app/contracts/dpm_waves.py` before
  changing code.

## Platform Capabilities Source-Result Extraction

- Scope: behavior-preserving platform capabilities aggregation modularity and CI ratchet
  enforcement.
- Existing owner pattern: `PlatformCapabilitiesService` remains the experience-API aggregation
  facade; upstream capability payloads and `app.contracts.platform_capabilities` remain the source
  of truth, with normalization and shell descriptors already owned by focused platform capability
  modules.
- Change: moved primary-source result parsing, Lotus Core policy result parsing, optional-source
  merge behavior, and upstream exception detail mapping into
  `src/app/services/platform_capabilities_sources.py` while preserving
  `get_platform_capabilities` response behavior.
- Measured signal: `src/app/services/platform_capabilities_service.py` reduced from 427 to 326
  lines; largest source file is now `src/app/contracts/risk_workspace_rolling.py` at 421 lines;
  longest function remains 49 lines.
- CI enforcement: blocking refactor threshold ratcheted from `427/49` to `421/49`; `421` passes
  and `420` fails only on `src/app/contracts/risk_workspace_rolling.py`.
- Tests: `tests/unit/test_platform_capabilities_service.py` preserves success, partial-failure,
  policy, timeout, optional-risk, and contract behavior; `tests/unit/test_service_layer_boundaries.py`
  pins source-result parsing ownership.
- Follow-up: next measured modularity slice should inspect
  `src/app/contracts/risk_workspace_rolling.py` before changing code.

## Advisor-Brief Runtime Context Extraction

- Scope: behavior-preserving advisor-brief service modularity and CI ratchet enforcement.
- Existing owner pattern: `AdvisorBriefService` remains the orchestration facade; source context,
  narrative shaping, workflow-pack runtime mapping, supportability loading, and client protocols
  are owned by focused advisor-brief service modules.
- Change: moved runtime evidence loading into
  `src/app/services/advisor_brief_runtime_context.py` and kept public advisor-brief response and
  review-action behavior unchanged.
- Measured signal: `src/app/services/advisor_brief_service.py` reduced from 438 to 397 lines;
  largest source file is now `src/app/services/performance_workspace_service.py` at 437 lines;
  longest function remains 49 lines.
- CI enforcement: blocking refactor threshold ratcheted from `438/49` to `437/49`; `437` passes
  and `436` fails only on `src/app/services/performance_workspace_service.py`.
- Tests: `tests/unit/test_advisor_brief_service.py` preserves runtime behavior and
  `tests/unit/test_service_layer_boundaries.py` now pins runtime-context ownership.
- Follow-up: next measured modularity slice should inspect
  `src/app/services/performance_workspace_service.py` before changing code.

## Performance Workspace Summary-View Extraction

- Scope: behavior-preserving performance workspace service modularity and CI ratchet enforcement.
- Existing owner pattern: `PerformanceWorkspaceService` remains the public Workbench performance
  workspace facade; request-context, trend, evidence, detail-view, response assembly, benchmark,
  and capability responsibilities are owned by focused performance workspace modules.
- Change: moved workspace summary fetch, summary parsing, and detail-view fan-out orchestration
  into `src/app/services/performance_workspace_summary_views.py` while preserving workspace,
  summary, detail, and portfolio performance snapshot behavior.
- Measured signal: `src/app/services/performance_workspace_service.py` reduced from 437 to 355
  lines; largest source file is now `src/app/services/risk_workspace_attribution.py` at 432
  lines; longest function remains 49 lines.
- CI enforcement: blocking refactor threshold ratcheted from `437/49` to `432/49`; `432` passes
  and `431` fails only on `src/app/services/risk_workspace_attribution.py` and
  `src/app/services/risk_workspace_rolling.py`.
- Tests: `tests/unit/test_performance_workspace_service.py` preserves facade behavior and
  `tests/unit/test_service_layer_boundaries.py` now pins summary-view orchestration ownership.
- Follow-up: next measured modularity slice should inspect
  `src/app/services/risk_workspace_attribution.py` before changing code.

## Risk Workspace Supportability Extraction

- Scope: behavior-preserving risk workspace rolling and attribution supportability modularity.
- Existing owner pattern: risk workspace mapper modules translate Lotus Risk stateful responses;
  rolling-window parsing, request payloads, envelopes, and attribution controls already live in
  focused helpers.
- Change: moved rolling supportability construction into
  `src/app/services/risk_workspace_rolling_supportability.py` and shared source-calculation
  supportability append logic into `src/app/services/risk_workspace_source_supportability.py`.
- Measured signal: `src/app/services/risk_workspace_rolling.py` reduced from 432 to 342 lines and
  `src/app/services/risk_workspace_attribution.py` reduced from 432 to 408 lines; largest source
  file is now `src/app/contracts/proposals.py` at 431 lines; longest function remains 49 lines.
- CI enforcement: blocking refactor threshold ratcheted from `432/49` to `431/49`; `431` passes
  and `430` fails only on `src/app/contracts/proposals.py`.
- Tests: `tests/unit/test_risk_workspace_rolling_supportability.py` covers supportability posture,
  `tests/unit/test_risk_workspace_service.py` preserves service behavior, and
  `tests/unit/test_service_layer_boundaries.py` pins shared source-supportability ownership.
- Follow-up: next measured modularity slice should inspect `src/app/contracts/proposals.py` before
  changing code.

## Proposal Generation Contract Extraction

- Scope: behavior-preserving proposal generation contract modularity and CI ratchet enforcement.
- Existing owner pattern: `app.contracts.proposals` remains the compatibility facade for
  Workbench-facing proposal imports; focused proposal contract families already live in
  `proposal_memos.py`, `proposal_lifecycle.py`, and `proposal_common.py`.
- Change: moved proposal simulation request/response/data DTOs into
  `src/app/contracts/proposal_generation.py` while preserving public
  `app.contracts.proposals` imports and router response models.
- Measured signal: `src/app/contracts/proposals.py` reduced from 431 to 314 lines; largest source
  file is now `src/app/services/advisor_brief_source.py` at 429 lines; longest function remains
  49 lines.
- CI enforcement: blocking refactor threshold ratcheted from `431/49` to `429/49`; `429` passes
  and `428` fails only on `src/app/services/advisor_brief_source.py`.
- Tests: `tests/contract/test_proposals_contract.py` preserves facade import compatibility and
  `tests/unit/test_contract_module_boundaries.py` pins proposal-generation DTO ownership.
- Follow-up: next measured modularity slice should inspect
  `src/app/services/advisor_brief_source.py` before changing code.

## Advisor-Brief Source Metric Extraction

- Scope: behavior-preserving advisor-brief source metric modularity and CI ratchet enforcement.
- Existing owner pattern: `advisor_brief_source.py` remains the source-context compatibility
  module; contributors, fact bundle, formatting, and source supportability already live in focused
  advisor-brief source modules.
- Change: moved return-source metric list construction and source metric DTO creation into
  `src/app/services/advisor_brief_source_metrics.py` while preserving
  `build_advisor_brief_source_metrics` behavior.
- Measured signal: `src/app/services/advisor_brief_source.py` reduced from 429 to 366 lines;
  largest source file is now `src/app/services/platform_capabilities_service.py` at 427 lines;
  longest function remains 49 lines.
- CI enforcement: blocking refactor threshold ratcheted from `429/49` to `427/49`; `427` passes
  and `426` fails only on `src/app/services/platform_capabilities_service.py`.
- Tests: `tests/unit/test_advisor_brief_source.py` preserves source metric output and
  `tests/unit/test_service_layer_boundaries.py` pins source metric construction ownership.
- Follow-up: next measured modularity slice should inspect
  `src/app/services/platform_capabilities_service.py` before changing code.

## Advisor-Brief Response Example Boundary Extraction

- Scope: behavior-preserving Advisor Brief contract modularity and CI ratchet enforcement.
- Existing owner pattern: `app.contracts.advisor_brief` remains the compatibility facade for
  Workbench-facing Advisor Brief DTO imports; focused item, supportability, workflow, and example
  modules own bulky contract families while Gateway remains the BFF response contract owner.
- Source of truth: Gateway owns the Advisor Brief response schema; source data remains upstream in
  `lotus-performance`, `lotus-ai`, and `lotus-advise`.
- Change: moved the static `AdvisorBriefResponse` OpenAPI example into
  `src/app/contracts/advisor_brief_examples.py` while preserving model field definitions,
  compatibility imports, and OpenAPI example content.
- Measured signal: `src/app/contracts/advisor_brief.py` reduced from 398 to 207 lines; largest
  source files are now `src/app/services/advisor_brief_service.py` and
  `src/app/services/risk_workspace_attribution_controls.py` at 397 lines; longest function remains
  49 lines.
- CI enforcement: blocking refactor threshold ratcheted from `398/49` to `397/49`; `397` passes
  and `396` fails on the tied 397-line service/control hotspots.
- Tests: `tests/unit/test_contract_module_boundaries.py` pins example ownership outside the
  response model, and `tests/integration/test_workbench_router.py` preserves Advisor Brief OpenAPI
  contract behavior.
- Integration review: no upstream or downstream API route, payload, workflow-pack call, or
  response semantic changed; no cross-repo GitHub issue is warranted from this slice.
- Follow-up: next measured modularity slice should inspect
  `src/app/services/advisor_brief_service.py` or
  `src/app/services/risk_workspace_attribution_controls.py` before changing code.

## Provider Provenance Boundary Enforcement (#528, #529)

- Scope: bounded provider-mode and deterministic/live stub-posture enforcement for the DPM typed
  execution boundary and completed Advisor Brief narratives.
- Source authority: `lotus-ai` owns provider and execution truth; Gateway owns the product-safe
  projection and Advisor Brief degradation decision, without inventing provider state.
- Change: added one shared closed provider-posture policy; DPM audit/run models now enforce the
  vocabulary and semantic mode/stub pairing, while Advisor Brief validates raw provenance before
  publishing completed structured output and discards invalid AI evidence on downgrade.
- Compatibility: valid `disabled|stub` deterministic and `openai|local_openai_compatible` live
  payloads remain unchanged; DPM invalid source payloads retain the existing
  `AI_WORKFLOW_EXECUTION_CONTRACT_INVALID` 502 contract, and Advisor Brief retains source-backed
  metrics with `PARTIAL` status and a stable warning for invalid completed provenance.
- Tests: table-driven policy, DPM missing/unknown/contradictory posture rejection, Advisor Brief
  narrative/service safe downgrade, and OpenAPI enum tests; focused validation passed with 100
  tests.
- Truth updates: repository context, supported-features documentation, API-surface guidance, and
  wiki source updated. No migration, upstream contract, route, or central skill change was needed;
  no additional issue was created because the agreed #528/#529 scope covers the discovered pattern.

## Proposal Risk-Impact Coherence (#561)

- Scope: Gateway anti-corruption validation for selected `proposal-risk-impact.v1` decision and
  workflow evidence.
- Source authority: `lotus-advise` owns proposal policy and progression truth; Gateway validates
  relationships and publishes only a safe experience projection.
- Change: centralized decision-status/top-level/action, gate/next-step, compatible decision/gate,
  and blocking-evidence rules. Source models fail closed on contradictions; degraded decision
  evidence downgrades executable-ready gates to explicit partial posture.
- Compatibility: valid source matrix and exact evidence/lineage remain unchanged. No Advise policy,
  public route, migration, auth, or Workbench implementation change.
- Tests: table-driven policy matrix, source/projection contradiction tests, degraded executable-gate
  regression, OpenAPI description assertions, and route-level product-safe failure test.
- Truth updates: proposal contract, supported-features, API-surface, repository context, and wiki
  source updated. No central skill change or new upstream issue was required.
