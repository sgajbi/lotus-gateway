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
`lotus-advise` as the source of cockpit action, preparation-packet, tactical house-view cohort,
snapshot, supportability, acknowledgement, evidence, and lineage truth.

Supported Gateway routes:

| Route | Upstream `lotus-advise` route | Purpose |
| --- | --- | --- |
| `GET /api/v1/advisor-cockpit/actions` | `GET /advisory/cockpit/actions` | Lists source-owned cockpit action items. |
| `GET /api/v1/advisor-cockpit/preparation-packets` | `GET /advisory/cockpit/preparation-packets` | Lists source-owned meeting preparation packets. |
| `GET /api/v1/advisor-cockpit/actions/{action_item_id}` | `GET /advisory/cockpit/actions/{action_item_id}` | Retrieves one source-owned cockpit action. |
| `GET /api/v1/advisor-cockpit/snapshot` | `GET /advisory/cockpit/snapshot` | Retrieves a source-owned operating snapshot. |
| `GET /api/v1/advisor-cockpit/supportability` | `GET /advisory/cockpit/supportability` | Retrieves source-owned supportability posture. |
| `POST /api/v1/advisor-cockpit/actions/{action_item_id}/acknowledgements` | `POST /advisory/cockpit/actions/{action_item_id}/acknowledgements` | Records a replay-safe acknowledgement in `lotus-advise`. |
| `POST /api/v1/advisor-cockpit/house-view-cohorts/evaluate` | `POST /advisory/tactical-house-view/cohorts/evaluate` | Publishes source-backed tactical house-view affected-cohort evidence for cockpit `HOUSE_VIEW_IMPACT_REVIEW` projection. |

## Boundary Rules

For every Cockpit read and acknowledgement, Gateway derives advisor identity and role from trusted
server-side caller context. Public `advisor_id` and `role` query parameters are rejected. An
optional portfolio remains a business filter only after it matches the singular trusted
`X-Authorized-Portfolio-Id`; single-action reads and acknowledgements require that portfolio scope.
Gateway binds `acknowledged_by` to `X-Actor-Id` and does not accept an actor override in the body.

Gateway validates the actor, calling application, tenant, region, booking centre, legal entity,
role, active-principal posture, capability, authorized advisor, and authorized portfolio before it
calls Advise. It then translates the trusted context to the exact Advise principal headers:
`X-Actor-Id`, `X-Role`, `X-Tenant-Id`, `X-Legal-Entity-Code`, `X-Service-Identity`,
`X-Capabilities`, `X-Principal-Status`, `X-Authorized-Advisor-Id`, and
`X-Authorized-Portfolio-Id`. Advisor callers are always bound to their authenticated actor id.

The tactical house-view cohort command is a separate source-product route. It is not folded into
the Advisor Cockpit read/acknowledgement capability model and Gateway does not invent a house-view
capability that `lotus-advise` does not support.

Workbench must strip browser authority and apply these headers from its server-side BFF principal.
The configured canonical-runtime principal remains non-production evidence while
`lotus-workbench#436` and `lotus-platform#563` govern the authenticated session contract; Gateway
does not restore query-authority compatibility while that platform dependency remains open.

Gateway forwards authorized portfolio filters, pagination, action id, the actor-bound
acknowledgement payload, tactical house-view affected-cohort payload, idempotency key, and
correlation context. Gateway does not reconstruct:

1. advisory policy result,
2. proposal memo posture,
3. cockpit action status, priority, owner, reason codes, SLA, or acknowledgement state,
4. meeting preparation packets, memo evidence, policy posture, or follow-up posture,
5. tactical house-view affected-cohort membership or DPM eligibility,
6. source refs, evidence refs, or lineage refs,
7. supportability or unsupported-capability posture,
8. client-ready publication or external client communication posture.

Workbench implementation, canonical `RFC26_ADVISOR_COCKPIT_CANONICAL` automation, and
data-product promotion are now proven in the coordinated RFC-0026 program. This Gateway slice
certifies the product-facing API publication boundary and records that Gateway preserves the
Advise-owned cockpit supportability posture used by the Workbench canonical proof.

## Validation Evidence

1. `tests/unit/test_advisor_cockpit_service.py`
   proves Gateway service envelopes preserve Advise-owned payload posture and propagate upstream
   acknowledgement conflicts without rewriting semantics.
2. `tests/integration/test_advisor_cockpit_router.py`
   proves routes reject browser-selected authority, fail closed for missing capability and
   cross-portfolio access, bind the acknowledgement actor, forward exact Advise principal headers,
   and preserve blocked/supportability posture.
3. `tests/contract/test_advise_gateway_route_coverage.py`
   proves all supported advisor cockpit route keys are present in the FastAPI app.
4. `tests/unit/test_upstream_clients.py`
   proves the Advise client forwards the tactical house-view cohort request to the source route.
5. OpenAPI assertions prove the acknowledgement idempotency header and conflict response are
   documented, authority query parameters are absent, and trusted context headers are visible.

## No Product Overclaim

This slice does not claim client-ready policy approval, OMS/order/fill/settlement support,
external client communication, CRM system-of-record behavior, or full RFC-0028 demo readiness.
Workbench advisor cockpit support and canonical populated browser proof are claimed only through
the separate Workbench evidence and Advise-owned supportability posture; Gateway remains a
semantics-preserving publication boundary.
