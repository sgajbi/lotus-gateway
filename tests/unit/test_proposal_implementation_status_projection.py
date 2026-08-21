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


def test_projection_preserves_valid_status_when_event_evidence_is_missing() -> None:
    payload = build_proposal_implementation_status_source_payload(status="ACCEPTED")
    payload["latest_workflow_event"] = None

    result = project_proposal_implementation_status(
        payload,
        expected_proposal_id="pp_implementation_001",
        correlation_id="corr-implementation-missing-event",
    )

    assert result.handoff_status == "ACCEPTED"
    assert result.evidence_state == "partial"
    assert result.latest_workflow_event is None
    event_lineage = next(item for item in result.capabilities if item.key == "event_lineage")
    assert event_lineage.state == "not_available"


def test_projection_preserves_executed_status_when_event_evidence_is_missing() -> None:
    payload = build_proposal_implementation_status_source_payload(status="EXECUTED")
    payload["latest_workflow_event"] = None

    result = project_proposal_implementation_status(
        payload,
        expected_proposal_id="pp_implementation_001",
        correlation_id="corr-implementation-executed-without-event",
    )

    assert result.handoff_status == "EXECUTED"
    assert result.evidence_state == "partial"
    assert result.executed_at is not None
    assert result.latest_workflow_event is None


def test_projection_preserves_historical_handoff_after_later_version_transition() -> None:
    payload = build_proposal_implementation_status_source_payload(
        status="ACCEPTED",
        current_version_no=3,
        related_version_no=2,
    )
    proposal = payload["proposal"]
    assert isinstance(proposal, dict)
    proposal["current_state"] = "DRAFT"

    result = project_proposal_implementation_status(
        payload,
        expected_proposal_id="pp_implementation_001",
        correlation_id="corr-implementation-historical-transition",
    )

    assert result.handoff_status == "ACCEPTED"
    assert result.current_state == "DRAFT"
    assert result.version_posture == "historical_version"


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
        "future_event_version_without_top_level_version",
        "event_version",
        "blank_request_reference",
        "blank_provider_reference",
        "blank_downstream_reference",
        "blank_event_id",
        "blank_event_actor",
        "proposal_state_contradiction",
        "event_state_contradiction",
        "historical_event_state_contradiction",
        "unversioned_event_state_contradiction",
        "current_event_without_top_level_version_contradiction",
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
    proposal = payload["proposal"]
    assert isinstance(proposal, dict)
    event = payload["latest_workflow_event"]
    assert isinstance(event, dict)
    explanation = payload["explanation"]
    assert isinstance(explanation, dict)

    if mutation == "proposal_identity":
        proposal["proposal_id"] = "pp_other"
    elif mutation == "event_identity":
        event["proposal_id"] = "pp_other"
    elif mutation == "future_version":
        payload["related_version_no"] = 3
    elif mutation == "future_event_version_without_top_level_version":
        payload["related_version_no"] = None
        event["related_version_no"] = 3
    elif mutation == "event_version":
        event["related_version_no"] = 1
    elif mutation == "blank_request_reference":
        payload["execution_request_id"] = " "
    elif mutation == "blank_provider_reference":
        payload["execution_provider"] = ""
    elif mutation == "blank_downstream_reference":
        payload["external_execution_id"] = " "
    elif mutation == "blank_event_id":
        event["event_id"] = " "
    elif mutation == "blank_event_actor":
        event["actor_id"] = ""
    elif mutation == "proposal_state_contradiction":
        proposal["current_state"] = "REJECTED"
    elif mutation == "event_state_contradiction":
        event["to_state"] = "REJECTED"
    elif mutation == "historical_event_state_contradiction":
        payload["related_version_no"] = 1
        event["related_version_no"] = 1
        event["to_state"] = "REJECTED"
    elif mutation == "unversioned_event_state_contradiction":
        payload["related_version_no"] = None
        event["related_version_no"] = None
        event["to_state"] = "REJECTED"
    elif mutation == "current_event_without_top_level_version_contradiction":
        payload["related_version_no"] = None
        proposal["current_state"] = "REJECTED"
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
