# Proposal memo response contract v1

`lotus-gateway` publishes the proposal-memo family as the Workbench experience contract over
`lotus-advise`. Advise remains authoritative for memo lifecycle, review events, report-package
events, commentary, lineage, replay evidence, hashes, and publication boundaries. Gateway
validates and composes those facts; it does not calculate memo readiness, approve a memo, generate
commentary, render or archive reports, or promote client-ready publication.

## Success response families

Every success envelope has the standard Gateway `correlation_id`, `contract_version`, and a typed
`data` payload. The payload models mirror the source-owned response shapes instead of exposing an
unconstrained `dict[str, Any]` at the API boundary.

| Gateway route family | Typed data payload | Source-owned evidence |
| --- | --- | --- |
| memo create/read | `ProposalMemoResponse` | proposal identity, immutable version, persisted memo, hashes, postures, audit events, replay and lineage paths |
| memo projection | `ProposalMemoProjectionResponse` | top-level audience, projection policy, source sections, supportability posture |
| memo review | `ProposalMemoReviewResponse` | refreshed memo, append-only `review_event`, `replayed` |
| report-package event | `ProposalMemoReportPackageEventResponse` | refreshed memo, append-only `report_package_event`, `replayed` |
| report-package request | `ProposalMemoReportPackageResponse` | refreshed memo, materialization event, typed Report handle, `replayed` |
| AI commentary request | `ProposalMemoAiCommentaryResponse` | refreshed memo, AI event, non-authoritative commentary, `replayed` |
| memo lineage | `ProposalMemoLineageResponse` | latest memo identity/order, typed lineage items, archive references, lineage posture |
| replay evidence | `ProposalMemoReplayEvidenceResponse` | subject, hashes, replay metadata, audit events, evidence, explanation |

The memo evidence pack, projection policy and sections, review/report/AI/read postures, replay
evidence, commentary, and report explanation use closed typed models with named OpenAPI
properties. Advise still owns the values and vocabulary; Gateway does not reinterpret them. A
small set of source-owned metadata fields remains a bounded scalar-keyed map so Gateway can
preserve evidence without inventing domain semantics.

## Compatibility and failure behavior

- Existing route paths, request bodies, correlation propagation, idempotency headers, and source
  calls are unchanged.
- The response schema is intentionally corrected to describe the existing Advise response. Clients
  must use `data.memo`, `data.review_event`, `data.report_package_event`, `data.ai_event`, and
  top-level `data.audience` where those fields apply; the old illustrative shapes such as
  `data.review_posture.advisor_use` are not contract truth.
- Gateway validates each successful upstream payload against its typed source projection. A
  missing required source field fails the response construction rather than publishing an
  incomplete success object that Workbench could mistake for authoritative evidence.
- If Advise returns HTTP 2xx with a malformed memo payload, Gateway returns a product-safe `502`
  with `error_code=ADVISE_PROPOSAL_MEMO_CONTRACT_INVALID`, identifies `lotus-advise` as the
  source, and does not publish the invalid payload as a `200` response.
- Memo detail requires `audit_events` and rejects any response where `event_count` differs from
  the number of returned events; Gateway never fabricates an empty event list for a claimed count.
- Memo lineage requires `memos`, requires `memo_count` to equal the returned item count, requires
  `latest_memo_id` to identify the final source-ordered item, and rejects descending proposal
  version order. This prevents contradictory completeness evidence from reaching Workbench.
- Upstream error mapping, source hashes, idempotency behavior, and client-ready blocking posture
  remain owned by the existing Gateway/Advise boundary.

## Fitness coverage

`tests/contract/test_proposals_contract.py` proves source-faithful payloads, rejects stale
illustrative nesting, and asserts that every memo-family envelope points to a closed OpenAPI
component with named properties; nested memo refs are checked recursively. It also rejects
missing or contradictory lineage and audit-count evidence. `tests/unit/test_proposal_service.py`
proves malformed successful upstream memo payloads map to the product-safe source-contract error;
the integration route test proves the report-package event route returns its typed event envelope.
