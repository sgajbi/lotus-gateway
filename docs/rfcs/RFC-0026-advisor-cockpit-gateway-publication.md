# RFC-0026: Advisor Cockpit Gateway Publication

| Metadata | Details |
| --- | --- |
| **Status** | IMPLEMENTED - GATEWAY API PUBLICATION |
| **Implemented Date** | 2026-05-27 |
| **Owner** | `lotus-gateway` |
| **Upstream Authority** | `lotus-advise` RFC-0026 advisor cockpit APIs |
| **Implementation Branch** | `rfc0026-advisor-cockpit-gold-standard` |

## Decision

Gateway exposes the RFC-0026 advisor cockpit as a product-facing API route family while preserving
`lotus-advise` as the source of cockpit action, snapshot, supportability, acknowledgement,
evidence, and lineage truth.

Supported Gateway routes:

| Route | Upstream `lotus-advise` route | Purpose |
| --- | --- | --- |
| `GET /api/v1/advisor-cockpit/actions` | `GET /advisory/cockpit/actions` | Lists source-owned cockpit action items. |
| `GET /api/v1/advisor-cockpit/actions/{action_item_id}` | `GET /advisory/cockpit/actions/{action_item_id}` | Retrieves one source-owned cockpit action. |
| `GET /api/v1/advisor-cockpit/snapshot` | `GET /advisory/cockpit/snapshot` | Retrieves a source-owned operating snapshot. |
| `GET /api/v1/advisor-cockpit/supportability` | `GET /advisory/cockpit/supportability` | Retrieves source-owned supportability posture. |
| `POST /api/v1/advisor-cockpit/actions/{action_item_id}/acknowledgements` | `POST /advisory/cockpit/actions/{action_item_id}/acknowledgements` | Records a replay-safe acknowledgement in `lotus-advise`. |

## Boundary Rules

Gateway forwards portfolio, advisor, caller role, pagination, action id, acknowledgement payload,
idempotency key, and correlation context. Gateway does not reconstruct:

1. advisory policy result,
2. proposal memo posture,
3. cockpit action status, priority, owner, reason codes, SLA, or acknowledgement state,
4. source refs, evidence refs, or lineage refs,
5. supportability or unsupported-capability posture,
6. client-ready publication or external client communication posture.

Workbench implementation, canonical `RFC26_ADVISOR_COCKPIT_CANONICAL` automation, data-product
promotion, and full product support remain mandatory later RFC-0026 slices. This Gateway slice only
certifies the product-facing API publication boundary.

## Validation Evidence

1. `tests/unit/test_advisor_cockpit_service.py`
   proves Gateway service envelopes preserve Advise-owned payload posture and propagate upstream
   acknowledgement conflicts without rewriting semantics.
2. `tests/integration/test_advisor_cockpit_router.py`
   proves routes forward filters, correlation ids, acknowledgement bodies, and `Idempotency-Key`
   to the Advise client while preserving blocked/supportability posture.
3. `tests/contract/test_advise_gateway_route_coverage.py`
   proves all supported advisor cockpit route keys are present in the FastAPI app.
4. OpenAPI assertions prove the acknowledgement idempotency header and conflict response are
   documented.

## No Product Overclaim

This slice does not claim Workbench advisor cockpit UI support, canonical populated browser proof,
data-product promotion, client-ready policy approval, OMS/order/fill/settlement support, external
client communication, or full demo readiness.
