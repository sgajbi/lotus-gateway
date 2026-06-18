from typing import Any

from pydantic import BaseModel, Field

from app.contracts.proposal_common import ProposalEnvelopeBase


class ProposalSummaryData(BaseModel):
    proposal_id: str = Field(description="Proposal identifier.", examples=["pp_1"])
    portfolio_id: str | None = Field(
        default=None,
        description="Portfolio identifier associated with the proposal.",
        examples=["PF_1001"],
    )
    mandate_id: str | None = Field(
        default=None,
        description="Optional mandate identifier carried through from proposal context.",
        examples=["mandate_growth_01"],
    )
    jurisdiction: str | None = Field(
        default=None,
        description="Optional jurisdiction code used for policy context.",
        examples=["SG"],
    )
    created_by: str | None = Field(
        default=None,
        description="Actor identifier that created the proposal aggregate.",
        examples=["advisor_1"],
    )
    created_at: str | None = Field(
        default=None,
        description="UTC ISO8601 timestamp when the proposal aggregate was created.",
        examples=["2026-02-19T12:00:00+00:00"],
    )
    last_event_at: str | None = Field(
        default=None,
        description="UTC ISO8601 timestamp for the latest workflow event on the proposal.",
        examples=["2026-02-19T12:05:00+00:00"],
    )
    current_state: str = Field(
        description="Current workflow state reported by lotus-advise.",
        examples=["DRAFT"],
    )
    current_version_no: int | None = Field(
        default=None,
        description="Current latest immutable proposal version number.",
        examples=[1],
    )
    title: str | None = Field(
        default=None,
        description="Optional advisor-facing proposal title.",
        examples=["Income tilt rebalance"],
    )


class ProposalVersionData(BaseModel):
    proposal_version_id: str | None = Field(
        default=None,
        description="Immutable proposal-version identifier.",
        examples=["ppv_1"],
    )
    proposal_id: str | None = Field(
        default=None,
        description="Parent proposal identifier for this immutable version.",
        examples=["pp_1"],
    )
    version_no: int | None = Field(
        default=None,
        description="Immutable proposal version number.",
        examples=[2],
    )
    created_at: str | None = Field(
        default=None,
        description="UTC ISO8601 timestamp when this immutable version was created.",
        examples=["2026-02-19T12:06:00+00:00"],
    )
    request_hash: str | None = Field(
        default=None,
        description="Canonical request hash for the version payload.",
        examples=["sha256:req-001"],
    )
    artifact_hash: str | None = Field(
        default=None,
        description="Canonical artifact hash for the immutable artifact JSON.",
        examples=["sha256:artifact-001"],
    )
    simulation_hash: str | None = Field(
        default=None,
        description="Canonical simulation-output hash for reproducibility.",
        examples=["sha256:sim-001"],
    )
    status_at_creation: str | None = Field(
        default=None,
        description="Simulation status captured at version creation time.",
        examples=["READY"],
    )
    proposal_result: dict[str, Any] = Field(
        default_factory=dict,
        description="Full proposal simulation output captured for this version.",
        examples=[{"proposal_run_id": "pr_1", "status": "READY"}],
    )
    artifact: dict[str, Any] = Field(
        default_factory=dict,
        description="Immutable proposal artifact payload captured for this version.",
        examples=[{"artifact_id": "artifact_1", "generated_at": "2026-02-19T12:06:01+00:00"}],
    )
    evidence_bundle: dict[str, Any] = Field(
        default_factory=dict,
        description="Immutable evidence bundle persisted for reproducibility and audit.",
        examples=[
            {"hashes": {"request_hash": "sha256:req-001", "artifact_hash": "sha256:artifact-001"}}
        ],
    )
    gate_decision: dict[str, Any] | None = Field(
        default=None,
        description="Optional gate decision snapshot captured at version creation time.",
        examples=[{"gate": "EXECUTION_READY", "recommended_next_step": "EXECUTE"}],
    )


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


class ProposalVersionLineageItemData(BaseModel):
    proposal_version_id: str | None = Field(
        default=None,
        description="Immutable proposal-version identifier.",
        examples=["ppv_1"],
    )
    version_no: int = Field(
        description="Immutable proposal version number.",
        examples=[1],
    )
    created_at: str | None = Field(
        default=None,
        description="UTC ISO8601 timestamp when the version was created.",
        examples=["2026-02-19T12:00:00+00:00"],
    )
    status_at_creation: str | None = Field(
        default=None,
        description="Simulation status captured when the version was created.",
        examples=["READY"],
    )
    request_hash: str | None = Field(
        default=None,
        description="Canonical request hash for the version payload.",
        examples=["sha256:req-001"],
    )
    simulation_hash: str | None = Field(
        default=None,
        description="Canonical simulation-output hash captured for the version.",
        examples=["sha256:sim-001"],
    )
    artifact_hash: str | None = Field(
        default=None,
        description="Canonical artifact hash captured for the version.",
        examples=["sha256:artifact-001"],
    )


class ProposalLineageData(BaseModel):
    proposal: ProposalSummaryData | None = Field(
        default=None,
        description="Proposal summary used as the lineage root context.",
        examples=[
            {
                "proposal_id": "pp_1",
                "current_version_no": 2,
                "current_state": "AWAITING_CLIENT_CONSENT",
            }
        ],
    )
    proposal_id: str | None = Field(
        default=None,
        description=(
            "Fallback proposal identifier retained for compatibility with legacy consumers."
        ),
        examples=["pp_1"],
    )
    versions: list[ProposalVersionLineageItemData] = Field(
        default_factory=list,
        description="Immutable proposal version lineage ordered by version number ascending.",
        examples=[
            [
                {
                    "proposal_version_id": "ppv_1",
                    "version_no": 1,
                    "request_hash": "sha256:req-001",
                    "simulation_hash": "sha256:sim-001",
                    "artifact_hash": "sha256:artifact-001",
                }
            ]
        ],
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
