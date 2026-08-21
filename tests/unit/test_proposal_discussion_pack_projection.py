from copy import deepcopy

import pytest
from fastapi import HTTPException

from app.services.proposal_discussion_pack_errors import (
    ProposalDiscussionPackSnapshotConflict,
)
from app.services.proposal_discussion_pack_projection import (
    ProposalDiscussionSourceResponse,
    project_proposal_discussion_pack,
)
from tests.shared.proposal_discussion_pack_payload import (
    build_discussion_pack_source_payloads,
)


def _response(
    payload: dict[str, object], status_code: int = 200
) -> ProposalDiscussionSourceResponse:
    return ProposalDiscussionSourceResponse(status_code=status_code, payload=payload)


def _project(payloads: dict[str, dict[str, object]]):
    return project_proposal_discussion_pack(
        detail_payload=payloads["detail"],
        narrative_response=_response(payloads["narrative"]),
        memo_response=_response(payloads["memo"]),
        approvals_response=_response(payloads["approvals"]),
        delivery_response=_response(payloads["delivery"]),
        expected_proposal_id="pp_discussion_001",
        expected_portfolio_id="PB_SG_GLOBAL_BAL_001",
        expected_version_no=2,
        correlation_id="corr-discussion-pack",
    )


def _prepared_payloads(
    *,
    state: str = "EXECUTION_READY",
    consent_approved: bool = True,
) -> dict[str, dict[str, object]]:
    payloads = build_discussion_pack_source_payloads(state=state)
    approvals = payloads["approvals"]
    approvals["approvals"].append(
        {
            "approval_id": "approval_consent_002",
            "proposal_id": "pp_discussion_001",
            "approval_type": "CLIENT_CONSENT",
            "approved": consent_approved,
            "actor_id": "client_1",
            "occurred_at": "2026-08-21T09:20:00Z",
            "related_version_no": 2,
        }
    )
    approvals["approval_count"] = 3
    approvals["latest_approval_at"] = "2026-08-21T09:20:00Z"
    payloads["delivery"]["reporting"] = {
        "report_request_id": "prr_002",
        "report_service": "lotus-report",
        "status": "READY",
        "report_reference_id": "report_002",
        "related_version_no": 2,
        "include_reviewed_narrative": True,
        "generated_at": "2026-08-21T09:15:00Z",
    }
    return payloads


def test_projection_separates_advisor_evidence_from_client_release() -> None:
    result = _project(build_discussion_pack_source_payloads())

    assert result.overall_state == "supported"
    assert result.narrative.review_state == "APPROVED_FOR_ADVISOR_USE"
    assert result.memo.latest_review_action == "APPROVE_FOR_ADVISOR_USE"
    assert result.package.package_state == "not_requested"
    assert result.consent.consent_state == "not_recorded"
    assert result.attention_required is True
    assert result.client_release.state == "blocked"
    assert result.client_release.publication_supported is False
    assert result.client_release.delivery_supported is False
    assert result.lineage.narrative_hash == "sha256:narrative-002"


def test_projection_preserves_independent_source_failure() -> None:
    payloads = build_discussion_pack_source_payloads()

    result = project_proposal_discussion_pack(
        detail_payload=payloads["detail"],
        narrative_response=ProposalDiscussionSourceResponse(503, {}),
        memo_response=_response(payloads["memo"]),
        approvals_response=ProposalDiscussionSourceResponse(403, {}),
        delivery_response=_response(payloads["delivery"]),
        expected_proposal_id="pp_discussion_001",
        expected_portfolio_id="PB_SG_GLOBAL_BAL_001",
        expected_version_no=2,
        correlation_id="corr-discussion-partial",
    )

    assert result.overall_state == "partial"
    assert result.narrative.state == "unavailable"
    assert result.memo.state == "supported"
    assert result.consent.state == "restricted"
    assert result.package.state == "not_available"


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("detail", "proposal", "portfolio_id"), "PF_OTHER"),
        (("narrative", "proposal_version_no"), 1),
        (("memo", "projection", "client_ready_publication"), "AVAILABLE"),
    ],
)
def test_projection_fails_closed_on_identity_or_release_contradiction(
    path: tuple[str, ...],
    value: object,
) -> None:
    payloads = build_discussion_pack_source_payloads()
    target: dict[str, object] = payloads[path[0]]
    for key in path[1:-1]:
        target = target[key]  # type: ignore[assignment]
    target[path[-1]] = value

    with pytest.raises(HTTPException) as exc_info:
        _project(payloads)

    assert exc_info.value.status_code == 502
    assert exc_info.value.detail["error_code"] == (
        "ADVISE_PROPOSAL_DISCUSSION_PACK_CONTRACT_INVALID"
    )


