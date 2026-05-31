from fastapi import APIRouter, Path

from app.contracts.proposals import (
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
