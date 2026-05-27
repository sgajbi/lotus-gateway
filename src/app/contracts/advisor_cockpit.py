from typing import Any, Literal

from pydantic import BaseModel, Field

AdvisorCockpitOwnerRole = Literal[
    "ADVISOR",
    "DESK_HEAD",
    "COMPLIANCE_REVIEWER",
    "INVESTMENT_DESK",
    "OPERATIONS",
    "CRM_OWNER",
    "REPORTING_OWNER",
    "ARCHIVE_OWNER",
    "EXECUTION_OWNER",
    "DPM_OWNER",
    "SYSTEM",
]


class AdvisorCockpitAcknowledgeRequest(BaseModel):
    action_item_version: int = Field(
        ge=1,
        description="Advise-owned action item version observed by the caller.",
        examples=[1],
    )
    acknowledged_by: str = Field(
        description="Actor acknowledging the advisor cockpit action item.",
        examples=["advisor_sg_001"],
    )
    acknowledgement_note: str | None = Field(
        default=None,
        description="Optional support-safe acknowledgement note forwarded to lotus-advise.",
        examples=["Reviewed pending policy action."],
    )


class AdvisorCockpitEnvelopeResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated through the gateway request.",
        examples=["corr-advisor-cockpit-1"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway contract version for advisor cockpit envelopes.",
        examples=["v1"],
    )
    data: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Advisor cockpit payload returned by lotus-advise. Gateway preserves action "
            "status, priority, owner role, reason codes, evidence refs, lineage refs, "
            "supportability posture, unsupported capabilities, and acknowledgement state without "
            "recomputing advisory semantics."
        ),
    )
