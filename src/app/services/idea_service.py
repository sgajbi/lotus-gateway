from typing import Any, Literal, NamedTuple, TypeVar

from fastapi import HTTPException, status
from pydantic import BaseModel, ValidationError

from app.contracts.idea_actions import (
    IdeaCandidateActionRequest,
    IdeaCandidateConversionIntentRequest,
    IdeaCandidateConversionIntentResponse,
    IdeaCandidateReviewActionRequest,
    IdeaCandidateReviewActionResponse,
)
from app.contracts.idea_interactions import (
    IdeaCandidateFeedbackRequest,
    IdeaCandidateFeedbackResponse,
    IdeaCandidatePresentationReceiptRequest,
    IdeaCandidatePresentationReceiptResponse,
)
from app.contracts.ideas import (
    IdeaGatewayCandidateDetailResponse,
    IdeaGatewayReviewQueueResponse,
)
from app.services.idea_client_protocols import IdeaClient
from app.services.idea_source_error_policy import (
    FEEDBACK_SOURCE_ERROR_MESSAGES,
    PRESENTATION_RECEIPT_SOURCE_ERROR_MESSAGES,
    STANDARD_IDEA_ERROR_MESSAGES,
    SourceErrorMessages,
)

ResponseModel = TypeVar("ResponseModel", bound=BaseModel)
IdeaCandidateActionMethod = Literal[
    "record_candidate_review_action",
    "record_candidate_feedback",
    "record_candidate_conversion_intent",
]


class _ActionEvidenceBinding(NamedTuple):
    """Binds one candidate action to the source evidence that must echo the submitted request."""

    request_type: type[IdeaCandidateActionRequest]
    response_type: type[BaseModel]
    evidence_field: str
    mismatch_code: str
    mismatch_message: str
    source_error_messages: SourceErrorMessages | None = None


