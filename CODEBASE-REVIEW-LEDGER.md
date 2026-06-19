# Codebase Review Ledger

Date: 2026-06-19
Repository: `lotus-gateway`
Branch: `feature/gateway-enterprise-hardening-dpm-wave-client`

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
