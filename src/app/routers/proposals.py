from fastapi import APIRouter, Header, Path, Query

from app.contracts.proposals import (
    ProposalApprovalActionRequest,
    ProposalApprovalsEnvelopeResponse,
    ProposalBodyRequest,
    ProposalCreateEnvelopeResponse,
    ProposalCreateRequest,
    ProposalDeliveryEventsEnvelopeResponse,
    ProposalDeliverySummaryEnvelopeResponse,
    ProposalDetailEnvelopeResponse,
    ProposalEnvelopeResponse,
    ProposalLineageEnvelopeResponse,
    ProposalListEnvelopeResponse,
    ProposalMemoAiCommentaryEnvelopeResponse,
    ProposalMemoAiCommentaryRequest,
    ProposalMemoCreateRequest,
    ProposalMemoEnvelopeResponse,
    ProposalMemoLineageEnvelopeResponse,
    ProposalMemoProjectionEnvelopeResponse,
    ProposalMemoReplayEvidenceEnvelopeResponse,
    ProposalMemoReportPackageEnvelopeResponse,
    ProposalMemoReportPackageRequest,
    ProposalMemoReviewEnvelopeResponse,
    ProposalMemoReviewRequest,
    ProposalNarrativeReviewEnvelopeResponse,
    ProposalNarrativeReviewRequest,
    ProposalReportRequest,
    ProposalReportRequestEnvelopeResponse,
    ProposalSimulateRequest,
    ProposalSimulateResponse,
    ProposalStateTransitionEnvelopeResponse,
    ProposalSubmitRequest,
    ProposalVersionCreateRequest,
    ProposalVersionEnvelopeResponse,
    ProposalWorkflowEventsEnvelopeResponse,
)
from app.middleware.correlation import correlation_id_var
from app.services.advisory_service_provider import proposal_service

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


@router.post(
    "/simulate",
    response_model=ProposalSimulateResponse,
    summary="Simulate Proposal",
    description=(
        "Runs proposal simulation through lotus-advise using a caller-supplied idempotency key "
        "to protect against duplicate submission."
    ),
)
async def simulate_proposal(
    request: ProposalSimulateRequest,
    idempotency_key: str = Header(
        alias="Idempotency-Key",
        description="Caller-supplied idempotency key for proposal simulation requests.",
        examples=["idem-simulate-1"],
    ),
) -> ProposalSimulateResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.simulate_proposal(
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )


@router.post(
    "/artifact",
    response_model=ProposalEnvelopeResponse,
    summary="Create Proposal Artifact",
    description=(
        "Creates a deterministic advisory proposal artifact through lotus-advise. Gateway "
        "preserves decision summary, alternatives, evidence bundle, and hashes without "
        "constructing artifact content locally."
    ),
)
async def create_proposal_artifact(
    request: ProposalBodyRequest,
    idempotency_key: str = Header(
        alias="Idempotency-Key",
        description="Caller-supplied idempotency key for proposal artifact generation.",
        examples=["idem-artifact-1"],
    ),
) -> ProposalEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.create_proposal_artifact(
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )


@router.post(
    "",
    response_model=ProposalCreateEnvelopeResponse,
    summary="Create Proposal",
    description=(
        "Creates a new advisory proposal draft in lotus-advise using a caller-supplied "
        "idempotency key."
    ),
)
async def create_proposal(
    request: ProposalCreateRequest,
    idempotency_key: str = Header(
        alias="Idempotency-Key",
        description="Caller-supplied idempotency key for proposal creation requests.",
        examples=["idem-create-1"],
    ),
) -> ProposalCreateEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.create_proposal(
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )


