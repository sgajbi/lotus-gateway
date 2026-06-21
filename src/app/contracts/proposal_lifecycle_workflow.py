from typing import Any

from pydantic import BaseModel, Field


class ProposalWorkflowEventData(BaseModel):
    event_id: str = Field(description="Workflow event identifier.", examples=["pwe_1"])
    proposal_id: str | None = Field(
        default=None,
        description="Proposal identifier linked to this workflow event.",
        examples=["pp_1"],
    )
    event_type: str = Field(
        description="Workflow event type emitted by lotus-advise.",
        examples=["SUBMITTED_FOR_RISK_REVIEW"],
    )
    from_state: str | None = Field(
        default=None,
        description="Previous workflow state before the event was applied.",
        examples=["DRAFT"],
    )
    to_state: str = Field(
        description="Workflow state after the event was applied.",
        examples=["RISK_REVIEW"],
    )
    actor_id: str = Field(
        description="Actor identifier that triggered the workflow event.",
        examples=["advisor_1"],
    )
    occurred_at: str = Field(
        description="UTC ISO8601 timestamp when the workflow event occurred.",
        examples=["2026-02-19T12:05:00+00:00"],
    )
    reason: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured reason payload captured for audit and investigations.",
        examples=[{"summary": "Submitted after client call", "ticket_id": "REQ-102"}],
    )
    related_version_no: int | None = Field(
        default=None,
        description="Optional proposal version number referenced by this event.",
        examples=[2],
    )


class ProposalWorkflowEventsData(BaseModel):
    proposal_id: str = Field(description="Proposal identifier.", examples=["pp_1"])
    current_state: str = Field(
        description="Current workflow state when the timeline was retrieved.",
        examples=["RISK_REVIEW"],
    )
    events: list[ProposalWorkflowEventData] = Field(
        default_factory=list,
        description="Append-only workflow events ordered by occurrence.",
        examples=[
            [
                {
                    "event_id": "pwe_1",
                    "event_type": "CREATED",
                    "to_state": "DRAFT",
                    "actor_id": "advisor_1",
                    "occurred_at": "2026-02-19T12:00:00+00:00",
                }
            ]
        ],
    )


class ProposalApprovalRecordData(BaseModel):
    approval_id: str = Field(description="Approval record identifier.", examples=["pap_1"])
    proposal_id: str | None = Field(
        default=None,
        description="Proposal identifier linked to this approval record.",
        examples=["pp_1"],
    )
    approval_type: str = Field(
        description="Approval or consent domain recorded for this action.",
        examples=["RISK"],
    )
    approved: bool = Field(description="Approval decision flag.", examples=[True])
    actor_id: str = Field(
        description="Actor identifier that recorded the approval decision.",
        examples=["risk_1"],
    )
    occurred_at: str = Field(
        description="UTC ISO8601 timestamp when the approval record was captured.",
        examples=["2026-02-19T12:07:00+00:00"],
    )
    details: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured approval metadata such as channel, comment, or document reference.",
        examples=[{"channel": "IN_PERSON", "comment": "Within mandate"}],
    )
    related_version_no: int | None = Field(
        default=None,
        description="Optional proposal version number referenced by the approval record.",
        examples=[2],
    )


class ProposalApprovalsData(BaseModel):
    proposal_id: str = Field(description="Proposal identifier.", examples=["pp_1"])
    current_state: str | None = Field(
        default=None,
        description=(
            "Current workflow state when the approvals view was retrieved, when supplied upstream."
        ),
        examples=["AWAITING_CLIENT_CONSENT"],
    )
    approvals: list[ProposalApprovalRecordData] = Field(
        default_factory=list,
        description="Structured approval and consent records ordered by occurrence.",
        examples=[
            [
                {
                    "approval_id": "pap_1",
                    "approval_type": "RISK",
                    "approved": True,
                    "actor_id": "risk_1",
                    "occurred_at": "2026-02-19T12:07:00+00:00",
                }
            ]
        ],
    )