@pytest.mark.parametrize(
    ("payload", "path"),
    [
        ("detail", ("proposal", "created_at")),
        ("detail", ("current_version", "created_at")),
        ("narrative", ("narrative_review", "reviewed_at")),
        ("memo", ("review_posture", "occurred_at")),
        ("approvals", ("approvals", 0, "occurred_at")),
        ("delivery", ("reporting", "generated_at")),
    ],
)
def test_projection_rejects_timezone_naive_source_chronology(
    payload: str,
    path: tuple[str | int, ...],
) -> None:
    payloads = (
        _prepared_payloads() if payload == "delivery" else build_discussion_pack_source_payloads()
    )
    target: object = payloads[payload]
    for key in path[:-1]:
        target = target[key]  # type: ignore[index]
    target[path[-1]] = "2026-08-21T08:30:00"  # type: ignore[index]

    with pytest.raises(HTTPException) as exc_info:
        _project(payloads)

    assert exc_info.value.status_code == 502
    assert exc_info.value.detail["error_code"] == (
        "ADVISE_PROPOSAL_DISCUSSION_PACK_CONTRACT_INVALID"
    )


def test_projection_rejects_duplicate_disclosure_identifiers() -> None:
    payloads = build_discussion_pack_source_payloads()
    narrative = payloads["narrative"]["proposal_narrative"]
    assert isinstance(narrative, dict)
    narrative["disclosures"].append(deepcopy(narrative["disclosures"][0]))

    with pytest.raises(HTTPException):
        _project(payloads)


@pytest.mark.parametrize(
    "field",
    ["jurisdiction", "product_type", "required_for", "text", "source_authority", "policy_version"],
)
def test_projection_rejects_disclosure_content_that_differs_from_policy(
    field: str,
) -> None:
    payloads = build_discussion_pack_source_payloads()
    narrative = payloads["narrative"]["proposal_narrative"]
    narrative["disclosures"][0][field] = f"altered-{field}"

    with pytest.raises(HTTPException) as exc_info:
        _project(payloads)

    assert exc_info.value.detail["error_code"] == (
        "ADVISE_PROPOSAL_DISCUSSION_PACK_CONTRACT_INVALID"
    )


def test_projection_rejects_narrative_review_before_selected_version() -> None:
    payloads = build_discussion_pack_source_payloads()
    review = payloads["narrative"]["narrative_review"]
    review["reviewed_at"] = "2026-08-21T08:00:00Z"

    with pytest.raises(HTTPException):
        _project(payloads)


def test_projection_rejects_consent_that_conflicts_with_lifecycle_state() -> None:
    payloads = build_discussion_pack_source_payloads()
    approvals = payloads["approvals"]
    approval = {
        "approval_id": "approval_consent_002",
        "proposal_id": "pp_discussion_001",
        "approval_type": "CLIENT_CONSENT",
        "approved": True,
        "actor_id": "client_1",
        "occurred_at": "2026-08-21T09:20:00Z",
        "related_version_no": 2,
    }
    approvals["approvals"].append(approval)
    approvals["approval_count"] = 3
    approvals["latest_approval_at"] = "2026-08-21T09:20:00Z"

    with pytest.raises(ProposalDiscussionPackSnapshotConflict):
        _project(payloads)


@pytest.mark.parametrize("state", ["EXECUTION_READY", "EXECUTED"])
def test_projection_rejects_declined_consent_for_execution_state(state: str) -> None:
    payloads = _prepared_payloads(state=state, consent_approved=False)

    with pytest.raises(ProposalDiscussionPackSnapshotConflict):
        _project(payloads)


def test_projection_rejects_consent_recorded_before_selected_version() -> None:
    payloads = _prepared_payloads()
    consent = payloads["approvals"]["approvals"][-1]
    consent["occurred_at"] = "2026-08-21T08:00:00Z"
    payloads["approvals"]["latest_approval_at"] = "2026-08-21T08:00:00Z"

    with pytest.raises(HTTPException):
        _project(payloads)


