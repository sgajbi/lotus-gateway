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

1. `src/app/services/portfolio_service.py` at 3,155 lines,
2. `src/app/services/performance_workspace_service.py` at 1,673 lines,
3. `src/app/services/advisor_brief_service.py` at 1,581 lines,
4. `src/app/services/dpm_command_center_service.py` at 1,217 lines,
5. `src/app/services/dpm_wave_service.py` at 1,030 lines.

The prior longest function, `register_routers` in `src/app/router_registry.py`, has been split
into explicit route-family groups and a short registration loop. The performance workspace
response builder has also been split into request-context, summary/detail, evidence, and assembly
helpers. The advisor-brief response builder has been split into source-context, AI narrative,
runtime supportability, and response assembly helpers. The risk drawdown mapper has been split into
period mapping, supportability, state, metadata, and payload helpers. The risk rolling mapper has
been split into period mapping, dependency context, supportability, state, metadata, Sharpe
fallback, and payload helpers. The risk attribution mapper has been split into period mapping,
set/contributor parsing, state, metadata, and payload helpers. The risk concentration mapper has
been extracted to `src/app/services/risk_workspace_concentration.py`, reducing
`risk_workspace_service.py` below 2,000 lines while preserving source-owned concentration fields
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
selection, and explicit response builders, reducing `_build_evidence_view` from 134 lines to
58 lines. Portfolio exception-summary construction has been extracted to
`src/app/services/portfolio_exception_summaries.py`, reducing `portfolio_service.py` from 2,839 to
2,744 lines and reducing `_build_portfolio_exception_summaries` from 133 lines to a short
delegation over readiness status. Performance workspace capability-input derivation has been
split into `PerformanceCapabilityInputs`, `build_performance_capability_inputs`, and
`resolve_history_date_range`, reducing `build_workspace_capabilities` from 127 lines to 99 lines
while keeping capability payload assembly in the original module. The current branch also splits
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
attribution trend query metadata extraction, risk rolling query metadata extraction, and
advisor-brief query metadata extraction. The current longest function is `_build_evidence_view`
at 58 lines.

## Progressive Enforcement

1. Phase 1: report-only quality baseline.
2. Phase 2: fail only new architecture regressions.
3. Phase 3: enforce thresholds for largest modules, function length, complexity, and import rules.
4. Phase 4: enterprise-readiness gate requiring architecture, API, security, observability, and
   docs scorecard targets to pass.
