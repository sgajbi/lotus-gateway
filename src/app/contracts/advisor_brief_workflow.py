from enum import Enum

from pydantic import BaseModel, Field


class AdvisorBriefWorkflowPackRunFinding(BaseModel):
    finding_id: str = Field(
        description="Stable workflow-pack supportability finding identifier.",
        examples=["review_pending"],
    )
    severity: str = Field(
        description="Workflow-pack supportability severity emitted by lotus-ai.",
        examples=["ACTION_REQUIRED"],
    )
    summary: str = Field(
        description="Short workflow-pack supportability summary.",
        examples=["Run is awaiting review."],
    )


class AdvisorBriefWorkflowPackRunReviewActionType(str, Enum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    REVISE = "REVISE"
    SUPERSEDE = "SUPERSEDE"
    ABANDON = "ABANDON"


class AdvisorBriefWorkflowPackRunReviewActionRequest(BaseModel):
    action_type: AdvisorBriefWorkflowPackRunReviewActionType = Field(
        description="Bounded workflow-pack review action to apply to the advisor-brief run.",
        examples=[AdvisorBriefWorkflowPackRunReviewActionType.ACCEPT],
    )
    reviewed_by: str = Field(
        min_length=1,
        description="Stable operator identifier recording the bounded review action.",
        examples=["advisor_1"],
    )
    reason: str = Field(
        min_length=1,
        description="Operator rationale preserved with the bounded review action.",
        examples=["Advisor brief accepted for bounded downstream workflow use."],
    )
    replacement_run_id: str | None = Field(
        default=None,
        description="Replacement workflow-pack run identifier when the action supersedes a run.",
        examples=["packrun_advisor_brief_req-2"],
    )


class AdvisorBriefWorkflowPackRun(BaseModel):
    run_id: str = Field(
        description="Stable lotus-ai workflow-pack run identifier backing this advisor brief.",
        examples=["packrun_advisor_brief_air_123"],
    )
    runtime_state: str = Field(
        description="Current lotus-ai runtime state for the workflow-pack run.",
        examples=["COMPLETED"],
    )
    review_state: str = Field(
        description="Current lotus-ai review state for the workflow-pack run.",
        examples=["AWAITING_REVIEW"],
    )
    allowed_review_actions: list[str] = Field(
        default_factory=list,
        description=(
            "Bounded lotus-ai review actions currently accepted by the workflow-pack ledger."
        ),
        examples=[["ACCEPT", "REJECT", "REVISE"]],
    )
    supportability_status: str = Field(
        description=(
            "Current lotus-ai operator-facing supportability posture for the workflow-pack run."
        ),
        examples=["ACTION_REQUIRED"],
    )
    review_pending: bool = Field(
        description="Whether lotus-ai still reports the workflow-pack run as pending review.",
    )
    superseded: bool = Field(
        description=(
            "Whether lotus-ai marks the workflow-pack run as historical due to replacement lineage."
        ),
    )
    workflow_authority_owner: str = Field(
        description=(
            "Service boundary retaining consequence-bearing workflow authority for the run."
        ),
        examples=["lotus-gateway"],
    )
    current_summary_note: str = Field(
        description="Single lotus-ai operator-facing summary note for the workflow-pack run.",
        examples=["Run completed but still requires bounded human review before downstream use."],
    )
    replacement_run_id: str | None = Field(
        default=None,
        description="Replacement workflow-pack run identifier when the current run is historical.",
    )
    findings: list[AdvisorBriefWorkflowPackRunFinding] = Field(
        default_factory=list,
        description="Workflow-pack supportability findings preserved from lotus-ai.",
    )


class AdvisorBriefWorkflowPackTaskFlowLineage(BaseModel):
    superseded_run_id: str = Field(
        description="Workflow-pack run id superseded by this lineage edge.",
        examples=["packrun_advisor_brief_req-1"],
    )
    replacement_run_id: str = Field(
        description="Replacement workflow-pack run id preserving lineage.",
        examples=["packrun_advisor_brief_req-2"],
    )
    review_action_ref: str = Field(
        description="Review action that created the replacement lineage edge.",
        examples=["REVISE"],
    )
    reason: str = Field(
        description="Operator reason preserved with the replacement lineage edge.",
        examples=["Advisor requested a revised brief."],
    )


class AdvisorBriefWorkflowPackTaskFlowHandoff(BaseModel):
    handoff_id: str = Field(
        description="Stable task-flow handoff identifier emitted by lotus-ai.",
        examples=["taskflow_advisor_brief_req-1_handoff_packrun_advisor_brief_req-1"],
    )
    owner_service: str = Field(
        description="Service boundary that owns the consequence-bearing handoff.",
        examples=["lotus-gateway"],
    )
    status: str = Field(
        description="Current lotus-ai handoff readiness posture.",
        examples=["READY_FOR_HANDOFF"],
    )
    domain_ref: str | None = Field(
        default=None,
        description="Domain-owned workflow reference when the owner service has created one.",
    )


class AdvisorBriefWorkflowPackTaskFlow(BaseModel):
    task_flow_id: str = Field(
        description="Stable lotus-ai task-flow identifier linked to this advisor-brief run.",
        examples=["taskflow_advisor_brief_packrun_advisor_brief_req-1"],
    )
    workflow_pack_id: str = Field(
        description="Workflow-pack id that owns this task-flow record.",
        examples=["advisor_brief.pack"],
    )
    version: str = Field(description="Workflow-pack version for this task flow.", examples=["v1"])
    flow_status: str = Field(
        description="Current lotus-ai task-flow lifecycle state.",
        examples=["WAITING_FOR_REVIEW"],
    )
    current_step_id: str | None = Field(
        default=None,
        description="Current task-flow step id when the task flow is active or waiting.",
        examples=["generate_advisor_brief"],
    )
    run_refs: list[str] = Field(
        default_factory=list,
        description="Workflow-pack run ids linked to this task flow.",
        examples=[["packrun_advisor_brief_req-1"]],
    )
    review_states: dict[str, str] = Field(
        default_factory=dict,
        description="Review-state snapshot by run or review id as emitted by lotus-ai.",
    )
    supportability_status: str = Field(
        description="Current lotus-ai supportability posture for this task flow.",
        examples=["ACTION_REQUIRED"],
    )
    replacement_lineage: list[AdvisorBriefWorkflowPackTaskFlowLineage] = Field(
        default_factory=list,
        description="Replacement lineage preserved from lotus-ai task-flow posture.",
    )
    handoff_refs: list[AdvisorBriefWorkflowPackTaskFlowHandoff] = Field(
        default_factory=list,
        description="Domain-owner handoff posture preserved from lotus-ai task-flow posture.",
    )
    updated_at: str = Field(
        description="UTC timestamp when lotus-ai last updated the task flow.",
        examples=["2026-04-21T03:22:00Z"],
    )
