from typing import Any

from pydantic import BaseModel, Field


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
            "Advise-owned advisory copilot payload returned without Gateway-side "
            "reinterpretation. Gateway preserves evidence packets, run state, review posture, "
            "supportability, lineage, guardrail posture, and unsupported capability boundaries."
        ),
    )
