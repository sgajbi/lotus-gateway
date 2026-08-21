# Proposal Discussion Pack Review Experience Contract v1

Status: implementation-backed by
`GET /api/v1/proposals/{proposal_id}/discussion-pack-review`.
Contract discriminator: `proposal-discussion-pack-review.v1`.

## Product purpose

This selected-record read gives Workbench a governed evidence contract for preparing a private
banking client conversation. It brings the current proposal version, advisor narrative, proposal
memo, disclosure policy, report-package posture, and approval/consent records into one bounded
decision view without asking the browser to interpret open dictionaries or call source services.

It does not decide that a proposal is suitable, approved for client release, published, delivered,
or consented. Advisor-use review is deliberately separate from every client-facing control.

## Request identity

The route requires all three selected-record identifiers:

1. path `proposal_id`,
2. query `portfolio_id`,
3. query `version_no`.

Gateway binds every successful source payload to that tuple. Missing or mismatched portfolio,
proposal, version, version id, narrative id/hash, memo version, approval id, or source chronology
fails closed with `ADVISE_PROPOSAL_DISCUSSION_PACK_CONTRACT_INVALID` and HTTP `502`.

## Source and authority map

| Evidence | Source authority | Gateway behavior |
| --- | --- | --- |
| proposal, portfolio, lifecycle, current version, and immutable hashes | `lotus-advise` proposal detail | validates request identity and version chronology |
| narrative sections and source references | immutable Advise proposal-version narrative | preserves text and grounding references; never regenerates on read |
| narrative review and source hash | Advise append-only narrative review | exposes advisor-use review separately from client-ready status |
| disclosures, policy status, and client-ready blockers | Advise narrative policy | preserves policy-selected disclosures and blocker text |
| memo sections, status, hashes, and review | persisted Advise memo evidence pack | preserves advisor-use evidence and requires client-ready publication to remain `BLOCKED` |
| report-package posture | Advise delivery summary over `lotus-report` evidence | classifies source status as not requested, pending, available, or attention; never calls it client delivery |
| approval and client-consent records | Advise structured approval ledger | selects only consent correlated to the requested immutable version |
| Gateway request trace | Gateway correlation context | binds lineage to the exact request correlation id |

Gateway performs five bounded concurrent reads for the selected record: proposal detail, narrative,
memo, approvals, and delivery summary. It retries that bounded set once when lifecycle and consent
facts show a transition-time mixed snapshot; a repeated contradiction fails closed. It never fans
out across the proposal worklist.

## Independent supportability

The proposal-detail read is mandatory. Its `403`, `404`, or service failure remains a product-safe
Gateway error. The other four capabilities are independent:

- `supported`: a successful source payload passed typed validation,
- `partial`: valid evidence exists but is not fully correlated to the requested version,
- `restricted`: the source returned `403`,
- `unavailable`: the source failed or could not answer,
- `not_available`: the source has no record, or no report package has been requested,
- `not_supported`: the platform does not expose the capability in this contract.

An invalid successful source payload fails the whole projection. Gateway does not hide contract
drift behind a partial state. `overall_state` describes source supportability only; it is never a
discussion-readiness, suitability, release, or consent decision.

## Client-conversation boundary

The following facts are intentionally independent:

1. narrative available for advisor review,
2. narrative approved for advisor use,
3. memo source evidence available,
4. memo approved for advisor use,
5. report package requested or materialized,
6. structured client consent recorded for the selected version,
7. client-ready release and publication,
8. client communication and delivery.

RFC-0023/RFC-0024 currently keep client-ready publication gated or blocked. The v1 contract
therefore exposes `client_release.state=blocked`, `publication_supported=false`, and
`delivery_supported=false`. A PDF, archive reference, lifecycle state, narrative approval, memo
approval, or consent record cannot override that boundary.

## Failure and contradiction rules

The projection rejects:

- source proposal, portfolio, version, version-id, narrative, memo, or approval identity mismatch,
- source chronology timestamps without an explicit timezone offset,
- narrative review evidence recorded before the selected immutable version was created,
- memo review or report-package event evidence recorded before the selected version was created,
- current-version report evidence generated before the selected version was created,
- current-version approval evidence recorded before the selected immutable version was created,
- malformed or unknown closed-enum state,
- duplicated disclosure or approval identifiers,
- narrative review whose id or hash does not match the selected narrative,
- disclosure inventory or any disclosure wording, jurisdiction, product type, audience,
  authority, or policy version that differs from the source policy requirement inventory,
- memo publication posture other than `BLOCKED`,
- memo event posture that claims recorded state without event identity, actor, and time,
- memo review/report-package events with a missing or cross-populated typed action/status,
- available report-package evidence without a source report reference,
- an approval ledger whose declared latest timestamp is not the latest recorded event,
- conflicting current-version consent decisions recorded at the same latest timestamp,
- report status outside the governed normalized status families,
- current-version consent approved while lifecycle still says `AWAITING_CLIENT_CONSENT`,
- `EXECUTION_READY` or `EXECUTED` without source-confirmed approved current-version consent.

## Workbench handoff

`lotus-workbench#749` should consume only the Gateway/BFF route. The screen should use the response
as a selected-record master/detail evidence view, preserve independent retry and restricted states,
and label internal advisor-use review separately from client-release and client-delivery boundaries.
It must not call Advise, Report, Render, Archive, or a communication service directly.

## Validation evidence

- `tests/unit/test_proposal_discussion_pack_projection.py`
- `tests/unit/test_proposal_discussion_pack_service.py`
- `tests/integration/test_proposal_discussion_pack_router.py`
- `tests/contract/test_proposal_discussion_pack_contract.py`
- `tests/unit/test_proposal_discussion_pack_documentation.py`

Focused live Gateway/BFF and Workbench browser evidence remains required before the consumer screen
is promoted from blocked to implementation-backed.
