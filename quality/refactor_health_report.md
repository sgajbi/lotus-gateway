# Refactor Health Report

Date: 2026-06-13
Phase: baseline/report-only

## Current Direction

Recent gateway hardening has reduced monolithic Workbench, router-registry, performance workspace,
advisor-brief, risk drawdown, risk rolling, and risk attribution responsibilities by extracting
focused service adapters and has extracted risk concentration response mapping behind a dedicated
service module. Shared risk unavailable-envelope helpers now centralize risk upstream failure
detail mapping, risk-service unavailable supportability, and risk metadata construction while
preserving public behavior and keeping CI green. The risk drawdown response mapper has now been
extracted to a dedicated drawdown module, reducing `risk_workspace_service.py` to 1,594 lines while
leaving request orchestration and cache semantics in the workspace service. The risk rolling
response mapper, Sharpe fallback policy, and unavailable envelope have been extracted to a
dedicated rolling module, reducing `risk_workspace_service.py` to 1,185 lines while preserving
retry, request, and cache semantics in the workspace service. The risk attribution response
mapper, blocked/unavailable envelopes, and focused attribution module tests have been extracted to
a dedicated attribution module, reducing `risk_workspace_service.py` to 780 lines while preserving
request, cache, and correlation semantics in the workspace service. The risk summary response
mapper and focused summary module tests have been extracted to a dedicated summary module,
reducing `risk_workspace_service.py` to 540 lines while preserving request, cache, and correlation
semantics in the workspace service. Platform capability normalization has been extracted to
`platform_capabilities_normalization.py`, reducing `platform_capabilities_service.py` to 330 lines
while preserving upstream orchestration, timeout handling, correlation propagation, and
partial-failure collection in the service. Shell-bootstrap contract assembly and workspace
descriptor state mapping have been extracted to `platform_capabilities_shell.py`, reducing
`platform_capabilities_normalization.py` to 355 lines while keeping shell navigation evidence
separately testable. Portfolio workspace-control capability construction has been extracted to
`portfolio_workspace_controls.py`, reducing `portfolio_service.py` to 2,839 lines and lowering the
longest-function baseline to 172 lines. The performance horizon comparison parser has now been
split into diagnostic, row-selection, row-construction, period-block, and date-resolution helpers,
reducing the parser itself from 172 lines to 50 lines and lowering the repository
longest-function baseline to 153 lines. The foundation core snapshot parser has now been split
into validation, section extraction, totals, enrichment indexing, position projection, allocation
finalization, and portfolio identity helpers, reducing `_parse_core_snapshot` from 153 lines to
38 lines and lowering the repository longest-function baseline to 144 lines. The advisor-brief
narrative-state builder has now been split into source fallback, AI result classification,
completed-output projection, unavailable-risk construction, and route-resolution helpers, reducing
`_build_advisor_brief_narrative_state` from 144 lines to 30 lines and lowering the repository
longest-function baseline to 143 lines. Platform-capabilities orchestration has now been split
into task assembly, primary-source classification, policy-result extraction, optional-source
merging, shared source-result mapping, and response construction helpers, reducing
`get_platform_capabilities` from 143 lines to 32 lines and lowering the repository
longest-function baseline to 135 lines. Performance attribution trend orchestration has now been
split into request-context, window-pair construction, attribution fan-out, and response assembly
helpers, reducing `get_performance_attribution_trend` from 135 lines to 56 lines and lowering the
repository longest-function baseline to 134 lines. Performance evidence-view orchestration has now
been split into request context, fetch state, requested-calculation selection, and explicit response
builders, later adding partial-failure recording extraction to reduce `_build_evidence_view` to
51 lines. Portfolio exception-summary construction has now been
extracted to `portfolio_exception_summaries.py`, reducing `portfolio_service.py` from 2,839 lines
to 2,744 lines and reducing `_build_portfolio_exception_summaries` from 133 lines to a short
readiness delegation. Performance workspace capability-input derivation has now been split into
explicit capability input and history-date helpers, reducing `build_workspace_capabilities` from
127 lines to 99 lines. A later hardening batch further split portfolio workspace source/analytics
assembly, portfolio insight rules, performance workspace summary/detail and horizon contexts,
foundation workspace assembly, risk rolling and attribution orchestration, shell workspace
descriptor specs, transaction query contracts, DPM exception-summary workflow orchestration,
advisor-brief source talking-point and review-action orchestration, and portfolio workflow-action
assembly. Workbench performance snapshot parsing has now been split into upstream-result
validation, period-map extraction, period selection, return-payload extraction, and shared
partial-failure construction. Horizon comparison row construction has now been split into period,
economics, and return-field projection helpers. Performance workspace summary parsing now has
separate upstream-result validation, period-payload selection, block extraction, and parsed-summary
projection helpers. Performance evidence-view mapping now has separate payload normalization,
reason construction, stage/snapshot projection, and artifact projection helpers. Foundation
workspace response assembly now has separate core-view, optional-view, and final response
composition helpers. PM operating quality summary orchestration now has separate Manage evidence
context loading, score-run validation, Lotus AI workflow execution, and gateway response
composition helpers. Risk attribution supportability construction now has separate base,
active-risk, and total-risk benchmark-exposure helpers. Attribution trend row parsing now has
separate upstream-result validation, period selection, period-payload extraction, and row
projection helpers. Portfolio position parsing now has a per-position mapper and reusable
valuation conversion helpers without adding monetary-float allowlist debt. Performance workspace
request-context assembly now has separate overview, report-window, and benchmark-context helpers.
The latest focused batch split advisor-brief review and read-route dependencies, risk attribution
route queries, portfolio performance snapshot query parsing, performance summary route
dependencies, risk drawdown orchestration, core snapshot summary parsing, and portfolio workspace
response-component assembly. Shell workspace descriptor-state extraction and rebalance
supportability failure-recording extraction then lowered the repository longest-function baseline
to 74 lines. The current 50-commit branch then split portfolio memory search filters, portfolio
workspace assembly state, advisor-brief fact sections, portfolio liquidity loading, transaction
ledger and risk-attribution request contexts, DPM operations handoff response assembly, shared
analytics async polling, workspace-summary payload assembly, portfolio transaction-summary
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
summary-count merging are now split out of the supportability payload extractor, and frequency-row
selection, peer-row validation, point construction, and active-return calculation are now split out
of the public chart-point mapper.
Shell-bootstrap section assembly now has separate supportability, freshness, evidence, versioning,
and caching helpers, lowering the repository longest-function baseline to 54 lines.
Portfolio performance snapshot projection now has separate sparkline, unavailable-state, and
partial-failure helpers while keeping the current longest-function baseline at 54 lines.
Contribution summary merging now has explicit detail-vs-summary selection helpers, keeping merge
policy reusable and separately auditable.
Risk rolling response mapping now has separate supportability enrichment and fallback warning
assembly helpers while keeping state resolution and response contract assembly unchanged.
Risk drawdown routing now has named OpenAPI query parameter descriptors separate from the public
query dependency, preserving contract metadata while reducing dependency-body size.
HTTP resilience retry handling now separates one-shot JSON/binary request sending, retryable
status decisions, retryable exception decisions, and backoff sleeping while preserving existing
timeout, network-error, status-retry, redirect, and non-JSON payload behavior. Portfolio
transaction-ledger response orchestration now loads transaction payloads behind a dedicated helper,
reducing `get_transaction_ledger` from 54 lines to 49 lines. Portfolio workspace source loading
now separates concurrent source gathering from typed source-result assembly, reducing
`_load_portfolio_workspace_sources` from 54 lines to 29 lines. Lotus Core transaction query
parameter construction now has a dedicated helper, reducing `get_portfolio_transactions` from 54
lines to 49 lines while keeping advanced filter and sorting parameters contract-tested.
Foundation optional-upstream handling now centralizes unavailable tuple construction behind a
failure-context helper, reducing `_unpack_optional_upstream` from 54 lines to 43 lines while
preserving warning and partial-failure behavior. Archive document error mapping now separates
specific archive error specs, fallback error specs, and safe HTTP exception construction, reducing
`_raise_archive_error` from 54 lines to 12 lines while preserving no-leak error tests.
Risk drawdown period mapping now separates valid result iteration and period partial-failure
recording, reducing `_map_drawdown_period_results` from 54 lines to 49 lines while preserving
drawdown unit and router integration behavior.
Performance workspace response orchestration now groups summary-view and response-component
construction behind `_build_workspace_response_parts`, reducing
`_build_performance_workspace_response` from 54 lines to 47 lines. Attribution-trend context
building now separates final context assembly behind `_assemble_attribution_trend_request_context`,
reducing `_build_attribution_trend_request_context` from 54 lines to 43 lines and lowering the
repository longest-function baseline to 53 lines.
Benchmark catalog result parsing now separates upstream failure recording, catalog record
projection, and duplicate-option merge policy, reducing `parse_benchmark_catalog_result` from 53
lines to 43 lines. Risk attribution response mapping now separates response-part assembly from the
public response constructor, reducing `map_attribution_response` from 53 lines to 36 lines. These
two mappers are no longer in the top hotspot list, while the repository longest-function baseline
remains 53 lines because other functions tie at that size.
Portfolio insight response orchestration now separates concurrent source loading behind a typed
`PortfolioInsightSources` bundle, reducing `get_portfolio_insights` from 53 lines to 27 lines.
Core snapshot current-position parsing now separates section input extraction, enrichment
indexing, row projection, and weight calculation, reducing `extract_current_positions` from 53
lines to 19 lines. These two functions are no longer in the top hotspot list, while the repository
longest-function baseline remains 53 lines because two functions still tie at that size.
Performance horizon-comparison routing now separates query metadata into named FastAPI query
descriptors, reducing `build_performance_horizon_comparison_query` from 53 lines to 16 lines
while preserving query-context and OpenAPI contract tests. The repository longest-function baseline
remains 53 lines because `_build_source_metrics` now owns the only remaining 53-line hotspot.
Advisor-brief source metric construction now uses a shared metric helper, reducing
`_build_source_metrics` from 53 lines to 48 lines and lowering the repository longest-function
baseline to 52 lines.
Risk concentration routing now separates query metadata into named descriptors, reducing
`get_workbench_risk_concentration` from 52 lines to 26 lines while preserving router query
behavior. Workbench analytics response construction now separates allocation buckets, top changes,
controlled risk-gap posture, and return metrics behind `WorkbenchAnalyticsParts`, reducing
`get_workbench_analytics` from 52 lines to 35 lines while preserving the controlled risk warning
and partial-failure behavior. The repository longest-function baseline remains 52 lines.
Workbench rebalance payload handling now uses a shared unavailable recorder, reducing
`_unpack_rebalance_payload` from 52 lines to 44 lines. Portfolio readiness response construction
now separates status derivation from indicator assembly, reducing `_build_readiness_indicators`
from 52 lines to 32 lines. The repository longest-function baseline remains 52 lines.
HTTP resilience JSON retry orchestration now separates response retry decisions, request-error
retry decisions, and per-attempt dispatch from `request_with_retry`, lowering the repository
longest-function baseline to 51 lines while preserving timeout, network-error, retry-status, and
non-JSON payload behavior in the focused HTTP resilience test pack.
DPM proof-pack PM memo orchestration now separates Lotus AI workflow execution and product-safe AI
error mapping out of the public service method, reducing `request_proof_pack_pm_memo` from 51
lines to 27 lines while preserving service and router integration behavior.
Portfolio readiness orchestration now separates concurrent workspace, readiness, positions,
allocations, and transaction-probe loading behind a typed source bundle, reducing
`get_portfolio_readiness` from 51 lines to 28 lines while preserving unit and router integration
behavior.
Performance workspace capability construction now groups contribution-ranking, attribution-detail,
and contribution-detail capability decisions behind a typed detail-capability bundle, reducing
`build_workspace_capabilities` from 51 lines to 35 lines while preserving focused capability tests.
Portfolio allocation payload loading now separates raw AUM, positions, and allocation query results
behind a typed helper, reducing `_load_portfolio_allocation_payloads` from 51 lines to 31 lines
while preserving focused unit and router integration behavior.
Workbench sandbox change application now groups optional policy feedback, warning, and
partial-failure state behind a typed helper, reducing `apply_sandbox_changes` from 51 lines to 46
lines while preserving focused unit and router integration behavior.
Performance evidence-view orchestration now delegates response-state resolution and warning or
partial-failure recording to a focused helper, reducing `_build_evidence_view` from 51 lines to 33
lines and lowering the repository longest-function baseline to 50 lines.
The final PR-readiness batch then split proposal list query metadata, Workbench rebalance
unavailable payload recording, render output-format supportability, workspace-summary request
context, benchmark catalog result parsing, chart-point row normalization, attribution result
payload parsing, comparative-summary economics normalization, analytics async poll-attempt
handling, and rolling risk request-context construction. The tracked longest-function baseline is
now 49 lines at branch head `1b2a4e5`, down from 50 lines on `origin/main` at `e7260c1`.
The current closure slice extracts portfolio position-book summary derivation, position parsing,
valuation fallback handling, cash-position summarization, and top-position ranking into
`portfolio_position_book.py`, reducing `portfolio_service.py` from 3,337 to 3,241 lines while
preserving the 49-line longest-function baseline. `portfolio_service.py` remains the largest-file
hotspot even though the position-book mapper is now separately testable. The remaining work is
still substantial: large portfolio, performance workspace, advisor-brief orchestration, contract,
and client modules remain.
The current transaction-ledger slice extracts `PortfolioTransactionsRequestContext`, response
metadata assembly, transaction row parsing, event-identifier preservation, and quantized amount
conversion into `portfolio_transaction_ledger.py`. It reduces `portfolio_service.py` from 3,062 to
2,993 lines while preserving the 49-line longest-function baseline and keeping upstream request,
cache, and filter pass-through behavior in `PortfolioService`.
The current Lotus Core transaction query-parameter slice extracts deterministic query-parameter
construction into `lotus_core_transaction_params.py`. It reduces `lotus_core_query_client.py` from
622 to 574 measured lines, removes `_portfolio_transaction_query_params` from the top
function-hotspot list, and preserves the public client method signature plus route-level filter
contract.
The current portfolio liquidity payload slice extracts concurrent AUM, cash-balance, and projected
cashflow loading into `portfolio_liquidity_payloads.py`. It reduces `portfolio_service.py` from
2,993 to 2,968 measured lines, removes `_load_portfolio_liquidity_payloads` from the top
function-hotspot list, and preserves liquidity request parameter forwarding plus required upstream
payload validation behavior.
The current merged transaction request-context slice separates transaction request construction
and cache-key responsibility from the public ledger method, reducing `portfolio_service.py` from
2,968 to 2,898 lines while preserving upstream filter, cache, and ledger response behavior.
The current merged performance workspace response slice extracts summary-view and response-part
assembly into `performance_workspace_response.py`, reducing `performance_workspace_service.py`
from 1,724 to 1,607 lines and making response contract construction directly unit-testable.
The current merged portfolio workspace response slice extracts response component/parts models and
pure `PortfolioWorkspaceResponse` construction into `portfolio_workspace_response.py`, reducing
`portfolio_service.py` from 2,898 to 2,872 lines while preserving the 49-line longest-function
baseline.
The current transaction client-kwargs slice moves upstream argument projection into
`portfolio_transaction_ledger.py`, reducing `portfolio_service.py` from 2,872 to 2,854 lines while
preserving the 49-line longest-function baseline.
The current transaction page-context slice moves income/activity transaction page defaults into
`portfolio_transaction_ledger.py`, reducing `portfolio_service.py` from 2,854 to 2,797 lines while
preserving the 49-line longest-function baseline.
The current portfolio workspace performance parser slice moves upstream performance summary
payload parsing into `portfolio_workspace_performance.py`, reducing `portfolio_service.py` from
2,797 to 2,772 lines while preserving the 49-line longest-function baseline.
The current portfolio workspace rebalance parser slice moves manage-owned rebalance run and
supportability payload parsing into `portfolio_workspace_rebalance.py`, reducing
`portfolio_service.py` from 2,772 to 2,729 lines while preserving the 49-line longest-function
baseline.
The current portfolio source-readiness parser slice moves source-readiness bucket, reason,
supportability, and indicator mapping into `portfolio_source_readiness.py`, reducing
`portfolio_service.py` from 2,729 to 2,629 lines while preserving the 49-line longest-function
baseline.
The current portfolio transaction summary mapper slice moves income/activity response mapping,
money aggregation, tax bucketing, and transaction-date filtering into
`portfolio_transaction_summary.py`, reducing `portfolio_service.py` from 2,629 to 2,438 lines
while preserving the 49-line longest-function baseline.
The current portfolio workflow mapper slice moves workflow launch cue construction, readiness
status labels, empty-book setup sequencing, and supported-cue action ordering into
`portfolio_workflow.py`, reducing `portfolio_service.py` from 2,438 to 2,076 lines while
preserving the 49-line longest-function baseline.
The current portfolio workflow contract slice moves readiness and workflow response models into
`portfolio_workflow.py`, keeps the legacy `app.contracts.portfolio` import surface intact, and
reduces `portfolio.py` from 2,226 to 1,974 lines while preserving OpenAPI contract tests.
The current portfolio transaction contract slice moves transaction row and ledger response models
into `portfolio_transactions.py`, keeps the legacy `app.contracts.portfolio` import surface
intact, refreshes the governed monetary-float allowlist for the moved response float fields, and
reduces `portfolio.py` from 1,885 to 1,717 lines while preserving OpenAPI contract tests.
The current portfolio performance snapshot contract slice moves the shared partial-failure model
and performance snapshot models into `portfolio_common.py` and
`portfolio_performance_snapshot.py`, keeps the legacy `app.contracts.portfolio` import surface
intact, refreshes the governed monetary-float allowlist for the moved percentage fields, and
reduces `portfolio.py` from 1,717 to 1,632 lines while preserving OpenAPI contract tests and the
49-line longest-function baseline.
The current portfolio income/activity contract slice moves money summary, income summary, and
activity summary contracts into `portfolio_activity_income.py`, keeps the legacy
`app.contracts.portfolio` import surface intact, refreshes the governed monetary-float allowlist
for the moved money fields, and reduces `portfolio.py` from 1,632 to 1,464 lines while preserving
OpenAPI contract tests and the 49-line longest-function baseline.
The current portfolio holdings contract slice moves shared identity/summary contracts into
`portfolio_core.py` and cash, allocation, position, and combined book contracts into
`portfolio_holdings.py`, keeps the legacy `app.contracts.portfolio` import surface intact,
refreshes the governed monetary-float allowlist for the moved holdings fields, and reduces
`portfolio.py` from 1,464 to 954 lines while preserving OpenAPI contract tests and the 49-line
longest-function baseline.
The current risk drawdown contract slice moves drawdown payload contracts into
`risk_workspace_drawdown.py`, keeps the legacy `app.contracts.risk_workspace` import surface
intact, refreshes the governed monetary-float allowlist for the moved drawdown-at-risk fields, and
reduces `risk_workspace.py` from 2,043 to 1,734 lines while preserving risk workspace contract
tests and the 49-line longest-function baseline.
The current reporting batch contract slice moves batch, worker-run, scheduler, and shared
reporting error-example contracts into `reporting_batches.py` and `reporting_errors.py`, keeps the
legacy `app.contracts.reporting` import surface intact, and reduces `reporting.py` from 1,840 to
1,184 lines while preserving reporting contract/router tests and the 49-line longest-function
baseline.
The current reporting query contract slice moves report-job list, lifecycle event, input snapshot,
upstream-call, and snapshot-lineage contracts into `reporting_query.py`, keeps the legacy
`app.contracts.reporting` import surface intact, and reduces `reporting.py` from 1,184 to 532
lines while preserving reporting query contract tests and the 49-line longest-function baseline.
The current risk concentration contract slice moves concentration payload and driver contracts
into `risk_workspace_concentration.py`, keeps the legacy `app.contracts.risk_workspace` import
surface intact, refreshes the governed monetary-float allowlist for the moved concentration weight
fields, and reduces `risk_workspace.py` from 1,647 to 1,343 lines while preserving focused risk
workspace tests and the 49-line longest-function baseline.
The current risk rolling contract slice moves rolling metric summary, series, dependency,
period-result, request-context, and payload contracts into `risk_workspace_rolling.py`, keeps the
legacy `app.contracts.risk_workspace` import surface intact, refreshes the governed monetary-float
allowlist for the moved rolling metric-value field, and reduces `risk_workspace.py` from 1,343 to
969 lines while preserving focused risk workspace tests and the 49-line longest-function baseline.
The current risk attribution contract slice moves attribution control, contributor, set,
period-result, methodology-context, and payload contracts into `risk_workspace_attribution.py`,
keeps the legacy `app.contracts.risk_workspace` import surface intact, refreshes the governed
monetary-float allowlist for the moved attribution contribution fields, and reduces
`risk_workspace.py` from 969 to 678 lines while preserving focused risk workspace tests and the
49-line longest-function baseline.
The current performance contribution contract slice moves contribution row, position, level,
smoothing-evidence, source-economics-evidence, and summary contracts into
`performance_contribution.py`, keeps the legacy `app.contracts.performance_workspace` import
surface intact, refreshes the governed monetary-float allowlist for the moved performance
contribution fields, and reduces `performance_workspace.py` from 1,539 to 1,499 lines while
preserving focused performance workspace/advisor brief tests and the 49-line longest-function
baseline.
The current performance attribution contract slice moves attribution row, level, reason,
residual-materiality, supportability-evidence, summary, trend-row, and trend-response contracts
into `performance_attribution.py`, keeps the legacy `app.contracts.performance_workspace` import
surface intact, refreshes the governed monetary-float allowlist for the moved performance
attribution fields, and reduces `performance_workspace.py` from 1,499 to 1,101 lines while
preserving focused performance workspace/advisor brief/OpenAPI tests and the 49-line
longest-function baseline.
The current performance evidence contract slice moves calculation, source-supportability, stage,
upstream-snapshot, artifact, and evidence-view contracts into `performance_evidence.py`, keeps the
legacy `app.contracts.performance_workspace` import surface intact, preserves the governed
monetary-float allowlist without churn, and reduces `performance_workspace.py` from 1,101 to 903
lines while preserving focused evidence/capabilities/response tests and the 49-line
longest-function baseline.
The current performance evidence-view builder slice moves evidence request context, fetch state,
source-supportability collection, durable calculation evidence fetching, and supported/partial/
unavailable evidence response resolution into `performance_workspace_evidence.py`, reducing
`performance_workspace_service.py` from 1,611 to 1,413 measured lines while preserving focused
evidence/service tests, Workbench performance evidence behavior, and the 49-line longest-function
baseline.
The current portfolio transaction-summary context slice moves reporting-window resolution, YTD
transaction pagination, page-row filtering, reporting-currency fallback, and requested-window row
selection into `portfolio_transaction_summary.py`, reducing `portfolio_service.py` from 1,970 to
1,888 physical lines while preserving income/activity endpoint behavior and the 49-line
longest-function baseline.
The current portfolio workspace payload mapper slice moves portfolio identity/profile projection,
workspace summary construction, cashflow outlook projection, display-name fallback, and operations
readiness projection into `portfolio_workspace_payloads.py`, reducing `portfolio_service.py` from
1,888 to 1,826 physical lines while preserving workspace response behavior and the 49-line
longest-function baseline.
The current portfolio catalog payload mapper slice moves portfolio catalog item projection,
metadata alias handling, display-name fallback, and deterministic sort order into
`portfolio_catalog_payloads.py`, reducing `portfolio_service.py` from 1,779 to 1,764 physical
lines while preserving catalog response behavior and the 49-line longest-function baseline.
The prior portfolio allocation response mapper slice moves allocation response projection and
look-through capability parsing into `portfolio_holdings_payloads.py`, reducing
`portfolio_service.py` from 1,764 to 1,740 physical lines while preserving allocation summary,
view, reporting-currency, and look-through behavior.
The current portfolio position-book response mapper slice moves position-book response construction
into `portfolio_position_book.py`, reducing `portfolio_service.py` from 1,740 to 1,718 physical
lines while preserving summary, top-position, full-position, and as-of-date fallback behavior.
The current portfolio readiness/insight source-loading slice moves readiness and insight fan-out
bundle construction into `portfolio_readiness_insight_sources.py`, reducing `portfolio_service.py`
from 1,659 to 1,607 script-counted lines while preserving workspace, source-readiness, holdings,
allocation, transaction-probe, and activity-summary request behavior.
The current portfolio book source-loading slice moves book source fan-out bundle construction into
`portfolio_book_sources.py`, reducing `portfolio_service.py` from 1,607 to 1,589 script-counted
lines while preserving allocation, position, cash-balance, portfolio-profile, projection, and
reporting-currency request behavior.
The current portfolio service wrapper-cleanup slice removes stale local pass-through wrappers for
portfolio identity/profile parsing, workspace control-capability construction, optional text
conversion, and unused optional-int conversion, reducing `portfolio_service.py` from 1,589 to
1,553 script-counted lines while preserving direct use of the extracted helper modules.
The current portfolio upstream-payload extraction slice moves portfolio-specific payload requiring,
optional partial-failure recording, product-safe upstream error detail construction, and client-error
mapping into `portfolio_upstream_payloads.py`, reducing `portfolio_service.py` from 1,553 to 1,489
script-counted lines while preserving upstream response behavior and partial-failure shape.
The current portfolio readiness-response extraction slice moves source-owned readiness response
construction and reporting-readiness fallback policy into `portfolio_readiness_response.py`,
reducing `portfolio_service.py` from 1,489 to 1,453 lines while preserving source-readiness
precedence, fallback indicators, and Workbench-facing readiness response behavior. The blocking
source-file threshold is ratcheted from 1,489 to 1,477 lines, making
`performance_workspace_service.py` the single largest residual source-file hotspot.
The current performance workspace request-context extraction slice moves workspace, horizon, and
attribution-trend request-context policy into `performance_workspace_context.py`, reducing
`performance_workspace_service.py` from 1,477 to 1,206 script-counted lines while preserving
control normalization, benchmark context, warning propagation, and source partial-failure behavior.
The blocking source-file threshold is ratcheted from 1,477 to 1,453 lines, making
`portfolio_service.py` the single largest residual source-file hotspot.
The current portfolio workspace component parser extraction slice moves workspace assembly state,
summary/cashflow/performance/rebalance/operations parsing, reporting-readiness part assembly, and
resolved-as-of-date extraction into `portfolio_workspace_components.py`, reducing
`portfolio_service.py` from 1,453 to 1,237 script-counted lines while preserving optional-upstream
warning and partial-failure behavior. The blocking source-file threshold is ratcheted from 1,453
to 1,362 lines, making `dpm_client.py` the single largest residual source-file hotspot.
The prior DPM PM operating-quality client-boundary slice moves score-run, fairness-analysis,
review-action, summary-invocation, and policy route methods into
`dpm_pm_operating_quality_client.py` while preserving the public `DpmClient` surface and shared
observed fan-out transport. The blocking source-file threshold is ratcheted from 1,362 to 1,237
lines, making `portfolio_service.py` the single largest residual source-file hotspot.
The prior DPM construction/proof-pack client-boundary slice moves construction-alternative and
proof-pack route methods into `dpm_construction_client.py` and `dpm_proof_pack_client.py` while
preserving the public `DpmClient` surface, observed fan-out transport, idempotency headers, and
Markdown binary response decoding. `dpm_client.py` is reduced from 1,121 to 1,041 physical lines.
At that point, the blocking source-file threshold remained 1,237 lines because
`portfolio_service.py` was still the largest source-file hotspot.
The current portfolio upstream-access extraction slice moves cached Lotus Core, performance, and
DPM upstream result acquisition into `portfolio_upstream_access.py` while preserving cache keys,
optional-client behavior, source fan-out call shapes, and the public `PortfolioService` API.
`portfolio_service.py` is reduced from 1,237 to 980 script-counted lines. The blocking source-file
threshold is ratcheted from 1,237 to 1,217 lines, making `dpm_command_center_service.py` the
single largest residual source-file hotspot.
The current DPM PM operating-quality service-boundary slice moves PM operating-quality policy,
score-run, fairness-analysis, review-action, summary-invocation, and AI summary workflow-pack
service orchestration into `dpm_pm_operating_quality_service.py` while preserving the public
`DpmCommandCenterService` surface, manage-owned evidence boundaries, and `lotus-ai` workflow-pack
execution behavior. `dpm_command_center_service.py` is reduced from 1,217 to 695 script-counted
lines. The blocking source-file threshold is ratcheted from 1,217 to 1,206 lines, making
`performance_workspace_service.py` the single largest residual source-file hotspot.
The current performance trend service-boundary slice moves horizon-comparison and
attribution-trend service orchestration into `performance_workspace_trend_service.py` while
preserving the public `PerformanceWorkspaceService` surface. `performance_workspace_service.py` is
reduced from 1,206 to 842 script-counted lines. The blocking source-file threshold is ratcheted
from 1,206 to 1,098 lines, making `advise_client.py` the single largest residual source-file
hotspot.
The merged Advise bank-demo proof client-boundary slice moves RFC-0028 bank-demo proof upstream
routes into `advise_bank_demo_proof_client.py` while preserving the public `AdviseClient` surface.
`advise_client.py` is reduced from 1,098 to 1,062 script-counted lines. The blocking source-file
threshold is ratcheted from 1,098 to 1,093 lines, making `dpm_wave_service.py` the single largest
residual source-file hotspot.
The current DPM wave AI handoff boundary slice moves PM memo and operations handoff summary
workflow-pack orchestration into `dpm_wave_ai_handoff.py` while preserving the public
`DpmWaveService` surface. `dpm_wave_service.py` is reduced from 1,093 to 692 script-counted lines.
The blocking source-file threshold is ratcheted from 1,093 to 1,062 lines, making
`advise_client.py` the single largest residual source-file hotspot.
The current Advise workspace client-boundary slice moves advisory-workspace upstream route methods
into `advise_workspace_client.py` while preserving the public `AdviseClient` surface.
`advise_client.py` is reduced from 1,062 to 909 script-counted lines. The blocking source-file
threshold is ratcheted from 1,062 to 1,041 lines, making `dpm_client.py` the single largest residual
source-file hotspot.
The previous DPM wave client-boundary slice moved rebalance-wave and campaign workflow upstream
route methods into `dpm_wave_client.py` while preserving the public `DpmClient` surface.
`dpm_client.py` was reduced from 1,041 to 452 script-counted lines. The blocking source-file
threshold was ratcheted from 1,041 to 980 lines, making `portfolio_service.py` the single largest
residual source-file hotspot.
The previous portfolio transaction-boundary slice moved transaction ledger, income summary, and
activity summary orchestration into `portfolio_transaction_service.py` while preserving the public
`PortfolioService` surface. `portfolio_service.py` was reduced from 980 script-counted lines to 811
physical lines. The blocking source-file threshold was ratcheted from 980 to 979 lines, making
`src/app/contracts/proposals.py` the single largest residual source-file hotspot.
The current proposal memo contract-boundary slice moves memo-specific proposal request and envelope
contracts into `proposal_memos.py` while preserving the public `app.contracts.proposals` import
surface. `src/app/contracts/proposals.py` is reduced from 979 to 828 script-counted lines. The
blocking source-file threshold is ratcheted from 979 to 954 lines, making
`src/app/contracts/portfolio.py` the single largest residual source-file hotspot.

