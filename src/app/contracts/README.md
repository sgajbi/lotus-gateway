# Contracts Guide

## Responsibility

`src/app/contracts/` owns Gateway response and request contract models that Workbench and other
consumers depend on. Contracts should describe product-facing truth, not leak upstream implementation
payloads.

## Boundary Rules

| Area | Rule | Evidence |
| --- | --- | --- |
| Consumer contract | Keep schemas stable, explicit, and source-preserving for Workbench. | `tests/contract/test_workbench_contract.py` |
| Anti-corruption | Normalize upstream-specific names and unsafe errors before they reach contracts. | `tests/unit/test_service_layer_boundaries.py` |
| Examples | Update OpenAPI examples and docs when public payload shape changes. | `.spectral.yaml` |
| Ownership | Do not move upstream domain authority into Gateway contract models. | `docs/standards/RFC-0082-upstream-contract-family-map.md` |

## Validation

Run `make openapi-gate` and focused unit/contract tests for the route family. Run Spectral through
the quality baseline when OpenAPI examples or descriptions change.

## Update Triggers

Update `wiki/API-Surface.md`, supported-feature truth, and relevant RFC docs when a contract adds,
removes, renames, or reclassifies public fields, errors, pagination, filters, or headers.
