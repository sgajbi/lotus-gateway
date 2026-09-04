"""Idea candidate action transport contracts.

Gateway validates transport shape and binds source success evidence to the exact submitted
action. Lotus Idea remains authoritative for candidate state, entitlement, idempotency,
audit, and every business transition.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.contracts.ideas import IdeaReasonCode


def _require_timezone_aware(alias: str, value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{alias} must include a timezone offset")
    return value


class IdeaCandidateActionRequest(BaseModel):
    """Base request contract for Idea-owned candidate mutations.

    Gateway validates transport shape only. Lotus Idea remains authoritative for candidate state,
    entitlement decisions, idempotency semantics, audit, and every business transition.
    """

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    def expected_evidence_fields(self) -> dict[str, Any]:
        """Field values Lotus Idea's success evidence must echo for this exact action."""
        return self.model_dump()


IdeaReviewActionName = Literal[
    "approve_for_conversion",
    "reject",
    "no_action",
    "suppress",
    "snooze",
    "escalate_to_pm",
    "escalate_to_compliance",
]

# Lotus Idea records the action-owned reason for the requested review action first and exactly
# once, whether or not the caller includes it (lotus-idea review_workflow_models /
# _canonical_owned_reason_codes). Gateway mirrors that documented echo relation only to verify
# the returned evidence; it never persists or invents reason codes.
_REVIEW_ACTION_OWNED_REASON_CODES: dict[str, IdeaReasonCode] = {
    "approve_for_conversion": IdeaReasonCode.REVIEW_APPROVED_FOR_CONVERSION,
    "reject": IdeaReasonCode.REVIEW_REJECTED,
    "no_action": IdeaReasonCode.REVIEW_NO_ACTION,
    "suppress": IdeaReasonCode.REVIEW_SUPPRESSED,
    "snooze": IdeaReasonCode.REVIEW_SNOOZED,
    "escalate_to_pm": IdeaReasonCode.REVIEW_ESCALATED,
    "escalate_to_compliance": IdeaReasonCode.REVIEW_ESCALATED,
}


class IdeaCandidateReviewActionRequest(IdeaCandidateActionRequest):
    review_id: str = Field(..., alias="reviewId", min_length=1)
    action: IdeaReviewActionName
    reason_codes: tuple[IdeaReasonCode, ...] = Field(..., alias="reasonCodes", min_length=1)
    decided_at_utc: datetime = Field(..., alias="decidedAtUtc")
    suppression_reason: (
        Literal[
            "duplicate",
            "recently_rejected",
            "below_materiality",
            "unsupported_evidence",
            "manual_suppression",
        ]
        | None
    ) = Field(default=None, alias="suppressionReason")
    snoozed_until_utc: datetime | None = Field(default=None, alias="snoozedUntilUtc")

    @field_validator("review_id")
    @classmethod
    def _review_id_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("reviewId must not be blank")
        return value

    @field_validator("decided_at_utc")
    @classmethod
    def _decided_at_must_be_timezone_aware(cls, value: datetime) -> datetime:
        return _require_timezone_aware("decidedAtUtc", value)

    @field_validator("snoozed_until_utc")
    @classmethod
    def _snoozed_until_must_be_timezone_aware(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return _require_timezone_aware("snoozedUntilUtc", value)

    def expected_evidence_fields(self) -> dict[str, Any]:
        owned_reason = _REVIEW_ACTION_OWNED_REASON_CODES[self.action]
        fields = self.model_dump()
        fields["reason_codes"] = (
            owned_reason,
            *(code for code in self.reason_codes if code != owned_reason),
        )
        return fields


class IdeaCandidateConversionIntentRequest(IdeaCandidateActionRequest):
    conversion_intent_id: str = Field(..., alias="conversionIntentId", min_length=1)
    target: Literal["advise_proposal", "manage_review", "report_evidence"]
    reason_codes: tuple[IdeaReasonCode, ...] = Field(..., alias="reasonCodes", min_length=1)
    requested_at_utc: datetime = Field(..., alias="requestedAtUtc")

    @field_validator("conversion_intent_id")
    @classmethod
    def _conversion_intent_id_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("conversionIntentId must not be blank")
        return value

    @field_validator("requested_at_utc")
    @classmethod
    def _requested_at_must_be_timezone_aware(cls, value: datetime) -> datetime:
        return _require_timezone_aware("requestedAtUtc", value)


class IdeaMutationPersistenceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    decision: str
    candidate_id: str | None = Field(default=None, alias="candidateId")
    lifecycle_status: str | None = Field(default=None, alias="lifecycleStatus")
    review_posture: str | None = Field(default=None, alias="reviewPosture")
    audit_event_type: str | None = Field(default=None, alias="auditEventType")


class IdeaCandidateActionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    persistence: IdeaMutationPersistenceResponse
    durable_storage_backed: bool = Field(..., alias="durableStorageBacked")
    supported_feature_promoted: bool = Field(..., alias="supportedFeaturePromoted")


class IdeaReviewDecisionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    review_id: str = Field(..., alias="reviewId")
    candidate_id: str = Field(..., alias="candidateId")
    evidence_packet_id: str = Field(..., alias="evidencePacketId")
    action: str
    resulting_posture: str = Field(..., alias="resultingPosture")
    actor_role: str = Field(..., alias="actorRole")
    reason_codes: tuple[str, ...] = Field(..., alias="reasonCodes")
    decided_at_utc: datetime = Field(..., alias="decidedAtUtc")
    suppression_reason: str | None = Field(default=None, alias="suppressionReason")
    snoozed_until_utc: datetime | None = Field(default=None, alias="snoozedUntilUtc")
    grants_downstream_authority: bool = Field(..., alias="grantsDownstreamAuthority")


class IdeaCandidateReviewActionResponse(IdeaCandidateActionResponse):
    review_decision: IdeaReviewDecisionResponse = Field(..., alias="reviewDecision")


class IdeaConversionIntentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    conversion_intent_id: str = Field(..., alias="conversionIntentId")
    candidate_id: str = Field(..., alias="candidateId")
    target: str
    source_status: str = Field(..., alias="sourceStatus")
    target_source_authority: str = Field(..., alias="targetSourceAuthority")
    evidence_packet_id: str = Field(..., alias="evidencePacketId")
    evidence_content_hash: str = Field(..., alias="evidenceContentHash")
    source_signal_ids: tuple[str, ...] = Field(..., alias="sourceSignalIds")
    boundary: str
    reason_codes: tuple[str, ...] = Field(..., alias="reasonCodes")
    requested_at_utc: datetime = Field(..., alias="requestedAtUtc")
    grants_downstream_authority: bool = Field(..., alias="grantsDownstreamAuthority")


class IdeaCandidateConversionIntentResponse(IdeaCandidateActionResponse):
    conversion_intent: IdeaConversionIntentResponse = Field(..., alias="conversionIntent")