## Health Signals

| Area | Current posture | Evidence |
| --- | --- | --- |
| Branch hygiene | Healthy | Current proposal memo contract-boundary branch was created from clean `main`; final remote/local cleanup remains a post-merge gate |
| Unit/contract coverage | Healthy | Current proposal memo contract-boundary branch focused validation passed with proposal contract tests, contract-boundary tests, and refactor-threshold trials proving `max_source_file_lines=954` passes while `953` fails on `src/app/contracts/portfolio.py`; full local `make check` passed with ruff, format check, monetary-float guard, refactor threshold gate, workflow action-runtime gate, mypy over 496 source files, Workbench/OpenAPI contract smoke, and 1,168 unit/contract tests |
| Integration coverage | Healthy | Full local `make ci` passed with 207 integration tests and migration contract smoke |
| Total coverage | Healthy | Full local `make ci` passed with 1,375 combined coverage tests and 94.22% total coverage |
| Security audit | Governed | Current proposal memo contract-boundary branch introduces no dependency, authentication, caller-context, monetary-float, or error-detail policy changes; full local `make ci` `pip-audit` reported no known vulnerabilities after the governed `PYSEC-2026-161` exception |
| Modularity | Improving, incomplete | Longest-function baseline remains 49 lines; recent response/request-context/parser/mapper/contract slices lower `portfolio_service.py` to 811 physical lines, `performance_workspace_service.py` to 842 lines, `advisor_brief_service.py` to 861 script-counted lines, `dpm_command_center_service.py` to 695 lines, `dpm_wave_service.py` to 692 script-counted lines, `advise_client.py` to 909 script-counted lines, `dpm_client.py` to 452 script-counted lines, and `src/app/contracts/proposals.py` to 828 script-counted lines; `src/app/contracts/portfolio.py` is now the largest current source-file hotspot at 954 lines |
| API governance | Improving, incomplete | 233 OpenAPI paths and 247 operations have summaries, descriptions, operation IDs, tags, and documented 4xx/5xx responses; Spectral remains report-only |
| Error consistency | Improving, incomplete | Reporting job and report-batch upstream error handling now uses explicit code-owned mapping rules with focused product-safe fallback tests; shared generic service-error status mapping is code-owned and tested; advisory-facing product-safe service-error defaults now use typed immutable configs; broader route/upstream error normalization remains open |
| Architecture rules | Improving, incomplete | AST boundary tests exist; import-linter is report-only; source-file and function-size thresholds are now blocking through `make lint` |
| Observability | Partial | Health/readiness/metrics/correlation exist; analytics UI structured log and audit event-family separation is enforced by unit tests; Prometheus metric-label contracts are enforced by a static unit gate; broader trace/log scoring is not enforced |

