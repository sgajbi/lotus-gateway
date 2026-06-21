from pydantic import BaseModel, Field

from app.contracts.proposal_common import ProposalEnvelopeBase
from app.contracts.proposal_lifecycle_lineage import ProposalLineageData
from app.contracts.proposal_lifecycle_summary import ProposalSummaryData, ProposalVersionData
from app.contracts.proposal_lifecycle_workflow import (
    ProposalApprovalRecordData,
    ProposalApprovalsData,
    ProposalWorkflowEventData,
    ProposalWorkflowEventsData,
)


class ProposalVersionEnvelopeResponse(ProposalEnvelopeBase):
    data: ProposalVersionData = Field(
        description="Immutable proposal-version payload returned by lotus-advise."
    )


class ProposalWorkflowEventsEnvelopeResponse(ProposalEnvelopeBase):
    data: ProposalWorkflowEventsData = Field(
        description="Workflow timeline payload returned by lotus-advise."
    )


class ProposalApprovalsEnvelopeResponse(ProposalEnvelopeBase):
    data: ProposalApprovalsData = Field(
        description="Approval and consent payload returned by lotus-advise."
    )


class ProposalLineageEnvelopeResponse(ProposalEnvelopeBase):
    data: ProposalLineageData = Field(
        description="Proposal lineage payload returned by lotus-advise."
    )


class ProposalCreateData(BaseModel):
    proposal: ProposalSummaryData = Field(
        description="Created or updated proposal aggregate summary.",
        examples=[{"proposal_id": "pp_1", "current_state": "DRAFT", "current_version_no": 2}],
    )
    version: ProposalVersionData = Field(
        description="Immutable proposal version produced by the create or create-version mutation.",
        examples=[{"proposal_version_id": "ppv_2", "proposal_id": "pp_1", "version_no": 2}],
    )
    latest_workflow_event: ProposalWorkflowEventData = Field(
        description="Latest workflow event emitted by the mutation.",
        examples=[
            {
                "event_id": "pwe_2",
                "event_type": "NEW_VERSION_CREATED",
                "to_state": "DRAFT",
                "actor_id": "advisor_1",
                "occurred_at": "2026-02-19T12:06:00+00:00",
            }
        ],
    )


class ProposalStateTransitionData(BaseModel):
    proposal_id: str = Field(description="Proposal identifier.", examples=["pp_1"])
    current_state: str = Field(
        description="Workflow state after the transition or approval action completed.",
        examples=["RISK_REVIEW"],
    )
    latest_workflow_event: ProposalWorkflowEventData = Field(
        description="Workflow event created by the transition or approval action.",
        examples=[
            {
                "event_id": "pwe_3",
                "event_type": "SUBMITTED_FOR_RISK_REVIEW",
                "from_state": "DRAFT",
                "to_state": "RISK_REVIEW",
                "actor_id": "advisor_1",
                "occurred_at": "2026-02-19T12:07:00+00:00",
            }
        ],
    )
    approval: ProposalApprovalRecordData | None = Field(
        default=None,
        description="Approval record created by the action when applicable.",
        examples=[
            {
                "approval_id": "pap_1",
                "approval_type": "RISK",
                "approved": True,
                "actor_id": "risk_1",
                "occurred_at": "2026-02-19T12:08:00+00:00",
            }
        ],
    )


class ProposalCreateEnvelopeResponse(ProposalEnvelopeBase):
    data: ProposalCreateData = Field(
        description="Create or create-version payload returned by lotus-advise."
    )


class ProposalStateTransitionEnvelopeResponse(ProposalEnvelopeBase):
    data: ProposalStateTransitionData = Field(
        description="Workflow transition or approval payload returned by lotus-advise."
    )
