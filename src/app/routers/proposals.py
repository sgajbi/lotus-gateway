from fastapi import APIRouter, Header, Path, Query

from app.clients.advise_client import AdviseClient
from app.config import settings
from app.contracts.proposals import (
    ProposalApprovalActionRequest,
    ProposalApprovalsEnvelopeResponse,
    ProposalCreateEnvelopeResponse,
    ProposalCreateRequest,
    ProposalDetailEnvelopeResponse,
    ProposalLineageEnvelopeResponse,
    ProposalListEnvelopeResponse,
    ProposalSimulateRequest,
    ProposalSimulateResponse,
    ProposalStateTransitionEnvelopeResponse,
    ProposalSubmitRequest,
    ProposalVersionCreateRequest,
    ProposalVersionEnvelopeResponse,
    ProposalWorkflowEventsEnvelopeResponse,
)
from app.middleware.correlation import correlation_id_var
from app.services.proposal_service import ProposalService

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


def _proposal_service() -> ProposalService:
    return ProposalService(
        advise_client=AdviseClient(
            base_url=settings.decisioning_service_base_url,
            timeout_seconds=settings.upstream_timeout_seconds,
            max_retries=settings.upstream_max_retries,
            retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
        )
    )


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
    service = _proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.simulate_proposal(
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
    service = _proposal_service()
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
    service = _proposal_service()
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
    service = _proposal_service()
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
    service = _proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_proposal_version(
        proposal_id=proposal_id,
        version_no=version_no,
        include_evidence=include_evidence,
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
    service = _proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.create_proposal_version(
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
    service = _proposal_service()
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
    service = _proposal_service()
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
    service = _proposal_service()
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
    service = _proposal_service()
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
    service = _proposal_service()
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
    service = _proposal_service()
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
    service = _proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_proposal_lineage(
        proposal_id=proposal_id,
        correlation_id=correlation_id,
    )