## Primary Refactor Backlog

1. Continue splitting large contract modules, `portfolio_service.py`, and remaining upstream
   clients around clear service and route-family boundaries.
2. Continue splitting `portfolio_service.py` around clear source-readiness, workspace, insight,
   book, and workflow adapters only when cohesive behavior-preserving seams remain.
   Exception-summary payload construction, workflow-action assembly, transaction-summary context
   loading, transaction page loading, book response assembly, transaction-ledger payload loading,
   workspace source gathering, position-book mapping,
   transaction-ledger response mapping, transaction client-kwargs mapping, transaction page
   context defaults, workspace payload mapping, workspace performance parsing, workspace
   rebalance parsing, source readiness parsing, transaction summary mapping and context loading,
   workflow cue/action mapping, workflow/readiness
   contracts, transaction ledger contracts, performance snapshot contracts, income/activity
   contracts, and holdings/book contracts are now separately testable.
3. Continue splitting `risk_workspace_service.py` around remaining orchestration helpers only when
   behavior-preserving seams are obvious; the risk response boundaries are now separately testable.
4. Continue splitting platform capability normalization or orchestration helpers if future changes
   expand the extracted modules.
5. Continue extracting performance workspace summary orchestration helpers behind stable response
   contracts only when future changes expand the surface; capability-input derivation, horizon
   parsing, horizon/attribution trend orchestration, and evidence-view orchestration are now below
   the current function-size baseline and separately testable.
