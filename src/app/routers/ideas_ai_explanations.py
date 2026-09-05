from typing import Annotated

from fastapi import APIRouter, Depends, Header, Path

from app.contracts.idea_ai_explanations import (
    IdeaAIExplanationReadinessResponse,
    IdeaCandidateAIExplanationRequest,
    IdeaCandidateAIExplanationResponse,
)
from app.contracts.idea_examples import (
    IDEA_AI_EXPLANATION_EXAMPLE,
    IDEA_AI_EXPLANATION_READINESS_EXAMPLE,
)
from app.middleware.correlation import correlation_id_var
from app.routers.ideas_common import IdeaCallerHeaders, idea_caller_headers, idea_error_response
from app.services.gateway_service_provider import idea_service

router = APIRouter(prefix="/api/v1/ideas", tags=["Ideas"])


async def _request_idea_candidate_ai_explanation(
    *,
    candidate_id: str,
    request: IdeaCandidateAIExplanationRequest,
    caller_headers: IdeaCallerHeaders,
    idempotency_key: str,
    causation_id: str | None,
) -> IdeaCandidateAIExplanationResponse:
    return await idea_service().request_candidate_ai_explanation(
        candidate_id=candidate_id,
        request=request,
        caller_headers=caller_headers.as_idea_context(),
        correlation_id=correlation_id_var.get(),
        idempotency_key=idempotency_key,
        causation_id=causation_id,
    )


async def _get_idea_ai_explanation_readiness(
    *,
    caller_headers: IdeaCallerHeaders,
) -> IdeaAIExplanationReadinessResponse:
    return await idea_service().get_ai_explanation_readiness(
        caller_headers=caller_headers.as_idea_context(),
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/candidates/{candidate_id}/ai-explanations",
    response_model=IdeaCandidateAIExplanationResponse,
    summary="Request idea candidate AI explanation",
    description=(
        "Forwards a bounded AI-explanation generation request to Lotus Idea, which owns "
        "generation, governed acceptance, provenance, and lineage. Gateway validates only the "
        "documented transport shape (request id, one of the three generation purposes, request "
        "time), forwards trusted caller context, idempotency, correlation, and optional "
        "causation lineage, and preserves the source outcome verbatim — including the explicit "
        "EXPLANATION_UNAVAILABLE degraded shape with its disposition reason class, which is "
        "never collapsed into an empty success. A served explanation without an accepted "
        "evaluation verdict, mismatched evidence identity, or any authority escalation in "
        "transit fails closed as a bounded 502. This route does not construct prompts, mutate "
        "content, approve suitability, or grant downstream authority."
    ),
    openapi_extra={
        "responses": {
            "200": {
                "content": {"application/json": {"example": IDEA_AI_EXPLANATION_EXAMPLE}},
            }
        }
    },
    responses={
        **idea_error_response(400, description="Lotus Idea rejected the generation request."),
        **idea_error_response(403, description="Caller lacks Idea AI-explanation permission."),
        **idea_error_response(404, description="Lotus Idea did not find the candidate."),
        **idea_error_response(409, description="Idea state or replay evidence conflicts."),
        **idea_error_response(
            422, description="Lotus Idea could not validate the generation request."
        ),
        **idea_error_response(502, description="Lotus Idea is unavailable or unsafe."),
    },
)
async def request_idea_candidate_ai_explanation(
    request: IdeaCandidateAIExplanationRequest,
    candidate_id: Annotated[str, Path(description="Lotus Idea-owned candidate identifier.")],
    idempotency_key: Annotated[
        str,
        Header(
            alias="Idempotency-Key",
            description="Required key forwarded unchanged to Lotus Idea for replay-safe recording.",
        ),
    ],
    causation_id: Annotated[str | None, Header(alias="X-Causation-Id")] = None,
    caller_headers: IdeaCallerHeaders = Depends(idea_caller_headers),
) -> IdeaCandidateAIExplanationResponse:
    return await _request_idea_candidate_ai_explanation(
        candidate_id=candidate_id,
        request=request,
        caller_headers=caller_headers,
        idempotency_key=idempotency_key,
        causation_id=causation_id,
    )


@router.get(
    "/ai-explanations/readiness",
    response_model=IdeaAIExplanationReadinessResponse,
    summary="Get idea AI explanation readiness",
    description=(
        "Forwards the Lotus Idea AI-explanation readiness posture without local interpretation. "
        "Lotus Idea remains authoritative for readiness, supportability, and certification "
        "blockers; the gateway adds transport and caller identity only."
    ),
    openapi_extra={
        "responses": {
            "200": {
                "content": {"application/json": {"example": IDEA_AI_EXPLANATION_READINESS_EXAMPLE}},
            }
        }
    },
    responses={
        **idea_error_response(403, description="Caller lacks Idea readiness permission."),
        **idea_error_response(502, description="Lotus Idea is unavailable or unsafe."),
    },
)
async def get_idea_ai_explanation_readiness(
    caller_headers: IdeaCallerHeaders = Depends(idea_caller_headers),
) -> IdeaAIExplanationReadinessResponse:
    return await _get_idea_ai_explanation_readiness(caller_headers=caller_headers)
