from pydantic import BaseModel, Field, model_validator

from app.contracts.dpm_wave_ai import (
    DpmOperationsHandoffSummaryGatewayResponse,
    DpmOperationsHandoffSummaryRequest,
    DpmWaveMemoGatewayResponse,
    DpmWaveMemoRequest,
)
from app.contracts.dpm_wave_campaign_definitions import (
    DpmCampaignDefinitionForwardRequest,
    DpmCampaignDefinitionGatewayResponse,
    DpmCampaignDefinitionLaunchRequest,
    DpmCampaignDefinitionLifecycleCommandRequest,
)
from app.contracts.dpm_wave_campaign_workflow import (
    DpmCampaignWorkflowForwardRequest,
    DpmCampaignWorkflowGatewayResponse,
)
from app.contracts.dpm_wave_supportability import DpmWaveSupportability

__all__ = [
    "DpmCampaignDefinitionForwardRequest",
    "DpmCampaignDefinitionGatewayResponse",
    "DpmCampaignDefinitionLaunchRequest",
    "DpmCampaignDefinitionLifecycleCommandRequest",
    "DpmCampaignWorkflowForwardRequest",
    "DpmCampaignWorkflowGatewayResponse",
    "DpmOperationsHandoffSummaryGatewayResponse",
    "DpmOperationsHandoffSummaryRequest",
    "DpmWaveCreateRequest",
    "DpmWaveErrorDetail",
    "DpmWaveForwardRequest",
    "DpmWaveGatewayResponse",
    "DpmWaveMemoGatewayResponse",
    "DpmWaveMemoRequest",
    "DpmWaveSupportability",
]

_CORE_DPM_PORTFOLIO_UNIVERSE = "CORE_DPM_PORTFOLIO_UNIVERSE"
_CORE_DISCOVERY_CALLER_SUPPLIED_FIELDS = ("portfolios", "portfolio_ids", "source_candidates")


def _has_supplied_value(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) > 0
    return True


class DpmWaveForwardRequest(BaseModel):
    body: dict[str, object] = Field(
        description=(
            "Request payload forwarded unchanged to the lotus-manage RFC-0041 rebalance-wave "
            "authority. Gateway does not discover PM books, infer affected portfolios, classify "
            "source readiness, simulate construction alternatives, approve items, stage items, "
            "create handoff evidence, or cancel wave state locally. For BULK_REVIEW_CAMPAIGN, "
            "`campaign_candidate_source=CORE_DPM_PORTFOLIO_UNIVERSE` asks lotus-manage to resolve "
            "bounded source-owned candidates from lotus-core `DpmPortfolioUniverseCandidate:v1`; "
            "Gateway preserves the request shape and rejects caller-supplied candidate portfolios "
            "in that mode so Workbench cannot mix source discovery with explicit-list input."
        ),
        examples=[
            {
                "trigger_type": "EXPLICIT_PORTFOLIO_LIST",
                "trigger_id": "manual-wave-20260503-001",
                "rationale": "CIO model update for the Singapore balanced DPM book.",
                "as_of_date": "2026-05-03",
                "actor_id": "pm_sg_1",
                "portfolios": [{"portfolio_id": "PB_SG_GLOBAL_BAL_001"}],
            },
            {
                "trigger_type": "BULK_REVIEW_CAMPAIGN",
                "trigger_id": "campaign-core-universe-20260524",
                "rationale": "Review bounded Core-owned DPM mandate candidates.",
                "as_of_date": "2026-05-24",
                "actor_id": "pm_sg_1",
                "campaign_candidate_source": "CORE_DPM_PORTFOLIO_UNIVERSE",
                "model_portfolio_ids": ["MODEL_PB_SG_GLOBAL_BAL_DPM"],
                "include_inactive_mandates": False,
                "campaign_candidate_page_size": 500,
            },
        ],
    )

    @model_validator(mode="after")
    def reject_caller_portfolios_for_core_candidate_source(self) -> "DpmWaveForwardRequest":
        if self.body.get("campaign_candidate_source") != _CORE_DPM_PORTFOLIO_UNIVERSE:
            return self
        supplied_fields = [
            field
            for field in _CORE_DISCOVERY_CALLER_SUPPLIED_FIELDS
            if _has_supplied_value(self.body.get(field))
        ]
        if supplied_fields:
            supplied = ", ".join(supplied_fields)
            raise ValueError(
                "CORE_DPM_PORTFOLIO_UNIVERSE candidate discovery supplies the portfolio set from "
                "lotus-core DpmPortfolioUniverseCandidate:v1; omit caller-supplied candidate "
                f"fields: {supplied}."
            )
        return self


class DpmWaveCreateRequest(DpmWaveForwardRequest):
    idempotency_key: str = Field(
        description=(
            "Required manage idempotency token for durable wave creation. Gateway forwards it as "
            "the `Idempotency-Key` header and does not derive replay keys."
        ),
        examples=["wave-idem-001"],
    )


class DpmWaveGatewayResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated across Gateway and lotus-manage.",
        examples=["corr-rfc41-wave-1"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway BFF contract version for DPM command-center wave responses.",
        examples=["v1"],
    )
    source_service: str = Field(
        default="lotus-manage",
        description="Upstream service that supplied the authoritative rebalance-wave payload.",
        examples=["lotus-manage"],
    )
    upstream_status: int = Field(
        description="HTTP status returned by lotus-manage before Gateway envelope composition.",
        examples=[200],
    )
    supportability: DpmWaveSupportability = Field(
        description=(
            "Gateway-normalized supportability summary derived only from manage-published fields."
        )
    )
    data: dict[str, object] = Field(
        description=(
            "Authoritative manage wave payload preserved for Workbench composition. Gateway does "
            "not alter wave_id, lifecycle state, item states, reason codes, aggregate metrics, "
            "proof-pack refs, handoff refs, source refs, or supportability."
        ),
        examples=[
            {
                "wave": {
                    "wave_id": "dwv_001",
                    "state": "HANDOFF_READY",
                    "aggregate_metrics": {"item_count": 1, "ready_item_count": 1},
                },
                "durable": True,
            }
        ],
    )


class DpmWaveErrorDetail(BaseModel):
    source_service: str = Field(
        default="lotus-manage",
        description="Upstream service that rejected or failed the rebalance-wave request.",
        examples=["lotus-manage"],
    )
    upstream_status: int = Field(
        description="HTTP status returned by lotus-manage.",
        examples=[422],
    )
    error_code: str = Field(
        description="Gateway error classification for the failed manage wave request.",
        examples=["MANAGE_WAVE_UPSTREAM_ERROR"],
    )
    detail: str = Field(
        description="Product-safe summary of the manage error payload.",
        examples=["Wave dwv_001 cannot be simulated from state DRAFT."],
    )
