# Services Guide

## Responsibility

`src/app/services/` owns Gateway application use cases: composition, partial-readiness handling,
bounded degraded states, source-preserving evidence mediation, and protocol-backed orchestration.

## Boundary Rules

| Area | Rule | Evidence |
| --- | --- | --- |
| Use cases | Services may compose upstream truth but must not become source systems for portfolio, risk, performance, report, archive, manage, advise, idea, or AI domains. | `README.md` |
| Client access | Only service factory/provider modules should import concrete clients. | `tests/unit/test_service_layer_boundaries.py` |
| Protocols | Prefer local protocol/port types for upstream behavior consumed by services. | `tests/unit/test_service_layer_boundaries.py` |
| Supportability | Preserve partial, unavailable, permission-blocked, and degraded states with bounded product-safe details. | `REPOSITORY-ENGINEERING-CONTEXT.md` |

## Validation

Run `python -m pytest tests/unit/test_service_layer_boundaries.py -q` for service architecture
changes. Add focused service tests for new degraded states, source-lineage behavior, and
anti-corruption mapping.

## Update Triggers

Update this guide and repo context when service-provider caching, protocol placement,
cross-upstream composition ownership, or supportability/degraded-state conventions change.
