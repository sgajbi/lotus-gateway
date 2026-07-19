from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

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
    "PORTFOLIO_MANAGER",
    "SYSTEM",
]


class AdvisorCockpitAcknowledgeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action_item_version: int = Field(
        ge=1,
        description="Advise-owned action item version observed by the caller.",
        examples=[1],
    )
    acknowledgement_note: str | None = Field(
        default=None,
        description="Optional support-safe acknowledgement note forwarded to lotus-advise.",
        examples=["Reviewed pending policy action."],
    )


class AdvisorCockpitHouseViewCohortRequest(BaseModel):
    body: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Opaque tactical house-view affected-cohort request forwarded unchanged to "
            "lotus-advise. Gateway does not discover the portfolio universe, infer DPM "
            "eligibility, create campaign waves, approve trades, or claim OMS execution."
        ),
        examples=[
            {
                "tactical_view": {
                    "tactical_view_id": "thv_2026_05_asia_duration",
                    "tactical_view_version": "2026.05",
                    "theme_id": "asia_duration_reduce",
                    "as_of_date": "2026-05-14",
                    "target_action": "REDUCE",
                    "rationale": "Reduce duration exposure in Asia balanced discretionary books.",
                    "source_refs": [
                        {
                            "source_system": "lotus-advise",
                            "source_type": "TACTICAL_HOUSE_VIEW",
                            "source_id": "thv_2026_05_asia_duration",
                            "source_version": "2026.05",
                            "content_hash": "sha256:house-view",
                        }
                    ],
                },
                "candidate_portfolios": [
                    {
                        "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                        "mandate_id": "MANDATE_PB_SG_GLOBAL_BAL_001",
                        "portfolio_type": "DPM",
                        "discretionary_mandate": True,
                        "booking_center_code": "Singapore",
                        "current_exposure_weight": "0.18",
                        "alignment_signal": "OVERWEIGHT",
                        "source_refs": [
                            {
                                "source_system": "lotus-core",
                                "source_type": "HoldingsAsOf",
                                "source_id": "holdings:PB_SG_GLOBAL_BAL_001:2026-05-14",
                                "source_version": "v1",
                                "content_hash": "sha256:holdings",
                            }
                        ],
                    }
                ],
                "eligible_portfolio_types": ["DPM"],
                "correlation_id": "corr-house-view-001",
            }
        ],
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
