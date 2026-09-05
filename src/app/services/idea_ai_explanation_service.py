from collections.abc import Mapping

from fastapi import HTTPException, status
from pydantic import BaseModel

from app.contracts.idea_ai_explanations import (
    IdeaAIExplanationReadinessResponse,
    IdeaCandidateAIExplanationRequest,
    IdeaCandidateAIExplanationResponse,
)
from app.services.idea_service import IdeaService

# Both accepted serialization spellings of each reserved authority claim.
_RESERVED_AUTHORITY_EXTRA_KEYS = (
    "grantsDownstreamAuthority",
    "grants_downstream_authority",
    "supportedFeaturePromoted",
    "supported_feature_promoted",
)


class IdeaAIExplanationService(IdeaService):
    """Transport-only fan-out for governed Idea AI explanations.

    Lotus Idea owns generation, acceptance, and provenance; the gateway validates
    the documented envelope, preserves the source payload verbatim, and fails
    closed when a served explanation does not carry an accepted verdict or
    tries to escalate authority in transit.
    """

    async def request_candidate_ai_explanation(
        self,
        *,
        candidate_id: str,
        request: IdeaCandidateAIExplanationRequest,
        caller_headers: dict[str, str],
        correlation_id: str,
        idempotency_key: str,
        causation_id: str | None,
    ) -> IdeaCandidateAIExplanationResponse:
        status_code, payload = await self._idea_client.request_candidate_ai_explanation(
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
            missing_code="idea_ai_explanation_unavailable",
        )
        response = self._validate_payload(IdeaCandidateAIExplanationResponse, payload)
        self._assert_ai_explanation_transport_safe(
            candidate_id=candidate_id,
            request=request,
            response=response,
        )
        return response

    async def get_ai_explanation_readiness(
        self,
        *,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> IdeaAIExplanationReadinessResponse:
        status_code, payload = await self._idea_client.get_ai_explanation_readiness(
            caller_headers=caller_headers,
            correlation_id=correlation_id,
        )
        self._raise_on_idea_error(
            status_code,
            payload,
            missing_code="idea_ai_explanation_readiness_unavailable",
        )
        response = self._validate_payload(IdeaAIExplanationReadinessResponse, payload)
        self._reject_authority_escalation_extras(response)
        return response

    def _assert_ai_explanation_transport_safe(
        self,
        *,
        candidate_id: str,
        request: IdeaCandidateAIExplanationRequest,
        response: IdeaCandidateAIExplanationResponse,
    ) -> None:
        explanation = response.explanation
        if response.status == "EXPLANATION_SERVED" and (
            response.evaluation_verdict != "accepted" or not explanation.explanation_text.strip()
        ):
            raise self._gateway_error(
                status.HTTP_502_BAD_GATEWAY,
                "idea_ai_explanation_unsafe",
                "Lotus Idea served an explanation without an accepted verdict and usable text.",
            )
        if explanation.request_id != request.request_id or explanation.candidate_id != candidate_id:
            raise self._gateway_error(
                status.HTTP_502_BAD_GATEWAY,
                "idea_ai_explanation_evidence_mismatch",
                "Lotus Idea returned explanation evidence that does not match the request.",
            )
        if explanation.grants_downstream_authority or explanation.supported_feature_promoted:
            raise self._authority_escalation_error()
        self._reject_authority_escalation_extras(explanation)
        self._reject_authority_escalation_extras(response)

    def _reject_authority_escalation_extras(self, response: BaseModel) -> None:
        """Fail closed when a source-preserving envelope carries reserved authority claims.

        The AI-explanation response models keep extra="allow" to preserve source
        truth, so every one of them must refuse undeclared top-level authority
        fields rather than serializing them onward.
        """
        self._reject_authority_claims_in(response.model_extra or {})

    def _reject_authority_claims_in(self, mapping: Mapping[str, object]) -> None:
        """Refuse any reserved authority key, in either spelling, that is not exactly False."""
        if any(
            key in mapping and mapping[key] is not False for key in _RESERVED_AUTHORITY_EXTRA_KEYS
        ):
            raise self._authority_escalation_error()

    def _authority_escalation_error(self) -> HTTPException:
        return self._gateway_error(
            status.HTTP_502_BAD_GATEWAY,
            "idea_ai_explanation_authority_escalation",
            "Lotus Idea explanation transport attempted an authority escalation.",
        )
