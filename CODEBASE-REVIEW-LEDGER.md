# Codebase Review Ledger

Date: 2026-06-21
Repository: `lotus-gateway`
Branch: `feature/gateway-risk-workspace-service-boundary`

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