@pytest.mark.parametrize("status_code", [403, 404, 503])
def test_projection_requires_supported_consent_for_execution_state(
    status_code: int,
) -> None:
    payloads = build_discussion_pack_source_payloads(state="EXECUTION_READY")

    with pytest.raises(ProposalDiscussionPackSnapshotConflict):
        project_proposal_discussion_pack(
            detail_payload=payloads["detail"],
            narrative_response=_response(payloads["narrative"]),
            memo_response=_response(payloads["memo"]),
            approvals_response=ProposalDiscussionSourceResponse(status_code, {}),
            delivery_response=_response(payloads["delivery"]),
            expected_proposal_id="pp_discussion_001",
            expected_portfolio_id="PB_SG_GLOBAL_BAL_001",
            expected_version_no=2,
            correlation_id="corr-discussion-consent-unavailable",
        )


def test_projection_rejects_memo_review_before_selected_version() -> None:
    payloads = build_discussion_pack_source_payloads()
    payloads["memo"]["review_posture"]["occurred_at"] = "2026-08-21T08:00:00Z"

    with pytest.raises(HTTPException):
        _project(payloads)


def test_projection_rejects_memo_package_event_before_selected_version() -> None:
    payloads = build_discussion_pack_source_payloads()
    payloads["memo"]["report_package_posture"] = {
        "status": "RECORDED",
        "event_id": "memo_package_002",
        "actor_id": "advisor_1",
        "occurred_at": "2026-08-21T08:00:00Z",
        "report_package_status": "RECORDED",
    }

    with pytest.raises(HTTPException):
        _project(payloads)


@pytest.mark.parametrize("posture_key", ["review_posture", "report_package_posture"])
def test_projection_rejects_recorded_memo_event_without_typed_detail(
    posture_key: str,
) -> None:
    payloads = build_discussion_pack_source_payloads()
    payloads["memo"][posture_key] = {
        "status": "RECORDED",
        "event_id": f"{posture_key}_002",
        "actor_id": "advisor_1",
        "occurred_at": "2026-08-21T09:10:00Z",
    }

    with pytest.raises(HTTPException):
        _project(payloads)


def test_projection_rejects_report_package_before_selected_version() -> None:
    payloads = _prepared_payloads()
    payloads["delivery"]["reporting"]["generated_at"] = "2026-08-21T08:00:00Z"

    with pytest.raises(HTTPException):
        _project(payloads)


def test_projection_rejects_available_package_without_source_reference() -> None:
    payloads = _prepared_payloads()
    payloads["delivery"]["reporting"]["report_reference_id"] = None

    with pytest.raises(HTTPException):
        _project(payloads)


def test_projection_uses_latest_consent_by_time_not_source_order() -> None:
    payloads = _prepared_payloads()
    approvals = payloads["approvals"]
    approvals["approvals"].append(
        {
            "approval_id": "approval_consent_earlier_002",
            "proposal_id": "pp_discussion_001",
            "approval_type": "CLIENT_CONSENT",
            "approved": False,
            "actor_id": "client_1",
            "occurred_at": "2026-08-21T09:00:00Z",
            "related_version_no": 2,
        }
    )
    approvals["approval_count"] = 4

    result = _project(payloads)

    assert result.consent.consent_state == "approved"
    assert result.consent.approval_id == "approval_consent_002"


def test_projection_rejects_conflicting_consent_at_the_latest_timestamp() -> None:
    payloads = _prepared_payloads()
    approvals = payloads["approvals"]
    approvals["approvals"].append(
        {
            "approval_id": "approval_consent_conflict_002",
            "proposal_id": "pp_discussion_001",
            "approval_type": "CLIENT_CONSENT",
            "approved": False,
            "actor_id": "client_1",
            "occurred_at": "2026-08-21T09:20:00Z",
            "related_version_no": 2,
        }
    )
    approvals["approval_count"] = 4

    with pytest.raises(HTTPException) as exc_info:
        _project(payloads)

    assert exc_info.value.detail["error_code"] == (
        "ADVISE_PROPOSAL_DISCUSSION_PACK_CONTRACT_INVALID"
    )


def test_projection_selects_same_decision_ties_deterministically() -> None:
    payloads = _prepared_payloads()
    approvals = payloads["approvals"]
    approvals["approvals"].append(
        {
            "approval_id": "approval_consent_z_002",
            "proposal_id": "pp_discussion_001",
            "approval_type": "CLIENT_CONSENT",
            "approved": True,
            "actor_id": "client_2",
            "occurred_at": "2026-08-21T09:20:00Z",
            "related_version_no": 2,
        }
    )
    approvals["approval_count"] = 4

    result = _project(payloads)

    assert result.consent.approval_id == "approval_consent_z_002"


