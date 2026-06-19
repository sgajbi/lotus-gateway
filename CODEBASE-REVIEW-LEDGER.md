# Codebase Review Ledger

Date: 2026-06-19
Repository: `lotus-gateway`
Branch: `feature/gateway-enterprise-hardening-dpm-wave-client`

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
