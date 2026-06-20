from typing import Any, Literal

from pydantic import BaseModel, Field

from app.contracts import proposal_generation as _proposal_generation
from app.contracts import proposal_lifecycle as _proposal_lifecycle
from app.contracts import proposal_memos as _proposal_memos
from app.contracts.proposal_common import ProposalEnvelopeBase

ProposalApprovalsData = _proposal_lifecycle.ProposalApprovalsData
ProposalApprovalsEnvelopeResponse = _proposal_lifecycle.ProposalApprovalsEnvelopeResponse
ProposalApprovalRecordData = _proposal_lifecycle.ProposalApprovalRecordData
ProposalCreateData = _proposal_lifecycle.ProposalCreateData
ProposalCreateEnvelopeResponse = _proposal_lifecycle.ProposalCreateEnvelopeResponse
ProposalLineageData = _proposal_lifecycle.ProposalLineageData
ProposalLineageEnvelopeResponse = _proposal_lifecycle.ProposalLineageEnvelopeResponse
ProposalMemoAiCommentaryEnvelopeResponse = _proposal_memos.ProposalMemoAiCommentaryEnvelopeResponse
ProposalMemoAiCommentaryRequest = _proposal_memos.ProposalMemoAiCommentaryRequest
ProposalMemoCreateRequest = _proposal_memos.ProposalMemoCreateRequest
ProposalMemoEnvelopeResponse = _proposal_memos.ProposalMemoEnvelopeResponse
ProposalMemoLineageEnvelopeResponse = _proposal_memos.ProposalMemoLineageEnvelopeResponse
ProposalMemoProjectionEnvelopeResponse = _proposal_memos.ProposalMemoProjectionEnvelopeResponse
ProposalMemoReplayEvidenceEnvelopeResponse = (
    _proposal_memos.ProposalMemoReplayEvidenceEnvelopeResponse
)
ProposalMemoReportPackageEnvelopeResponse = (
    _proposal_memos.ProposalMemoReportPackageEnvelopeResponse
)
ProposalMemoReportPackageRequest = _proposal_memos.ProposalMemoReportPackageRequest
ProposalMemoReviewEnvelopeResponse = _proposal_memos.ProposalMemoReviewEnvelopeResponse
ProposalMemoReviewRequest = _proposal_memos.ProposalMemoReviewRequest
ProposalSimulateRequest = _proposal_generation.ProposalSimulateRequest
ProposalSimulateResponse = _proposal_generation.ProposalSimulateResponse
ProposalSimulationData = _proposal_generation.ProposalSimulationData
ProposalStateTransitionData = _proposal_lifecycle.ProposalStateTransitionData
ProposalStateTransitionEnvelopeResponse = (
    _proposal_lifecycle.ProposalStateTransitionEnvelopeResponse
)
ProposalSummaryData = _proposal_lifecycle.ProposalSummaryData
ProposalVersionData = _proposal_lifecycle.ProposalVersionData
ProposalVersionEnvelopeResponse = _proposal_lifecycle.ProposalVersionEnvelopeResponse
ProposalVersionLineageItemData = _proposal_lifecycle.ProposalVersionLineageItemData
ProposalWorkflowEventData = _proposal_lifecycle.ProposalWorkflowEventData
ProposalWorkflowEventsData = _proposal_lifecycle.ProposalWorkflowEventsData
ProposalWorkflowEventsEnvelopeResponse = _proposal_lifecycle.ProposalWorkflowEventsEnvelopeResponse


class ProposalCreateRequest(BaseModel):
    body: dict[str, Any] = Field(
        description="Opaque proposal-create request payload forwarded unchanged to lotus-advise.",
        examples=[
            {
                "portfolio_id": "PF_1001",
                "proposal_name": "Income tilt rebalance",
                "created_by": "advisor_1",
            }
        ],
    )


class ProposalVersionCreateRequest(BaseModel):
    body: dict[str, Any] = Field(
        description=(
            "Opaque proposal-version request payload forwarded unchanged to lotus-advise."
        ),
        examples=[
            {
                "change_summary": "Reduce concentrated equity exposure.",
                "proposed_trades": [{"instrument_id": "EQ_1", "action": "SELL"}],
            }
        ],
    )


class ProposalBodyRequest(BaseModel):
    body: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Opaque advisory proposal payload forwarded unchanged to lotus-advise for "
            "source-owned support, execution, memo, narrative, async, or artifact workflows."
        ),
        examples=[
            {
                "actor_id": "advisor_1",
                "reason": {"summary": "Advisor workflow action requested from Workbench."},
            }
        ],
    )


class ProposalSubmitRequest(BaseModel):
    actor_id: str = Field(
        description="Actor identifier requesting the submit transition.",
        examples=["advisor_1"],
    )
    expected_state: str = Field(
        default="DRAFT",
        description="Expected current state for optimistic concurrency check.",
        examples=["DRAFT"],
    )
    review_type: Literal["RISK", "COMPLIANCE"] = Field(
        default="RISK",
        description="First review stage that should receive the submitted proposal.",
        examples=["RISK"],
    )
    related_version_no: int | None = Field(
        default=None,
        description="Optional related version number for audit linkage.",
        examples=[2],
    )
    reason: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured reason payload captured in workflow event.",
        examples=[{"summary": "Client requested income tilt", "ticket_id": "REQ-102"}],
    )


class ProposalApprovalActionRequest(BaseModel):
    actor_id: str = Field(
        description="Actor identifier recording the approval or consent action.",
        examples=["risk_1"],
    )
    expected_state: str = Field(
        description="Expected current workflow state before the action is applied.",
        examples=["RISK_REVIEW"],
    )
    related_version_no: int | None = Field(
        default=None,
        description="Optional related version number for audit linkage.",
        examples=[2],
    )
    details: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured approval metadata/details.",
        examples=[{"decision": "APPROVED", "comment": "Within mandate"}],
    )


