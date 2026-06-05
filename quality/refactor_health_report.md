# Refactor Health Report

Date: 2026-06-05
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
127 lines to 99 lines. The current branch has further split portfolio workspace source/analytics
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
`portfolio_service.py` is now 3,183 lines after explicit typed workspace component, transaction
summary, transaction page, book assembly, transaction-ledger payload, and workspace source
gathering helpers; it remains the largest-file hotspot even though individual portfolio
orchestration functions are smaller. The remaining work is still substantial: large portfolio,
performance workspace, advisor-brief orchestration, contract, and client modules remain.

## Health Signals

| Area | Current posture | Evidence |
| --- | --- | --- |
| Branch hygiene | Healthy | active focused feature branch over `origin/main` |
| Unit/contract coverage | Healthy | 969 tests passed in current-branch `make check` evidence after commit `4db5e24` |
| Integration coverage | Healthy | 207 integration tests passed in latest `make ci` evidence on commit `b8f01c4` |
| Total coverage | Healthy | 93.36%, above the 84% floor |
| Security audit | Governed | `pip-audit` passes with one documented FastAPI/Starlette exception and no known vulnerabilities on commit `b8f01c4` |
| Modularity | Improving, incomplete | Portfolio workspace assembly, portfolio insight rules, position parsing, performance workspace summary/detail, horizon, attribution-trend, and request contexts, foundation workspace assembly and response composition, risk drawdown/rolling/attribution orchestration and attribution supportability, shell workspace descriptor specs and descriptor state, transaction query contracts, DPM exception-summary and PM quality summary workflow orchestration, advisor-brief talking-point/review-action/route dependency orchestration, portfolio workflow-action and workspace response-component assembly, Workbench performance snapshot parsing and route query extraction, horizon comparison row-field projection, performance workspace summary parsing and route dependencies, risk attribution route query extraction, rebalance supportability failure recording, performance evidence-view mapping, performance workspace capability inputs, core snapshot summary parsing, portfolio exception summaries, performance attribution trend orchestration, platform-capabilities orchestration, advisor-brief narrative state, foundation snapshot parser, performance horizon parser, portfolio workspace controls, platform capability normalization, shell bootstrap, shared analytics request polling, workspace-summary payload assembly, portfolio transaction-summary context, transaction page loading, portfolio book response assembly, performance horizon-comparison dependency phases, performance summary/detail route query metadata, DPM wave PM memo payload/response construction, risk summary period/metric-state mapping, advisor-brief workflow-pack run profile extraction, attribution-trend row orchestration, benchmark-context task/result handling, shell descriptor contract construction, rebalance supportability result validation, performance chart-point construction, shell-bootstrap section assembly, performance snapshot projection, contribution summary merge policy, risk rolling response supportability orchestration, risk drawdown route query metadata, HTTP retry control helpers, portfolio transaction-ledger payload loading, portfolio workspace source gathering, core transaction query-parameter construction, foundation optional-upstream failure mapping, and archive error response mapping extracted; several service files remain above 1,000 lines |
| API governance | Improving, incomplete | Operation-level OpenAPI description, tag, error-response, and global tag-catalog gaps are closed and contract-tested; Spectral remains report-only |
| Architecture rules | Improving, incomplete | AST boundary tests exist; import-linter is new report-only baseline |
| Observability | Partial | Health/readiness/metrics/correlation exist; trace/log scoring not enforced |

## Primary Refactor Backlog

1. Continue splitting `portfolio_service.py` into source-readiness, workspace, insight, and
   workflow-cue adapters. Exception-summary payload construction, workflow-action assembly,
   transaction-summary context loading, transaction page loading, book response assembly,
   transaction-ledger payload loading, and workspace source gathering are now separately testable.
2. Continue splitting `risk_workspace_service.py` around remaining orchestration helpers only when
   behavior-preserving seams are obvious; the risk response boundaries are now separately testable.
3. Continue splitting platform capability normalization or orchestration helpers if future changes
   expand the extracted modules.
4. Continue extracting performance workspace summary orchestration helpers behind stable response
   contracts; capability-input derivation, horizon parsing, attribution trend orchestration, and
   evidence-view orchestration are now below the current function-size baseline.
5. Continue splitting advisor-brief service orchestration around stable reviewed-narrative
   contracts if future changes expand the remaining runtime or review helpers.
6. Split large contract modules only when contract ownership boundaries are clear and tests remain
   stable.
7. Normalize route-specific upstream errors toward shared problem-details mapping.
   Foundation optional-upstream and archive-document mappings are now smaller and safer, but
   broader route/upstream error normalization remains open.
8. Extend API governance tests beyond operation completeness to cover deprecation posture and
   explicit operation ID policy once those standards are approved.

## Quality-Gate Roadmap

1. Report-only workflow introduced in this slice.
2. Report-only workflow uploads quality logs for baseline classification.
3. Then enforce no-new-regression thresholds for:
   - ruff/mypy,
   - coverage,
   - import-linter,
   - OpenAPI spectral warnings,
   - largest-file and longest-function thresholds,
   - `pip-audit` and high-confidence `bandit` findings.
4. Enterprise-readiness gates should require docs, API, security, observability, and architecture
   scorecard sections to be green before release promotion.
