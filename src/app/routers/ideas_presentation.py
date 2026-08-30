from typing import Annotated

from fastapi import APIRouter, Depends, Header, Path, Response, status

from app.contracts.idea_examples import (
    IDEA_PRESENTATION_RECEIPT_ACCEPTED_EXAMPLE,
    IDEA_PRESENTATION_RECEIPT_REPLAYED_EXAMPLE,
)
from app.contracts.idea_interactions import (
    IdeaCandidatePresentationReceiptRequest,
    IdeaCandidatePresentationReceiptResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.ideas_common import IdeaCallerHeaders, idea_caller_headers, idea_error_response
from app.services.gateway_service_provider import idea_service

router = APIRouter(prefix="/api/v1/ideas", tags=["Ideas"])


async def _record_idea_candidate_presentation_receipt(
    *,
    candidate_id: str,
    request: IdeaCandidatePresentationReceiptRequest,
    response: Response,
    caller_headers: IdeaCallerHeaders,
    idempotency_key: str,
    causation_id: str | None,
) -> IdeaCandidatePresentationReceiptResponse:
    source_status, receipt = await idea_service().record_candidate_presentation_receipt(
        candidate_id=candidate_id,
        request=request,
        caller_headers=caller_headers.as_idea_context(),
        correlation_id=correlation_id_var.get(),
        idempotency_key=idempotency_key,
        causation_id=causation_id,
    )
    response.status_code = source_status
    return receipt


@router.post(
    "/candidates/{candidate_id}/presentation-receipts",
    response_model=IdeaCandidatePresentationReceiptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record visible idea candidate presentation",
    description=(
        "Forwards one Workbench-authored visible-render receipt to Lotus Idea without deriving "
        "rank, visible count, queue digest, policy versions, candidate versions, or presentation "
        "time. Queue retrieval and prefetch never create presentation evidence. Lotus Idea owns "
        "candidate validation, immutable persistence, and effectiveness methodology; this route "
        "does not certify the consumer journey or promote a supported feature."
    ),
    openapi_extra={
        "responses": {
            "200": {
                "description": "An exact immutable presentation receipt was replayed.",
                "content": {
                    "application/json": {
                        "example": IDEA_PRESENTATION_RECEIPT_REPLAYED_EXAMPLE,
                    }
                },
            },
            "201": {
                "description": "The visible-render presentation receipt was recorded.",
                "content": {
                    "application/json": {
                        "example": IDEA_PRESENTATION_RECEIPT_ACCEPTED_EXAMPLE,
                    }
                },
            },
        }
    },
    responses={
        **idea_error_response(400, description="Lotus Idea rejected the bounded receipt."),
        **idea_error_response(403, description="Caller lacks presentation-receipt permission."),
        **idea_error_response(404, description="Lotus Idea did not find the candidate."),
        **idea_error_response(409, description="Receipt identity or candidate state conflicts."),
        **idea_error_response(422, description="Gateway rejected malformed receipt transport."),
        **idea_error_response(502, description="Lotus Idea returned unsafe transport evidence."),
        **idea_error_response(503, description="Lotus Idea receipt persistence is unavailable."),
    },
)
async def record_idea_candidate_presentation_receipt(
    request: IdeaCandidatePresentationReceiptRequest,
    response: Response,
    candidate_id: Annotated[str, Path(description="Lotus Idea-owned candidate identifier.")],
    idempotency_key: Annotated[
        str,
        Header(
            alias="Idempotency-Key",
            min_length=1,
            pattern=r"\S",
            description="Stable receipt identity forwarded unchanged to Lotus Idea.",
        ),
    ],
    causation_id: Annotated[
        str | None,
        Header(
            alias="X-Causation-Id",
            description="Optional governed parent-event identifier forwarded unchanged.",
        ),
    ] = None,
    caller_headers: IdeaCallerHeaders = Depends(idea_caller_headers),
) -> IdeaCandidatePresentationReceiptResponse:
    return await _record_idea_candidate_presentation_receipt(
        candidate_id=candidate_id,
        request=request,
        response=response,
        caller_headers=caller_headers,
        idempotency_key=idempotency_key,
        causation_id=causation_id,
    )
