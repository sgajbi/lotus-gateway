# Architecture Rules

This document records the baseline architecture rules for the `lotus-gateway` enterprise
hardening program. The first implementation phase is report-only; later phases should fail only
new regressions, then enforce agreed thresholds.

## Layering

1. Routers call gateway services or use-case modules only.
2. Routers must not import or instantiate concrete downstream clients, HTTP clients, database
   clients, Kafka, Redis, or persistence adapters.
3. Middleware remains cross-cutting and thin. It must not contain portfolio, advisory, reporting,
   analytics, or workflow business logic.
4. Contracts define product-facing DTOs and must not depend on routers, services, clients, or
   middleware.
5. Service modules may orchestrate upstream calls through typed protocol surfaces and factories.
6. Only service factory modules may construct concrete upstream clients.
7. Gateway must not become the authority for portfolio source data, analytics methodology, advisory
   workflow truth, management workflow truth, reporting truth, archive truth, or AI output truth.

## Import-Linter Contracts

`.importlinter` defines report-only contracts for:

1. routers not importing `app.clients`,
2. middleware not importing `app.clients` or `app.services`,
3. contracts not importing runtime layers,
4. services not importing routers.

Existing AST-based unit boundary tests remain the blocking local protection for the currently
validated rules. Import-linter expands the governed baseline and will become blocking after the
report-only baseline is reviewed.

## Baseline Findings

The largest current modularity risks are:

1. `src/app/services/portfolio_service.py` at 980 script-counted lines,
2. `src/app/contracts/proposals.py` at 979 script-counted lines,
3. `src/app/contracts/portfolio.py` at 954 script-counted lines,
4. `src/app/services/foundation_service.py` at 951 script-counted lines,
5. `src/app/contracts/performance_workspace.py` at 930 script-counted lines.

