# Proposal Implementation Status Experience Contract v1

Status: implementation-backed by `GET /api/v1/proposals/{proposal_id}/execution-status`.
Contract discriminator: `proposal-implementation-status.v1`.

## Product purpose

This selected-record read gives Workbench a governed decision contract for proposal implementation
follow-up. It answers whether an advisory handoff exists, which immutable proposal version it
references, what source event and provider references are available, and whether the current
posture requires attention. It is not an order-management, fill, or settlement contract.

Gateway performs one bounded `lotus-advise` execution-status read. Advise remains the authority for
advisory handoff and reconciliation posture. The named downstream execution provider remains the
execution system of record.

## Source and authority map

| Evidence | Source | Gateway behavior |
| --- | --- | --- |
| proposal, portfolio, lifecycle, and current-version identity | Advise proposal summary | validates route identity and preserves source values |
| handoff state | Advise `handoff_status` | preserves all eight states without collapsing exceptions or partial execution |
| request, provider, and related version | Advise execution-status projection | exposes exact references; missing optional evidence becomes `partial` |
| handoff and execution time | Advise workflow projection | validates timezone and chronology; never supplies a browser or Gateway timestamp |
| latest execution event | Advise append-only workflow event | validates proposal, event type, version, and status correlation; exposes bounded event identity |
| external execution reference | downstream update reconciled by Advise | exposes the reference only when source-provided; it is not order, fill, or settlement detail |
| ownership boundary | Advise execution boundary | requires `DOWNSTREAM_EXECUTION_PROVIDER` as execution system of record |
| request tracing | Gateway correlation context | binds the returned lineage to the exact Gateway correlation id |

Malformed vocabulary, identity, future-version references, event/status disagreement, ownership
drift, non-UTC-aware time, or impossible chronology fail closed with
`ADVISE_PROPOSAL_IMPLEMENTATION_STATUS_CONTRACT_INVALID` and HTTP `502`.

## Business status mapping

| Source handoff status | Status family | Recommended next action | Attention | Terminal |
| --- | --- | --- | --- | --- |
| `NOT_REQUESTED` | `not_started` | `REQUEST_HANDOFF` | no | no |
| `REQUESTED` | `pending` | `MONITOR_HANDOFF` | no | no |
| `ACCEPTED` | `pending` | `MONITOR_IMPLEMENTATION` | no | no |
| `PARTIALLY_EXECUTED` | `attention` | `REVIEW_PARTIAL_EXECUTION` | yes | no |
| `EXECUTED` | `completed` | `NO_ACTION` | no | yes |
| `REJECTED` | `attention` | `INVESTIGATE_REJECTION` | yes | yes |
| `CANCELLED` | `attention` | `REVIEW_CANCELLATION` | yes | yes |
| `EXPIRED` | `attention` | `REVALIDATE_HANDOFF` | yes | yes |

These values are an experience-layer classification over the preserved source state. They do not
change workflow state or create execution authority.

## Supportability and freshness

- `supported`: the source status is valid and the request, provider, related-version, handoff-time,
  and event evidence expected after handoff are present.
- `partial`: the source status is valid, but request, provider, related-version, handoff-time, or
  event evidence is absent. Workbench must show the gap and must not infer it.
- `executed_at`: is required only for `EXECUTED`; a completed status without this source timestamp,
  or any earlier/exception status carrying it, is contract-invalid rather than partial evidence.
- `freshness.observed_at`: the latest source execution-event time, or the proposal's source
  `last_event_at` when no handoff has been requested.
- `version_posture`: distinguishes current-version, historical-version, and not-correlated evidence.
- capabilities keep missing provider, downstream reference, or event evidence explicit and always
  mark `order_fill_settlement_detail` as `not_supported`.

No wall-clock freshness threshold is invented in v1. Consumers receive the exact source observation
time and decide how to present it under their governed business-date policy.

## Failure behavior

- source `403`, `404`, and service failures retain their product-safe Gateway status and
  `ADVISE_PROPOSAL_UPSTREAM_ERROR` contract,
- invalid successful source payloads return `502` with the implementation-status contract-invalid
  error code,
- a successful response never contains fabricated owner, SLA, priority, order, quantity, fill,
  settlement, or universal execution-action fields.

## Validation evidence

- `tests/unit/test_proposal_implementation_status_projection.py`
- `tests/unit/test_proposal_implementation_status_service.py`
- `tests/contract/test_proposals_contract.py`
- `tests/integration/test_proposals_router.py`

Focused live API evidence is required before the dependent Workbench implementation-status screen
is promoted from blocked to implementation-backed.