@router.get(
    "",
    response_model=ProposalListEnvelopeResponse,
    summary="List Proposals",
    description=(
        "Lists advisory proposals from lotus-advise using optional portfolio, workflow-state, "
        "creator, and creation-window filters."
    ),
)
async def list_proposals(
    portfolio_id: str | None = Query(
        default=None,
        description="Optional portfolio identifier used to scope the proposal list.",
        examples=["PF_1001"],
    ),
    state: str | None = Query(
        default=None,
        description="Optional workflow state filter such as DRAFT or RISK_REVIEW.",
        examples=["DRAFT"],
    ),
    created_by: str | None = Query(
        default=None,
        description="Optional actor identifier used to filter proposals by creator.",
        examples=["advisor_1"],
    ),
    created_from: str | None = Query(
        default=None,
        description="Inclusive creation-date lower bound in YYYY-MM-DD format.",
        examples=["2026-01-01"],
    ),
    created_to: str | None = Query(
        default=None,
        description="Inclusive creation-date upper bound in YYYY-MM-DD format.",
        examples=["2026-03-31"],
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of proposals returned in one page.",
        examples=[20],
    ),
    cursor: str | None = Query(
        default=None,
        description="Opaque pagination cursor returned by the previous proposal list response.",
        examples=["pp_00042"],
    ),
) -> ProposalListEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    filters = {
        "portfolio_id": portfolio_id,
        "state": state,
        "created_by": created_by,
        "created_from": created_from,
        "created_to": created_to,
        "limit": limit,
        "cursor": cursor,
    }
    return await service.list_proposals(filters=filters, correlation_id=correlation_id)


@router.post(
    "/async",
    response_model=ProposalEnvelopeResponse,
    summary="Create Proposal Asynchronously",
    description=(
        "Starts an asynchronous proposal create operation in lotus-advise. Gateway returns the "
        "source-owned operation reference and does not manage advisory operation state locally."
    ),
)
async def create_proposal_async(
    request: ProposalBodyRequest,
    idempotency_key: str = Header(
        alias="Idempotency-Key",
        description="Caller-supplied idempotency key for async proposal creation.",
        examples=["idem-proposal-async-1"],
    ),
) -> ProposalEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.create_proposal_async(
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )


@router.get(
    "/operations/{operation_id}",
    response_model=ProposalEnvelopeResponse,
    summary="Get Proposal Operation",
    description="Returns async proposal operation state from lotus-advise.",
)
async def get_proposal_operation(
    operation_id: str = Path(
        ...,
        description="lotus-advise async proposal operation identifier.",
        examples=["apo_001"],
    ),
) -> ProposalEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_proposal_operation(
        operation_id=operation_id,
        correlation_id=correlation_id,
    )


@router.get(
    "/operations/by-correlation/{operation_correlation_id}",
    response_model=ProposalEnvelopeResponse,
    summary="Get Proposal Operation by Correlation",
    description="Looks up a source-owned async proposal operation by its operation correlation id.",
)
async def get_proposal_operation_by_correlation(
    operation_correlation_id: str = Path(
        ...,
        description="Operation correlation identifier recorded by lotus-advise.",
        examples=["corr-operation-001"],
    ),
) -> ProposalEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_proposal_operation_by_correlation(
        operation_correlation_id=operation_correlation_id,
        correlation_id=correlation_id,
    )


@router.get(
    "/operations/{operation_id}/replay-evidence",
    response_model=ProposalEnvelopeResponse,
    summary="Get Proposal Operation Replay Evidence",
    description=(
        "Returns source-owned replay evidence for an async proposal operation from lotus-advise."
    ),
)
async def get_proposal_operation_replay_evidence(
    operation_id: str = Path(
        ...,
        description="lotus-advise async proposal operation identifier.",
        examples=["apo_001"],
    ),
) -> ProposalEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_proposal_operation_replay_evidence(
        operation_id=operation_id,
        correlation_id=correlation_id,
    )


@router.get(
    "/idempotency/{idempotency_key}",
    response_model=ProposalEnvelopeResponse,
    summary="Get Proposal Idempotency Record",
    description=(
        "Returns the source-owned idempotency record from lotus-advise for support and replay "
        "diagnosis. Gateway does not interpret or mutate idempotency state."
    ),
)
async def get_proposal_idempotency_record(
    idempotency_key: str = Path(
        ...,
        description="Idempotency key recorded by lotus-advise.",
        examples=["idem-create-1"],
    ),
) -> ProposalEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_proposal_idempotency_record(
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )


@router.get(
    "/{proposal_id}",
    response_model=ProposalDetailEnvelopeResponse,
    summary="Get Proposal",
    description="Returns the latest proposal envelope for a specific advisory proposal id.",
)
async def get_proposal(
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    include_evidence: bool = Query(
        default=False,
        description="Whether to request proposal evidence and support metadata when available.",
        examples=[True],
    ),
) -> ProposalDetailEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_proposal(
        proposal_id=proposal_id,
        include_evidence=include_evidence,
        correlation_id=correlation_id,
    )


@router.get(
    "/{proposal_id}/versions/{version_no}",
    response_model=ProposalVersionEnvelopeResponse,
    summary="Get Proposal Version",
    description="Returns one persisted version of an advisory proposal.",
)
async def get_proposal_version(
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    version_no: int = Path(
        ...,
        description="Persisted proposal version number to retrieve.",
        examples=[2],
    ),
    include_evidence: bool = Query(
        default=False,
        description=(
            "Whether to request version-level evidence and support metadata when available."
        ),
        examples=[True],
    ),
) -> ProposalVersionEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_proposal_version(
        proposal_id=proposal_id,
        version_no=version_no,
        include_evidence=include_evidence,
        correlation_id=correlation_id,
    )


@router.get(
    "/{proposal_id}/versions/{version_no}/replay-evidence",
    response_model=ProposalEnvelopeResponse,
    summary="Get Proposal Version Replay Evidence",
    description=(
        "Returns source-owned replay evidence for one immutable proposal version from lotus-advise."
    ),
)
async def get_proposal_version_replay_evidence(
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    version_no: int = Path(
        ...,
        description="Persisted proposal version number to retrieve replay evidence for.",
        examples=[2],
    ),
) -> ProposalEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_proposal_version_replay_evidence(
        proposal_id=proposal_id,
        version_no=version_no,
        correlation_id=correlation_id,
    )


@router.post(
    "/{proposal_id}/versions",
    response_model=ProposalCreateEnvelopeResponse,
    summary="Create Proposal Version",
    description="Creates the next persisted version for an existing advisory proposal.",
)
async def create_proposal_version(
    request: ProposalVersionCreateRequest,
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    idempotency_key: str = Header(
        alias="Idempotency-Key",
        description="Caller-supplied idempotency key for proposal-version creation requests.",
        examples=["idem-version-2"],
    ),
) -> ProposalCreateEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.create_proposal_version(
        proposal_id=proposal_id,
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )


@router.post(
    "/{proposal_id}/versions/async",
    response_model=ProposalEnvelopeResponse,
    summary="Create Proposal Version Asynchronously",
    description=(
        "Starts an asynchronous version-create operation in lotus-advise for an existing "
        "proposal. Gateway returns source-owned operation posture only."
    ),
)
async def create_proposal_version_async(
    request: ProposalBodyRequest,
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    idempotency_key: str = Header(
        alias="Idempotency-Key",
        description="Caller-supplied idempotency key for async proposal-version creation.",
        examples=["idem-version-async-1"],
    ),
) -> ProposalEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.create_proposal_version_async(
        proposal_id=proposal_id,
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )


@router.post(
    "/{proposal_id}/submit",
    response_model=ProposalStateTransitionEnvelopeResponse,
    summary="Submit Proposal",
    description="Submits a proposal into the next workflow review state.",
)
async def submit_proposal(
    request: ProposalSubmitRequest,
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    idempotency_key: str = Header(
        alias="Idempotency-Key",
        description="Caller-supplied idempotency key for proposal workflow submission requests.",
        examples=["idem-submit-1"],
    ),
) -> ProposalStateTransitionEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.submit_proposal(
        proposal_id=proposal_id,
        actor_id=request.actor_id,
        expected_state=request.expected_state,
        review_type=request.review_type,
        reason=request.reason,
        related_version_no=request.related_version_no,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )


@router.post(
    "/{proposal_id}/approve-risk",
    response_model=ProposalStateTransitionEnvelopeResponse,
    summary="Approve Proposal Risk Review",
    description="Records the risk approval decision for a proposal in risk review.",
)
async def approve_risk(
    request: ProposalApprovalActionRequest,
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    idempotency_key: str = Header(
        alias="Idempotency-Key",
        description="Caller-supplied idempotency key for proposal risk-approval requests.",
        examples=["idem-approve-risk-1"],
    ),
) -> ProposalStateTransitionEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.approve_risk(
        proposal_id=proposal_id,
        actor_id=request.actor_id,
        expected_state=request.expected_state,
        details=request.details,
        related_version_no=request.related_version_no,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )


@router.post(
    "/{proposal_id}/approve-compliance",
    response_model=ProposalStateTransitionEnvelopeResponse,
    summary="Approve Proposal Compliance Review",
    description="Records the compliance approval decision for a proposal in compliance review.",
)
async def approve_compliance(
    request: ProposalApprovalActionRequest,
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    idempotency_key: str = Header(
        alias="Idempotency-Key",
        description="Caller-supplied idempotency key for proposal compliance-approval requests.",
        examples=["idem-approve-compliance-1"],
    ),
) -> ProposalStateTransitionEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.approve_compliance(
        proposal_id=proposal_id,
        actor_id=request.actor_id,
        expected_state=request.expected_state,
        details=request.details,
        related_version_no=request.related_version_no,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )


@router.post(
    "/{proposal_id}/record-client-consent",
    response_model=ProposalStateTransitionEnvelopeResponse,
    summary="Record Proposal Client Consent",
    description="Records client consent for a proposal that has completed internal approvals.",
)
async def record_client_consent(
    request: ProposalApprovalActionRequest,
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    idempotency_key: str = Header(
        alias="Idempotency-Key",
        description="Caller-supplied idempotency key for client-consent recording requests.",
        examples=["idem-client-consent-1"],
    ),
) -> ProposalStateTransitionEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.record_client_consent(
        proposal_id=proposal_id,
        actor_id=request.actor_id,
        expected_state=request.expected_state,
        details=request.details,
        related_version_no=request.related_version_no,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )


@router.get(
    "/{proposal_id}/workflow-events",
    response_model=ProposalWorkflowEventsEnvelopeResponse,
    summary="Get Proposal Workflow Events",
    description="Returns the workflow event timeline for a specific advisory proposal.",
)
async def get_workflow_events(
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
) -> ProposalWorkflowEventsEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_workflow_events(
        proposal_id=proposal_id,
        correlation_id=correlation_id,
    )


@router.get(
    "/{proposal_id}/approvals",
    response_model=ProposalApprovalsEnvelopeResponse,
    summary="Get Proposal Approvals",
    description="Returns approval records already captured for a specific advisory proposal.",
)
async def get_approvals(
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
) -> ProposalApprovalsEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_approvals(
        proposal_id=proposal_id,
        correlation_id=correlation_id,
    )


@router.get(
    "/{proposal_id}/lineage",
    response_model=ProposalLineageEnvelopeResponse,
    summary="Get Proposal Lineage",
    description="Returns immutable version lineage metadata and hashes for a specific proposal.",
)
async def get_proposal_lineage(
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
) -> ProposalLineageEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_proposal_lineage(
        proposal_id=proposal_id,
        correlation_id=correlation_id,
    )


@router.post(
    "/{proposal_id}/versions/{version_no}/narrative/regenerate",
    response_model=ProposalEnvelopeResponse,
    summary="Regenerate Proposal Narrative Candidate",
    description=(
        "Requests a non-persistent advisor-review narrative candidate from lotus-advise for a "
        "persisted proposal version. Gateway does not generate or edit narrative text locally."
    ),
)
async def regenerate_proposal_narrative(
    request: ProposalBodyRequest,
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    version_no: int = Path(
        ...,
        ge=1,
        description="Immutable proposal version number containing narrative evidence.",
        examples=[2],
    ),
) -> ProposalEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.regenerate_proposal_narrative(
        proposal_id=proposal_id,
        version_no=version_no,
        body=request.body,
        correlation_id=correlation_id,
    )


