from typing import Any, Literal

from pydantic import BaseModel, Field

from app.contracts import proposal_memos as _proposal_memos
from app.contracts.proposal_common import ProposalEnvelopeBase

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


class ProposalSimulateRequest(BaseModel):
    body: dict[str, Any] = Field(
        description="Opaque simulation request payload forwarded unchanged to lotus-advise.",
        examples=[
            {
                "portfolio_id": "PF_1001",
                "objective": "income",
                "constraints": {"max_cash_weight_pct": 5.0},
            }
        ],
    )


class ProposalSimulateResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated through the gateway request.",
        examples=["corr-proposals-1"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway contract version for the proposal simulation response.",
        examples=["v1"],
    )
    data: "ProposalSimulationData" = Field(
        description="Proposal simulation payload returned by lotus-advise.",
    )


class ProposalSimulationData(BaseModel):
    proposal_run_id: str = Field(
        description="Proposal simulation run identifier.",
        examples=["pr_1"],
    )
    correlation_id: str = Field(
        description="Correlation identifier emitted by the simulation engine.",
        examples=["corr_engine_1"],
    )
    status: str = Field(
        description="Top-level domain outcome for the simulated proposal.",
        examples=["READY"],
    )
    before: dict[str, Any] = Field(
        default_factory=dict,
        description="Before-state valuation snapshot used as the simulation baseline.",
        examples=[{"portfolio_value": {"amount": "100000.00", "currency": "USD"}}],
    )
    intents: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Deterministically ordered proposal intents applied during simulation.",
        examples=[
            [
                {
                    "intent_type": "CASH_FLOW",
                    "intent_id": "oi_cf_1",
                    "currency": "USD",
                    "amount": "2000.00",
                },
                {
                    "intent_type": "SECURITY_TRADE",
                    "intent_id": "oi_1",
                    "side": "BUY",
                    "instrument_id": "EQ_GROWTH",
                    "quantity": "40",
                },
            ]
        ],
    )
    after_simulated: dict[str, Any] = Field(
        default_factory=dict,
        description="After-state valuation snapshot after all proposal intents are applied.",
        examples=[{"portfolio_value": {"amount": "102000.00", "currency": "USD"}}],
    )
    reconciliation: dict[str, Any] | None = Field(
        default=None,
        description="Optional reconciliation output comparing before and after states.",
        examples=[{"cash_balance_delta": {"amount": "2000.00", "currency": "USD"}}],
    )
    rule_results: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Rule-engine evaluations produced during simulation.",
        examples=[[{"rule_id": "CASH_BAND", "severity": "SOFT", "status": "PASS"}]],
    )
    explanation: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional explanatory payload emitted by the simulation engine.",
        examples=[{"summary": "Proposal remains within mandate concentration limits."}],
    )
    diagnostics: dict[str, Any] = Field(
        default_factory=dict,
        description="Diagnostics and warning payload for the simulation run.",
        examples=[
            {
                "warnings": [],
                "data_quality": {"price_missing": [], "fx_missing": []},
            }
        ],
    )
    drift_analysis: dict[str, Any] | None = Field(
        default=None,
        description="Optional reference-model drift analytics when supplied upstream.",
        examples=[{"tracking_error_pct": 1.2}],
    )
    suitability: dict[str, Any] | None = Field(
        default=None,
        description="Optional advisory suitability scanner output.",
        examples=[{"status": "PASS", "issues": []}],
    )
    gate_decision: dict[str, Any] | None = Field(
        default=None,
        description="Deterministic workflow gate decision for advisory routing.",
        examples=[
            {"gate": "CLIENT_CONSENT_REQUIRED", "recommended_next_step": "REQUEST_CLIENT_CONSENT"}
        ],
    )
    lineage: dict[str, Any] = Field(
        default_factory=dict,
        description="Lineage identifiers and request hash for the simulation run.",
        examples=[{"request_hash": "sha256:req-1", "idempotency_key": "idem-simulate-1"}],
    )


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


class ProposalListEnvelopeResponse(ProposalEnvelopeBase):
    data: ProposalListData = Field(description="Proposal list payload returned by lotus-advise.")


class ProposalDetailEnvelopeResponse(ProposalEnvelopeBase):
    data: ProposalDetailData = Field(
        description="Current proposal detail payload returned by lotus-advise."
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


class ProposalEnvelopeResponse(ProposalEnvelopeBase):
    data: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Opaque lotus-advise proposal payload returned unchanged by gateway for write actions."
        ),
        examples=[{"proposal": {"proposal_id": "pp_1", "current_state": "DRAFT"}}],
    )