The prior longest function, `register_routers` in `src/app/router_registry.py`, has been split
into explicit route-family groups and a short registration loop. The performance workspace
response builder has also been split into request-context, summary/detail, evidence, and assembly
helpers. Advisor-brief source-context, fallback narrative, source-metric, supportability, route,
and AI fact-bundle shaping are split into `advisor_brief_source.py`, leaving the service focused on
orchestration, AI narrative parsing, runtime supportability, and response assembly. The risk drawdown mapper has been split into
period mapping, supportability, state, metadata, and payload helpers. The risk rolling mapper has
been split into period mapping, dependency context, supportability, state, metadata, Sharpe
fallback, and payload helpers. The risk attribution mapper has been split into period mapping,
set/contributor parsing, state, metadata, and payload helpers. The risk concentration mapper has
been extracted to `src/app/services/risk_workspace_concentration.py`, reducing
`risk_workspace_service.py` below the current source-file ceiling while preserving source-owned concentration fields
and supportability semantics. Risk unavailable-envelope primitives have been centralized in
`src/app/services/risk_workspace_envelopes.py` so upstream failure detail mapping, product-safe
unavailable supportability, and risk metadata construction are no longer duplicated across risk
surfaces. The drawdown response mapper and unavailable envelope have been extracted to
`src/app/services/risk_workspace_drawdown.py`, reducing `risk_workspace_service.py` to 1,594 lines
while keeping request orchestration and caching in the workspace service. The rolling response
mapper, Sharpe fallback policy, window parsing, and unavailable envelope have been extracted to
`src/app/services/risk_workspace_rolling.py`, reducing `risk_workspace_service.py` to 1,185 lines.
The risk attribution response mapper, blocked/unavailable envelopes, period/set/contributor
parsing, methodology metadata, and metric conversion have been extracted to
`src/app/services/risk_workspace_attribution.py`, reducing `risk_workspace_service.py` to 780
lines while keeping attribution request orchestration and cache semantics in the workspace service.
The risk summary response mapper, unavailable envelope, metric labelling, dependency
supportability, source-calculation supportability, and empty-result envelope have been extracted to
`src/app/services/risk_workspace_summary.py`, reducing `risk_workspace_service.py` to 540 lines
while keeping summary request orchestration, caching, and correlation handling in the workspace
service. Platform capability normalization, shell-bootstrap construction, workspace descriptors,
module-health classification, policy diagnostics, workflow flags, and input-mode normalization have
been extracted to `src/app/services/platform_capabilities_normalization.py`, reducing
`platform_capabilities_service.py` to 330 lines while keeping upstream orchestration, timeout
handling, correlation propagation, and partial-failure collection in the service. Shell-bootstrap
contract assembly and workspace descriptor state mapping have been further extracted to
`src/app/services/platform_capabilities_shell.py`, reducing the capability normalization module to
355 lines and keeping shell navigation evidence separately testable. Portfolio workspace-control
capability construction has been extracted to
`src/app/services/portfolio_workspace_controls.py`, reducing `portfolio_service.py` to 2,839 lines
and moving historical-snapshot and reporting-currency support matrices behind focused tests. The
performance horizon comparison parser has been split into diagnostic propagation, row-list
selection, row construction, period-block extraction, and date-resolution helpers, reducing
`parse_horizon_comparison_result` from 172 lines to 50 lines. The foundation core snapshot parser
has been split into validation, section extraction, totals,
enrichment indexing, position projection, allocation finalization, and portfolio identity helpers,
reducing `_parse_core_snapshot` from 153 lines to 38 lines. The advisor-brief narrative-state
builder has been split into source fallback, AI result
classification, completed-output projection, unavailable-risk construction, and route-resolution
helpers, reducing `_build_advisor_brief_narrative_state` from 144 lines to 30 lines. The current
platform-capabilities orchestration has been split into task assembly, primary-source
classification, policy-result extraction, optional-source merging, shared source-result mapping,
and response construction helpers, reducing `get_platform_capabilities` from 143 lines to 32
lines. The performance attribution trend orchestrator has been split into request-context,
window-pair construction, attribution fan-out, and response assembly helpers, reducing
`get_performance_attribution_trend` from 135 lines to 56 lines. The performance evidence-view
orchestrator has now been split into request context, fetch state, requested-calculation
selection, explicit response builders, and partial-failure recording, reducing
`_build_evidence_view` from 134 lines to 51 lines. Portfolio exception-summary construction has
been extracted to
`src/app/services/portfolio_exception_summaries.py`, reducing `portfolio_service.py` from 2,839 to
2,744 lines and reducing `_build_portfolio_exception_summaries` from 133 lines to a short
delegation over readiness status. Performance workspace capability-input derivation has been
split into `PerformanceCapabilityInputs`, `build_performance_capability_inputs`, and
`resolve_history_date_range`, reducing `build_workspace_capabilities` from 127 lines to 99 lines
while keeping capability payload assembly in the original module. Later merged slices also split
portfolio workspace source/analytics assembly, portfolio insight-rule helpers, performance
workspace summary/detail and horizon contexts, foundation workspace assembly, risk rolling and
attribution orchestration, shell workspace descriptor specs, transaction query contracts, DPM
exception-summary workflow orchestration, advisor-brief source talking-point and review-action
orchestration, portfolio workflow-action assembly, Workbench performance snapshot parsing, horizon
comparison row-field projection, performance workspace summary parsing, and performance
evidence-view mapping, foundation workspace response assembly, PM operating quality summary
orchestration, risk attribution supportability construction, attribution trend row parsing,
portfolio position parsing, performance workspace request-context assembly, advisor-brief and
portfolio performance route dependencies, risk drawdown orchestration, core snapshot summary
parsing, portfolio workspace response-component assembly, risk attribution route query extraction,
performance summary route dependency extraction, shell workspace descriptor-state extraction, and
rebalance supportability failure-recording extraction. The latest hardening branch further splits
shared analytics async polling, workspace-summary payload assembly, portfolio transaction-summary
context loading, transaction page loading, portfolio book response assembly, performance
attribution trend query metadata extraction, risk rolling query metadata extraction,
advisor-brief query metadata extraction, and performance evidence-view partial-failure recording
extraction, DPM portfolio-memory search query metadata extraction, performance chart-point row
projection extraction, HTTP resilience JSON dispatch extraction, and performance
horizon-comparison dependency-phase extraction, followed by performance summary/detail route
query metadata extraction and DPM wave PM memo payload/response construction extraction. The
latest risk summary mapper slice split period and metric-state mapping out of the response
composer. Advisor-brief workflow-pack run loading now separates source-profile retrieval from
run-posture projection. Performance attribution trend now delegates row orchestration to a
focused helper. Benchmark-context loading now separates concurrent task construction from
gathered-result resolution. Shell workspace descriptor assembly now delegates contract
construction behind the public descriptor helper. Rebalance supportability result validation and
summary-count merging are now separate from payload selection. Performance chart-point mapping now
separates frequency-row selection, peer-row validation, point construction, and active-return
calculation. Shell-bootstrap section construction now delegates supportability, freshness,
evidence, versioning, and caching assembly to focused helpers. Portfolio performance snapshot
projection now delegates sparkline, unavailable-state, and partial-failure mapping to focused
helpers. Contribution summary merging now delegates detail-vs-summary selection policy to reusable
helpers. Risk rolling response mapping now delegates supportability enrichment and fallback warning
assembly to focused helpers. Risk drawdown routing now keeps OpenAPI query metadata in named
descriptors separate from the public query dependency. Portfolio position-book mapping now lives in
`src/app/services/portfolio_position_book.py`, and transaction-ledger request context plus row
mapping now live in `src/app/services/portfolio_transaction_ledger.py`. Portfolio liquidity
upstream payload loading now lives in `src/app/services/portfolio_liquidity_payloads.py`.
Transaction request-context handling, transaction page-context handling, transaction client-kwargs
mapping, portfolio workspace performance and rebalance parsing, portfolio source-readiness parsing,
portfolio transaction-summary mapping/context loading, portfolio workspace payload mapping, and
final portfolio workspace response assembly lowered `portfolio_service.py` to 1,826 physical
lines. Portfolio readiness and insight source fan-out now lives in
`src/app/services/portfolio_readiness_insight_sources.py`, reducing `portfolio_service.py` to
1,607 script-counted lines while preserving workspace, source-readiness, positions, allocations,
transaction-probe, and activity-summary request behavior. Portfolio book source fan-out now lives
in `src/app/services/portfolio_book_sources.py`, reducing `portfolio_service.py` to 1,589
script-counted lines while preserving allocation, position, cash-balance, portfolio-profile,
projection, and reporting-currency request behavior. Portfolio service stale workspace wrapper
methods have been removed, reducing
`portfolio_service.py` to 1,553 script-counted lines while preserving direct use of the extracted
portfolio workspace payload and control-capability helpers. Portfolio-specific upstream payload
requiring, optional partial-failure recording, and safe client-error mapping now live in
`src/app/services/portfolio_upstream_payloads.py`, reducing `portfolio_service.py` from 1,553 to
1,489 script-counted lines. Portfolio readiness response construction and reporting-readiness
fallback policy now live in `src/app/services/portfolio_readiness_response.py`, reducing
`portfolio_service.py` to 1,453 lines. Performance workspace final response assembly now lives in
`src/app/services/performance_workspace_response.py`, and performance workspace request-context
policy now lives in `src/app/services/performance_workspace_context.py`, lowering
`performance_workspace_service.py` from 1,477 to 1,206 script-counted lines. Lotus Core transaction
query-parameter construction now lives in
`src/app/clients/lotus_core_transaction_params.py`, reducing `lotus_core_query_client.py` to 574
measured lines and removing `_portfolio_transaction_query_params` from the current top hotspot
list. Portfolio workspace component parsing, reporting-readiness part assembly, and
resolved-as-of-date extraction now live in `src/app/services/portfolio_workspace_components.py`,
reducing `portfolio_service.py` from 1,453 to 1,237 script-counted lines and making
`dpm_client.py` the largest remaining source-file hotspot. PM operating-quality client route
methods now live in `src/app/clients/dpm_pm_operating_quality_client.py`, reducing
`dpm_client.py` below the current source-file ceiling and making `portfolio_service.py` the largest
remaining source-file hotspot. Construction-alternative and proof-pack client route methods now
live in `src/app/clients/dpm_construction_client.py` and
`src/app/clients/dpm_proof_pack_client.py`, reducing `dpm_client.py` to 1,041 physical lines while
preserving `DpmClient` as the public upstream client surface. Cached Lotus Core, performance, and
DPM upstream result acquisition for portfolio surfaces now lives in
`src/app/services/portfolio_upstream_access.py`, reducing `portfolio_service.py` from 1,237 to 980
script-counted lines while preserving cache keys, optional-client behavior, and source fan-out
call shapes. DPM PM operating-quality service orchestration now lives in
`src/app/services/dpm_pm_operating_quality_service.py`, reducing
`dpm_command_center_service.py` from 1,217 to 695 script-counted lines while preserving the public
`DpmCommandCenterService` surface and manage/AI workflow-pack boundaries. Performance workspace
horizon-comparison and attribution-trend orchestration now lives in
`src/app/services/performance_workspace_trend_service.py`, reducing
`performance_workspace_service.py` from 1,206 to 842 script-counted lines while preserving the
public `PerformanceWorkspaceService` surface. RFC-0028 bank-demo proof Advise client routes now
live in `src/app/clients/advise_bank_demo_proof_client.py`, reducing `advise_client.py` from 1,098
to 1,062 script-counted lines while preserving the public `AdviseClient` surface. The DPM wave AI
handoff slice moves PM memo and operations handoff summary workflow-pack orchestration into
`src/app/services/dpm_wave_ai_handoff.py`, reducing `dpm_wave_service.py` from 1,093 to 692
script-counted lines while preserving the public `DpmWaveService` surface. The current Advise
workspace client-boundary slice moves advisory-workspace upstream route methods into
`src/app/clients/advise_workspace_client.py`, reducing `advise_client.py` from 1,062 to 909
script-counted lines while preserving the public `AdviseClient` surface. The current
longest functions are
49-line helpers:
`get_transaction_ledger` in `portfolio_service.py` and `get_portfolio_transactions` in
`lotus_core_query_client.py`.

## Progressive Enforcement

1. Phase 1: report-only quality baseline.
2. Phase 2: fail only new architecture regressions.
3. Phase 3: enforce thresholds for largest modules, function length, complexity, and import rules.
4. Phase 4: enterprise-readiness gate requiring architecture, API, security, observability, and
   docs scorecard targets to pass.
