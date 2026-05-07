from pydantic import BaseModel, Field


class DpmWaveForwardRequest(BaseModel):
    body: dict[str, object] = Field(
        description=(
            "Request payload forwarded unchanged to the lotus-manage RFC-0041 rebalance-wave "
            "authority. Gateway does not discover PM books, infer affected portfolios, classify "
            "source readiness, simulate construction alternatives, approve items, stage items, "
            "create handoff evidence, or cancel wave state locally."
        ),
        examples=[
            {
                "trigger_type": "EXPLICIT_PORTFOLIO_LIST",
                "trigger_id": "manual-wave-20260503-001",
                "rationale": "CIO model update for the Singapore balanced DPM book.",
                "as_of_date": "2026-05-03",
                "actor_id": "pm_sg_1",
                "portfolios": [{"portfolio_id": "PB_SG_GLOBAL_BAL_001"}],
            }
        ],
    )


class DpmWaveCreateRequest(DpmWaveForwardRequest):
    idempotency_key: str = Field(
        description=(
            "Required manage idempotency token for durable wave creation. Gateway forwards it as "
            "the `Idempotency-Key` header and does not derive replay keys."
        ),
        examples=["wave-idem-001"],
    )


class DpmWaveSupportability(BaseModel):
    source_service: str = Field(
        default="lotus-manage",
        description="Authoritative service that owns rebalance-wave state and supportability.",
        examples=["lotus-manage"],
    )
    authority: str = Field(
        default="lotus-manage:RFC-0041",
        description="Business authority and RFC provenance for DPM rebalance waves.",
        examples=["lotus-manage:RFC-0041"],
    )
    state: str = Field(
        description=(
            "Manage-published supportability state. Gateway preserves this value and defaults to "
            "UNKNOWN only when the upstream payload omits explicit supportability."
        ),
        examples=["ready", "degraded", "blocked", "UNKNOWN"],
    )
    reason_codes: list[str] = Field(
        default_factory=list,
        description="Manage-published bounded reason codes for blocked or degraded wave posture.",
        examples=[["wave_supportability_ready"]],
    )
    blocked_actions: list[str] = Field(
        default_factory=list,
        description="Manage-published action identifiers that Workbench should disable.",
        examples=[["simulate", "approve"]],
    )
    wave_id: str | None = Field(
        default=None,
        description="Manage-owned rebalance-wave identifier when available.",
        examples=["dwv_001"],
    )
    wave_state: str | None = Field(
        default=None,
        description="Manage-owned wave lifecycle state when available.",
        examples=["HANDOFF_READY"],
    )
    item_count: int | None = Field(
        default=None,
        description="Manage-published item count when available.",
        examples=[12],
    )
    issue_count: int = Field(
        default=0,
        description="Count of manage-published supportability issues, if supplied.",
        examples=[0],
    )
    remediation_owner: str | None = Field(
        default=None,
        description="Manage-published owner for source repair or operational remediation.",
        examples=["Portfolio Operations"],
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
