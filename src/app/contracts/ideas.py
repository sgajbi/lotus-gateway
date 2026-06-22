from typing import Any

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


IDEA_REVIEW_QUEUE_EXAMPLE: dict[str, Any] = {
    "policyVersion": "idea-deterministic-ranking-v1",
    "evaluatedAtUtc": "2026-06-21T10:10:00Z",
    "items": [
        {
            "rank": 1,
            "candidate": {
                "candidateId": "idea_high_cash_8d57adbf52f7f5a7",
                "family": "high_cash",
                "lifecycleStatus": "generated",
                "reviewPosture": "advisor_review_required",
                "evidencePacketId": "iep_high_cash_8d57adbf52f7f5a7",
                "score": "82",
                "scorePolicyVersion": "idle-liquidity-v1",
                "sourceSignalIds": ["signal_high_cash_8d57adbf52f7f5a7"],
            },
            "score": "82",
            "priorityBucket": "high",
            "policyVersion": "idle-liquidity-v1",
            "reasonCodes": ["high_cash_ratio", "review_required"],
        }
    ],
    "exclusions": [],
    "durableStorageBacked": True,
    "supportedFeaturePromoted": False,
}

IDEA_CANDIDATE_DETAIL_EXAMPLE: dict[str, Any] = {
    "candidate": {
        "candidateId": "idea_high_cash_8d57adbf52f7f5a7",
        "family": "high_cash",
        "lifecycleStatus": "generated",
        "reviewPosture": "advisor_review_required",
        "evidencePacketId": "iep_high_cash_8d57adbf52f7f5a7",
        "supportability": "ready",
        "score": "82",
        "scorePolicyVersion": "idle-liquidity-v1",
        "sourceSignalIds": ["signal_high_cash_8d57adbf52f7f5a7"],
        "reasonCodes": ["high_cash_ratio", "review_required"],
        "unsupportedReasons": [],
        "suppressionReason": None,
        "createdAtUtc": "2026-06-21T10:00:00Z",
        "updatedAtUtc": "2026-06-21T10:15:00Z",
    },
    "evidence": {
        "evidencePacketId": "iep_high_cash_8d57adbf52f7f5a7",
        "evidenceContentHash": "sha256:evidence-lineage",
        "supportability": "ready",
        "lineageId": "lineage_high_cash_8d57adbf52f7f5a7",
        "createdAtUtc": "2026-06-21T10:00:00Z",
        "sourceRefs": [
            {
                "productId": "lotus-core:PortfolioStateSnapshot:v1",
                "sourceSystem": "lotus-core",
                "productVersion": "v1",
                "asOfDate": "2026-06-21",
                "generatedAtUtc": "2026-06-21T10:00:00Z",
                "dataQualityStatus": "complete",
                "freshness": "current",
            }
        ],
    },
    "lifecycleHistory": [],
    "reviewDecisions": [],
    "feedbackEvents": [],
    "conversionIntents": [],
    "conversionOutcomes": [],
    "reportEvidencePacks": [],
    "auditSummary": {
        "eventCount": 1,
        "latestEventType": "idea.candidate.persisted",
        "latestEventOutcome": "accepted",
        "latestOccurredAtUtc": "2026-06-21T10:00:00Z",
    },
    "durableStorageBacked": True,
    "supportedFeaturePromoted": False,
}
