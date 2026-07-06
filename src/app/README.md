# App Package Guide

## Responsibility

`src/app/` is the Gateway application package. Keep the request path layered:
external consumer -> router -> request mapper -> application use case -> domain/service logic ->
port/protocol -> infrastructure adapter -> upstream system.

## Boundary Rules

| Area | Rule | Evidence |
| --- | --- | --- |
| Entry point | `main.py` wires FastAPI, middleware, and routers only. | `tests/contract/test_workbench_contract.py` |
| Routers | Routers parse HTTP and delegate; they do not own upstream calls or domain logic. | `tests/unit/test_router_layer_boundaries.py` |
| Services | Services compose Gateway use cases and preserve upstream authority. | `tests/unit/test_service_layer_boundaries.py` |
| Clients | Clients are infrastructure adapters behind service protocols and factories. | `tests/unit/test_service_layer_boundaries.py` |

## Validation

Run `make check` for the normal local gate. Run `python -m pytest
tests/unit/test_router_layer_boundaries.py tests/unit/test_service_layer_boundaries.py -q` when a
change touches layering, imports, factories, or service/provider boundaries.

## Update Triggers

Update this guide and `REPOSITORY-ENGINEERING-CONTEXT.md` when package ownership, routing shape,
service-provider conventions, or upstream adapter placement changes.
