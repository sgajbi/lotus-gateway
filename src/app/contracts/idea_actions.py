"""Idea candidate action transport contracts.

Gateway validates transport shape and binds source success evidence to the exact submitted
action. Lotus Idea remains authoritative for candidate state, entitlement, idempotency,
audit, and every business transition.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.contracts.datetime_transport import TransportDatetime
from app.contracts.idea_action_authority import (
    SHA256_DIGEST_PATTERN,
    IdeaReviewActionName,
    IdeaReviewChannel,
    IdeaSourceCutPosture,
    require_timezone_aware,
)
from app.contracts.idea_action_responses import (
    IdeaCandidateActionResponse,
    IdeaCandidateConversionIntentResponse,
    IdeaCandidateReviewActionResponse,
)
from app.contracts.ideas import IdeaReasonCode


class IdeaCandidateActionRequest(BaseModel):
    """Base request contract for Idea-owned candidate mutations.

    Gateway validates transport shape only. Lotus Idea remains authoritative for candidate state,
    entitlement decisions, idempotency semantics, audit, and every business transition.
    """

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    def expected_evidence_fields(self) -> dict[str, Any]:
        """Field values Lotus Idea's success evidence must echo for this exact action."""
        return self.model_dump()

    @classmethod
    def response_evidence_field_names(cls) -> set[str]:
        """Response fields that must bind a source success to the submitted action."""
        return set(cls.model_fields)


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

_REVIEW_EVIDENCE_FIELD_MAP = {
    "review_id": "review_id",
    "action": "action",
    "reason_codes": "reason_codes",
    "decided_at_utc": "decided_at_utc",
    "review_channel": "review_channel",
    "expected_material_version": "candidate_material_version",
    "expected_evidence_version": "candidate_evidence_version",
    "expected_evidence_packet_id": "evidence_packet_id",
    "expected_evidence_content_hash": "evidence_content_hash",
    "expected_source_revision_vector_digest": "source_revision_vector_digest",
    "expected_source_cut_posture": "source_cut_posture",
    "presentation_receipt_id": "presentation_receipt_id",
    "suppression_reason": "suppression_reason",
    "snoozed_until_utc": "snoozed_until_utc",
}


class _IdeaCandidateSourceEvidenceRequest(IdeaCandidateActionRequest):
    """Immutable source evidence shared by review and conversion mutations."""

    expected_material_version: int = Field(
        ...,
        alias="expectedMaterialVersion",
        gt=0,
        strict=True,
    )
    expected_evidence_version: int = Field(
        ...,
        alias="expectedEvidenceVersion",
        gt=0,
        strict=True,
    )
    expected_evidence_packet_id: str = Field(
        ...,
        alias="expectedEvidencePacketId",
        min_length=1,
    )
    expected_evidence_content_hash: str = Field(
        ...,
        alias="expectedEvidenceContentHash",
        pattern=SHA256_DIGEST_PATTERN,
    )
    expected_source_revision_vector_digest: str = Field(
        ...,
        alias="expectedSourceRevisionVectorDigest",
        pattern=SHA256_DIGEST_PATTERN,
    )
    expected_source_cut_posture: IdeaSourceCutPosture = Field(
        ...,
        alias="expectedSourceCutPosture",
    )

    @field_validator("expected_evidence_packet_id")
    @classmethod
    def _evidence_packet_id_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("evidence authority identity fields must not be blank")
        return value


