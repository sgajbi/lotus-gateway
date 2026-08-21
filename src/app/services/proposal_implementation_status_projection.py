from dataclasses import dataclass

from app.contracts.proposal_implementation_status import (
    ProposalImplementationCapability,
    ProposalImplementationCapabilityKey,
    ProposalImplementationCapabilityState,
    ProposalImplementationEvidenceState,
    ProposalImplementationFreshness,
    ProposalImplementationHandoffStatus,
    ProposalImplementationLatestEvent,
    ProposalImplementationLineage,
    ProposalImplementationNextAction,
    ProposalImplementationOwnership,
    ProposalImplementationStatusData,
    ProposalImplementationStatusFamily,
    ProposalImplementationVersionPosture,
)
from app.services.proposal_implementation_status_source_contract import (
    SourceProposalImplementationEvent,
    SourceProposalImplementationStatus,
)
from app.services.proposal_implementation_status_source_validation import (
    validated_proposal_implementation_status_source,
)


@dataclass(frozen=True)
class _StatusSemantics:
    family: ProposalImplementationStatusFamily
    next_action: ProposalImplementationNextAction
    attention_required: bool
    terminal: bool
    reason_code: str


_STATUS_SEMANTICS: dict[ProposalImplementationHandoffStatus, _StatusSemantics] = {
    "NOT_REQUESTED": _StatusSemantics(
        "not_started", "REQUEST_HANDOFF", False, False, "implementation_handoff_not_requested"
    ),
    "REQUESTED": _StatusSemantics(
        "pending", "MONITOR_HANDOFF", False, False, "implementation_handoff_requested"
    ),
    "ACCEPTED": _StatusSemantics(
        "pending", "MONITOR_IMPLEMENTATION", False, False, "implementation_handoff_accepted"
    ),
    "PARTIALLY_EXECUTED": _StatusSemantics(
        "attention",
        "REVIEW_PARTIAL_EXECUTION",
        True,
        False,
        "implementation_partially_executed",
    ),
    "EXECUTED": _StatusSemantics("completed", "NO_ACTION", False, True, "implementation_executed"),
    "REJECTED": _StatusSemantics(
        "attention", "INVESTIGATE_REJECTION", True, True, "implementation_rejected"
    ),
    "CANCELLED": _StatusSemantics(
        "attention", "REVIEW_CANCELLATION", True, True, "implementation_cancelled"
    ),
    "EXPIRED": _StatusSemantics(
        "attention", "REVALIDATE_HANDOFF", True, True, "implementation_handoff_expired"
    ),
}


def project_proposal_implementation_status(
    payload: dict[str, object],
    *,
    expected_proposal_id: str,
    correlation_id: str,
) -> ProposalImplementationStatusData:
    """Project source-owned handoff evidence without claiming execution-system authority."""

    source = validated_proposal_implementation_status_source(payload, expected_proposal_id)
    semantics = _STATUS_SEMANTICS[source.handoff_status]
    event = _latest_event(source.latest_workflow_event)
    version_posture = _version_posture(source)
    evidence_state = _evidence_state(source)
    return ProposalImplementationStatusData(
        proposal_id=source.proposal.proposal_id,
        portfolio_id=source.proposal.portfolio_id,
        title=source.proposal.title,
        current_state=source.proposal.current_state,
        current_version_no=source.proposal.current_version_no,
        handoff_status=source.handoff_status,
        status_family=semantics.family,
        next_action=semantics.next_action,
        attention_required=semantics.attention_required,
        terminal=semantics.terminal,
        evidence_state=evidence_state,
        reason_code=(
            semantics.reason_code
            if evidence_state == "supported"
            else "implementation_evidence_partial"
        ),
        execution_request_id=source.execution_request_id,
        execution_provider=source.execution_provider,
        related_version_no=source.related_version_no,
        version_posture=version_posture,
        handoff_requested_at=source.handoff_requested_at,
        executed_at=source.executed_at,
        external_execution_id=source.external_execution_id,
        latest_workflow_event=event,
        ownership=ProposalImplementationOwnership.model_validate(
            source.execution_ownership.model_dump()
        ),
        freshness=ProposalImplementationFreshness(
            observed_at=(source.proposal.last_event_at if event is None else event.occurred_at),
            basis="PROPOSAL_LAST_EVENT" if event is None else "LATEST_EXECUTION_EVENT",
        ),
        capabilities=_capabilities(source),
        lineage=ProposalImplementationLineage(
            proposal_id=source.proposal.proposal_id,
            portfolio_id=source.proposal.portfolio_id,
            related_version_no=source.related_version_no,
            latest_event_id=None if event is None else event.event_id,
            gateway_correlation_id=correlation_id,
        ),
    )


def _latest_event(
    event: SourceProposalImplementationEvent | None,
) -> ProposalImplementationLatestEvent | None:
    if event is None:
        return None
    return ProposalImplementationLatestEvent(
        event_id=event.event_id,
        event_type=event.event_type,
        actor_id=event.actor_id,
        occurred_at=event.occurred_at,
        related_version_no=event.related_version_no,
    )


def _version_posture(
    source: SourceProposalImplementationStatus,
) -> ProposalImplementationVersionPosture:
    if source.related_version_no is None:
        return "not_correlated"
    if source.related_version_no == source.proposal.current_version_no:
        return "current_version"
    return "historical_version"


def _evidence_state(
    source: SourceProposalImplementationStatus,
) -> ProposalImplementationEvidenceState:
    if source.handoff_status == "NOT_REQUESTED":
        return "supported"
    required_values = (
        source.execution_request_id,
        source.execution_provider,
        source.related_version_no,
        source.latest_workflow_event,
    )
    return "supported" if all(value is not None for value in required_values) else "partial"


def _capabilities(
    source: SourceProposalImplementationStatus,
) -> list[ProposalImplementationCapability]:
    return [
        ProposalImplementationCapability(
            key="handoff_posture",
            state="supported",
            reason_code="advise_handoff_status_available",
            source_service="lotus-advise",
        ),
        _optional_capability(
            key="provider_reference",
            available=bool(source.execution_request_id and source.execution_provider),
            available_reason="provider_and_request_reference_available",
            unavailable_reason="provider_or_request_reference_not_available",
        ),
        _optional_capability(
            key="downstream_reference",
            available=source.external_execution_id is not None,
            available_reason="downstream_execution_reference_available",
            unavailable_reason="downstream_execution_reference_not_available",
        ),
        _optional_capability(
            key="event_lineage",
            available=source.latest_workflow_event is not None,
            available_reason="latest_execution_event_available",
            unavailable_reason="latest_execution_event_not_available",
        ),
        ProposalImplementationCapability(
            key="order_fill_settlement_detail",
            state="not_supported",
            reason_code="downstream_execution_authority_not_exposed",
        ),
    ]


def _optional_capability(
    *,
    key: ProposalImplementationCapabilityKey,
    available: bool,
    available_reason: str,
    unavailable_reason: str,
) -> ProposalImplementationCapability:
    state: ProposalImplementationCapabilityState = "supported" if available else "not_available"
    return ProposalImplementationCapability(
        key=key,
        state=state,
        reason_code=available_reason if available else unavailable_reason,
        source_service="lotus-advise" if available else None,
    )


__all__ = ["project_proposal_implementation_status"]
