# RFC-0014: Experience API Foundation and Pre-Live Replacement Strategy

- Status: PROPOSED
- Date: 2026-03-26
- Owners: lotus-gateway
- Requires Approval From:
  - lotus-gateway maintainers
  - lotus-workbench maintainers
  - lotus-platform maintainers

## Summary

`lotus-gateway` must evolve from a feature-by-feature aggregation layer into the primary
experience API for `lotus-workbench`.

The first and most important gateway-local step is not adding more route families around the
current structure. It is establishing:

1. an experience-API architecture,
2. a shared response-envelope and partial-failure model,
3. journey-shaped contracts,
4. a pre-live replacement strategy that favors removing stale APIs instead of preserving them under
   versioned duplication.

Because the project is not live, this RFC explicitly rejects the assumption that legacy endpoints
must be kept under `v2` or similar compatibility layers by default.

The preferred strategy is:

1. replace weak or stale APIs,
2. delete old APIs when the new ones are ready,
3. keep the surface clean,
4. avoid carrying dead contracts and dead implementation forward.

## Why This Is Next

`lotus-workbench` is moving toward a premium application shell.

That only works if `lotus-gateway` stops behaving primarily like:

1. a pass-through API,
2. a route-mirroring layer,
3. an accumulation of historical slices.

The gateway must become the clean product-facing orchestration layer for:

1. workspace entry payloads,
2. shell-wide data surfaces,
3. action-oriented user workflows,
4. degraded-but-usable multi-service reads,
5. supportability and evidence access for UI experiences.

If this foundation is not established now:

1. old API shapes will keep leaking into the new product shell,
2. frontend teams will keep stitching around inconsistent payloads,
3. versioned route sprawl will appear before the product is even live,
4. the gateway will become harder to simplify later.

## Problem Statement

The current `lotus-gateway` provides useful business value, but the architecture remains too
incremental for the product direction we want.

Current issues:

1. many endpoints reflect feature slices more than product journeys,
2. shared envelope and partial-failure conventions are not yet the governing center of the API,
3. gateway packaging still leans heavily on route families and service-specific clients rather than
   product-area orchestration modules,
4. there is not yet an explicit rule for replacing pre-live APIs instead of versioning and
   preserving stale contracts.

The gateway therefore needs:

1. an experience-API foundation,
2. a consistent contract model,
3. a replacement-first pre-live migration strategy.

## Goals

1. Make `lotus-gateway` the primary experience API for `lotus-workbench`.
2. Organize contracts around user journeys and workspaces rather than thin upstream parity.
3. Introduce a shared envelope and partial-failure model for product surfaces.
4. Establish a pre-live rule that stale APIs should be replaced or removed rather than retained by
   default under versioned duplication.
5. Create a packaging and migration direction that supports future Foundation, Performance, Risk,
   Proposal, Manage, and Reporting workspaces.

## Non-Goals

1. Defining every future gateway endpoint in this RFC.
2. Preserving every existing route for compatibility.
3. Moving domain ownership from upstream services into the gateway.
4. Solving every orchestration use case in one implementation wave.
5. Defining AI-specific gateway experiences in this RFC.

## Decision

`lotus-gateway` will adopt an experience-API foundation with a replacement-first pre-live
strategy.

### 1. Experience-shaped contracts

The gateway will prioritize contracts shaped around:

1. workspace home and entry payloads,
2. portfolio-centered workspaces,
3. task and activity surfaces,
4. action-driven workflow interactions,
5. supportability and evidence views.

### 2. Shared envelope and partial-failure model

The gateway should converge on a contract style that includes:

1. correlation and contract metadata,
2. warnings,
3. partial failures,
4. source-aware degradation semantics,
5. UI-usable action results.

### 3. No automatic `v2` proliferation

This RFC establishes the following pre-live rule:

1. if an API shape is weak, stale, or no longer aligned with the product direction, it should be
   replaced,
2. once the replacement is ready and consumers are updated, the old route should be deleted,
3. versioned duplication should be used only when there is a clear short-lived migration need,
4. the default should be one clean current API surface, not a growing archive of endpoint families.

### 4. Upstream ownership remains intact

The gateway may compose and normalize.

It may not become the permanent owner of:

1. domain truth,
2. rendering-input defects that belong upstream,
3. domain-specific business semantics that should live in the owning application.

If building the gateway exposes upstream UX or contract gaps, those gaps should be raised in the
owning repository and fixed at the source.

## Proposed Architecture

### Route and module direction

The target internal direction should move toward product-area orchestration such as:

1. `workspace`
2. `foundation`
3. `performance`
4. `risk`
5. `proposal`
6. `manage`
7. `reporting`
8. `activity`

### Layering direction

The gateway should continue to separate:

1. routers,
2. contracts,
3. upstream clients,
4. orchestration services,
5. resilience helpers.

But orchestration should increasingly be organized by product area rather than by historical route
addition order.

### Migration rule

When rebuilding a route family:

1. define the new target contract,
2. wire the frontend to the new contract,
3. remove the stale route and stale implementation when the replacement is ready,
4. do not keep old endpoints indefinitely "just in case."

## Delivery Slices

### Slice 1: Foundation contract model

Outcome:

1. shared envelope and partial-failure conventions are explicit,
2. the first experience-shaped contract family is identified.

Acceptance gate:

1. contract conventions are documented and reusable,
2. new strategic routes follow them.

### Slice 2: Replacement-first migration

Outcome:

1. the first strategic route family is rebuilt on the new contract model,
2. stale predecessor routes are retired rather than preserved by default.

Acceptance gate:

1. the migration proves that pre-live cleanup is acceptable,
2. the active surface becomes cleaner rather than larger.

### Slice 3: Product-area orchestration modules

Outcome:

1. gateway internals reflect product areas more clearly,
2. later workspaces can be added without further structural drift.

Acceptance gate:

1. at least one product-area module is implemented cleanly,
2. new work no longer depends on historical route sprawl.

## Risks

1. teams may keep old routes around out of habit.
2. the gateway may still absorb upstream issues that should be fixed elsewhere.
3. migration may slow temporarily if route cleanup is treated as optional.

## Alternatives Considered

### Alternative 1: Introduce `v2` everywhere up front

Rejected.

Reason:

1. the project is pre-live,
2. pre-live is the right moment to simplify and replace, not to accumulate compatibility baggage.

### Alternative 2: Keep current routes and only add new ones beside them

Rejected.

Reason:

1. that would increase API sprawl,
2. it would preserve low-quality shapes too long,
3. it would make the gateway harder to reason about.

## Initial Implementation Focus

The first implementation work after approval should be:

1. define and add the shared gateway envelope and partial-failure contracts,
2. choose the first route family to rebuild around the new experience model,
3. update `lotus-workbench` to consume the new contract,
4. remove stale routes once the replacement is ready.

## Acceptance Criteria

This RFC is complete when:

1. `lotus-gateway` has an explicit experience-API foundation,
2. the replacement-first pre-live migration rule is established,
3. at least one strategic route family follows the new model,
4. old routes are treated as removable implementation history rather than permanent baggage.

## Approval Requested

Approve this RFC if the team agrees that:

1. `lotus-gateway` should become the experience API for `lotus-workbench`,
2. pre-live gateway evolution should prefer replacement and deletion over routine versioning,
3. future gateway work should follow the contract, migration, and ownership rules defined here.
