# Repository Engineering Context

This file provides repository-local engineering context for `lotus-gateway`.

For platform-wide truth, read:

1. `C:\Users\Sandeep\projects\lotus-platform\context\LOTUS-QUICKSTART-CONTEXT.md`
2. `C:\Users\Sandeep\projects\lotus-platform\context\LOTUS-ENGINEERING-CONTEXT.md`
3. `C:\Users\Sandeep\projects\lotus-platform\context\CONTEXT-REFERENCE-MAP.md`

## Repository Role

`lotus-gateway` is the Lotus experience API and composition boundary.

It provides the governed client contract for `lotus-workbench` and related product consumers.

## Business And Domain Responsibility

This repository owns:

1. product-facing API composition,
2. partial-readiness-aware aggregation,
3. gateway-level routing and contract governance,
4. experience-oriented payload shaping across domain services.

It does not replace domain authority in upstream services.

## Current-State Summary

Current repository posture:

1. `lotus-gateway` is the primary backend contract for `lotus-workbench`,
2. the repository is moving from thin pass-through behavior to a cleaner experience-API posture,
3. performance, proposal, foundation, reporting, and capability aggregation routes are active,
4. canonical local startup now depends on environment-scoped service identity and `--app-dir src` to avoid misleading Windows import-path failures.

## Architecture And Module Map

Primary areas:

1. `src/app/`
   FastAPI application, routing, and service logic.
2. `tests/contract/`
   Contract tests for workbench-facing behavior.
3. `tests/integration/`
   Integration behavior across composed flows.
4. `tests/e2e/`
   Live or stack-backed behavior checks where applicable.
5. `docs/`
   Experience-API architecture and standards documentation.
6. `scripts/`
   quality gates, migration checks, and canonical startup helpers.

## Runtime And Integration Boundaries

Runtime model:

1. FastAPI experience API,
2. consumed primarily by `lotus-workbench`,
3. depends on `lotus-core`, `lotus-performance`, `lotus-risk`, `lotus-advise`, `lotus-manage`, `lotus-report`, and `lotus-ai`.

Boundary rules:

1. gateway payloads should be product-oriented and governed,
2. domain ownership must remain upstream,
3. route contracts should prefer replacement and cleanup over versioned clutter while pre-live,
4. canonical service identity is part of the operational contract.

## Repo-Native Commands

Use these commands as the primary local contract:

1. install
   `make install`
2. lint and formatting guard
   `make lint`
3. typecheck
   `make typecheck`
4. contract and unit gate
   `make check`
5. PR-grade local gate
   `make ci`
6. Docker parity
   `make ci-local-docker`
7. canonical local runtime
   `make run-canonical`

## Validation And CI Expectations

`lotus-gateway` uses explicit CI lanes:

1. `Remote Feature Lane`
2. `Pull Request Merge Gate`
3. `Main Releasability Gate`
4. platform-facing validation when cross-app experience contracts are affected

Important validation expectations:

1. OpenAPI and workbench contract quality are part of the gate,
2. migration smoke remains required,
3. security audit and monetary-float governance remain active,
4. Docker parity matters because the gateway is a live integration boundary.

## Standards And RFCs That Govern This Repository

Most relevant current governance:

1. `C:\Users\Sandeep\projects\lotus-platform\rfcs\RFC-0007-bff-integration-contract-for-ui-platform.md`
2. `C:\Users\Sandeep\projects\lotus-platform\rfcs\RFC-0041-platform-integration-architecture-bible-governance.md`
3. `C:\Users\Sandeep\projects\lotus-platform\rfcs\RFC-0067-centralized-api-vocabulary-inventory-and-openapi-documentation-governance.md`
4. `C:\Users\Sandeep\projects\lotus-platform\rfcs\RFC-0071-centralized-environment-scoped-service-addressing-and-ingress-governance.md`
5. `C:\Users\Sandeep\projects\lotus-platform\rfcs\RFC-0072-platform-wide-multi-lane-ci-validation-and-release-governance.md`
6. `C:\Users\Sandeep\projects\lotus-platform\rfcs\RFC-0073-lotus-ecosystem-engineering-context-and-agent-guidance-system.md`

## Known Constraints And Implementation Notes

1. Windows startup can serve a misleading health-only process if `--app-dir src` is omitted,
2. stale thin-pass-through routes should be retired as better experience contracts replace them,
3. gateway fixes should not smuggle domain logic out of authoritative upstream services,
4. integration drift is most dangerous here because it directly affects the product UI.

## Context Maintenance Rule

Update this document when:

1. major route families or product-facing responsibilities change,
2. canonical startup commands or CI expectations change,
3. upstream dependency boundaries change,
4. gateway composition patterns or partial-readiness behavior change materially,
5. current-state architectural direction changes.

## Cross-Links

1. `C:\Users\Sandeep\projects\lotus-platform\context\LOTUS-QUICKSTART-CONTEXT.md`
2. `C:\Users\Sandeep\projects\lotus-platform\context\LOTUS-ENGINEERING-CONTEXT.md`
3. `C:\Users\Sandeep\projects\lotus-platform\context\CONTEXT-REFERENCE-MAP.md`
4. `C:\Users\Sandeep\projects\lotus-platform\context\Repository-Engineering-Context-Contract.md`
