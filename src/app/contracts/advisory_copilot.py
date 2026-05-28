from typing import Any

from pydantic import BaseModel, Field


class AdvisoryCopilotBodyRequest(BaseModel):
    body: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Opaque advisory copilot request body forwarded unchanged to lotus-advise. Gateway "
            "does not generate prompts, reconstruct evidence packets, evaluate guardrails, "
            "change review state, or infer client-ready publication."
        ),
        examples=[
            {
                "evidence_packet_id": "copilot_packet_pb_sg_001",
                "audience": "ADVISOR",
                "requested_outputs": ["advisor_review_summary"],
                "requested_by": "advisor_sg_001",
                "reason": {"business_reason": "Prepare advisor review."},
            }
        ],
    )


class AdvisoryCopilotEnvelopeResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated through the gateway request.",
        examples=["corr-advisory-copilot-1"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway contract version for advisory copilot envelopes.",
        examples=["v1"],
    )
    data: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Advisory copilot payload returned by lotus-advise. Gateway preserves evidence "
            "packet, action, run, review, lineage, supportability, guardrail, and blocked "
            "client-ready posture without recomputing advisory or AI semantics."
        ),
    )
