from typing import Any

from pydantic import BaseModel, Field


class AdvisoryWorkspaceBodyRequest(BaseModel):
    body: dict[str, Any] = Field(
        description="Opaque advisory workspace payload forwarded unchanged to lotus-advise.",
        examples=[
            {
                "workspace_name": "Smith Family Trust tactical rebalance draft",
                "created_by": "advisor_1",
                "input_mode": "stateful",
                "stateful_input": {
                    "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                    "as_of": "2026-05-24",
                    "mandate_id": "mandate_growth_01",
                },
            }
        ],
    )


class AdvisoryWorkspaceEnvelopeResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated through the gateway request.",
        examples=["corr-advisory-workspace-1"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway contract version for advisory workspace envelopes.",
        examples=["v1"],
    )
    data: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Advisory workspace payload returned by lotus-advise. Gateway preserves workspace "
            "draft state, evaluation summary, replay evidence, and lifecycle handoff posture "
            "without recomputing proposal facts."
        ),
    )
