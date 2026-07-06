# Clients Guide

## Responsibility

`src/app/clients/` owns infrastructure adapters for upstream HTTP APIs. Clients translate transport
details, timeouts, retries, and upstream response envelopes into service-consumable results.

## Boundary Rules

| Area | Rule | Evidence |
| --- | --- | --- |
| Adapter boundary | Clients are called through service factories/providers, not directly from routers. | `tests/unit/test_router_layer_boundaries.py` |
| Resilience | Keep timeout, retry, and bounded error behavior consistent with `http_resilience.py`. | `src/app/clients/http_resilience.py` |
| Product safety | Do not pass arbitrary upstream error strings directly into product-facing details. | `tests/unit/test_service_layer_boundaries.py` |
| Source authority | Preserve upstream service identity and source references for supportability. | `REPOSITORY-ENGINEERING-CONTEXT.md` |

## Validation

Run focused unit tests for the owning service and adapter path. Run `make ci` when changing retry,
timeout, security, dependency, or integration behavior.

## Update Triggers

Update this guide, service protocols, runbooks, and upstream contract-family docs when a new
upstream system, route family, timeout setting, retry policy, auth behavior, or error mapping is
introduced.
