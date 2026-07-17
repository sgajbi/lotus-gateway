from typing import Any, Literal, TypeVar

from fastapi import HTTPException, status
from pydantic import BaseModel, ValidationError

from app.contracts.ideas import (
    IdeaCandidateActionRequest,
    IdeaCandidateActionResponse,
    IdeaGatewayCandidateDetailResponse,
    IdeaGatewayReviewQueueResponse,
)
from app.services.idea_client_protocols import IdeaClient

ResponseModel = TypeVar("ResponseModel", bound=BaseModel)
IdeaCandidateActionMethod = Literal[
    "record_candidate_review_action",
    "record_candidate_feedback",
    "record_candidate_conversion_intent",
]


class IdeaService:
    def __init__(self, *, idea_client: IdeaClient) -> None:
        self._idea_client = idea_client

    async def get_advisor_review_queue(
        self,
        *,
        evaluated_at_utc: str | None,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> IdeaGatewayReviewQueueResponse:
        status_code, payload = await self._idea_client.get_advisor_review_queue(
            evaluated_at_utc=evaluated_at_utc,
            caller_headers=caller_headers,
            correlation_id=correlation_id,
        )
        self._raise_on_idea_error(status_code, payload, missing_code="idea_queue_unavailable")
        return self._validate_payload(IdeaGatewayReviewQueueResponse, payload)

    async def get_candidate_detail(
        self,
        *,
        candidate_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> IdeaGatewayCandidateDetailResponse:
        status_code, payload = await self._idea_client.get_candidate_detail(
            candidate_id=candidate_id,
            caller_headers=caller_headers,
            correlation_id=correlation_id,
        )
        self._raise_on_idea_error(status_code, payload, missing_code="idea_candidate_unavailable")
        return self._validate_payload(IdeaGatewayCandidateDetailResponse, payload)

    async def record_candidate_action(
        self,
        *,
        action: IdeaCandidateActionMethod,
        candidate_id: str,
        request: IdeaCandidateActionRequest,
        response_model: type[ResponseModel],
        caller_headers: dict[str, str],
        correlation_id: str,
        idempotency_key: str,
        causation_id: str | None,
    ) -> ResponseModel:
        action_methods = {
            "record_candidate_review_action": self._idea_client.record_candidate_review_action,
            "record_candidate_feedback": self._idea_client.record_candidate_feedback,
            "record_candidate_conversion_intent": (
                self._idea_client.record_candidate_conversion_intent
            ),
        }
        action_method = action_methods[action]
        status_code, payload = await action_method(
            candidate_id=candidate_id,
            body=request.model_dump(by_alias=True, exclude_none=True, mode="json"),
            caller_headers=caller_headers,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
            causation_id=causation_id,
        )
        self._raise_on_idea_error(
            status_code, payload, missing_code="idea_candidate_action_unavailable"
        )
        response = self._validate_payload(response_model, payload)
        if isinstance(response, IdeaCandidateActionResponse) and (
            response.supported_feature_promoted is not False
        ):
            raise self._gateway_error(
                status.HTTP_502_BAD_GATEWAY,
                "idea_supported_feature_claim_invalid",
                "Lotus Idea returned an unsupported feature-promotion claim.",
            )
        return response

    def _validate_payload(
        self,
        response_model: type[ResponseModel],
        payload: dict[str, Any],
    ) -> ResponseModel:
        try:
            response = response_model.model_validate(payload)
        except ValidationError as exc:
            raise self._gateway_error(
                status.HTTP_502_BAD_GATEWAY,
                "idea_contract_invalid",
                "Lotus Idea returned a response that does not match the gateway contract.",
            ) from exc
        if response.model_dump(by_alias=True)["supportedFeaturePromoted"] is not False:
            raise self._gateway_error(
                status.HTTP_502_BAD_GATEWAY,
                "idea_supported_feature_claim_invalid",
                "Lotus Idea returned an unsupported feature-promotion claim.",
            )
        return response

    def _raise_on_idea_error(
        self,
        status_code: int,
        payload: dict[str, Any],
        *,
        missing_code: str,
    ) -> None:
        if status_code < status.HTTP_400_BAD_REQUEST:
            return
        if status_code == status.HTTP_400_BAD_REQUEST:
            raise self._gateway_error(
                status.HTTP_400_BAD_REQUEST,
                "idea_invalid_request",
                "Lotus Idea rejected the request.",
            )
        if status_code == status.HTTP_403_FORBIDDEN:
            raise self._gateway_error(
                status.HTTP_403_FORBIDDEN,
                "idea_permission_denied",
                "Caller is not permitted to use the requested Idea capability.",
            )
        if status_code == status.HTTP_404_NOT_FOUND:
            raise self._gateway_error(
                status.HTTP_404_NOT_FOUND,
                "idea_resource_not_found",
                "The requested Idea resource was not found.",
            )
        if status_code == status.HTTP_409_CONFLICT:
            raise self._gateway_error(
                status.HTTP_409_CONFLICT,
                "idea_conflict",
                "The requested Idea action conflicts with current source state or replay evidence.",
            )
        if status_code == status.HTTP_422_UNPROCESSABLE_CONTENT:
            raise self._gateway_error(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                "idea_validation_failed",
                "Lotus Idea could not validate the action request.",
            )
        raise self._gateway_error(
            status.HTTP_502_BAD_GATEWAY,
            missing_code,
            "Lotus Idea is unavailable or returned an unsafe failure.",
        )

    def _gateway_error(self, status_code: int, code: str, message: str) -> HTTPException:
        return HTTPException(status_code=status_code, detail={"code": code, "message": message})
