# RFC-0001: lotus-gateway Proposal Simulation Slice

- Status: IMPLEMENTED
- Date: 2026-02-22
- Current implementation note: superseded by the 2026-05-01 downstream ownership split.
  Gateway now routes proposal simulation to `lotus-advise`
  `POST /advisory/proposals/simulate`; `lotus-manage` is no longer a proposal upstream.

## Goal

Deliver proposal simulation as the first production UX path behind `lotus-gateway`.

## Decision

- lotus-gateway exposes `POST /api/v1/proposals/simulate`.
- lotus-gateway forwards payload to `lotus-advise` `POST /advisory/proposals/simulate`.
- lotus-gateway enforces correlation id propagation and idempotency handling.

## Out of Scope

- Portfolio core and performance integrations in this phase.
- Non-proposal workflows.

## Acceptance Criteria

- Endpoint covered by unit/contract/integration tests.
- CI green with `make check` and `make test-integration`.
