# Security and Governance

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
- monetary-float approvals are matched in a line-shift tolerant way, so routine formatting changes
  do not force import-order suppressions or approval churn
- Docker parity matters because this is a live integration boundary
- gateway must not smuggle domain logic out of authoritative upstream services

## Operational discipline

- preserve correlation, evidence, supportability, and degraded-state signals
- keep gateway contracts product-oriented instead of accreting thin pass-through clutter
- document endpoint-specific parameter conventions explicitly when they differ by route family