class ProposalNarrativeReviewRequest(BaseModel):
    action: Literal["APPROVE", "REJECT", "REQUEST_REGENERATION"] = Field(
        description=(
            "Bounded review action for the persisted proposal narrative version. Gateway forwards "
            "the action to lotus-advise and does not regenerate or edit narrative locally."
        ),
        examples=["APPROVE"],
    )
    reviewed_by: str = Field(
        description="Actor identifier recording the narrative review decision.",
        examples=["compliance_reviewer_001"],
    )
    reason: str = Field(
        description="Human-readable review rationale captured by lotus-advise for audit.",
        examples=["Narrative is evidence-grounded and suitable for advisor use."],
    )
    client_ready_release_requested: bool = Field(
        default=False,
        description=(
            "Whether the reviewer requests client-ready release posture. RFC-0023 keeps "
            "client-ready publication gated until later slices prove the full control path."
        ),
        examples=[False],
    )
    replacement_narrative_id: str | None = Field(
        default=None,
        description="Optional replacement narrative identifier when a regeneration review applies.",
        examples=["pn_replacement_001"],
    )


class ProposalReportRequest(BaseModel):
    report_type: str = Field(
        description="Lotus-branded advisory report payload requested from lotus-report.",
        examples=["PORTFOLIO_REVIEW"],
    )
    requested_by: str = Field(
        description="Actor identifier requesting advisory report generation.",
        examples=["advisor_123"],
    )
    related_version_no: int | None = Field(
        default=None,
        description=(
            "Optional immutable proposal version number to anchor the report payload. "
            "Defaults to the current proposal version when omitted upstream."
        ),
        examples=[2],
    )
    include_execution_summary: bool = Field(
        default=True,
        description=(
            "Whether advisory execution-state summary should be included in report context."
        ),
        examples=[True],
    )
    include_reviewed_narrative: bool = Field(
        default=False,
        description=(
            "Whether the request must include the approved, source-backed proposal narrative "
            "package. lotus-advise blocks the request unless review posture and source hash "
            "continuity are sufficient."
        ),
        examples=[True],
    )


class ProposalListData(BaseModel):
    items: list[ProposalSummaryData] = Field(
        default_factory=list,
        description="Paginated proposal summary rows returned for the requested filter set.",
        examples=[[{"proposal_id": "pp_1", "portfolio_id": "PF_1001", "current_state": "DRAFT"}]],
    )
    next_cursor: str | None = Field(
        default=None,
        description="Opaque cursor used to request the next page when more rows are available.",
        examples=["pp_00042"],
    )


class ProposalDetailData(BaseModel):
    proposal: ProposalSummaryData = Field(
        description="Current proposal aggregate summary.",
        examples=[{"proposal_id": "pp_1", "current_state": "RISK_REVIEW", "current_version_no": 2}],
    )
    current_version: ProposalVersionData = Field(
        description="Current latest immutable proposal version.",
        examples=[{"proposal_version_id": "ppv_2", "version_no": 2, "status_at_creation": "READY"}],
    )
    last_gate_decision: dict[str, Any] | None = Field(
        default=None,
        description="Latest gate decision associated with the current version when available.",
        examples=[
            {"gate": "CLIENT_CONSENT_REQUIRED", "recommended_next_step": "REQUEST_CLIENT_CONSENT"}
        ],
    )


class ProposalListEnvelopeResponse(ProposalEnvelopeBase):
    data: ProposalListData = Field(description="Proposal list payload returned by lotus-advise.")


class ProposalDetailEnvelopeResponse(ProposalEnvelopeBase):
    data: ProposalDetailData = Field(
        description="Current proposal detail payload returned by lotus-advise."
    )


class ProposalNarrativeReviewEnvelopeResponse(ProposalEnvelopeBase):
    data: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Narrative review payload returned by lotus-advise, including review state, policy "
            "version, guardrail, disclosure, source-hash, and workflow-event evidence."
        ),
        examples=[
            {
                "narrative_review": {
                    "review_id": "pwe_narrative_review_001",
                    "review_state": "APPROVED_FOR_ADVISOR_USE",
                    "source_narrative_hash": "sha256:9c8a2f1d",
                }
            }
        ],
    )


class ProposalReportRequestEnvelopeResponse(ProposalEnvelopeBase):
    data: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Report-request payload returned by lotus-advise. When requested and approved, the "
            "payload includes a compact reviewed advisory narrative package for downstream report, "
            "render, and archive realization."
        ),
        examples=[
            {
                "report_request_id": "prr_001",
                "status": "READY",
                "explanation": {
                    "include_reviewed_narrative": True,
                    "proposal_narrative_package": {"package_status": "INCLUDED_REVIEWED_NARRATIVE"},
                },
            }
        ],
    )


class ProposalDeliverySummaryEnvelopeResponse(ProposalEnvelopeBase):
    data: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Latest proposal delivery posture from lotus-advise, including execution and reporting "
            "summaries, reviewed narrative package posture where present, and source ownership "
            "explanation."
        ),
    )


class ProposalDeliveryEventsEnvelopeResponse(ProposalEnvelopeBase):
    data: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Delivery-only proposal workflow history from lotus-advise, preserving append-only "
            "report, archive, and execution posture without gateway recomputation."
        ),
    )


class ProposalEnvelopeResponse(ProposalEnvelopeBase):
    data: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Opaque lotus-advise proposal payload returned unchanged by gateway for write actions."
        ),
        examples=[{"proposal": {"proposal_id": "pp_1", "current_state": "DRAFT"}}],
    )
