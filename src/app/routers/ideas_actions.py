from typing import Annotated, Literal, cast

from fastapi import APIRouter, Depends, Header, Path

from app.contracts.ideas import (
    IdeaCandidateConversionIntentRequest,
    IdeaCandidateConversionIntentResponse,
    IdeaCandidateFeedbackRequest,
    IdeaCandidateFeedbackResponse,
    IdeaCandidateReviewActionRequest,
    IdeaCandidateReviewActionResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.ideas_common import IdeaCallerHeaders, idea_caller_headers, idea_error_response
from app.services.gateway_service_provider import idea_service

router = APIRouter(prefix="/api/v1/ideas", tags=["Ideas"])


async def _record_idea_candidate_action(
    *,
    action: Literal[
        "record_candidate_review_action",
        "record_candidate_feedback",
        "record_candidate_conversion_intent",
    ],
    candidate_id: str,
    request: IdeaCandidateReviewActionRequest
    | IdeaCandidateFeedbackRequest
    | IdeaCandidateConversionIntentRequest,
    response_model: type[
        IdeaCandidateReviewActionResponse
        | IdeaCandidateFeedbackResponse
        | IdeaCandidateConversionIntentResponse
    ],
    caller_headers: IdeaCallerHeaders,
    idempotency_key: str,
    causation_id: str | None,
) -> (
    IdeaCandidateReviewActionResponse
    | IdeaCandidateFeedbackResponse
    | IdeaCandidateConversionIntentResponse
):
    return await idea_service().record_candidate_action(
        action=action,
        candidate_id=candidate_id,
        request=request,
        response_model=response_model,
        caller_headers=caller_headers.as_idea_context(),
        correlation_id=correlation_id_var.get(),
        idempotency_key=idempotency_key,
        causation_id=causation_id,
    )


@router.post(
    "/candidates/{candidate_id}/review-actions",
    response_model=IdeaCandidateReviewActionResponse,
    summary="Record idea candidate review action",
    description=(
        "Forwards an advisor review action to Lotus Idea. Gateway validates only the documented "
        "transport shape and forwards trusted caller context, idempotency, correlation, trace, and "
        "optional causation lineage. Lotus Idea remains authoritative for entitlement, lifecycle, "
        "replay, audit, and downstream-authority decisions; this route does not approve "
        "suitability, compliance, mandate, execution, or client communication."
    ),
    responses={
        **idea_error_response(400, description="Lotus Idea rejected the action request."),
        **idea_error_response(403, description="Caller lacks Idea review permission."),
        **idea_error_response(404, description="Lotus Idea did not find the candidate."),
        **idea_error_response(409, description="Idea lifecycle or replay evidence conflicts."),
        **idea_error_response(422, description="Lotus Idea could not validate the action request."),
        **idea_error_response(502, description="Lotus Idea is unavailable or unsafe."),
    },
)
async def record_idea_candidate_review_action(
    request: IdeaCandidateReviewActionRequest,
    candidate_id: Annotated[str, Path(description="Lotus Idea-owned candidate identifier.")],
    idempotency_key: Annotated[
        str,
        Header(
            alias="Idempotency-Key",
            description="Required key forwarded unchanged to Lotus Idea for replay-safe recording.",
        ),
    ],
    causation_id: Annotated[
        str | None,
        Header(
            alias="X-Causation-Id",
            description=(
                "Optional governed parent-event identifier forwarded unchanged to Lotus Idea."
            ),
        ),
    ] = None,
    caller_headers: IdeaCallerHeaders = Depends(idea_caller_headers),
) -> IdeaCandidateReviewActionResponse:
    return cast(
        IdeaCandidateReviewActionResponse,
        await _record_idea_candidate_action(
            action="record_candidate_review_action",
            candidate_id=candidate_id,
            request=request,
            response_model=IdeaCandidateReviewActionResponse,
            caller_headers=caller_headers,
            idempotency_key=idempotency_key,
            causation_id=causation_id,
        ),
    )


@router.post(
    "/candidates/{candidate_id}/feedback",
    response_model=IdeaCandidateFeedbackResponse,
    summary="Record idea candidate feedback",
    description=(
        "Forwards source-provenanced advisor feedback to Lotus Idea with trusted caller context, "
        "idempotency, and request lineage. Gateway does not interpret feedback, mutate candidate "
        "state locally, or grant downstream authority."
    ),
    responses={
        **idea_error_response(400, description="Lotus Idea rejected the feedback request."),
        **idea_error_response(403, description="Caller lacks Idea feedback permission."),
        **idea_error_response(404, description="Lotus Idea did not find the candidate."),
        **idea_error_response(409, description="Idea replay evidence conflicts."),
        **idea_error_response(
            422, description="Lotus Idea could not validate the feedback request."
        ),
        **idea_error_response(502, description="Lotus Idea is unavailable or unsafe."),
    },
)
async def record_idea_candidate_feedback(
    request: IdeaCandidateFeedbackRequest,
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
) -> IdeaCandidateFeedbackResponse:
    return cast(
        IdeaCandidateFeedbackResponse,
        await _record_idea_candidate_action(
            action="record_candidate_feedback",
            candidate_id=candidate_id,
            request=request,
            response_model=IdeaCandidateFeedbackResponse,
            caller_headers=caller_headers,
            idempotency_key=idempotency_key,
            causation_id=causation_id,
        ),
    )


@router.post(
    "/candidates/{candidate_id}/conversion-intents",
    response_model=IdeaCandidateConversionIntentResponse,
    summary="Record idea candidate conversion intent",
    description=(
        "Forwards a candidate conversion intent to Lotus Idea. The intent remains source-owned and "
        "does not create an Advise proposal, Manage action, Report evidence pack, rebalance, "
        "execution instruction, suitability approval, or client communication."
    ),
    responses={
        **idea_error_response(
            400, description="Lotus Idea rejected the conversion-intent request."
        ),
        **idea_error_response(403, description="Caller lacks Idea conversion-intent permission."),
        **idea_error_response(404, description="Lotus Idea did not find the candidate."),
        **idea_error_response(409, description="Idea lifecycle or replay evidence conflicts."),
        **idea_error_response(
            422, description="Lotus Idea could not validate the conversion-intent request."
        ),
        **idea_error_response(502, description="Lotus Idea is unavailable or unsafe."),
    },
)
async def record_idea_candidate_conversion_intent(
    request: IdeaCandidateConversionIntentRequest,
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
) -> IdeaCandidateConversionIntentResponse:
    return cast(
        IdeaCandidateConversionIntentResponse,
        await _record_idea_candidate_action(
            action="record_candidate_conversion_intent",
            candidate_id=candidate_id,
            request=request,
            response_model=IdeaCandidateConversionIntentResponse,
            caller_headers=caller_headers,
            idempotency_key=idempotency_key,
            causation_id=causation_id,
        ),
    )
