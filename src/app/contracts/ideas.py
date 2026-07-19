from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class IdeaGatewayErrorResponse(BaseModel):
    code: str = Field(..., description="Stable gateway error code.")
    message: str = Field(..., description="Product-safe error message.")


class IdeaGatewayReviewQueueResponse(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    policy_version: str = Field(..., alias="policyVersion", description="Lotus Idea queue policy.")
    evaluated_at_utc: str = Field(
        ...,
        alias="evaluatedAtUtc",
        description="Source evaluation instant returned by lotus-idea.",
    )
    items: list[dict[str, Any]] = Field(
        ...,
        description="Lotus Idea-ranked queue entries preserved without Gateway reranking.",
    )
    exclusions: list[dict[str, Any]] = Field(
        ...,
        description="Lotus Idea exclusion entries preserved without Gateway reinterpretation.",
    )
    durable_storage_backed: bool = Field(
        ...,
        alias="durableStorageBacked",
        description="Whether lotus-idea reports durable storage-backed queue evidence.",
    )
    supported_feature_promoted: bool = Field(
        ...,
        alias="supportedFeaturePromoted",
        description="Source-owned supported-feature promotion flag. Gateway must not promote it.",
    )


class IdeaGatewayCandidateDetailResponse(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    candidate: dict[str, Any] = Field(
        ...,
        description="Lotus Idea candidate summary, lifecycle, score, and source signal identity.",
    )
    evidence: dict[str, Any] = Field(
        ...,
        description="Lotus Idea redacted evidence, lineage, and source reference posture.",
    )
    lifecycle_history: list[dict[str, Any]] = Field(
        ...,
        alias="lifecycleHistory",
        description="Lotus Idea lifecycle history entries.",
    )
    review_decisions: list[dict[str, Any]] = Field(
        ...,
        alias="reviewDecisions",
        description="Lotus Idea review decisions preserved as source truth.",
    )
    feedback_events: list[dict[str, Any]] = Field(
        ...,
        alias="feedbackEvents",
        description="Lotus Idea feedback events preserved as source truth.",
    )
    conversion_intents: list[dict[str, Any]] = Field(
        ...,
        alias="conversionIntents",
        description="Lotus Idea conversion intent summaries.",
    )
    conversion_outcomes: list[dict[str, Any]] = Field(
        ...,
        alias="conversionOutcomes",
        description="Lotus Idea conversion outcome summaries.",
    )
    report_evidence_packs: list[dict[str, Any]] = Field(
        ...,
        alias="reportEvidencePacks",
        description="Lotus Idea governed report evidence pack summaries.",
    )
    audit_summary: dict[str, Any] = Field(
        ...,
        alias="auditSummary",
        description="Lotus Idea audit summary without raw source payloads.",
    )
    durable_storage_backed: bool = Field(
        ...,
        alias="durableStorageBacked",
        description="Whether lotus-idea reports durable storage-backed candidate evidence.",
    )
    supported_feature_promoted: bool = Field(
        ...,
        alias="supportedFeaturePromoted",
        description="Source-owned supported-feature promotion flag. Gateway must not promote it.",
    )


class IdeaCandidateActionRequest(BaseModel):
    """Base request contract for Idea-owned candidate mutations.

    Gateway validates transport shape only. Lotus Idea remains authoritative for candidate state,
    entitlement decisions, idempotency semantics, audit, and every business transition.
    """

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class IdeaCandidateReviewActionRequest(IdeaCandidateActionRequest):
    review_id: str = Field(..., alias="reviewId", min_length=1)
    action: Literal[
        "approve_for_conversion",
        "reject",
        "no_action",
        "suppress",
        "snooze",
        "escalate_to_pm",
        "escalate_to_compliance",
    ]
    reason_codes: tuple[str, ...] = Field(..., alias="reasonCodes", min_length=1)
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


class IdeaCandidateFeedbackRequest(IdeaCandidateActionRequest):
    feedback_id: str = Field(..., alias="feedbackId", min_length=1)
    outcome: Literal[
        "useful",
        "not_useful",
        "duplicate",
        "too_late",
        "missing_context",
        "unsupported_claim",
    ]
    reason_codes: tuple[str, ...] = Field(..., alias="reasonCodes", min_length=1)
    recorded_at_utc: datetime = Field(..., alias="recordedAtUtc")


class IdeaCandidateConversionIntentRequest(IdeaCandidateActionRequest):
    conversion_intent_id: str = Field(..., alias="conversionIntentId", min_length=1)
    target: Literal["advise_proposal", "manage_review", "report_evidence"]
    reason_codes: tuple[str, ...] = Field(..., alias="reasonCodes", min_length=1)
    requested_at_utc: datetime = Field(..., alias="requestedAtUtc")


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
    review_decision: IdeaReviewDecisionResponse | None = Field(default=None, alias="reviewDecision")


class IdeaFeedbackEventResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    feedback_id: str = Field(..., alias="feedbackId")
    candidate_id: str = Field(..., alias="candidateId")
    evidence_packet_id: str = Field(..., alias="evidencePacketId")
    outcome: str
    actor_role: str = Field(..., alias="actorRole")
    reason_codes: tuple[str, ...] = Field(..., alias="reasonCodes")
    recorded_at_utc: datetime = Field(..., alias="recordedAtUtc")


class IdeaCandidateFeedbackResponse(IdeaCandidateActionResponse):
    feedback_event: IdeaFeedbackEventResponse | None = Field(default=None, alias="feedbackEvent")


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
    conversion_intent: IdeaConversionIntentResponse | None = Field(
        default=None,
        alias="conversionIntent",
    )
