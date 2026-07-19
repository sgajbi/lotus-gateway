from typing import Any

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

IDEA_REVIEW_ACTION_EXAMPLE: dict[str, Any] = {
    "reviewDecision": {
        "reviewId": "review-001",
        "candidateId": "idea_high_cash_8d57adbf52f7f5a7",
        "evidencePacketId": "iep_high_cash_8d57adbf52f7f5a7",
        "action": "approve_for_conversion",
        "resultingPosture": "approved_for_conversion",
        "actorRole": "advisor",
        "reasonCodes": ["review_required"],
        "decidedAtUtc": "2026-06-21T10:15:00Z",
        "suppressionReason": None,
        "snoozedUntilUtc": None,
        "grantsDownstreamAuthority": False,
    },
    "persistence": {
        "decision": "accepted",
        "candidateId": "idea_high_cash_8d57adbf52f7f5a7",
        "lifecycleStatus": "generated",
        "reviewPosture": "advisor_review_required",
        "auditEventType": "idea.candidate.review.recorded",
    },
    "durableStorageBacked": True,
    "supportedFeaturePromoted": False,
}

IDEA_FEEDBACK_EXAMPLE: dict[str, Any] = {
    "feedbackEvent": {
        "feedbackId": "feedback-001",
        "candidateId": "idea_high_cash_8d57adbf52f7f5a7",
        "evidencePacketId": "iep_high_cash_8d57adbf52f7f5a7",
        "outcome": "useful",
        "actorRole": "advisor",
        "reasonCodes": ["review_required"],
        "recordedAtUtc": "2026-06-21T10:16:00Z",
    },
    "persistence": {
        "decision": "accepted",
        "candidateId": "idea_high_cash_8d57adbf52f7f5a7",
        "lifecycleStatus": "generated",
        "reviewPosture": "advisor_review_required",
        "auditEventType": "idea.candidate.feedback.recorded",
    },
    "durableStorageBacked": True,
    "supportedFeaturePromoted": False,
}

IDEA_CONVERSION_INTENT_EXAMPLE: dict[str, Any] = {
    "conversionIntent": {
        "conversionIntentId": "conversion-001",
        "candidateId": "idea_high_cash_8d57adbf52f7f5a7",
        "target": "report_evidence",
        "sourceStatus": "approved_for_conversion",
        "targetSourceAuthority": "lotus-report",
        "evidencePacketId": "iep_high_cash_8d57adbf52f7f5a7",
        "evidenceContentHash": "sha256:evidence-lineage",
        "sourceSignalIds": ["signal_high_cash_8d57adbf52f7f5a7"],
        "boundary": "intent_only",
        "reasonCodes": ["review_required"],
        "requestedAtUtc": "2026-06-21T10:17:00Z",
        "grantsDownstreamAuthority": False,
    },
    "persistence": {
        "decision": "accepted",
        "candidateId": "idea_high_cash_8d57adbf52f7f5a7",
        "lifecycleStatus": "generated",
        "reviewPosture": "advisor_review_required",
        "auditEventType": "idea.candidate.conversion_intent.recorded",
    },
    "durableStorageBacked": True,
    "supportedFeaturePromoted": False,
}
