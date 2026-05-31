from fastapi import APIRouter, Header, Path

from app.contracts.proposals import (
    ProposalBodyRequest,
    ProposalDeliveryEventsEnvelopeResponse,
    ProposalDeliverySummaryEnvelopeResponse,
    ProposalEnvelopeResponse,
    ProposalReportRequest,
    ProposalReportRequestEnvelopeResponse,
)
from app.middleware.correlation import correlation_id_var
from app.services.advisory_service_provider import proposal_service

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


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