@pytest.mark.parametrize(
    "occurred_at",
    ["2026-08-21T09:20:00Z", "2026-08-21T09:21:00Z"],
)
def test_projection_marks_latest_uncorrelated_consent_partial(
    occurred_at: str,
) -> None:
    payloads = _prepared_payloads(state="AWAITING_CLIENT_CONSENT")
    approvals = payloads["approvals"]
    approvals["approvals"].append(
        {
            "approval_id": "approval_consent_uncorrelated_003",
            "proposal_id": "pp_discussion_001",
            "approval_type": "CLIENT_CONSENT",
            "approved": False,
            "actor_id": "client_1",
            "occurred_at": occurred_at,
            "related_version_no": None,
        }
    )
    approvals["approval_count"] = 4
    approvals["latest_approval_at"] = max(
        "2026-08-21T09:20:00Z",
        occurred_at,
    )

    result = _project(payloads)

    assert result.consent.state == "partial"
    assert result.consent.consent_state == "not_recorded"
    assert result.consent.reason_code == "client_consent_version_not_correlated"
    assert result.attention_required is True


def test_projection_rejects_execution_when_latest_consent_is_uncorrelated() -> None:
    payloads = _prepared_payloads(state="EXECUTION_READY")
    approvals = payloads["approvals"]
    approvals["approvals"].append(
        {
            "approval_id": "approval_consent_uncorrelated_003",
            "proposal_id": "pp_discussion_001",
            "approval_type": "CLIENT_CONSENT",
            "approved": False,
            "actor_id": "client_1",
            "occurred_at": "2026-08-21T09:21:00Z",
            "related_version_no": None,
        }
    )
    approvals["approval_count"] = 4
    approvals["latest_approval_at"] = "2026-08-21T09:21:00Z"

    with pytest.raises(ProposalDiscussionPackSnapshotConflict):
        _project(payloads)


def test_projection_retains_newer_correlated_consent_over_older_uncorrelated_record() -> None:
    payloads = _prepared_payloads(state="EXECUTION_READY")
    approvals = payloads["approvals"]
    approvals["approvals"].append(
        {
            "approval_id": "approval_consent_uncorrelated_001",
            "proposal_id": "pp_discussion_001",
            "approval_type": "CLIENT_CONSENT",
            "approved": False,
            "actor_id": "client_1",
            "occurred_at": "2026-08-21T09:19:00Z",
            "related_version_no": None,
        }
    )
    approvals["approval_count"] = 4

    result = _project(payloads)

    assert result.consent.state == "supported"
    assert result.consent.consent_state == "approved"
    assert result.consent.approval_id == "approval_consent_002"


def test_projection_clears_attention_only_when_review_controls_are_resolved() -> None:
    result = _project(_prepared_payloads())

    assert result.attention_required is False


def test_projection_requires_attention_for_declined_consent() -> None:
    result = _project(
        _prepared_payloads(
            state="AWAITING_CLIENT_CONSENT",
            consent_approved=False,
        )
    )

    assert result.consent.consent_state == "declined"
    assert result.attention_required is True


def test_projection_requires_attention_while_report_package_is_pending() -> None:
    payloads = _prepared_payloads()
    payloads["delivery"]["reporting"]["status"] = "PENDING"

    result = _project(payloads)

    assert result.package.package_state == "pending"
    assert result.attention_required is True


@pytest.mark.parametrize(
    ("evidence", "field", "value"),
    [
        ("narrative", "review_state", "REJECTED"),
        ("narrative", "review_state", "REGENERATION_REQUESTED"),
        ("memo", "review_action", "REQUEST_CHANGES"),
        ("memo", "review_action", "REJECT"),
    ],
)
def test_projection_requires_attention_for_unresolved_advisor_review(
    evidence: str,
    field: str,
    value: str,
) -> None:
    payloads = _prepared_payloads()
    if evidence == "narrative":
        payloads["narrative"]["narrative_review"][field] = value
    else:
        payloads["memo"]["review_posture"][field] = value

    result = _project(payloads)

    assert result.attention_required is True


def test_projection_rejects_unknown_report_status() -> None:
    payloads = build_discussion_pack_source_payloads()
    payloads["delivery"]["reporting"] = {
        "report_request_id": "prr_002",
        "report_service": "lotus-report",
        "status": "MYSTERY",
        "report_reference_id": "report_002",
        "related_version_no": 2,
        "include_reviewed_narrative": True,
        "generated_at": "2026-08-21T09:15:00Z",
    }

    with pytest.raises(HTTPException):
        _project(payloads)