@router.get(
    "/{proposal_id}/versions/{version_no}/narrative",
    response_model=ProposalEnvelopeResponse,
    summary="Get Proposal Narrative",
    description=(
        "Returns the persisted proposal narrative and review posture from lotus-advise. Gateway "
        "does not regenerate narrative text on read."
    ),
)
async def get_proposal_narrative(
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    version_no: int = Path(
        ...,
        ge=1,
        description="Immutable proposal version number containing narrative evidence.",
        examples=[2],
    ),
) -> ProposalEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_proposal_narrative(
        proposal_id=proposal_id,
        version_no=version_no,
        correlation_id=correlation_id,
    )


@router.post(
    "/{proposal_id}/versions/{version_no}/narrative/review",
    response_model=ProposalNarrativeReviewEnvelopeResponse,
    summary="Review Proposal Narrative",
    description=(
        "Records a review decision for a persisted proposal-version narrative through "
        "lotus-advise. Gateway preserves review, source-hash, policy, disclosure, and guardrail "
        "evidence returned by the advisory authority and never regenerates narrative locally."
    ),
)
async def review_proposal_narrative(
    request: ProposalNarrativeReviewRequest,
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    version_no: int = Path(
        ...,
        ge=1,
        description="Immutable proposal version number containing the narrative to review.",
        examples=[2],
    ),
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        description="Optional idempotency key for replay-safe narrative review writes.",
        examples=["proposal-narrative-review-idem-001"],
    ),
) -> ProposalNarrativeReviewEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.review_proposal_narrative(
        proposal_id=proposal_id,
        version_no=version_no,
        body=request.model_dump(exclude_none=True),
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )


@router.post(
    "/{proposal_id}/report-requests",
    response_model=ProposalReportRequestEnvelopeResponse,
    summary="Request Proposal Report",
    description=(
        "Requests a proposal report through lotus-advise and the downstream report/render/archive "
        "path. When `include_reviewed_narrative=true`, lotus-advise blocks unsupported requests "
        "unless approved advisor-use narrative posture and source-hash continuity are present."
    ),
)
async def create_report_request(
    request: ProposalReportRequest,
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
) -> ProposalReportRequestEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.create_report_request(
        proposal_id=proposal_id,
        body=request.model_dump(exclude_none=True),
        correlation_id=correlation_id,
    )


@router.post(
    "/{proposal_id}/execution-handoffs",
    response_model=ProposalEnvelopeResponse,
    summary="Create Proposal Execution Handoff",
    description=(
        "Records a source-owned advisory execution handoff in lotus-advise. Gateway preserves "
        "the boundary that downstream systems remain execution authorities."
    ),
)
async def create_execution_handoff(
    request: ProposalBodyRequest,
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        description="Optional idempotency key for execution handoff requests.",
        examples=["idem-execution-handoff-1"],
    ),
) -> ProposalEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.create_execution_handoff(
        proposal_id=proposal_id,
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )


@router.get(
    "/{proposal_id}/delivery-summary",
    response_model=ProposalDeliverySummaryEnvelopeResponse,
    summary="Get Proposal Delivery Summary",
    description=(
        "Returns lotus-advise delivery posture for proposal execution and reporting. The reporting "
        "summary includes reviewed advisory narrative package posture when it was included in a "
        "source-backed report/render/archive flow."
    ),
)
async def get_delivery_summary(
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
) -> ProposalDeliverySummaryEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_delivery_summary(
        proposal_id=proposal_id,
        correlation_id=correlation_id,
    )


@router.get(
    "/{proposal_id}/delivery-events",
    response_model=ProposalDeliveryEventsEnvelopeResponse,
    summary="Get Proposal Delivery Events",
    description=(
        "Returns delivery-only advisory workflow events from lotus-advise so product consumers can "
        "inspect report, archive, and execution posture without gateway-side inference."
    ),
)
async def get_delivery_events(
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
) -> ProposalDeliveryEventsEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_delivery_events(
        proposal_id=proposal_id,
        correlation_id=correlation_id,
    )


@router.get(
    "/{proposal_id}/execution-status",
    response_model=ProposalEnvelopeResponse,
    summary="Get Proposal Execution Status",
    description=(
        "Returns advisory execution status projection from lotus-advise without Gateway claiming "
        "OMS, fill, or settlement authority."
    ),
)
async def get_execution_status(
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
) -> ProposalEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_execution_status(
        proposal_id=proposal_id,
        correlation_id=correlation_id,
    )


