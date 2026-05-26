from typing import Any

from pydantic import BaseModel, Field


class AdvisoryPolicyBodyRequest(BaseModel):
    body: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Opaque advisory policy payload forwarded unchanged to lotus-advise. Gateway "
            "does not evaluate policy rules, infer supportability, approve sign-off, or create "
            "client-ready publication posture locally."
        ),
        examples=[
            {
                "requested_by": "advisor_1",
                "source_evaluation_hash": "sha256:policy-evaluation-001",
                "reason": {"purpose": "advisor and compliance review"},
            }
        ],
    )


class AdvisoryPolicyEnvelopeResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated through the gateway request.",
        examples=["corr-advisory-policy-1"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway contract version for advisory policy envelopes.",
        examples=["v1"],
    )
    data: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Advisory policy payload returned by lotus-advise. Gateway preserves policy-pack, "
            "policy-evaluation, workflow, sign-off, report-package, AI-evidence, lineage, "
            "replay, degraded, and blocked posture without recomputing or promoting policy facts."
        ),
    )
