from typing import Any, TypeVar

from fastapi import HTTPException, status
from pydantic import BaseModel, ValidationError

from app.contracts.ideas import (
    IdeaGatewayCandidateDetailResponse,
    IdeaGatewayReviewQueueResponse,
)
from app.services.idea_client_protocols import IdeaClient

ResponseModel = TypeVar("ResponseModel", bound=BaseModel)


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
        raise self._gateway_error(
            status.HTTP_502_BAD_GATEWAY,
            missing_code,
            "Lotus Idea is unavailable or returned an unsafe failure.",
        )

    def _gateway_error(self, status_code: int, code: str, message: str) -> HTTPException:
        return HTTPException(status_code=status_code, detail={"code": code, "message": message})