@router.post(
    "/{proposal_id}/execution-updates",
    response_model=ProposalEnvelopeResponse,
    summary="Record Proposal Execution Update",
    description=(
        "Records a downstream execution-status update in lotus-advise while preserving external "
        "execution-system ownership."
    ),
)
async def record_execution_update(
    request: ProposalBodyRequest,
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        description="Optional idempotency key for execution update requests.",
        examples=["idem-execution-update-1"],
    ),
) -> ProposalEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.record_execution_update(
        proposal_id=proposal_id,
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )


@router.post(
    "/{proposal_id}/versions/{version_no}/memo",
    response_model=ProposalMemoEnvelopeResponse,
    summary="Create Proposal Memo",
    description=(
        "Creates or replays the advisor proposal memo through lotus-advise. Gateway preserves "
        "memo evidence, supportability, review posture, report/render/archive posture, and "
        "client-ready blockers without local inference."
    ),
)
async def create_proposal_memo(
    request: ProposalMemoCreateRequest,
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    version_no: int = Path(
        ...,
        description="Immutable proposal version number used as the memo source.",
        examples=[2],
    ),
    idempotency_key: str = Header(
        alias="Idempotency-Key",
        description="Caller-supplied idempotency key for memo creation or replay requests.",
        examples=["idem-memo-create-1"],
    ),
) -> ProposalMemoEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.create_proposal_memo(
        proposal_id=proposal_id,
        version_no=version_no,
        body=request.model_dump(exclude_none=True),
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )


@router.get(
    "/{proposal_id}/versions/{version_no}/memo",
    response_model=ProposalMemoEnvelopeResponse,
    summary="Get Proposal Memo",
    description=(
        "Returns the source-owned proposal memo from lotus-advise. Gateway does not recompute "
        "suitability, readiness, supportability, archive refs, or memo sections locally."
    ),
)
async def get_proposal_memo(
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    version_no: int = Path(
        ...,
        description="Immutable proposal version number used as the memo source.",
        examples=[2],
    ),
) -> ProposalMemoEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_proposal_memo(
        proposal_id=proposal_id,
        version_no=version_no,
        correlation_id=correlation_id,
    )


@router.get(
    "/{proposal_id}/versions/{version_no}/memo/projection",
    response_model=ProposalMemoProjectionEnvelopeResponse,
    summary="Get Proposal Memo Projection",
    description=(
        "Returns an audience-specific memo projection from lotus-advise for advisor, compliance, "
        "operations, or client-draft review. Gateway forwards the requested audience and does not "
        "redact, rank, or construct memo content locally."
    ),
)
async def get_proposal_memo_projection(
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    version_no: int = Path(
        ...,
        description="Immutable proposal version number used as the memo source.",
        examples=[2],
    ),
    audience: str | None = Query(
        default=None,
        description="Optional lotus-advise memo projection audience.",
        examples=["COMPLIANCE"],
    ),
) -> ProposalMemoProjectionEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_proposal_memo_projection(
        proposal_id=proposal_id,
        version_no=version_no,
        audience=audience,
        correlation_id=correlation_id,
    )


@router.post(
    "/{proposal_id}/versions/{version_no}/memo/review",
    response_model=ProposalMemoReviewEnvelopeResponse,
    summary="Review Proposal Memo",
    description=(
        "Records an advisor-use memo review decision through lotus-advise. Gateway forwards the "
        "source memo hash and does not promote client-ready release, mutate memo facts, or bypass "
        "upstream stale-hash controls."
    ),
)
async def review_proposal_memo(
    request: ProposalMemoReviewRequest,
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    version_no: int = Path(
        ...,
        description="Immutable proposal version number used as the memo source.",
        examples=[2],
    ),
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        description="Caller-supplied idempotency key for memo review requests.",
        examples=["idem-memo-review-1"],
    ),
) -> ProposalMemoReviewEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.review_proposal_memo(
        proposal_id=proposal_id,
        version_no=version_no,
        body=request.model_dump(exclude_none=True),
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )


