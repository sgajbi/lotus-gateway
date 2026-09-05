from datetime import datetime, timedelta
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.contracts.datetime_transport import TransportDatetime
from app.contracts.idea_actions import IdeaCandidateActionRequest, IdeaCandidateActionResponse

IDEA_FEEDBACK_TAXONOMY_VERSION = "idea-feedback-taxonomy-v1"
_GOVERNED_REFERENCE = r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,255}$"
_SHA256_DIGEST = r"^sha256:[0-9a-f]{64}$"


class IdeaFeedbackOutcome(StrEnum):
    """Lotus Idea-owned usefulness outcomes."""

    USEFUL = "useful"
    NOT_USEFUL = "not_useful"


class IdeaFeedbackReason(StrEnum):
    """Lotus Idea-owned reasons in ``idea-feedback-taxonomy-v1``."""

    RELEVANT = "relevant"
    NOT_RELEVANT = "not_relevant"
    ALREADY_KNOWN = "already_known"
    WRONG_TIMING = "wrong_timing"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    WRONG_PRIORITY = "wrong_priority"
    DUPLICATE = "duplicate"
    CLIENT_SPECIFIC_CONSTRAINT = "client_specific_constraint"


class IdeaCandidateFeedbackRequest(IdeaCandidateActionRequest):
    feedback_id: str = Field(..., alias="feedbackId", min_length=1)
    taxonomy_version: Literal["idea-feedback-taxonomy-v1"] = Field(
        ...,
        alias="taxonomyVersion",
        description="Lotus Idea-owned governed feedback taxonomy version.",
    )
    outcome: IdeaFeedbackOutcome
    reason: IdeaFeedbackReason
    recorded_at_utc: TransportDatetime = Field(..., alias="recordedAtUtc")

    @field_validator("feedback_id")
    @classmethod
    def _feedback_id_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("feedbackId must not be blank")
        return value

    @field_validator("recorded_at_utc")
    @classmethod
    def _recorded_at_must_be_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("recordedAtUtc must include a timezone offset")
        return value


class IdeaFeedbackEventResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    feedback_id: str = Field(..., alias="feedbackId")
    candidate_id: str = Field(..., alias="candidateId")
    evidence_packet_id: str = Field(..., alias="evidencePacketId")
    taxonomy_version: Literal["idea-feedback-taxonomy-v1"] = Field(
        ...,
        alias="taxonomyVersion",
    )
    outcome: IdeaFeedbackOutcome
    reason: IdeaFeedbackReason
    actor_role: str = Field(..., alias="actorRole")
    recorded_at_utc: datetime = Field(..., alias="recordedAtUtc")

    @field_validator("recorded_at_utc")
    @classmethod
    def _recorded_at_must_be_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("recordedAtUtc must include a timezone offset")
        return value


class IdeaCandidateFeedbackResponse(IdeaCandidateActionResponse):
    feedback_event: IdeaFeedbackEventResponse = Field(..., alias="feedbackEvent")


class IdeaPresentationReceiptFields(BaseModel):
    """Fields that must be identical in submitted and persisted receipt evidence."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    tenant_id: str = Field(..., alias="tenantId", pattern=_GOVERNED_REFERENCE)
    presented_at_utc: TransportDatetime = Field(..., alias="presentedAtUtc")
    rank_at_presentation: int = Field(
        ...,
        alias="rankAtPresentation",
        ge=1,
        strict=True,
    )
    visible_candidate_count: int = Field(
        ...,
        alias="visibleCandidateCount",
        ge=1,
        le=100,
        strict=True,
    )
    queue_snapshot_digest: str = Field(..., alias="queueSnapshotDigest", pattern=_SHA256_DIGEST)
    queue_policy_version: str = Field(
        ...,
        alias="queuePolicyVersion",
        pattern=_GOVERNED_REFERENCE,
    )
    ranking_policy_version: str = Field(
        ...,
        alias="rankingPolicyVersion",
        pattern=_GOVERNED_REFERENCE,
    )
    candidate_material_version: int = Field(
        ...,
        alias="candidateMaterialVersion",
        ge=1,
        strict=True,
    )
    candidate_evidence_version: int = Field(
        ...,
        alias="candidateEvidenceVersion",
        ge=1,
        strict=True,
    )

    @field_validator("presented_at_utc")
    @classmethod
    def _presented_at_must_be_utc(cls, value: datetime) -> datetime:
        if value.utcoffset() != timedelta(0):
            raise ValueError("presentedAtUtc must be a UTC timestamp")
        return value


class IdeaCandidatePresentationReceiptRequest(IdeaPresentationReceiptFields):
    pass


class IdeaPresentationReceiptEvidenceResponse(IdeaPresentationReceiptFields):
    receipt_id: str = Field(..., alias="receiptId", pattern=_GOVERNED_REFERENCE)
    candidate_id: str = Field(..., alias="candidateId", pattern=_GOVERNED_REFERENCE)
    schema_version: Literal["lotus-idea.candidate-presentation-receipt.v1"] = Field(
        ...,
        alias="schemaVersion",
    )
    surface: Literal["advisor_review_queue"]
    producer: Literal["lotus-workbench"]


class IdeaCandidatePresentationReceiptResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    receipt: IdeaPresentationReceiptEvidenceResponse
    persistence_decision: Literal["accepted", "replayed"] = Field(
        ...,
        alias="persistenceDecision",
    )
    durable_storage_backed: Literal[True] = Field(..., alias="durableStorageBacked")
    effectiveness_measurement_status: Literal["stored_consumer_certification_pending"] = Field(
        ...,
        alias="effectivenessMeasurementStatus",
    )
    certification_status: Literal["not_certified"] = Field(..., alias="certificationStatus")
    certification_blockers: tuple[str, ...] = Field(..., alias="certificationBlockers")
    supported_feature_promoted: bool = Field(..., alias="supportedFeaturePromoted")
