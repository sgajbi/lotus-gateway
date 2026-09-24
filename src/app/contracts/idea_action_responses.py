"""Source-owned Idea review and conversion success evidence contracts."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.contracts.datetime_transport import TransportDatetime
from app.contracts.idea_action_authority import (
    SHA256_DIGEST_PATTERN,
    IdeaPersistedReviewChannel,
    IdeaReviewActionName,
    IdeaSourceCutPosture,
    require_non_blank,
    require_timezone_aware,
)


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
    evidence_packet_id: str = Field(..., alias="evidencePacketId", min_length=1)
    evidence_content_hash: str = Field(
        ...,
        alias="evidenceContentHash",
        pattern=SHA256_DIGEST_PATTERN,
    )
    source_revision_vector_digest: str = Field(
        ...,
        alias="sourceRevisionVectorDigest",
        pattern=SHA256_DIGEST_PATTERN,
    )
    source_cut_posture: IdeaSourceCutPosture = Field(..., alias="sourceCutPosture")
    candidate_material_version: int = Field(
        ...,
        alias="candidateMaterialVersion",
        gt=0,
        strict=True,
    )
    candidate_evidence_version: int = Field(
        ...,
        alias="candidateEvidenceVersion",
        gt=0,
        strict=True,
    )
    review_channel: IdeaPersistedReviewChannel = Field(..., alias="reviewChannel")
    presentation_receipt_id: str | None = Field(default=None, alias="presentationReceiptId")
    queue_snapshot_digest: str | None = Field(
        default=None,
        alias="queueSnapshotDigest",
        pattern=SHA256_DIGEST_PATTERN,
    )
    review_policy_version: str = Field(..., alias="reviewPolicyVersion", min_length=1)
    authority_policy_version: str = Field(..., alias="authorityPolicyVersion", min_length=1)
    action: IdeaReviewActionName
    resulting_posture: str = Field(..., alias="resultingPosture")
    actor_role: str = Field(..., alias="actorRole")
    reason_codes: tuple[str, ...] = Field(..., alias="reasonCodes")
    decided_at_utc: TransportDatetime = Field(..., alias="decidedAtUtc")
    accepted_at_utc: TransportDatetime = Field(..., alias="acceptedAtUtc")
    acceptance_time_source: Literal["server_accepted"] = Field(
        ...,
        alias="acceptanceTimeSource",
    )
    suppression_reason: str | None = Field(default=None, alias="suppressionReason")
    snoozed_until_utc: TransportDatetime | None = Field(default=None, alias="snoozedUntilUtc")
    grants_downstream_authority: bool = Field(..., alias="grantsDownstreamAuthority")

    @field_validator("decided_at_utc", "accepted_at_utc", "snoozed_until_utc")
    @classmethod
    def _chronology_must_be_timezone_aware(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return require_timezone_aware("review chronology", value)

    @field_validator("review_policy_version", "authority_policy_version")
    @classmethod
    def _policy_versions_must_not_be_blank(cls, value: str) -> str:
        return require_non_blank("review authority policy version", value)

    @field_validator("presentation_receipt_id")
    @classmethod
    def _presentation_receipt_id_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return require_non_blank("presentationReceiptId", value)

    @model_validator(mode="after")
    def _presentation_receipt_must_match_channel(self) -> "IdeaReviewDecisionResponse":
        if self.review_channel == "workbench" and self.presentation_receipt_id is None:
            raise ValueError("Workbench review evidence requires presentationReceiptId")
        if self.review_channel != "workbench" and self.presentation_receipt_id is not None:
            raise ValueError("non-Workbench review evidence cannot carry presentationReceiptId")
        return self


class IdeaCandidateReviewActionResponse(IdeaCandidateActionResponse):
    review_decision: IdeaReviewDecisionResponse = Field(..., alias="reviewDecision")


class IdeaConversionIntentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    conversion_intent_id: str = Field(..., alias="conversionIntentId")
    candidate_id: str = Field(..., alias="candidateId")
    target: Literal["advise_proposal", "manage_review", "report_evidence"]
    source_status: str = Field(..., alias="sourceStatus")
    target_source_authority: str = Field(..., alias="targetSourceAuthority")
    evidence_packet_id: str = Field(..., alias="evidencePacketId", min_length=1)
    evidence_content_hash: str = Field(
        ...,
        alias="evidenceContentHash",
        pattern=SHA256_DIGEST_PATTERN,
    )
    source_revision_vector_digest: str = Field(
        ...,
        alias="sourceRevisionVectorDigest",
        pattern=SHA256_DIGEST_PATTERN,
    )
    source_cut_posture: IdeaSourceCutPosture = Field(..., alias="sourceCutPosture")
    source_signal_ids: tuple[str, ...] = Field(..., alias="sourceSignalIds")
    review_id: str = Field(..., alias="reviewId", min_length=1)
    review_channel: IdeaPersistedReviewChannel = Field(..., alias="reviewChannel")
    review_policy_version: str = Field(..., alias="reviewPolicyVersion", min_length=1)
    authority_policy_version: str = Field(..., alias="authorityPolicyVersion", min_length=1)
    presentation_receipt_id: str | None = Field(default=None, alias="presentationReceiptId")
    candidate_material_version: int = Field(
        ...,
        alias="candidateMaterialVersion",
        gt=0,
        strict=True,
    )
    candidate_evidence_version: int = Field(
        ...,
        alias="candidateEvidenceVersion",
        gt=0,
        strict=True,
    )
    boundary: Literal["intent_only"]
    reason_codes: tuple[str, ...] = Field(..., alias="reasonCodes")
    requested_at_utc: TransportDatetime = Field(..., alias="requestedAtUtc")
    accepted_at_utc: TransportDatetime = Field(..., alias="acceptedAtUtc")
    acceptance_time_source: Literal["server_accepted"] = Field(
        ...,
        alias="acceptanceTimeSource",
    )
    grants_downstream_authority: bool = Field(..., alias="grantsDownstreamAuthority")

    @field_validator("requested_at_utc", "accepted_at_utc")
    @classmethod
    def _chronology_must_be_timezone_aware(cls, value: datetime) -> datetime:
        return require_timezone_aware("conversion chronology", value)

    @field_validator("review_policy_version", "authority_policy_version")
    @classmethod
    def _policy_versions_must_not_be_blank(cls, value: str) -> str:
        return require_non_blank("conversion authority policy version", value)

    @field_validator("presentation_receipt_id")
    @classmethod
    def _presentation_receipt_id_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return require_non_blank("presentationReceiptId", value)

    @model_validator(mode="after")
    def _presentation_receipt_must_match_channel(self) -> "IdeaConversionIntentResponse":
        if self.review_channel == "workbench" and self.presentation_receipt_id is None:
            raise ValueError("Workbench conversion evidence requires presentationReceiptId")
        if self.review_channel != "workbench" and self.presentation_receipt_id is not None:
            raise ValueError("non-Workbench conversion evidence cannot carry presentationReceiptId")
        return self


class IdeaCandidateConversionIntentResponse(IdeaCandidateActionResponse):
    conversion_intent: IdeaConversionIntentResponse = Field(..., alias="conversionIntent")
