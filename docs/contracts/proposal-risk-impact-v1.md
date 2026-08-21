# Proposal Risk And Impact Experience Contract v1

Status: implementation-backed by `GET /api/v1/proposals/{proposal_id}/risk-impact`.

## Product purpose

This selected-record read gives Workbench enough governed evidence to build a proposal Risk and
Impact decision workspace without parsing the opaque persistence payload returned by the general
proposal-detail route. It is an experience projection, not a new analytics engine.

Gateway performs one bounded `lotus-advise` proposal-detail read. It does not fan out across the
proposal worklist, does not call Core or Risk directly, and does not calculate risk or allocation
deltas.

## Authority map

| Evidence | Contract source | Semantic authority | Gateway behavior |
| --- | --- | --- | --- |
| proposal, portfolio, lifecycle, and version identity | Advise proposal detail | `lotus-advise` | validates proposal/version continuity |
| current and proposed allocation views | `proposal_result.before` and `after_simulated` | calculator named by `allocation_lens.source` | preserves exact decimal strings and keeps snapshots separate; no delta calculation |
| allocation contract and calculator versions | `proposal_result.allocation_lens` | `lotus-core` or bounded Advise fallback | reports source mode; fallback is partial evidence |
| proposal risk lens | `artifact.risk_lens` | source service named by Advise, normally `lotus-risk` | preserves status, summary, and highlights |
| decision posture and requirements | `proposal_decision_summary` | `lotus-advise` | preserves reason, action, confidence, requirements, material-change summaries, and evidence refs |
| workflow gate | current-version gate snapshots | `lotus-advise` | keeps workflow gate separate from proof of recorded approval |
| lineage | immutable proposal-version hashes | `lotus-advise` | preserves request, artifact, and simulation hashes |

If the proposal-result and artifact copies of decision or gate evidence disagree, the relevant
section is `partial` with a stable source-mismatch reason. Invalid identity, duplicated allocation
dimensions, or malformed typed values fail closed with
`ADVISE_PROPOSAL_RISK_IMPACT_CONTRACT_INVALID`.

Decision and workflow-gate evidence publish the exact selected source path in both the section and
its capability posture. Consumers therefore never receive provenance for an absent copy when
another validated source copy supplied the visible evidence.

## Supportability states

- `ready`: the typed source evidence required for that section is present and internally aligned.
- `partial`: usable evidence exists, but a source copy differs, one comparison side is missing, or
  the allocation calculation used the bounded local fallback.
- `unavailable`: the producer explicitly did not supply usable evidence.
- `not_supported`: the current proposal lifecycle contract does not define the capability.

`overall_state` is evidence supportability only. It is not approval, acceptability, suitability,
client consent, or execution readiness.

## Explicit v1 boundaries

The current Advise lifecycle detail does not publish a governed proposal benchmark/limit package,
scenario-analysis package, or requested/effective valuation date. v1 therefore publishes those
capabilities as `not_supported` with stable reason codes. Workbench must not infer them from titles,
free text, lifecycle state, or unrelated portfolio analytics.

The general `GET /api/v1/proposals/{proposal_id}` contract remains unchanged for compatibility.

## Validation evidence

- `tests/unit/test_proposal_risk_impact_projection.py`
- `tests/unit/test_proposal_risk_impact_service.py`
- `tests/contract/test_proposals_contract.py`
- `tests/integration/test_proposals_router.py`
