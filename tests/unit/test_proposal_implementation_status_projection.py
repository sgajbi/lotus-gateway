from copy import deepcopy

import pytest
from fastapi import HTTPException

from app.contracts.proposal_implementation_status import (
    ProposalImplementationHandoffStatus,
    ProposalImplementationNextAction,
    ProposalImplementationStatusFamily,
)
from app.services.proposal_implementation_status_projection import (
    project_proposal_implementation_status,
)
from tests.shared.proposal_implementation_status_payload import (
    build_proposal_implementation_status_source_payload,
)


@pytest.mark.parametrize(
    ("status", "family", "next_action", "attention", "terminal"),
    [
        ("NOT_REQUESTED", "not_started", "REQUEST_HANDOFF", False, False),
        ("REQUESTED", "pending", "MONITOR_HANDOFF", False, False),
        ("ACCEPTED", "pending", "MONITOR_IMPLEMENTATION", False, False),
        (
            "PARTIALLY_EXECUTED",
            "attention",
            "REVIEW_PARTIAL_EXECUTION",
            True,
            False,
        ),
        ("EXECUTED", "completed", "NO_ACTION", False, True),
        ("REJECTED", "attention", "INVESTIGATE_REJECTION", True, True),
        ("CANCELLED", "attention", "REVIEW_CANCELLATION", True, True),
        ("EXPIRED", "attention", "REVALIDATE_HANDOFF", True, True),
    ],
)
def test_projection_preserves_every_source_handoff_state(
    status: ProposalImplementationHandoffStatus,
    family: ProposalImplementationStatusFamily,
    next_action: ProposalImplementationNextAction,
    attention: bool,
    terminal: bool,
) -> None:
    result = project_proposal_implementation_status(
        build_proposal_implementation_status_source_payload(status=status),
        expected_proposal_id="pp_implementation_001",
        correlation_id="corr-implementation-001",
    )

    assert result.handoff_status == status
    assert result.status_family == family
    assert result.next_action == next_action
    assert result.attention_required is attention
    assert result.terminal is terminal
    assert result.evidence_state == "supported"
    assert result.lineage.gateway_correlation_id == "corr-implementation-001"
    assert result.ownership.execution_system_of_record == "DOWNSTREAM_EXECUTION_PROVIDER"
    assert result.capabilities[-1].key == "order_fill_settlement_detail"
    assert result.capabilities[-1].state == "not_supported"


def test_projection_marks_missing_optional_handoff_evidence_as_partial() -> None:
    payload = build_proposal_implementation_status_source_payload(status="ACCEPTED")
    payload["execution_provider"] = None

    result = project_proposal_implementation_status(
        payload,
        expected_proposal_id="pp_implementation_001",
        correlation_id="corr-implementation-partial",
    )

    assert result.evidence_state == "partial"
    assert result.reason_code == "implementation_evidence_partial"
    provider = next(item for item in result.capabilities if item.key == "provider_reference")
    assert provider.state == "not_available"


def test_projection_identifies_historical_version_without_calling_it_current() -> None:
    result = project_proposal_implementation_status(
        build_proposal_implementation_status_source_payload(
            status="ACCEPTED",
            current_version_no=3,
            related_version_no=2,
        ),
        expected_proposal_id="pp_implementation_001",
        correlation_id="corr-implementation-history",
    )

    assert result.version_posture == "historical_version"
    assert result.related_version_no == 2
    assert result.current_version_no == 3


@pytest.mark.parametrize(
    "mutation",
    [
        "proposal_identity",
        "event_identity",
        "future_version",
        "event_version",
        "status_event",
        "state_correlation",
        "ownership",
        "chronology",
        "executed_timestamp",
        "status_vocabulary",
    ],
)
def test_projection_fails_closed_for_unverifiable_source_contract(mutation: str) -> None:
    payload = build_proposal_implementation_status_source_payload(status="EXECUTED")
    event = payload["latest_workflow_event"]
    assert isinstance(event, dict)
    explanation = payload["explanation"]
    assert isinstance(explanation, dict)

    if mutation == "proposal_identity":
        proposal = payload["proposal"]
        assert isinstance(proposal, dict)
        proposal["proposal_id"] = "pp_other"
    elif mutation == "event_identity":
        event["proposal_id"] = "pp_other"
    elif mutation == "future_version":
        payload["related_version_no"] = 3
    elif mutation == "event_version":
        event["related_version_no"] = 1
    elif mutation == "status_event":
        event["event_type"] = "EXECUTION_ACCEPTED"
    elif mutation == "state_correlation":
        explanation["state_correlation"] = "EXECUTION_REQUESTED_AND_ACCEPTED_EVENTS"
    elif mutation == "ownership":
        ownership = explanation["execution_ownership"]
        assert isinstance(ownership, dict)
        ownership["execution_system_of_record"] = "lotus-advise"
    elif mutation == "chronology":
        payload["handoff_requested_at"] = "2026-08-20T09:20:00+00:00"
    elif mutation == "executed_timestamp":
        payload["executed_at"] = "2026-08-20T09:09:00+00:00"
    else:
        payload["handoff_status"] = "READY"

    with pytest.raises(HTTPException) as exc_info:
        project_proposal_implementation_status(
            deepcopy(payload),
            expected_proposal_id="pp_implementation_001",
            correlation_id="corr-invalid",
        )

    assert exc_info.value.status_code == 502
    assert exc_info.value.detail["error_code"] == (
        "ADVISE_PROPOSAL_IMPLEMENTATION_STATUS_CONTRACT_INVALID"
    )