_ACTION_EVIDENCE_BINDINGS: dict[IdeaCandidateActionMethod, _ActionEvidenceBinding] = {
    "record_candidate_review_action": _ActionEvidenceBinding(
        request_type=IdeaCandidateReviewActionRequest,
        response_type=IdeaCandidateReviewActionResponse,
        evidence_field="review_decision",
        mismatch_code="idea_review_evidence_mismatch",
        mismatch_message=(
            "Lotus Idea returned review-decision evidence that does not match the submitted "
            "adviser review action."
        ),
    ),
    "record_candidate_feedback": _ActionEvidenceBinding(
        request_type=IdeaCandidateFeedbackRequest,
        response_type=IdeaCandidateFeedbackResponse,
        evidence_field="feedback_event",
        mismatch_code="idea_feedback_evidence_mismatch",
        mismatch_message=(
            "Lotus Idea returned feedback evidence that does not match the submitted adviser "
            "feedback event."
        ),
        source_error_messages=FEEDBACK_SOURCE_ERROR_MESSAGES,
    ),
    "record_candidate_conversion_intent": _ActionEvidenceBinding(
        request_type=IdeaCandidateConversionIntentRequest,
        response_type=IdeaCandidateConversionIntentResponse,
        evidence_field="conversion_intent",
        mismatch_code="idea_conversion_evidence_mismatch",
        mismatch_message=(
            "Lotus Idea returned conversion-intent evidence that does not match the submitted "
            "adviser conversion intent."
        ),
    ),
}


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
        caller_headers: dict[str, str],
        correlation_id: str,
        idempotency_key: str,
        causation_id: str | None,
    ) -> BaseModel:
        binding = _ACTION_EVIDENCE_BINDINGS[action]
        if not isinstance(request, binding.request_type):
            raise self._gateway_error(
                status.HTTP_502_BAD_GATEWAY,
                "idea_contract_invalid",
                "Lotus Idea candidate-action transport is not bound to the governed contract.",
            )
        action_method = getattr(self._idea_client, action)
        status_code, payload = await action_method(
            candidate_id=candidate_id,
            body=request.model_dump(by_alias=True, exclude_none=True, mode="json"),
            caller_headers=caller_headers,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
            causation_id=causation_id,
        )
        self._raise_on_idea_error(
            status_code,
            payload,
            missing_code="idea_candidate_action_unavailable",
            source_error_messages=binding.source_error_messages,
        )
        response = self._validate_payload(binding.response_type, payload)
        self._assert_evidence_echoes_request(
            candidate_id=candidate_id,
            submitted_fields=request.expected_evidence_fields(),
            evidence=getattr(response, binding.evidence_field),
            mismatch_code=binding.mismatch_code,
            mismatch_message=binding.mismatch_message,
        )
        return response

    def _assert_evidence_echoes_request(
        self,
        *,
        candidate_id: str,
        submitted_fields: dict[str, Any],
        evidence: BaseModel,
        mismatch_code: str,
        mismatch_message: str,
    ) -> None:
        persisted_fields = evidence.model_dump(include=set(submitted_fields))
        if (
            getattr(evidence, "candidate_id", None) != candidate_id
            or persisted_fields != submitted_fields
        ):
            raise self._gateway_error(
                status.HTTP_502_BAD_GATEWAY,
                mismatch_code,
                mismatch_message,
            )

    async def record_candidate_presentation_receipt(
        self,
        *,
        candidate_id: str,
        request: IdeaCandidatePresentationReceiptRequest,
        caller_headers: dict[str, str],
        correlation_id: str,
        idempotency_key: str,
        causation_id: str | None,
    ) -> tuple[int, IdeaCandidatePresentationReceiptResponse]:
        status_code, payload = await self._idea_client.record_candidate_presentation_receipt(
            candidate_id=candidate_id,
            body=request.model_dump(by_alias=True, mode="json"),
            caller_headers=caller_headers,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
            causation_id=causation_id,
        )
        self._raise_on_idea_error(
            status_code,
            payload,
            missing_code="idea_presentation_receipt_problem_invalid",
            source_error_messages=PRESENTATION_RECEIPT_SOURCE_ERROR_MESSAGES,
            require_allowlisted_source_error=True,
        )
        if status_code not in {status.HTTP_200_OK, status.HTTP_201_CREATED}:
            raise self._gateway_error(
                status.HTTP_502_BAD_GATEWAY,
                "idea_presentation_receipt_status_invalid",
                "Lotus Idea returned an invalid presentation-receipt success status.",
            )
        response = self._validate_presentation_receipt_response(
            candidate_id=candidate_id,
            request=request,
            status_code=status_code,
            payload=payload,
        )
        return status_code, response

    def _validate_presentation_receipt_response(
        self,
        *,
        candidate_id: str,
        request: IdeaCandidatePresentationReceiptRequest,
        status_code: int,
        payload: dict[str, Any],
    ) -> IdeaCandidatePresentationReceiptResponse:
        response = self._validate_payload(IdeaCandidatePresentationReceiptResponse, payload)
        expected_decision = "accepted" if status_code == status.HTTP_201_CREATED else "replayed"
        if response.persistence_decision != expected_decision:
            raise self._gateway_error(
                status.HTTP_502_BAD_GATEWAY,
                "idea_presentation_receipt_decision_invalid",
                "Lotus Idea returned presentation-receipt persistence evidence that contradicts "
                "the source status.",
            )
        self._assert_evidence_echoes_request(
            candidate_id=candidate_id,
            submitted_fields=request.model_dump(),
            evidence=response.receipt,
            mismatch_code="idea_presentation_receipt_evidence_mismatch",
            mismatch_message=(
                "Lotus Idea returned presentation-receipt evidence that does not match the "
                "submitted visible-render event."
            ),
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
        if getattr(response, "supported_feature_promoted", None) is not False:
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
        source_error_messages: SourceErrorMessages | None = None,
        require_allowlisted_source_error: bool = False,
    ) -> None:
        if status_code < status.HTTP_400_BAD_REQUEST:
            return
        source_code = payload.get("code")
        if isinstance(source_code, str) and source_error_messages is not None:
            safe_message = source_error_messages.get(status_code, {}).get(source_code)
            if safe_message is not None:
                raise self._gateway_error(status_code, source_code, safe_message)
        if require_allowlisted_source_error:
            raise self._gateway_error(
                status.HTTP_502_BAD_GATEWAY,
                missing_code,
                "Lotus Idea returned an unrecognized presentation-receipt failure.",
            )
        standard_error = STANDARD_IDEA_ERROR_MESSAGES.get(status_code)
        if standard_error is not None:
            code, message = standard_error
            raise self._gateway_error(status_code, code, message)
        raise self._gateway_error(
            status.HTTP_502_BAD_GATEWAY,
            missing_code,
            "Lotus Idea is unavailable or returned an unsafe failure.",
        )

    def _gateway_error(self, status_code: int, code: str, message: str) -> HTTPException:
        return HTTPException(status_code=status_code, detail={"code": code, "message": message})
