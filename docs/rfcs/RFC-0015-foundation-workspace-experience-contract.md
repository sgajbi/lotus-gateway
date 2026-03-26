# RFC-0015: Foundation Workspace Experience Contract

- Status: PROPOSED
- Date: 2026-03-26
- Owners: lotus-gateway
- Requires Approval From:
  - lotus-gateway maintainers
  - lotus-workbench maintainers
  - lotus-core maintainers
  - lotus-performance maintainers
  - lotus-report maintainers
  - lotus-platform maintainers

## Summary

The first concrete implementation contract on the new `lotus-gateway` experience-API foundation
should be the `Foundation` workspace contract for `lotus-workbench`.

This RFC defines the gateway-side contract family for the first production-grade `Foundation` app.

The purpose is to replace the current fragmented portfolio-entry experience with a single
experience-oriented contract family that supports:

1. portfolio catalog and portfolio selection,
2. portfolio summary and health,
3. composition and readiness views,
4. workflow launch context,
5. partial-failure-aware rendering.

This RFC intentionally does **not** create new `lotus-core` APIs by default.

After reviewing current `lotus-core` capabilities, the immediate need is in gateway orchestration
and contract shaping, not in a clearly missing or unjustified new core surface.

## Why This Is Next

The shell foundation in `lotus-workbench` needs one real app to prove the new model.

That app is `Foundation`.

For `Foundation` to work as a premium portfolio-first experience, `lotus-gateway` needs to stop
making the frontend stitch together a route mix designed around historical slices such as:

1. lookups,
2. workbench overview,
3. portfolio 360,
4. reporting snapshot,
5. capability negotiation.

The gateway should instead provide a clean workspace contract for `Foundation`.

Because the project is pre-live, this is the right moment to replace weak or fragmented endpoint
shapes rather than introducing more compatibility layers.

## Problem Statement

Current gateway surfaces provide useful ingredients for the `Foundation` experience, but not yet a
single product-grade contract family.

Current issues:

1. the portfolio entry experience is spread across multiple endpoint families,
2. the frontend has to know too much about which endpoint provides which slice of context,
3. partial-failure behavior is present in some places but not yet a governing contract pattern,
4. current contracts are good enough for current pages but not ideal as the first-class API for a
   premium `Foundation` app.

The gateway therefore needs:

1. a unified `Foundation` contract family,
2. shared metadata and partial-failure semantics,
3. cleaner product-oriented orchestration.

## Goals

1. Define the first concrete experience contract for the `Foundation` workspace.
2. Reduce frontend stitching for portfolio entry and readiness views.
3. Provide product-grade gateway shaping for portfolio-first UX.
4. Reuse existing `lotus-core`, `lotus-performance`, and `lotus-report` surfaces where they are
   already sufficient.
5. Avoid introducing new upstream APIs unless a real source-owned gap is proven.

## Non-Goals

1. Designing the full Performance or Risk workspace contracts in this RFC.
2. Preserving fragmented predecessor routes indefinitely.
3. Creating new `lotus-core` APIs without a justified source-owned gap.
4. Moving domain truth into the gateway.
5. Solving later AI-enabled product contracts in this RFC.

## Review of Current Upstream Fit

Before proposing any upstream change, the current upstream posture was checked.

### `lotus-core`

Relevant existing surfaces already exist:

1. `/lookups/portfolios`
2. `/portfolios`
3. `/portfolios/{portfolio_id}`
4. `/integration/portfolios/{portfolio_id}/core-snapshot`
5. support and lineage surfaces documented in the query/control-plane boundary note

Assessment:

1. `lotus-core` already owns the canonical portfolio reads,
2. `lotus-core` already exposes a governed core-snapshot integration surface,
3. the first `Foundation` pass does not yet justify a new `lotus-core` RFC by default.

### `lotus-performance`

Relevant summary signals already exist through the current gateway integration patterns.

Assessment:

1. there may be later product-grade summary improvements worth requesting,
2. but the first `Foundation` gateway contract can proceed without a new `lotus-performance` RFC.

### `lotus-report`

Reporting snapshot shaping already exists and can contribute to first-pass Foundation readiness and
summary cues.

Assessment:

1. current reporting inputs are sufficient for the first gateway contract,
2. later refinements may still be needed as product quality rises.

## Decision

`lotus-gateway` will introduce a `Foundation` workspace experience contract as the first concrete
implementation of the experience-API program.

### 1. Foundation contract family

The gateway should provide a clean contract family centered on portfolio-first experience needs.

The initial family should cover:

1. portfolio catalog,
2. workspace entry payload,
3. composition and readiness payload,
4. workflow launch context.

