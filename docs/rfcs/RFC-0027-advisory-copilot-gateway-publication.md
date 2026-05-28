# RFC-0027 Advisory Copilot Gateway Publication

Status: IMPLEMENTED - GATEWAY API PUBLICATION ONLY

## Scope

This slice publishes the `lotus-gateway` experience-API boundary for RFC-0027 governed advisory
copilot APIs. Gateway remains a source-preserving BFF over `lotus-advise`; it does not call
`lotus-ai`, generate prompts, rebuild evidence packets, evaluate guardrails, mutate review state
locally, or infer client-ready publication.

## Routes

| Gateway route | Advise route | Purpose |
| --- | --- | --- |
| `POST /api/v1/advisory-copilot/evidence-packets` | `POST /advisory/copilot/evidence-packets` | Creates a bounded Advise-owned evidence packet. |
| `GET /api/v1/advisory-copilot/evidence-packets/{evidence_packet_id}` | `GET /advisory/copilot/evidence-packets/{evidence_packet_id}` | Reads a persisted Advise-owned evidence packet. |
| `POST /api/v1/advisory-copilot/actions` | `POST /advisory/copilot/actions` | Runs an Advise-owned governed copilot action. |
| `GET /api/v1/advisory-copilot/actions/{run_id}` | `GET /advisory/copilot/actions/{run_id}` | Reads an Advise-owned copilot run and review audit. |
| `POST /api/v1/advisory-copilot/actions/{run_id}/reviews` | `POST /advisory/copilot/actions/{run_id}/reviews` | Records a replay-safe human review action. |
| `GET /api/v1/advisory-copilot/supportability` | `GET /advisory/copilot/supportability` | Reads Advise-owned supportability and blocked claims. |
| `GET /api/v1/advisory-copilot/proposals/{proposal_id}/versions/{version_id}/runs` | `GET /advisory/proposals/{proposal_id}/versions/{version_id}/copilot-runs` | Lists copilot runs for a proposal version. |

## Boundaries

Gateway preserves:

1. evidence-packet posture,
2. action and run state,
3. review audit,
4. guardrail posture,
5. workflow-pack and model-risk lineage,
6. supportability and blocked client-ready posture,
7. upstream status codes and idempotency conflicts.

Gateway does not claim:

1. client-ready publication,
2. policy approval or sign-off authority,
3. proposal lifecycle approval,
4. order, fill, settlement, or OMS authority,
5. Workbench product proof,
6. data-product promotion.

## Validation Evidence

Targeted commands:

1. `python -m ruff check src/app/clients/advise_client.py src/app/contracts/advisory_copilot.py src/app/services/advisory_copilot_service.py src/app/routers/advisory_copilot.py src/app/main.py tests/unit/test_advisory_copilot_service.py tests/contract/test_advise_gateway_route_coverage.py`
2. `python -m pytest tests/unit/test_advisory_copilot_service.py tests/contract/test_advise_gateway_route_coverage.py -q`

Implementation-backed tests verify route coverage, absence of a free-form prompt route, payload
preservation, idempotency propagation, and upstream conflict propagation.
