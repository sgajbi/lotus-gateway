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

1. `src/app/services/portfolio_service.py` at 3,016 lines,
2. `src/app/services/risk_workspace_service.py` at 1,942 lines,
3. `src/app/services/advisor_brief_service.py` at 1,392 lines,
4. `src/app/services/performance_workspace_service.py` at 1,152 lines,
5. `src/app/services/dpm_command_center_service.py` at 1,032 lines.

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
`risk_workspace_service.py` to 1,942 lines while preserving source-owned concentration fields and
supportability semantics. The current longest function is `_build_normalized_capabilities` in
`src/app/services/platform_capabilities_service.py` at 195 lines.

## Progressive Enforcement

1. Phase 1: report-only quality baseline.
2. Phase 2: fail only new architecture regressions.
3. Phase 3: enforce thresholds for largest modules, function length, complexity, and import rules.
4. Phase 4: enterprise-readiness gate requiring architecture, API, security, observability, and
   docs scorecard targets to pass.