### 2. Replacement-first route strategy

Because the project is pre-live:

1. if existing route families are not the right product shape, they should be replaced,
2. old fragmented routes should be removed when the replacement is ready,
3. the contract family should converge toward one clean active surface.

### 3. Upstream changes require proof

No new `lotus-core` RFC should be created from this gateway RFC alone.

A follow-on core RFC should be created only if implementation shows a true source-owned gap such as:

1. missing canonical freshness or readiness metadata that only `lotus-core` can truthfully own,
2. missing source-owned portfolio context needed across multiple consumers,
3. missing or weak governed snapshot semantics that the gateway cannot responsibly invent.

Until such a gap is observed, the right work is in `lotus-gateway`, not in creating speculative
new core APIs.

## Proposed Contract Direction

### Foundation portfolio catalog

Purpose:

1. provide portfolio discovery and selector-ready context,
2. support shell entry and portfolio switching.

Desired characteristics:

1. selector-ready,
2. lightweight,
3. sortable and searchable,
4. enriched enough for UX, but not overloaded.

### Foundation workspace entry payload

Purpose:

1. provide the top-level portfolio summary for the selected portfolio,
2. present the first trusted view of health, posture, and next-step readiness.

Desired characteristics:

1. correlation metadata,
2. as-of date,
3. warnings,
4. partial failures,
5. portfolio summary,
6. workflow entry cues.

### Foundation composition and readiness payload

Purpose:

1. provide top holdings, allocation shape, valuation posture, and report/readiness cues.

Desired characteristics:

1. composition summary,
2. readiness indicators,
3. degraded-but-usable behavior when one upstream is unavailable,
4. direct linkage to deeper product apps.

## Delivery Slices

### Slice 1: Contract definition

Outcome:

1. the `Foundation` contract family is explicit,
2. shared envelope and partial-failure usage are applied concretely.

Acceptance gate:

1. the workbench team can build against one product-oriented gateway contract family instead of
   stitching legacy route shapes.

### Slice 2: Gateway orchestration implementation

Outcome:

1. gateway orchestration for Foundation is implemented cleanly,
2. existing upstream surfaces are reused where they are sufficient.

Acceptance gate:

1. the first Foundation app can run without speculative upstream changes.

### Slice 3: Cleanup of stale route shapes

Outcome:

1. stale predecessor routes are identified,
2. replacement and removal are planned,
3. the active surface becomes cleaner.

Acceptance gate:

1. pre-live cleanup actually happens instead of being deferred indefinitely.

### Slice 4: Upstream-gap escalation only when justified

Outcome:

1. if implementation reveals a real source-owned gap, it is documented precisely,
2. a follow-on RFC is created in the owning repository only if the gap is justified.

Acceptance gate:

1. no speculative upstream RFCs are created,
2. any proposed upstream RFC has a concrete product reason and source-ownership rationale.

## Risks

1. teams may still prefer to keep old fragmented routes around.
2. the gateway may be tempted to fabricate source-owned readiness semantics it should not own.
3. upstream issues may be noticed but not escalated quickly enough.

## Alternatives Considered

### Alternative 1: Create a new `lotus-core` RFC immediately

Rejected for now.

Reason:

1. current `lotus-core` already has canonical reads and governed core-snapshot surfaces,
2. no clearly proven missing source-owned API has been identified yet,
3. the first justified work is gateway contract shaping.

### Alternative 2: Keep current route mix and let the frontend compose it

Rejected.

Reason:

1. that would keep the product entry experience fragmented,
2. it would push too much orchestration into the frontend.

## Initial Implementation Focus

The first implementation work after approval should be:

1. define the concrete `Foundation` gateway contracts,
2. map current upstream sources onto them,
3. identify which current gateway routes are superseded,
4. remove stale routes when the replacement is ready,
5. create upstream issues or RFCs only if implementation exposes a clearly justified source-owned
   gap.

## Acceptance Criteria

This RFC is complete when:

1. `lotus-gateway` has a concrete `Foundation` workspace contract family,
2. the first `Foundation` app in `lotus-workbench` can rely on it as its primary product contract,
3. the work proceeds without speculative `lotus-core` expansion,
4. any later upstream RFC is justified by a real identified gap rather than assumption,
5. stale gateway route shapes are treated as removable pre-live history.

## Approval Requested

Approve this RFC if the team agrees that:

1. the first concrete gateway implementation RFC should be the `Foundation` workspace contract,
2. the immediate need is gateway-side contract shaping rather than speculative new `lotus-core`
   APIs,
3. any future `lotus-core` RFC should be created only after a real source-owned gap is observed,
4. implementation should proceed in the slices defined here.
