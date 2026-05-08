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


class DpmWaveMemoRequest(BaseModel):
    requested_outputs: list[str] = Field(
        default_factory=lambda: [
            "wave_pm_memo",
            "wave_rationale_summary",
            "approval_checklist",
            "risk_caveats",
            "operations_handoff",
            "evidence_gaps",
        ],
        min_length=1,
        description=(
            "Bounded support-only outputs requested from lotus-ai dpm_wave_pm_memo.pack@v1. "
            "Gateway forwards these labels as caller intent and does not allow outputs that "
            "approve trades, place orders, contact clients, score PMs, or invent missing evidence."
        ),
        examples=[["wave_pm_memo", "approval_checklist", "evidence_gaps"]],
    )
    audience: list[str] = Field(
        default_factory=lambda: ["portfolio_manager", "investment_control", "operations"],
        min_length=1,
        description=(
            "Intended human review audiences for the generated support memo. The lotus-ai pack "
            "still returns review-required evidence text; Gateway does not route the output to "
            "clients or operational execution systems."
        ),
        examples=[["portfolio_manager", "investment_control", "operations"]],
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


class DpmWaveMemoGatewayResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated across Gateway, lotus-manage, and lotus-ai.",
        examples=["corr-rfc41-wave-ai-pm-memo"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway BFF contract version for DPM wave AI memo handoff responses.",
        examples=["v1"],
    )
    source_service: str = Field(
        default="lotus-ai",
        description="Service that executed the governed workflow-pack run.",
        examples=["lotus-ai"],
    )
    evidence_source_service: str = Field(
        default="lotus-manage",
        description="Service that supplied the authoritative wave report-input evidence.",
        examples=["lotus-manage"],
    )
    manage_upstream_status: int = Field(
        description="HTTP status returned by lotus-manage for the wave report-input request.",
        examples=[200],
    )
    ai_upstream_status: int = Field(
        description="HTTP status returned by lotus-ai for workflow-pack execution.",
        examples=[200],
    )
    supportability: DpmWaveSupportability = Field(
        description=(
            "Gateway-normalized supportability summary derived only from manage-published wave "
            "report-input fields and carried into the lotus-ai guardrail request."
        )
    )
    wave_report_input: dict[str, object] = Field(
        description=(
            "Authoritative manage DpmWaveReportInput payload preserved for traceability. Gateway "
            "does not rewrite item evidence, source refs, hashes, approval posture, or proof-pack "
            "posture before calling lotus-ai."
        ),
        examples=[
            {
                "wave_id": "dwv_001",
                "report_input_ref": "report-input:dwv_001",
                "source_refs": ["lotus-manage:wave:dwv_001"],
            }
        ],
    )
    memo_request: dict[str, object] = Field(
        description=(
            "Bounded caller intent sent to lotus-ai. This object is support-only and excludes "
            "trade approval, order placement, client contact, PM scoring, and evidence invention."
        ),
        examples=[
            {
                "requested_outputs": ["wave_pm_memo", "approval_checklist"],
                "audience": ["portfolio_manager", "investment_control"],
            }
        ],
    )
    data: dict[str, object] = Field(
        description=(
            "lotus-ai workflow-pack execution response. Gateway preserves the AI authority "
            "payload and does not post-process generated memo content into execution actions."
        )
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
