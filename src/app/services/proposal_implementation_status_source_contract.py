from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.contracts.proposal_implementation_status import (
    ProposalImplementationEventType,
    ProposalImplementationHandoffStatus,
    ProposalImplementationWorkflowState,
)


class SourceProposalImplementationProposal(BaseModel):
    proposal_id: str = Field(min_length=1)
    portfolio_id: str = Field(min_length=1)
    created_at: datetime
    last_event_at: datetime
    current_state: ProposalImplementationWorkflowState
    current_version_no: int = Field(ge=1)
    title: str | None = None


class SourceProposalImplementationEvent(BaseModel):
    event_id: str = Field(min_length=1)
    proposal_id: str = Field(min_length=1)
    event_type: ProposalImplementationEventType
    from_state: ProposalImplementationWorkflowState | None = None
    to_state: ProposalImplementationWorkflowState
    actor_id: str = Field(min_length=1)
    occurred_at: datetime
    reason: dict[str, Any] = Field(default_factory=dict)
    related_version_no: int | None = Field(default=None, ge=1)


class SourceProposalImplementationOwnership(BaseModel):
    advisory_role: Literal["HANDOFF_REQUEST_AND_STATUS_RECONCILIATION"]
    execution_system_of_record: Literal["DOWNSTREAM_EXECUTION_PROVIDER"]
    ownership_boundary: Literal["DOWNSTREAM_EXECUTION_SYSTEM_OF_RECORD"]


class SourceProposalImplementationExplanation(BaseModel):
    source: Literal["ADVISORY_WORKFLOW_EVENTS"]
    state_correlation: Literal[
        "NO_EXECUTION_EVENTS_RECORDED",
        "EXECUTION_REQUESTED_EVENT",
        "EXECUTION_REQUESTED_AND_ACCEPTED_EVENTS",
        "EXECUTION_REQUESTED_AND_PARTIAL_EXECUTION_EVENTS",
        "EXECUTION_REQUESTED_AND_EXECUTED_EVENTS",
        "EXECUTION_REQUESTED_AND_REJECTED_EVENTS",
        "EXECUTION_REQUESTED_AND_CANCELLED_EVENTS",
        "EXECUTION_REQUESTED_AND_EXPIRED_EVENTS",
    ]
    execution_ownership: SourceProposalImplementationOwnership


class SourceProposalImplementationStatus(BaseModel):
    proposal: SourceProposalImplementationProposal
    handoff_status: ProposalImplementationHandoffStatus
    execution_request_id: str | None = None
    execution_provider: str | None = None
    related_version_no: int | None = Field(default=None, ge=1)
    handoff_requested_at: datetime | None = None
    executed_at: datetime | None = None
    external_execution_id: str | None = None
    latest_workflow_event: SourceProposalImplementationEvent | None = None
    execution_ownership: SourceProposalImplementationOwnership
    explanation: SourceProposalImplementationExplanation


__all__ = [
    "SourceProposalImplementationEvent",
    "SourceProposalImplementationStatus",
]
