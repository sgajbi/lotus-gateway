# Tests Guide

## Responsibility

`tests/` proves Gateway behavior at the right level: unit tests for use-case and helper behavior,
contract tests for public API truth, integration tests for composed behavior, and e2e tests for live
workflow posture.

## Boundary Rules

| Area | Rule | Evidence |
| --- | --- | --- |
| Unit | Use focused unit tests for services, mappers, degraded states, and architecture boundaries. | `tests/unit/test_service_layer_boundaries.py` |
| Contract | Use contract tests for Workbench-facing route and OpenAPI behavior. | `tests/contract/test_workbench_contract.py` |
| Integration | Use integration tests when multiple Gateway components or upstream assumptions interact. | `Makefile` |
| E2E | Use e2e/live tests for workflow posture, not for cheap local unit coverage. | `tests/e2e/` |

## Validation

Run `make test-unit`, `make openapi-gate`, `make test-integration`, or `make test-e2e` according to
the changed boundary. `make check` is the normal pre-commit gate.

## Update Triggers

Add or update tests when routes, contracts, degraded states, upstream mapping, supportability,
security behavior, or architecture boundaries change. Do not add superficial coverage that does not
protect a real behavior or contract.
