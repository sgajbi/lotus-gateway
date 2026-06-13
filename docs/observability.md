# Observability

`lotus-gateway` observability must support product users, operations, support engineers, and
enterprise adoption without exposing sensitive portfolio, client, prompt, model-output, or
entitlement detail.

## Current Surfaces

1. `/health`
2. `/health/live`
3. `/health/ready`
4. `/metrics`
5. `X-Correlation-Id` propagation
6. analytics UI fan-out logs and metrics
7. protected analytics diagnostics lookup
8. bounded audit records for selected analytics reads and denial paths

## Logging Rules

1. Logs should be structured.
2. Logs must not include raw portfolio holdings, client PII, prompts, model outputs, transaction
   payloads, entitlement payloads, or generated report content.
3. Audit records should use bounded fields and explicit route/operation/panel/state/reason labels.
4. Analytics fan-out structured logs and analytics audit logs must use their own governed event
   families; validators reject cross-family event drift.
5. Correlation IDs should be present on ingress and propagated to upstream clients.

## Metrics Rules

1. Metrics labels must be low-cardinality.
2. Do not use portfolio, client, transaction, document, prompt, model-output, or entitlement IDs as
   metric labels.
3. Degraded upstream posture should be counted with bounded service and reason labels.
4. Prometheus collector label sets must be declared in code-owned metric label contracts and remain
   covered by the static unit gate before new metric families are added.

## Traceability

Current traceability relies primarily on correlation IDs, support references, evidence references,
and upstream lineage payloads. Distributed tracing is a future hardening track and should preserve
the same sensitive-data constraints.

## Baseline Gaps

1. Structured log and audit field allowlists are enforced by unit tests for analytics UI
   observability, including event-family separation.
2. Prometheus collector label cardinality is enforced by a static unit gate for gateway metric
   definitions; broader structured telemetry scoring remains future hardening.
3. Trace propagation beyond correlation IDs is not yet governed.
4. Diagnostics authorization and masking should get dedicated security regression tests.