class IdeaCandidateReviewActionRequest(_IdeaCandidateSourceEvidenceRequest):
    review_id: str = Field(..., alias="reviewId", min_length=1)
    action: IdeaReviewActionName
    reason_codes: tuple[IdeaReasonCode, ...] = Field(..., alias="reasonCodes", min_length=1)
    decided_at_utc: TransportDatetime = Field(..., alias="decidedAtUtc")
    review_channel: IdeaReviewChannel = Field(..., alias="reviewChannel")
    presentation_receipt_id: str | None = Field(default=None, alias="presentationReceiptId")
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
    snoozed_until_utc: TransportDatetime | None = Field(default=None, alias="snoozedUntilUtc")

    @field_validator("review_id")
    @classmethod
    def _required_identity_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("review authority identity fields must not be blank")
        return value

    @field_validator("presentation_receipt_id")
    @classmethod
    def _presentation_receipt_id_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("presentationReceiptId must not be blank")
        return value

    @field_validator("decided_at_utc")
    @classmethod
    def _decided_at_must_be_timezone_aware(cls, value: datetime) -> datetime:
        return require_timezone_aware("decidedAtUtc", value)

    @field_validator("snoozed_until_utc")
    @classmethod
    def _snoozed_until_must_be_timezone_aware(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return require_timezone_aware("snoozedUntilUtc", value)

    @model_validator(mode="after")
    def _presentation_receipt_must_match_channel(self) -> "IdeaCandidateReviewActionRequest":
        if self.review_channel == "workbench" and self.presentation_receipt_id is None:
            raise ValueError("Workbench review requires presentationReceiptId")
        if self.review_channel == "operator" and self.presentation_receipt_id is not None:
            raise ValueError("operator review cannot carry presentationReceiptId")
        return self

    def expected_evidence_fields(self) -> dict[str, Any]:
        owned_reason = _REVIEW_ACTION_OWNED_REASON_CODES[self.action]
        fields = self.model_dump()
        fields["reason_codes"] = (
            owned_reason,
            *(code for code in self.reason_codes if code != owned_reason),
        )
        return {
            response_field: fields[request_field]
            for request_field, response_field in _REVIEW_EVIDENCE_FIELD_MAP.items()
        }

    @classmethod
    def response_evidence_field_names(cls) -> set[str]:
        return set(_REVIEW_EVIDENCE_FIELD_MAP.values())


_CONVERSION_EVIDENCE_FIELD_MAP = {
    "conversion_intent_id": "conversion_intent_id",
    "target": "target",
    "reason_codes": "reason_codes",
    "requested_at_utc": "requested_at_utc",
    "expected_review_id": "review_id",
    "expected_material_version": "candidate_material_version",
    "expected_evidence_version": "candidate_evidence_version",
    "expected_evidence_packet_id": "evidence_packet_id",
    "expected_evidence_content_hash": "evidence_content_hash",
    "expected_source_revision_vector_digest": "source_revision_vector_digest",
    "expected_source_cut_posture": "source_cut_posture",
}


class IdeaCandidateConversionIntentRequest(_IdeaCandidateSourceEvidenceRequest):
    conversion_intent_id: str = Field(..., alias="conversionIntentId", min_length=1)
    target: Literal["advise_proposal", "manage_review", "report_evidence"]
    reason_codes: tuple[IdeaReasonCode, ...] = Field(..., alias="reasonCodes", min_length=1)
    requested_at_utc: TransportDatetime = Field(..., alias="requestedAtUtc")
    expected_review_id: str = Field(..., alias="expectedReviewId", min_length=1)

    @field_validator(
        "conversion_intent_id",
        "expected_review_id",
    )
    @classmethod
    def _required_identity_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("conversion authority identity fields must not be blank")
        return value

    @field_validator("requested_at_utc")
    @classmethod
    def _requested_at_must_be_timezone_aware(cls, value: datetime) -> datetime:
        return require_timezone_aware("requestedAtUtc", value)

    def expected_evidence_fields(self) -> dict[str, Any]:
        fields = self.model_dump()
        return {
            response_field: fields[request_field]
            for request_field, response_field in _CONVERSION_EVIDENCE_FIELD_MAP.items()
        }

    @classmethod
    def response_evidence_field_names(cls) -> set[str]:
        return set(_CONVERSION_EVIDENCE_FIELD_MAP.values())


__all__ = [
    "IdeaCandidateActionRequest",
    "IdeaCandidateActionResponse",
    "IdeaCandidateConversionIntentRequest",
    "IdeaCandidateConversionIntentResponse",
    "IdeaCandidateReviewActionRequest",
    "IdeaCandidateReviewActionResponse",
    "IdeaReviewActionName",
]