6. Continue splitting advisor-brief service orchestration around stable reviewed-narrative
   contracts if future changes expand the remaining runtime or review helpers.
7. Split large contract modules only when contract ownership boundaries are clear and tests remain
   stable.
8. Continue normalizing route-specific upstream errors toward shared problem-details mapping.
   Foundation optional-upstream and archive-document mappings are smaller and safer, reporting
   job/batch error mapping and shared generic service-error status mapping are now rule-table
   driven, advisory-facing product-safe service-error defaults now use typed immutable configs, but
   broader route/upstream error normalization remains open.
9. Extend API governance tests beyond operation completeness to cover deprecation posture and
   explicit operation ID policy once those standards are approved.

## Quality-Gate Roadmap

1. Report-only workflow uploads quality logs for baseline classification.
2. Blocking refactor threshold gate now enforces:
   - no Python source file under `src/app` above 954 script-counted lines,
   - no Python function or async function above the remediated 49-line AST span baseline.
3. Then enforce no-new-regression thresholds for:
   - ruff/mypy,
   - coverage,
   - import-linter,
   - OpenAPI spectral warnings,
   - `pip-audit` and high-confidence `bandit` findings.
4. Enterprise-readiness gates should require docs, API, security, observability, and architecture
   scorecard sections to be green before release promotion.
