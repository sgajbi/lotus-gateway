from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.contracts.idea_evidence_identity import IdeaSourceEvidenceIdentity


class IdeaReasonCode(StrEnum):
    """Lotus Idea-owned reason vocabulary accepted by candidate actions."""

    HIGH_CASH_RATIO = "high_cash_ratio"
    CASH_SOURCE_READY = "cash_source_ready"
    CONCENTRATION_ATTENTION = "concentration_attention"
    UNDERPERFORMANCE_ATTENTION = "underperformance_attention"
    ALLOCATION_DRIFT_ATTENTION = "allocation_drift_attention"
    MATURITY_WINDOW = "maturity_window"
    INCOME_ATTENTION = "income_attention"
    VOLATILITY_ATTENTION = "volatility_attention"
    DRAWDOWN_ATTENTION = "drawdown_attention"
    MISSING_BENCHMARK = "missing_benchmark"
    MISSING_RISK_PROFILE = "missing_risk_profile"
    SUITABILITY_CONTEXT_MISSING = "suitability_context_missing"
    MANDATE_RESTRICTION_REVIEW = "mandate_restriction_review"
    SOURCE_STALE = "source_stale"
    SOURCE_DATE_MISMATCH = "source_date_mismatch"
    SOURCE_GENERATED_AFTER_EVALUATION = "source_generated_after_evaluation"
    SOURCE_PARTIAL = "source_partial"
    DUPLICATE_SUPPRESSED = "duplicate_suppressed"
    BELOW_MATERIALITY = "below_materiality"
    REVIEW_REQUIRED = "review_required"
    MATERIALITY_SCORE = "materiality_score"
    URGENCY_SCORE = "urgency_score"
    CONFIDENCE_SCORE = "confidence_score"
    EVIDENCE_QUALITY_SCORE = "evidence_quality_score"
    FRESHNESS_SCORE = "freshness_score"
    RELEVANCE_SCORE = "relevance_score"
    DOWNSTREAM_FIT_SCORE = "downstream_fit_score"
    CONFLICT_PENALTY = "conflict_penalty"
    QUEUE_PRIORITY = "queue_priority"
    QUEUE_EXCLUDED = "queue_excluded"
    REVIEW_APPROVED_FOR_CONVERSION = "review_approved_for_conversion"
    REVIEW_REJECTED = "review_rejected"
    REVIEW_NO_ACTION = "review_no_action"
    REVIEW_SUPPRESSED = "review_suppressed"
    REVIEW_SNOOZED = "review_snoozed"
    REVIEW_ESCALATED = "review_escalated"
    FEEDBACK_RECORDED = "feedback_recorded"
    ENTITLEMENT_DENIED = "entitlement_denied"
    AI_REDACTION_APPLIED = "ai_redaction_applied"
    AI_FALLBACK_USED = "ai_fallback_used"
    AI_VERIFIER_PASSED = "ai_verifier_passed"
    AI_UNSUPPORTED_CLAIM_BLOCKED = "ai_unsupported_claim_blocked"
    AI_FORBIDDEN_ACTION_BLOCKED = "ai_forbidden_action_blocked"
    AI_ACTION_CONTENT_BLOCKED = "ai_action_content_blocked"


class IdeaGatewayErrorResponse(BaseModel):
    code: str = Field(..., description="Stable gateway error code.")
    message: str = Field(..., description="Product-safe error message.")


class IdeaGatewayReviewQueueCandidateResponse(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    candidate_id: str = Field(..., alias="candidateId")
    material_version: int = Field(..., alias="materialVersion", ge=1)
    evidence_version: int = Field(..., alias="evidenceVersion", ge=1)
    score_policy_version: str = Field(
        ...,
        alias="scorePolicyVersion",
        min_length=1,
        pattern=r"\S",
    )


class IdeaGatewayReviewQueueItemResponse(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    rank: int = Field(..., ge=1)
    candidate: IdeaGatewayReviewQueueCandidateResponse
    policy_version: str = Field(..., alias="policyVersion")


class IdeaGatewayReviewQueueResponse(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    policy_version: str = Field(..., alias="policyVersion", description="Lotus Idea queue policy.")
    evaluated_at_utc: str = Field(
        ...,
        alias="evaluatedAtUtc",
        description="Source evaluation instant returned by lotus-idea.",
    )
    items: list[IdeaGatewayReviewQueueItemResponse] = Field(
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
    evidence: IdeaSourceEvidenceIdentity = Field(
        ...,
        description=(
            "Lotus Idea redacted evidence, lineage, and source reference posture. The typed "
            "identity fields bind the candidate to its current evidence revision; the remaining "
            "source posture is preserved verbatim."
        ),
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
