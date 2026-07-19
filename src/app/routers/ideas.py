from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.contracts.idea_examples import IDEA_CANDIDATE_DETAIL_EXAMPLE, IDEA_REVIEW_QUEUE_EXAMPLE
from app.contracts.ideas import (
    IdeaGatewayCandidateDetailResponse,
    IdeaGatewayReviewQueueResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.ideas_common import IdeaCallerHeaders, idea_caller_headers, idea_error_response
from app.services.gateway_service_provider import idea_service

router = APIRouter(prefix="/api/v1/ideas", tags=["Ideas"])


async def _get_advisor_idea_review_queue(
    *,
    evaluated_at_utc: str | None,
    caller_headers: IdeaCallerHeaders,
) -> IdeaGatewayReviewQueueResponse:
    return await idea_service().get_advisor_review_queue(
        evaluated_at_utc=evaluated_at_utc,
        caller_headers=caller_headers.as_idea_context(),
        correlation_id=correlation_id_var.get(),
    )


async def _get_idea_candidate_detail(
    *,
    candidate_id: str,
    caller_headers: IdeaCallerHeaders,
) -> IdeaGatewayCandidateDetailResponse:
    return await idea_service().get_candidate_detail(
        candidate_id=candidate_id,
        caller_headers=caller_headers.as_idea_context(),
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/review-queues/advisor",
    response_model=IdeaGatewayReviewQueueResponse,
    summary="Get advisor idea review queue",
    description=(
        "Returns the product-facing advisor idea review queue by forwarding to lotus-idea. "
        "Gateway preserves lotus-idea ranking, candidate identity, source signal identifiers, "
        "caller entitlement scope, durable-storage posture, and supported-feature promotion "
        "state; it does not rank, generate, or certify idea candidates locally."
    ),
    openapi_extra={
        "responses": {
            "200": {
                "content": {"application/json": {"example": IDEA_REVIEW_QUEUE_EXAMPLE}},
            }
        }
    },
    responses={
        **idea_error_response(400, description="Lotus Idea rejected the queue request."),
        **idea_error_response(403, description="Caller lacks Idea review-queue permission."),
        **idea_error_response(502, description="Lotus Idea is unavailable or unsafe."),
    },
)
async def get_advisor_idea_review_queue(
    evaluated_at_utc: Annotated[
        str | None,
        Query(
            alias="evaluatedAtUtc",
            description=(
                "Optional timezone-aware evaluation instant forwarded to lotus-idea. "
                "When omitted, lotus-idea returns its governed active advisor queue snapshot."
            ),
            examples=["2026-06-21T10:10:00Z"],
        ),
    ] = None,
    caller_headers: IdeaCallerHeaders = Depends(idea_caller_headers),
) -> IdeaGatewayReviewQueueResponse:
    return await _get_advisor_idea_review_queue(
        evaluated_at_utc=evaluated_at_utc,
        caller_headers=caller_headers,
    )


@router.get(
    "/candidates/{candidate_id}",
    response_model=IdeaGatewayCandidateDetailResponse,
    summary="Get idea candidate detail",
    description=(
        "Returns source-safe idea candidate detail by forwarding to lotus-idea. Gateway preserves "
        "lotus-idea candidate lifecycle, redacted evidence, source references, review, feedback, "
        "conversion, report-evidence, audit, durable-storage, and supported-feature posture; it "
        "also forwards caller entitlement-scope headers for lotus-idea fail-closed access checks. "
        "It does not enrich, re-score, or grant downstream authority locally."
    ),
    openapi_extra={
        "responses": {
            "200": {
                "content": {"application/json": {"example": IDEA_CANDIDATE_DETAIL_EXAMPLE}},
            }
        }
    },
    responses={
        **idea_error_response(400, description="Lotus Idea rejected the candidate request."),
        **idea_error_response(403, description="Caller lacks Idea candidate-detail permission."),
        **idea_error_response(404, description="Lotus Idea did not find the candidate."),
        **idea_error_response(502, description="Lotus Idea is unavailable or unsafe."),
    },
)
async def get_idea_candidate_detail(
    candidate_id: Annotated[
        str,
        Path(
            description="Lotus Idea-owned candidate identifier.",
            examples=["idea_high_cash_8d57adbf52f7f5a7"],
        ),
    ],
    caller_headers: IdeaCallerHeaders = Depends(idea_caller_headers),
) -> IdeaGatewayCandidateDetailResponse:
    return await _get_idea_candidate_detail(
        candidate_id=candidate_id,
        caller_headers=caller_headers,
    )
