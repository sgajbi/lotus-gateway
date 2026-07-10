from pydantic import BaseModel, Field


class PortfolioProfile(BaseModel):
    status: str | None = Field(
        default=None,
        description="Optional upstream portfolio status.",
        examples=["ACTIVE"],
    )
    portfolio_type: str | None = Field(
        default=None,
        description="Optional portfolio mandate or operating type.",
        examples=["ADVISORY"],
    )
    risk_exposure: str | None = Field(
        default=None,
        description=(
            "Optional risk-exposure classification returned by the source portfolio record."
        ),
        examples=["Moderate Growth"],
    )
    investment_time_horizon: str | None = Field(
        default=None,
        description="Optional investment horizon associated with the portfolio mandate.",
        examples=["Long Term"],
    )
    objective: str | None = Field(
        default=None,
        description="Optional investment objective associated with the portfolio mandate.",
        examples=["Long-term capital appreciation."],
    )
    is_leverage_allowed: bool | None = Field(
        default=None,
        description="Whether leverage is permitted for the portfolio when the source exposes it.",
        examples=[False],
    )
    advisor_id: str | None = Field(
        default=None,
        description="Optional advisor identifier associated with the portfolio.",
        examples=["ADV_1001"],
    )
    open_date: str | None = Field(
        default=None,
        description="Optional portfolio open date in YYYY-MM-DD format.",
        examples=["2024-01-15"],
    )
    close_date: str | None = Field(
        default=None,
        description="Optional portfolio close date in YYYY-MM-DD format.",
        examples=["2026-03-31"],
    )


class PortfolioRebalanceSupportabilitySummary(BaseModel):
    feature_key: str = Field(
        default="manage.observability.action_register_supportability",
        description=(
            "Capability key for the manage action-register supportability posture carried "
            "through the portfolio workspace contract."
        ),
        examples=["manage.observability.action_register_supportability"],
    )
    state: str = Field(
        description="Manage action-register supportability state.",
        examples=["healthy"],
    )
    reason: str | None = Field(
        default=None,
        description="Machine-readable reason for degraded or unavailable supportability.",
        examples=["action_register_current"],
    )
    freshness_bucket: str | None = Field(
        default=None,
        description="Freshness bucket reported by lotus-manage for action-register evidence.",
        examples=["fresh"],
    )
    run_count: int | None = Field(
        default=None,
        description="Count of rebalance runs considered by the supportability summary.",
        examples=[4],
    )
    operation_count: int | None = Field(
        default=None,
        description="Count of action-register operations considered by the summary.",
        examples=[12],
    )
    workflow_decision_count: int | None = Field(
        default=None,
        description="Count of workflow decisions considered by the supportability summary.",
        examples=[3],
    )


class PortfolioRebalanceSummary(BaseModel):
    status: str = Field(
        description="Latest rebalance workflow status returned by lotus-manage or decisioning.",
        examples=["PENDING_REVIEW"],
    )
    last_run_at_utc: str | None = Field(
        default=None,
        description="UTC timestamp of the latest rebalance workflow run associated with the book.",
        examples=["2026-03-27T12:00:00Z"],
    )
    last_rebalance_run_id: str | None = Field(
        default=None,
        description="Identifier of the latest rebalance run when an upstream run exists.",
        examples=["rr_100"],
    )
    supportability: PortfolioRebalanceSupportabilitySummary | None = Field(
        default=None,
        description=(
            "Source-backed lotus-manage action-register supportability posture used by "
            "operators to understand whether rebalance action evidence is current."
        ),
    )


class PortfolioReportingReadiness(BaseModel):
    status: str = Field(
        description="Reporting readiness posture returned or derived for the portfolio.",
        examples=["READY"],
    )
    generated_at_utc: str | None = Field(
        default=None,
        description="Optional UTC timestamp of the most recent reporting output generation.",
        examples=["2026-03-27T12:00:00Z"],
    )
    row_count: int = Field(
        default=0,
        description="Count of reporting rows currently available for the portfolio snapshot.",
        examples=[3],
    )


class PortfolioOperationalReadiness(BaseModel):
    business_date: str | None = Field(
        default=None,
        description="Current business date used by the operational support overview.",
        examples=["2026-03-27"],
    )
    latest_booked_transaction_date: str | None = Field(
        default=None,
        description="Most recent booked transaction date available for the portfolio.",
        examples=["2026-03-27"],
    )
    latest_booked_position_snapshot_date: str | None = Field(
        default=None,
        description="Most recent booked position snapshot date available for the portfolio.",
        examples=["2026-03-27"],
    )
    publish_allowed: bool | None = Field(
        default=None,
        description=(
            "Whether the current operational posture allows publication or downstream processing."
        ),
        examples=[True],
    )
    controls_blocking: bool | None = Field(
        default=None,
        description=(
            "Whether blocking controls are preventing publication or downstream processing."
        ),
        examples=[False],
    )
    active_reprocessing_keys: int | None = Field(
        default=None,
        description="Count of active reprocessing keys affecting the portfolio when available.",
        examples=[0],
    )
    stale_reprocessing_keys: int | None = Field(
        default=None,
        description="Count of stale reprocessing keys affecting the portfolio when available.",
        examples=[0],
    )
    failed_valuation_jobs_within_window: int | None = Field(
        default=None,
        description=(
            "Count of failed valuation jobs observed within the support window when available."
        ),
        examples=[0],
    )
    failed_aggregation_jobs_within_window: int | None = Field(
        default=None,
        description=(
            "Count of failed aggregation jobs observed within the support window when available."
        ),
        examples=[0],
    )
