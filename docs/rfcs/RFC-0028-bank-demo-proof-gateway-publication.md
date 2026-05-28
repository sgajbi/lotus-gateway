# RFC-0028: Bank Demo Proof Gateway Publication

| Metadata | Details |
| --- | --- |
| **Status** | IMPLEMENTED - GATEWAY API PUBLICATION |
| **Implemented Date** | 2026-05-28 |
| **Owner** | `lotus-gateway` |
| **Upstream Authority** | `lotus-advise` RFC-0028 bank-demo proof APIs |
| **Implementation Branch** | `rfc0028-slice7-gateway-proof-contract` |

## Decision

Gateway exposes the RFC-0028 bank-demo proof contract as a product-facing API route family while
preserving `lotus-advise` as the source of scenario-contract, supported-claim, material-review,
proof-pack, and proof-classification truth.

Supported Gateway routes:

| Route | Upstream `lotus-advise` route | Purpose |
| --- | --- | --- |
| `GET /api/v1/advisory/bank-demo-proof/scenario-contract` | `GET /advisory/bank-demo-proof/scenario-contract` | Retrieves the source-owned canonical bank-demo scenario contract. |
| `GET /api/v1/advisory/bank-demo-proof/supported-claim-register` | `GET /advisory/bank-demo-proof/supported-claim-register` | Retrieves source-owned supported, blocked, and unsupported claim classifications. |
| `POST /api/v1/advisory/bank-demo-proof/proof-packs` | `POST /advisory/bank-demo-proof/proof-packs` | Builds a sanitized Advise-owned backend proof bundle from governed runtime evidence. |

## Boundary Rules

Gateway forwards proof-capture request bodies and correlation context to `lotus-advise`. Gateway
does not reconstruct:

1. canonical scenario identity,
2. supported-claim classifications,
3. material-review or evidence-drift decisions,
4. proof-pack sections, hashes, source refs, lineage refs, or evidence markers,
5. client-ready publication posture,
6. RFP, security, screenshot, Workbench browser, OMS, order, fill, settlement, or external client
   communication claims.

Gateway preserves source-owned blocked posture and propagates `409 Conflict` material-review
responses from `lotus-advise` without rewriting business semantics. The route family is for
Workbench and automation consumption; it does not by itself prove the Workbench product UI or
demo screenshot pack.

## Validation Evidence

1. `tests/unit/test_bank_demo_proof_service.py`
   proves Gateway service envelopes preserve Advise-owned proof payloads and propagate upstream
   material-review conflicts.
2. `tests/integration/test_bank_demo_proof_router.py`
   proves Gateway routes forward correlation context and proof-pack requests to the Advise client
   while preserving source-owned payload shape.
3. `tests/contract/test_advise_gateway_route_coverage.py`
   proves all RFC-0028 Gateway route keys are present in the FastAPI app.
4. `tests/unit/test_upstream_clients.py`
   proves the Advise client uses the source RFC-0028 routes.
5. `tests/unit/test_rfc0028_bank_demo_proof_documentation.py`
   pins the public documentation and wiki boundary language so Gateway does not overclaim demo,
   Workbench, RFP, security, or client-ready support.

## No Product Overclaim

This slice does not claim client-ready advice, client-ready document publication, RFP/security
evidence completeness, Workbench UI completion, browser proof, screenshot readiness,
external client communication, CRM system-of-record behavior, or OMS/order/fill/settlement
support. Those claims require the owning service and Workbench/runtime evidence to be implemented
and validated separately.
