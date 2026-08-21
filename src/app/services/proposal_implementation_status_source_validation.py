from datetime import datetime

from pydantic import ValidationError

from app.contracts.proposal_implementation_status import (
    ProposalImplementationEventType,
    ProposalImplementationHandoffStatus,
    ProposalImplementationWorkflowState,
)
from app.services.proposal_implementation_status_errors import (
    raise_proposal_implementation_status_contract_invalid,
)
from app.services.proposal_implementation_status_source_contract import (
    SourceProposalImplementationStatus,
)

_EXPECTED_EVENT_BY_STATUS: dict[
    ProposalImplementationHandoffStatus,
    ProposalImplementationEventType | None,
] = {
    "NOT_REQUESTED": None,
    "REQUESTED": "EXECUTION_REQUESTED",
    "ACCEPTED": "EXECUTION_ACCEPTED",
    "PARTIALLY_EXECUTED": "EXECUTION_PARTIALLY_EXECUTED",
    "EXECUTED": "EXECUTED",
    "REJECTED": "EXECUTION_REJECTED",
    "CANCELLED": "EXECUTION_CANCELLED",
    "EXPIRED": "EXECUTION_EXPIRED",
}
_EXPECTED_CORRELATION_BY_STATUS: dict[ProposalImplementationHandoffStatus, str] = {
    "NOT_REQUESTED": "NO_EXECUTION_EVENTS_RECORDED",
    "REQUESTED": "EXECUTION_REQUESTED_EVENT",
    "ACCEPTED": "EXECUTION_REQUESTED_AND_ACCEPTED_EVENTS",
    "PARTIALLY_EXECUTED": "EXECUTION_REQUESTED_AND_PARTIAL_EXECUTION_EVENTS",
    "EXECUTED": "EXECUTION_REQUESTED_AND_EXECUTED_EVENTS",
    "REJECTED": "EXECUTION_REQUESTED_AND_REJECTED_EVENTS",
    "CANCELLED": "EXECUTION_REQUESTED_AND_CANCELLED_EVENTS",
    "EXPIRED": "EXECUTION_REQUESTED_AND_EXPIRED_EVENTS",
}
_EXPECTED_PROPOSAL_STATE: dict[
    ProposalImplementationHandoffStatus,
    ProposalImplementationWorkflowState,
] = {
    "REQUESTED": "EXECUTION_READY",
    "ACCEPTED": "EXECUTION_READY",
    "PARTIALLY_EXECUTED": "EXECUTION_READY",
    "EXECUTED": "EXECUTED",
    "REJECTED": "REJECTED",
    "CANCELLED": "CANCELLED",
    "EXPIRED": "EXPIRED",
}


def validated_proposal_implementation_status_source(
    payload: dict[str, object],
    expected_proposal_id: str,
) -> SourceProposalImplementationStatus:
    """Validate source identity, lifecycle correlation, chronology, and ownership."""

    try:
        source = SourceProposalImplementationStatus.model_validate(payload)
    except ValidationError as exc:
        raise_proposal_implementation_status_contract_invalid(exc)

    _validate_identity(source, expected_proposal_id)
    _validate_status_correlation(source)
    _validate_chronology(source)
    return source


def _validate_identity(
    source: SourceProposalImplementationStatus,
    expected_proposal_id: str,
) -> None:
    event = source.latest_workflow_event
    if source.proposal.proposal_id != expected_proposal_id:
        raise_proposal_implementation_status_contract_invalid()
    if not source.proposal.portfolio_id.strip():
        raise_proposal_implementation_status_contract_invalid()
    if event is not None and event.proposal_id != source.proposal.proposal_id:
        raise_proposal_implementation_status_contract_invalid()
    if event is not None and (not event.event_id.strip() or not event.actor_id.strip()):
        raise_proposal_implementation_status_contract_invalid()
    if (
        source.related_version_no is not None
        and source.related_version_no > source.proposal.current_version_no
    ):
        raise_proposal_implementation_status_contract_invalid()
    if (
        event is not None
        and event.related_version_no is not None
        and event.related_version_no > source.proposal.current_version_no
    ):
        raise_proposal_implementation_status_contract_invalid()
    if (
        event is not None
        and event.related_version_no is not None
        and source.related_version_no is not None
        and event.related_version_no != source.related_version_no
    ):
        raise_proposal_implementation_status_contract_invalid()


def _validate_status_correlation(source: SourceProposalImplementationStatus) -> None:
    expected_event = _EXPECTED_EVENT_BY_STATUS[source.handoff_status]
    event = source.latest_workflow_event
    if expected_event is None and event is not None:
        raise_proposal_implementation_status_contract_invalid()
    if event is not None and event.event_type != expected_event:
        raise_proposal_implementation_status_contract_invalid()
    if (
        source.explanation.state_correlation
        != _EXPECTED_CORRELATION_BY_STATUS[source.handoff_status]
    ):
        raise_proposal_implementation_status_contract_invalid()
    if source.execution_ownership != source.explanation.execution_ownership:
        raise_proposal_implementation_status_contract_invalid()
    if any(
        value is not None and not value.strip()
        for value in (
            source.execution_request_id,
            source.execution_provider,
            source.external_execution_id,
        )
    ):
        raise_proposal_implementation_status_contract_invalid()
    if source.handoff_status == "NOT_REQUESTED" and any(
        value is not None
        for value in (
            source.execution_request_id,
            source.execution_provider,
            source.related_version_no,
            source.handoff_requested_at,
            source.executed_at,
            source.external_execution_id,
        )
    ):
        raise_proposal_implementation_status_contract_invalid()
    _validate_versioned_state_correlation(source)
    _validate_execution_timestamp(source)


def _validate_versioned_state_correlation(
    source: SourceProposalImplementationStatus,
) -> None:
    event = source.latest_workflow_event
    expected_proposal_state = _EXPECTED_PROPOSAL_STATE.get(source.handoff_status)
    evidence_is_current_version = source.related_version_no == source.proposal.current_version_no
    if (
        expected_proposal_state is not None
        and evidence_is_current_version
        and source.proposal.current_state != expected_proposal_state
    ):
        raise_proposal_implementation_status_contract_invalid()
    if (
        event is not None
        and event.related_version_no == source.proposal.current_version_no
        and event.to_state != source.proposal.current_state
    ):
        raise_proposal_implementation_status_contract_invalid()


def _validate_execution_timestamp(source: SourceProposalImplementationStatus) -> None:
    event = source.latest_workflow_event
    if source.handoff_status == "EXECUTED":
        if source.executed_at is None:
            raise_proposal_implementation_status_contract_invalid()
        if event is not None and source.executed_at != event.occurred_at:
            raise_proposal_implementation_status_contract_invalid()
    elif source.executed_at is not None:
        raise_proposal_implementation_status_contract_invalid()


def _validate_chronology(source: SourceProposalImplementationStatus) -> None:
    timestamps: list[datetime] = [source.proposal.created_at]
    if source.handoff_requested_at is not None:
        timestamps.append(source.handoff_requested_at)
    if source.latest_workflow_event is not None:
        timestamps.append(source.latest_workflow_event.occurred_at)
    if source.executed_at is not None:
        timestamps.append(source.executed_at)
    timestamps.append(source.proposal.last_event_at)
    if any(value.tzinfo is None or value.utcoffset() is None for value in timestamps):
        raise_proposal_implementation_status_contract_invalid()
    if any(left > right for left, right in zip(timestamps, timestamps[1:])):
        raise_proposal_implementation_status_contract_invalid()


__all__ = ["validated_proposal_implementation_status_source"]
