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

1. `src/app/services/dpm_command_center_service.py` at 521 script-counted lines,
2. `src/app/services/proposal_service.py` at 520 script-counted lines,
3. `src/app/services/workbench_service.py` at 515 script-counted lines,
4. `src/app/services/advisor_brief_source.py` at 508 script-counted lines,
5. `src/app/services/portfolio_transaction_summary.py` at 504 script-counted lines.

`src/app/services/proposal_service.py` is reduced from 658 to 520 script-counted lines after
proposal lifecycle transition orchestration moved into
`src/app/services/proposal_transition_service.py`.

The prior longest function, `register_routers` in `src/app/router_registry.py`, has been split
into explicit route-family groups and a short registration loop. Advise-owned router groups have
also been extracted into `src/app/router_groups/advisory.py`, reducing `router_registry.py` to 632
script-counted lines while preserving concrete route registration. DPM command-center, campaign,
proof-pack, construction, and wave router groups now live in `src/app/router_groups/dpm.py`,
reducing `router_registry.py` to 294 script-counted lines while preserving route registration
order. Risk workspace cache-key construction and response replay cache-status/correlation stamping
now live in `src/app/services/risk_workspace_cache.py`, reducing `risk_workspace_service.py` below
the current source-file ceiling while preserving risk workspace response behavior. The performance workspace
response builder has also been split into request-context, summary/detail, evidence, and assembly
helpers. Performance workspace context loading, report-window resolution, benchmark context
assembly, and analytics-reference fallback are now split into
`src/app/services/performance_workspace_context_service.py`, reducing
`performance_workspace_service.py` to 639 script-counted lines. Performance workspace detail-view
orchestration now lives in `src/app/services/performance_workspace_detail_views.py`, reducing
`performance_workspace_service.py` below the current top-file ceiling. Advisor-brief source-context,
fallback narrative, source-metric, supportability, route, source formatting,
source-contributor ranking, AI fact-bundle shaping, and AI narrative parsing are split into
`advisor_brief_source.py`, `advisor_brief_source_formatting.py`,
`advisor_brief_source_contributors.py`, `advisor_brief_source_fact_bundle.py`, and
`advisor_brief_narrative.py`, leaving the service focused on orchestration, runtime supportability,
review actions, and response assembly. The proposal memo route-family forwarding methods have been split into
`src/app/services/proposal_memo_service.py`, leaving `proposal_service.py` focused on core proposal
lifecycle, workflow, approval, narrative, operation, and delivery-summary orchestration.
PM operating-quality request, supportability, gateway response, and AI-summary handoff contracts
have been split into `src/app/contracts/dpm_pm_operating_quality.py`, leaving
`dpm_command_center.py` as a compatibility facade for that PM quality contract family and reducing
the command-center facade to 593 script-counted lines.
Advisor-brief workflow-pack and task-flow contracts have been split into
`src/app/contracts/advisor_brief_workflow.py`, reducing `advisor_brief.py` from 812 to 646
script-counted lines while preserving compatibility imports. Proposal lifecycle, version,
workflow, approval, and lineage contracts have been split into
`src/app/contracts/proposal_lifecycle.py`, reducing `proposals.py` from 812 to 431 script-counted
lines while preserving the proposal facade.
Portfolio workflow orchestration has been split into
`src/app/services/portfolio_workflow_service.py`, preserving the public `PortfolioService` surface
while reducing `portfolio_service.py` from 811 to 768 script-counted lines and moving the largest
remaining source-file hotspot to `src/app/contracts/workbench.py` at 794 script-counted lines.
Workbench common, overview, portfolio-360, sandbox, and analytics contracts have been split into
`src/app/contracts/workbench_common.py`, `src/app/contracts/workbench_overview.py`, and
`src/app/contracts/workbench_sandbox.py`, preserving the public `app.contracts.workbench` facade
while reducing `workbench.py` from 794 to 47 script-counted lines and moving the largest remaining
source-file hotspot to `src/app/services/performance_workspace_evidence.py` at 771 script-counted
lines.
Performance calculation evidence artifact retrieval, lineage polling, execution refresh, payload
normalization, stage/snapshot mapping, and artifact URL construction have been split into
`src/app/services/performance_calculation_evidence.py`, preserving the public
`app.services.performance_workspace_evidence` facade while reducing
`performance_workspace_evidence.py` from 771 to 461 script-counted lines and moving the largest
remaining source-file hotspot to `src/app/services/risk_workspace_service.py` at 769 script-counted
lines.
Risk workspace request-context dataclasses, latest-business-day fallback, as-of date resolution, and
context construction have been split into `src/app/services/risk_workspace_requests.py`, reducing
`risk_workspace_service.py` from 769 to 633 script-counted lines and moving the largest remaining
source-file hotspot to `src/app/services/portfolio_service.py` at 768 script-counted lines.
Stale private pass-through wrappers around portfolio workspace assembly have been removed from
`src/app/services/portfolio_service.py`; the service now calls the extracted workspace assembly
helpers directly, reducing the file from 768 to 716 script-counted lines and moving the largest
remaining source-file hotspot to `src/app/contracts/portfolio.py` at 754 script-counted lines.
Portfolio workspace response, profile, rebalance, reporting, operations, and control-capability
contracts have been split into `src/app/contracts/portfolio_workspace.py`, preserving the public
`app.contracts.portfolio` facade while reducing that facade from 754 to 281 script-counted lines.
The largest remaining source-file hotspot is now `src/app/services/advisor_brief_source.py` at 742
script-counted lines.
Advisor-brief source formatting, source-contributor ranking, and AI fact-bundle shaping have been
split out of `src/app/services/advisor_brief_source.py`, preserving the compatibility import for
`build_advisor_brief_ai_fact_bundle` while reducing `advisor_brief_source.py` to 508
script-counted lines. The blocking source-file threshold is ratcheted from 742 to 714
script-counted lines, making `src/app/services/portfolio_service.py` the largest residual
source-file hotspot.
Portfolio liquidity and projected-cashflow response assembly now live in
`src/app/services/portfolio_liquidity_response.py`, keeping upstream loading in
`PortfolioService` while reducing `portfolio_service.py` to 689 script-counted lines. The blocking
source-file threshold is ratcheted from 714 to 712 script-counted lines, making
`src/app/clients/advise_client.py` the largest residual source-file hotspot.
Advise proposal lifecycle and memo upstream route forwarding now lives in
`src/app/clients/advise_proposal_client.py`, reducing `advise_client.py` from 712 to 220
script-counted lines while preserving the public `AdviseClient` surface. The blocking source-file
threshold is ratcheted from 712 to 709 script-counted lines, making
`src/app/contracts/risk_workspace.py` the largest residual source-file hotspot.
Risk workspace response OpenAPI examples now live in
`src/app/contracts/risk_workspace_examples.py`, reducing `risk_workspace.py` from 709 to 312
script-counted lines while preserving response model schema names and examples. The blocking
source-file threshold is ratcheted from 709 to 700 script-counted lines, making
`src/app/services/dpm_wave_service.py` the largest residual source-file hotspot.
DPM wave campaign-definition orchestration now lives in
`src/app/services/dpm_wave_campaign_definitions.py`, preserving the public `DpmWaveService`
method surface while reducing `dpm_wave_service.py` from 700 to 479 script-counted lines. The
blocking source-file threshold is ratcheted from 700 to 695 script-counted lines, making
`src/app/services/dpm_command_center_service.py` the largest residual source-file hotspot.
DPM command-center exception-summary orchestration now lives in
`src/app/services/dpm_command_center_exception_summary.py`, preserving the public
`DpmCommandCenterService` method surface while reducing `dpm_command_center_service.py` from 695
to 521 script-counted lines. Shared product-safe Manage command-center error raising now lives in
`src/app/services/dpm_command_center_errors.py`. The blocking source-file threshold is ratcheted
from 695 to 692 script-counted lines, making `src/app/services/advisory_client_protocols.py` the
largest residual source-file hotspot.
Advisor Brief AI and Advise client protocol surfaces now live in
`src/app/services/advisor_brief_client_protocols.py`, preserving the typed protocol contracts used
by the Advisor Brief service, supportability, and workflow-pack helpers while reducing
`advisory_client_protocols.py` from 692 to 630 script-counted lines. The blocking source-file
threshold is ratcheted from 692 to 689 script-counted lines, making
`src/app/clients/lotus_analytics_client.py` and `src/app/services/portfolio_service.py` the
largest residual source-file hotspots.
Analytics workspace-summary request payload construction now lives in
`src/app/clients/lotus_analytics_workspace_payloads.py`, and portfolio catalog response loading
now lives in `src/app/services/portfolio_catalog_payloads.py`. The public analytics client and
`PortfolioService` behavior is preserved while reducing `lotus_analytics_client.py` from 689 to
623 script-counted lines and `portfolio_service.py` from 689 to 680 script-counted lines. The
blocking source-file threshold is ratcheted from 689 to 685 script-counted lines, making
`src/app/services/workbench_service.py` the largest residual source-file hotspot.
Workbench overview enrichment orchestration now lives in
`src/app/services/workbench_overview_enrichment.py`, preserving public Workbench overview,
portfolio-360, and analytics behavior while reducing `src/app/services/workbench_service.py` from
685 to 562 script-counted lines. The blocking source-file threshold is ratcheted from 685 to 680
script-counted lines, making `src/app/services/portfolio_service.py` the largest residual
source-file hotspot.
Portfolio insights response assembly now lives in
`src/app/services/portfolio_insight_response.py`, preserving portfolio insight and exception
semantics while reducing `src/app/services/portfolio_service.py` from 680 to 589 script-counted
lines. The blocking source-file threshold is ratcheted from 680 to 667 script-counted lines,
making `src/app/services/performance_workspace_horizon.py` the largest residual source-file
hotspot.
Performance horizon comparison row assembly now lives in
`src/app/services/performance_workspace_horizon_rows.py`, preserving public performance horizon
comparison semantics while reducing `src/app/services/performance_workspace_horizon.py` from 667
to 441 script-counted lines. The blocking source-file threshold is ratcheted from 667 to 664
script-counted lines, making `src/app/contracts/reporting_query.py` the largest residual
source-file hotspot.
Reporting query contracts have been split into status-event, job-search, snapshot-lineage, and
example modules behind the existing `src/app/contracts/reporting_query.py` compatibility facade.
The blocking source-file threshold is ratcheted from 664 to 662 script-counted lines, making
`src/app/contracts/reporting_batches.py` the largest residual source-file hotspot.
Performance workspace common, summary-response, and details-response contracts now live in
`src/app/contracts/performance_workspace_common.py`,
`src/app/contracts/performance_workspace_summary_contract.py`, and
`src/app/contracts/performance_workspace_details_contract.py`, reducing
`performance_workspace.py` to a 79-line compatibility facade while preserving the public
`app.contracts.performance_workspace` import surface. Report-batch examples, shared status
literals, materialization/status/control contracts, worker runtime contracts, and scheduler
contracts now live in dedicated `reporting_batch_*` modules, reducing `reporting_batches.py` to a
75-line compatibility facade. The blocking source-file threshold is ratcheted from 662 to 658
script-counted lines, making `src/app/services/proposal_service.py` the largest residual
source-file hotspot.
Proposal lifecycle transition orchestration now lives in
`src/app/services/proposal_transition_service.py`, preserving the public `ProposalService`
submit/approval/client-consent method surface while reducing `proposal_service.py` from 658 to
520 script-counted lines. The blocking source-file threshold is ratcheted from 658 to 646
script-counted lines, making `src/app/contracts/advisor_brief.py` the largest residual
source-file hotspot.
Advisor Brief presentation/source item contracts now live in
`src/app/contracts/advisor_brief_items.py`, and source-supportability contracts now live in
`src/app/contracts/advisor_brief_supportability.py`, preserving the public
`app.contracts.advisor_brief` facade while reducing it from 646 to 398 script-counted lines. The
blocking source-file threshold is ratcheted from 646 to 639 script-counted lines. The current
performance workspace detail-view slice ratchets the ceiling again to 632 script-counted lines,
making `src/app/router_registry.py` and `src/app/services/risk_workspace_service.py` the largest
residual source-file hotspots. The prior DPM router-group boundary slice then moved DPM
registration groups into `src/app/router_groups/dpm.py`, reducing `router_registry.py` to 294
script-counted lines and leaving `src/app/services/risk_workspace_service.py` as the single
632-line source-file ceiling blocker.
The current risk workspace cache-boundary slice moves cache-key construction and response replay
cache-status/correlation stamping into `src/app/services/risk_workspace_cache.py`, reducing
`risk_workspace_service.py` below the source-file ceiling and ratcheting the blocking threshold to
630 script-counted lines.
The current advisory protocol-boundary slice splits bank-demo proof, copilot, workspace, cockpit,
policy, and proposal protocol families out of `src/app/services/advisory_client_protocols.py`.
The compatibility facade remains in place for existing imports, but advisory services now import
their focused protocol families directly. The blocking threshold is ratcheted to 628
script-counted lines, with `src/app/clients/dpm_wave_client.py` as the largest residual hotspot.
The current DPM wave client-boundary slice splits Manage rebalance-wave core, campaign-definition,
and campaign-workflow route forwarding into focused client mixins behind the existing
`DpmWaveClientMixin` compatibility facade. The blocking threshold is ratcheted to 623
script-counted lines, with `src/app/clients/lotus_analytics_client.py` as the largest residual
hotspot.
The current analytics risk-client boundary slice moves risk calculate, concentration, drawdown,
rolling metrics, and historical-attribution forwarding into `lotus_analytics_risk_client.py`
behind the public `LotusAnalyticsClient` surface. The blocking threshold is ratcheted to 618
script-counted lines, with `src/app/services/foundation_service.py` as the largest residual
hotspot.
The current Foundation catalog-payload boundary slice moves portfolio catalog item parsing into
`foundation_catalog_payloads.py` while preserving the `FoundationService` API surface. The
blocking threshold is ratcheted to 610 script-counted lines, with
`src/app/clients/lotus_core_query_client.py` as the largest residual hotspot.
The current Lotus Core lookup-client boundary slice moves portfolio, instrument, and currency
lookup forwarding into `lotus_core_lookup_client.py` while preserving the public
`LotusCoreQueryClient` surface. The blocking threshold is ratcheted to 606 script-counted lines,
with `src/app/services/dpm_client_protocols.py` as the largest residual hotspot.
The current DPM wave protocol-family boundary slice moves `DpmWaveClient` into
`dpm_wave_client_protocols.py` and updates DPM wave services to import the focused protocol module
directly. The blocking threshold is ratcheted to 595 script-counted lines, with
`src/app/contracts/dpm_command_center.py` as the largest residual hotspot.
The current DPM portfolio-memory contract-family boundary slice moves
`DpmPortfolioMemorySupportability` and `DpmPortfolioMemoryGatewayResponse` into
`src/app/contracts/dpm_portfolio_memory.py` while preserving the public
`dpm_command_center` compatibility facade. The blocking threshold is ratcheted from 595 to 591
script-counted lines, with `src/app/services/foundation_service.py` as the largest residual
hotspot.
The current Foundation optional-workspace boundary slice moves optional performance, rebalance,
reporting, evidence-summary, and workflow-cue parsing into
`src/app/services/foundation_workspace_optional.py`. `FoundationService` is reduced from 591 to
316 script-counted lines and stays focused on source loading and response orchestration. The
blocking threshold is ratcheted from 591 to 589 script-counted lines, with
`src/app/services/portfolio_service.py` as the largest residual hotspot.
The current portfolio holdings-orchestration boundary slice moves portfolio book, liquidity,
projected cashflow, allocation, and position-book orchestration into
`src/app/services/portfolio_holdings_service.py`. `PortfolioService` is reduced from 589 to 314
script-counted lines, the extracted mixin is 347 lines, and the blocking threshold is ratcheted
from 589 to 575 script-counted lines, with `src/app/observability/analytics_ui.py` as the largest
residual hotspot.
The current analytics UI field-governance boundary slice moves bounded analytics UI labels,
forbidden fields, event vocabularies, and log/audit field validators into
`src/app/observability/analytics_ui_fields.py` while preserving the public
`app.observability.analytics_ui` import surface. `src/app/observability/analytics_ui.py` is reduced
from 575 to 343 script-counted lines, and the blocking threshold is ratcheted from 575 to 567
script-counted lines, with `src/app/contracts/dpm_waves.py` as the largest residual hotspot.
The current DPM wave campaign-definition contract slice moves campaign-definition request, launch,
lifecycle-command, and gateway response contracts into
`src/app/contracts/dpm_wave_campaign_definitions.py` while preserving the public `dpm_waves`
compatibility facade. `src/app/contracts/dpm_waves.py` is reduced from 567 to 480 script-counted
lines, and the blocking threshold is ratcheted from 567 to 562 script-counted lines, with
`src/app/services/workbench_service.py` as the largest residual hotspot.
The current Workbench snapshot-context slice moves Core portfolio/snapshot fan-out,
product-safe Core snapshot error mapping, and `WorkbenchSnapshotContext` assembly into
`src/app/services/workbench_snapshot_context.py` while preserving the public `WorkbenchService`
surface. `src/app/services/workbench_service.py` is reduced from 562 to 515 script-counted lines,
and the blocking threshold is ratcheted from 562 to 560 script-counted lines, with
`src/app/contracts/reporting.py` as the largest residual hotspot.
The current reporting job contract slice moves report-job request, error, handle, and status DTOs
into `src/app/contracts/reporting_jobs.py` while preserving the public `app.contracts.reporting`
import surface. `src/app/contracts/reporting.py` is reduced from 560 to 355 script-counted lines,
the extracted contract module is 221 lines, and the blocking threshold is ratcheted from 560 to
559 script-counted lines, with `src/app/clients/lotus_analytics_client.py` as the largest residual
hotspot.
The current analytics performance client slice moves TWR, MWR, composite, contribution,
attribution, lineage, and workspace-summary route methods into
`src/app/clients/lotus_analytics_performance_client.py` while preserving the public
`LotusAnalyticsClient` surface. `src/app/clients/lotus_analytics_client.py` is reduced from 559 to
290 script-counted lines, the extracted performance mixin is 298 lines, and the blocking threshold
is ratcheted from 559 to 556 script-counted lines, with
`src/app/services/risk_workspace_service.py` as the largest residual hotspot.
The current risk workspace attribution service slice moves attribution request normalization,
blocked-response handling, cache orchestration, upstream fan-out, and response mapping into
`src/app/services/risk_workspace_attribution_service.py` while preserving the public
`RiskWorkspaceService.get_attribution` surface. `risk_workspace_service.py` is reduced from 556 to
380 script-counted lines, the extracted attribution orchestration mixin is 161 lines, and the
blocking threshold is ratcheted from 556 to 549 script-counted lines, with
`src/app/services/dpm_pm_operating_quality_service.py` as the largest residual hotspot.
The current DPM PM operating-quality summary slice moves Manage score-run evidence loading,
Lotus AI workflow-pack execution, missing-score-run validation, and summary response assembly into
`src/app/services/dpm_pm_operating_quality_summary_service.py` while preserving the public
`request_pm_operating_quality_summary` surface. `dpm_pm_operating_quality_service.py` is reduced
from 549 to 360 script-counted lines, the extracted summary workflow mixin is 169 lines, and the
blocking threshold is ratcheted from 549 to 536 script-counted lines, with
`src/app/clients/advise_proposal_client.py` as the largest residual hotspot.
The previous Advise proposal memo client slice moved proposal memo create/read/projection/review,
report-package, AI-commentary, lineage, and replay-evidence route methods into
`src/app/clients/advise_proposal_memo_client.py` while preserving the public `AdviseClient`
surface. `advise_proposal_client.py` is reduced from 536 to 370 script-counted lines, the
extracted memo mixin is 154 lines, and the blocking threshold is ratcheted from 536 to 535
script-counted lines, with `src/app/clients/lotus_core_query_client.py` as the largest residual
hotspot.
The previous Lotus Core simulation-session client slice moved simulation-session create, change,
projected-position, and projected-summary route methods into
`src/app/clients/lotus_core_simulation_client.py` while preserving the public
`LotusCoreQueryClient` surface. `lotus_core_query_client.py` is reduced from 535 to 481
script-counted lines, the extracted simulation mixin is 78 lines, and the blocking threshold is
ratcheted from 535 to 525 script-counted lines, with
`src/app/services/performance_workspace_attribution.py` as the largest residual hotspot.
The current performance attribution supportability slice moves attribution reason,
residual-materiality, and supportability-evidence parsers into
`src/app/services/performance_workspace_attribution_supportability.py` while preserving the
existing `performance_workspace_attribution` import surface. `performance_workspace_attribution.py`
is reduced from 525 to 471 script-counted lines, the extracted parser module is 65 lines, and the
blocking threshold is ratcheted from 525 to 522 script-counted lines, with
`src/app/services/risk_workspace_rolling.py` as the largest residual hotspot.
The current risk rolling window-boundary slice moves rolling-window, metric-series,
dependency-context, and window-length mapping into
`src/app/services/risk_workspace_rolling_windows.py` while preserving the public rolling response
mapper. The blocking threshold is ratcheted from 522 to 521 script-counted lines, with
`src/app/services/dpm_command_center_service.py` as the largest residual hotspot.
The risk drawdown mapper has been split into
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
`parse_horizon_comparison_result` from 172 lines to 50 lines. Performance horizon-comparison
contract models now live in `src/app/contracts/performance_horizon.py`, reducing the performance
workspace contract facade while preserving compatibility imports for existing consumers. The
foundation core snapshot parser has been split into validation, section extraction, totals,
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
script-counted lines while preserving the public `DpmWaveService` surface. The Advise
workspace client-boundary slice moves advisory-workspace upstream route methods into
`src/app/clients/advise_workspace_client.py`, reducing `advise_client.py` from 1,062 to 909
script-counted lines while preserving the public `AdviseClient` surface. The Advise policy
client-boundary slice moves advisory policy-pack, policy-evaluation, sign-off, report-package, and
AI-evidence upstream route methods into `src/app/clients/advise_policy_client.py`, reducing
`advise_client.py` from 914 to 712 script-counted lines while preserving the public `AdviseClient`
surface. The Advise proposal client-boundary slice moves proposal lifecycle and memo
upstream route methods into `src/app/clients/advise_proposal_client.py`, reducing
`advise_client.py` from 712 to 220 script-counted lines while preserving the public `AdviseClient`
surface. The portfolio
transaction workflow slice moves transaction ledger, income summary, and activity summary
orchestration into `src/app/services/portfolio_transaction_service.py`, reducing
`portfolio_service.py` to 811 physical lines while preserving the public `PortfolioService`
surface and Lotus Core transaction request behavior. The current longest functions are
49-line helpers:
`get_transaction_ledger` in `portfolio_transaction_service.py` and `get_portfolio_transactions` in
`lotus_core_query_client.py`.

## Progressive Enforcement

1. Phase 1: report-only quality baseline.
2. Phase 2: fail only new architecture regressions.
3. Phase 3: enforce thresholds for largest modules, function length, complexity, and import rules.
4. Phase 4: enterprise-readiness gate requiring architecture, API, security, observability, and
   docs scorecard targets to pass.