@router.post(
    "/{proposal_id}/versions/{version_no}/memo/report-package-events",
    response_model=ProposalEnvelopeResponse,
    summary="Record Proposal Memo Report Package Event",
    description=(
        "Records report/render/archive package event posture through lotus-advise. Gateway does "
        "not synthesize archive refs, render state, or memo lineage locally."
    ),
)
async def record_proposal_memo_report_package_event(
    request: ProposalBodyRequest,
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    version_no: int = Path(
        ...,
        description="Immutable proposal version number used as the memo source.",
        examples=[2],
    ),
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        description="Caller-supplied idempotency key for memo report-package events.",
        examples=["idem-memo-report-package-event-1"],
    ),
) -> ProposalEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.record_proposal_memo_report_package_event(
        proposal_id=proposal_id,
        version_no=version_no,
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )


@router.post(
    "/{proposal_id}/versions/{version_no}/memo/report-packages",
    response_model=ProposalMemoReportPackageEnvelopeResponse,
    summary="Request Proposal Memo Report Package",
    description=(
        "Requests memo report/render/archive materialization through lotus-advise. Gateway keeps "
        "client-ready document requests governed by upstream blockers and does not synthesize "
        "archive refs or render status locally."
    ),
)
async def request_proposal_memo_report_package(
    request: ProposalMemoReportPackageRequest,
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    version_no: int = Path(
        ...,
        description="Immutable proposal version number used as the memo source.",
        examples=[2],
    ),
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        description="Caller-supplied idempotency key for memo report-package requests.",
        examples=["idem-memo-report-package-1"],
    ),
) -> ProposalMemoReportPackageEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.request_proposal_memo_report_package(
        proposal_id=proposal_id,
        version_no=version_no,
        body=request.model_dump(exclude_none=True),
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )


@router.post(
    "/{proposal_id}/versions/{version_no}/memo/ai-commentary",
    response_model=ProposalMemoAiCommentaryEnvelopeResponse,
    summary="Request Proposal Memo AI Commentary",
    description=(
        "Requests review-gated advisor-use AI commentary through lotus-advise. Gateway does not "
        "treat commentary as memo evidence and does not alter memo approval or readiness posture."
    ),
)
async def request_proposal_memo_ai_commentary(
    request: ProposalMemoAiCommentaryRequest,
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    version_no: int = Path(
        ...,
        description="Immutable proposal version number used as the memo source.",
        examples=[2],
    ),
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        description="Caller-supplied idempotency key for memo AI-commentary requests.",
        examples=["idem-memo-ai-commentary-1"],
    ),
) -> ProposalMemoAiCommentaryEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.request_proposal_memo_ai_commentary(
        proposal_id=proposal_id,
        version_no=version_no,
        body=request.model_dump(exclude_none=True),
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )


@router.get(
    "/{proposal_id}/memos/lineage",
    response_model=ProposalMemoLineageEnvelopeResponse,
    summary="Get Proposal Memo Lineage",
    description=(
        "Returns proposal memo lineage from lotus-advise, including memo hashes, review posture, "
        "report-package posture, archive refs, replay evidence, and AI commentary posture without "
        "gateway-side recomputation."
    ),
)
async def get_proposal_memo_lineage(
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
) -> ProposalMemoLineageEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_proposal_memo_lineage(
        proposal_id=proposal_id,
        correlation_id=correlation_id,
    )


@router.get(
    "/{proposal_id}/versions/{version_no}/memo/replay-evidence",
    response_model=ProposalMemoReplayEvidenceEnvelopeResponse,
    summary="Get Proposal Memo Replay Evidence",
    description=(
        "Returns memo replay evidence from lotus-advise so operations can inspect source hashes, "
        "audit events, supportability, and blocked client-ready posture without local Gateway "
        "interpretation."
    ),
)
async def get_proposal_memo_replay_evidence(
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    version_no: int = Path(
        ...,
        description="Immutable proposal version number used as the memo source.",
        examples=[2],
    ),
) -> ProposalMemoReplayEvidenceEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_proposal_memo_replay_evidence(
        proposal_id=proposal_id,
        version_no=version_no,
        correlation_id=correlation_id,
    )
