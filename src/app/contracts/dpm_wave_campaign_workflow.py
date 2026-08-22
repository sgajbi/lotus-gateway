from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.contracts.dpm_wave_campaign_command_types import (
    CampaignApprovalDecisionType,
    CampaignAssignmentActionType,
    CampaignAssignmentEscalationTier,
    CampaignAssignmentSlaPosture,
    CampaignAssignmentTaskTransitionType,
    CampaignAssignmentTaskType,
    CampaignMakerCheckerControlAction,
    CampaignMakerCheckerControlOutcome,
    DpmCampaignSourceRef,
)


class _StrictCampaignCommandBody(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _StrictCampaignCommandRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DpmCampaignApprovalDecisionBody(_StrictCampaignCommandBody):
    decision_type: CampaignApprovalDecisionType = Field(
        description="Bounded campaign approval decision.", examples=["APPROVED"]
    )
    decision_ref: str = Field(
        min_length=1,
        description="Bank workflow or committee reference.",
        examples=["BRC-APPROVAL-001"],
    )
    decided_by: str = Field(
        min_length=1, description="Actor recording the decision.", examples=["cio_ops_committee"]
    )
    decision_reason: str = Field(
        min_length=1,
        description="Human-authored decision rationale.",
        examples=["Approved for review launch."],
    )
    correlation_id: str = Field(
        min_length=1, description="Source correlation id.", examples=["corr-campaign-approval-001"]
    )
    source_refs: list[DpmCampaignSourceRef] = Field(
        default_factory=list, description="Optional source-owned decision evidence."
    )


class DpmCampaignApprovalDecisionRequest(_StrictCampaignCommandRequest):
    body: DpmCampaignApprovalDecisionBody = Field(
        description="Typed approval-decision evidence forwarded to lotus-manage."
    )


class DpmCampaignAssignmentActionBody(_StrictCampaignCommandBody):
    action_type: CampaignAssignmentActionType = Field(
        description="Bounded assignment or escalation action.", examples=["ASSIGNED"]
    )
    action_ref: str = Field(
        min_length=1, description="Bank workflow or queue reference.", examples=["BRC-ASSIGN-001"]
    )
    recorded_by: str = Field(
        min_length=1, description="Actor recording the action.", examples=["ops"]
    )
    action_reason: str = Field(
        min_length=1,
        description="Human-authored action rationale.",
        examples=["Assigned to the responsible PM."],
    )
    assigned_actor_ids: list[str] = Field(
        default_factory=list, description="Actors assigned by this action.", examples=[["pm_sg_1"]]
    )
    escalation_tier: CampaignAssignmentEscalationTier = Field(
        description="Operational escalation tier after the action.", examples=["PM"]
    )
    sla_posture: CampaignAssignmentSlaPosture = Field(
        description="Operational SLA posture after the action.", examples=["ON_TRACK"]
    )
    correlation_id: str = Field(
        min_length=1,
        description="Source correlation id.",
        examples=["corr-campaign-assignment-001"],
    )
    source_refs: list[DpmCampaignSourceRef] = Field(
        default_factory=list, description="Optional source-owned assignment evidence."
    )


class DpmCampaignAssignmentActionRequest(_StrictCampaignCommandRequest):
    body: DpmCampaignAssignmentActionBody = Field(
        description="Typed assignment-action evidence forwarded to lotus-manage."
    )


class DpmCampaignAssignmentTaskBody(_StrictCampaignCommandBody):
    task_ref: str = Field(
        min_length=1,
        description="Bank workflow or queue task reference.",
        examples=["BRC-TASK-001"],
    )
    task_type: CampaignAssignmentTaskType = Field(
        description="Bounded assignment task type.", examples=["ASSIGNMENT"]
    )
    opened_by: str = Field(min_length=1, description="Actor opening the task.", examples=["ops"])
    task_reason: str = Field(
        min_length=1,
        description="Human-authored task rationale.",
        examples=["PM acknowledgement required."],
    )
    assigned_actor_ids: list[str] = Field(
        description="Current task assignees.", examples=[["pm_sg_1"]]
    )
    escalation_tier: CampaignAssignmentEscalationTier = Field(
        description="Current task escalation tier.", examples=["PM"]
    )
    sla_posture: CampaignAssignmentSlaPosture = Field(
        description="Current task SLA posture.", examples=["ON_TRACK"]
    )
    due_at: datetime | None = Field(
        default=None, description="Optional task due timestamp.", examples=["2026-05-11T08:00:00Z"]
    )
    correlation_id: str = Field(
        min_length=1, description="Source correlation id.", examples=["corr-campaign-task-001"]
    )
    source_refs: list[DpmCampaignSourceRef] = Field(
        default_factory=list, description="Optional source-owned task evidence."
    )


class DpmCampaignAssignmentTaskRequest(_StrictCampaignCommandRequest):
    body: DpmCampaignAssignmentTaskBody = Field(
        description="Typed assignment-task evidence forwarded to lotus-manage."
    )


class DpmCampaignAssignmentTaskTransitionBody(_StrictCampaignCommandBody):
    transition_type: CampaignAssignmentTaskTransitionType = Field(
        description="Bounded task transition.", examples=["ACKNOWLEDGED"]
    )
    transition_ref: str = Field(
        min_length=1,
        description="Bank workflow transition reference.",
        examples=["BRC-TASK-001:ack"],
    )
    transitioned_by: str = Field(
        min_length=1, description="Actor recording the transition.", examples=["pm_sg_1"]
    )
    transition_reason: str = Field(
        min_length=1,
        description="Human-authored transition rationale.",
        examples=["PM acknowledged the task."],
    )
    assigned_actor_ids: list[str] | None = Field(
        default=None,
        description="Optional replacement assignees.",
        examples=[["pm_sg_1", "ops_lead"]],
    )
    escalation_tier: CampaignAssignmentEscalationTier | None = Field(
        default=None, description="Optional replacement escalation tier.", examples=["OPS"]
    )
    sla_posture: CampaignAssignmentSlaPosture | None = Field(
        default=None, description="Optional replacement SLA posture.", examples=["ATTENTION"]
    )
    due_at: datetime | None = Field(
        default=None,
        description="Optional replacement due timestamp.",
        examples=["2026-05-12T08:00:00Z"],
    )
    correlation_id: str = Field(
        min_length=1,
        description="Source correlation id.",
        examples=["corr-campaign-task-transition-001"],
    )
    source_refs: list[DpmCampaignSourceRef] = Field(
        default_factory=list, description="Optional source-owned transition evidence."
    )


class DpmCampaignAssignmentTaskTransitionRequest(_StrictCampaignCommandRequest):
    body: DpmCampaignAssignmentTaskTransitionBody = Field(
        description="Typed assignment-task transition evidence forwarded to lotus-manage."
    )


class DpmCampaignMakerCheckerControlBody(_StrictCampaignCommandBody):
    control_action: CampaignMakerCheckerControlAction = Field(
        description="Bounded maker-checker control action.", examples=["REVIEW_COMPLETED"]
    )
    control_ref: str = Field(
        min_length=1, description="Bank workflow or control reference.", examples=["BRC-MC-001"]
    )
    recorded_by: str = Field(
        min_length=1, description="Actor recording the control evidence.", examples=["ops"]
    )
    submitter_actor_id: str | None = Field(
        default=None, description="Maker actor when applicable.", examples=["pm_sg_1"]
    )
    reviewer_actor_id: str | None = Field(
        default=None, description="Checker actor when applicable.", examples=["cio_ops_committee"]
    )
    required_reviewer_role: str | None = Field(
        default=None,
        description="Required checker role when applicable.",
        examples=["CIO_OPERATIONS_REVIEWER"],
    )
    control_outcome: CampaignMakerCheckerControlOutcome = Field(
        description="Bounded control outcome after the action.", examples=["PASSED"]
    )
    control_reason: str = Field(
        min_length=1,
        description="Human-authored control rationale.",
        examples=["Independent review completed."],
    )
    correlation_id: str = Field(
        min_length=1,
        description="Source correlation id.",
        examples=["corr-campaign-maker-checker-001"],
    )
    source_refs: list[DpmCampaignSourceRef] = Field(
        default_factory=list, description="Optional source-owned control evidence."
    )


class DpmCampaignMakerCheckerControlRequest(_StrictCampaignCommandRequest):
    body: DpmCampaignMakerCheckerControlBody = Field(
        description="Typed maker-checker control evidence forwarded to lotus-manage."
    )


class DpmCampaignWorkflowGatewayResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated across Gateway and lotus-manage.",
        examples=["corr-campaign-workflow-001"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway BFF contract version for DPM campaign workflow/audit responses.",
        examples=["v1"],
    )
    source_service: str = Field(
        default="lotus-manage",
        description=(
            "Upstream service that supplied the authoritative campaign workflow/audit payload."
        ),
        examples=["lotus-manage"],
    )
    upstream_status: int = Field(
        description="HTTP status returned by lotus-manage before Gateway envelope composition.",
        examples=[200],
    )
    data: dict[str, object] = Field(
        description=(
            "Authoritative manage campaign workflow/audit payload preserved for Workbench "
            "composition. Gateway preserves count/page metadata, supportability, source refs, "
            "reason codes, operating boundaries, content hashes, no-order/no-OMS/no-external-"
            "workflow posture, approval-decision evidence, assignment-action evidence, "
            "assignment-task evidence, task-transition evidence, and maker-checker evidence "
            "without local workflow or state calculation."
        ),
        examples=[
            {
                "product_name": "BulkReviewCampaignOperatingQueue",
                "product_version": "v1",
                "items": [],
                "count": 0,
                "limit": 50,
                "offset": 0,
                "operating_boundaries": [
                    "NO_ORDER_GENERATION",
                    "NO_OMS_EXECUTION_CLAIM",
                    "NO_EXTERNAL_WORKFLOW_ORCHESTRATION",
                ],
            }
        ],
    )
