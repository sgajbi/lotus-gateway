# Security and Governance

Gateway is a high-sensitivity boundary because it sits between Workbench and domain-authoritative
services. Security posture must be expressed through implemented controls, tests, CI gates, and
operator evidence rather than broad readiness claims.

## Current governance

- RFC-0007
  BFF integration contract for the UI platform
- RFC-0041
  platform integration architecture governance
- RFC-0067
  centralized OpenAPI and vocabulary governance
- RFC-0071
  environment-scoped service identity and ingress posture
- RFC-0072
  multi-lane CI and release governance
- RFC-0073
  ecosystem context and agent guidance system
- RFC-0082
  upstream contract-family boundary hardening

## Repo-specific guardrails

- OpenAPI contract proof is active
- migration smoke, monetary-float guard, and security audit remain active
- refactor quality thresholds, workflow action-runtime governance, and agent quality evidence
  governance are active through `make lint`
- monetary-float approvals are matched in a line-shift tolerant way, so routine formatting changes
  do not force import-order suppressions or approval churn
- Docker parity matters because this is a live integration boundary
- gateway must not smuggle domain logic out of authoritative upstream services
- archive document retrieval must remain Gateway-first and caller-context governed; Workbench
  should not bypass Gateway to call `lotus-archive`
- AI handoffs must use governed `lotus-ai` workflow-pack execution seams and must not expose raw
  prompts, model output, or unsupported generated advice
- DPM AI response validation must bind the returned task identity and output-use label to the
  contract Gateway actually requested; internal source-field consistency alone is insufficient
- DPM product callers provide caller audit identity, never Gateway workload authority; Gateway
  derives its own exact `lotus-gateway` / `manage.write` authority only for request-scoped Manage
  mutations and keeps reads least-privilege

## Operational discipline

- preserve correlation, evidence, supportability, and degraded-state signals
- redact sensitive audit metadata across normalized key variants before logging
- evaluate write capability rules with path-segment-aware matching before allowing privileged actions
- keep upstream HTTP retries bounded and defensive: negative retry counts still make one attempt,
  negative backoff is clamped, and unsupported shared-client methods fail closed instead of being
  sent as another verb
- keep gateway contracts product-oriented instead of accreting thin pass-through clutter
- document endpoint-specific parameter conventions explicitly when they differ by route family

## Sensitive data rules

Do not put these values in metric labels, support tickets, screenshots, demo notes, or generated
evidence unless a governed artifact explicitly allows it:

1. client names or account identifiers,
2. portfolio, holding, transaction, session, upload, or document identifiers as metric labels,
3. request bodies, response bodies, raw prompts, model output, or raw entitlement failures,
4. trace IDs and correlation IDs as metric labels.

Use support references, bounded state/reason codes, source service, route family, status class, and
operator guidance instead.
