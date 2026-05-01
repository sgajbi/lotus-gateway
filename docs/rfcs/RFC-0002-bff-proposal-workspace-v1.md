# RFC-0002: lotus-gateway Proposal Workspace v1 (Create/List/Detail/Submit)

- Status: IMPLEMENTED
- Date: 2026-02-22
- Depends on: RFC-0001
- Current implementation note: superseded by the 2026-05-01 downstream ownership split.
  Gateway proposal create, list, detail, version, workflow, approval, and lineage routes now call
  `lotus-advise` `/advisory/proposals/*`; `lotus-manage` is limited to strategic management
  run/supportability/capability endpoints.

## Goal

Extend the gateway proposal simulation slice to a minimal end-to-end proposal workspace contract
for UI integration.

## Decision

Expose and standardize these lotus-gateway endpoints:

- `POST /api/v1/proposals` -> `lotus-advise` `POST /advisory/proposals`
- `GET /api/v1/proposals` -> `lotus-advise` `GET /advisory/proposals`
- `GET /api/v1/proposals/{proposal_id}` -> `lotus-advise`
  `GET /advisory/proposals/{proposal_id}`
- `POST /api/v1/proposals/{proposal_id}/submit` -> `lotus-advise`
  `POST /advisory/proposals/{proposal_id}/transitions`

Submit mapping in lotus-gateway:

- `review_type=RISK` maps to `event_type=SUBMITTED_FOR_RISK_REVIEW`
- `review_type=COMPLIANCE` maps to `event_type=SUBMITTED_FOR_COMPLIANCE_REVIEW`

## Out of Scope

- Full approval workflow and execution orchestration.
- Multi-service aggregation beyond proposal workflow.

## Acceptance Criteria

- Contract and integration tests cover create/list/detail/submit routes.
- `make check` and `make test-integration` pass.
- README endpoint documentation updated in same PR.
