from pydantic import BaseModel, Field


class FoundationPartialFailure(BaseModel):
    source_service: str = Field(
        description="Upstream service that returned a degraded or unavailable response.",
        examples=["lotus-report"],
    )
    error_code: str = Field(
        description="Gateway-preserved upstream error code or synthesized failure category.",
        examples=["HTTP_503"],
    )
    detail: str = Field(
        description="Operator-facing detail describing the degraded upstream dependency.",
        examples=["report unavailable"],
    )


class FoundationPortfolioCatalogItem(BaseModel):
    portfolio_id: str = Field(
        description="Stable portfolio identifier used to open the Foundation workspace.",
        examples=["PF_1001"],
    )
    display_name: str = Field(
        description="Advisor-facing portfolio label shown in selectors and page headers.",
        examples=["Alpha Growth"],
    )
    base_currency: str = Field(
        description="Portfolio base currency code.",
        examples=["USD"],
    )
    client_id: str | None = Field(
        default=None,
        description="Client identifier associated with the portfolio when available.",
        examples=["CIF_1001"],
    )
    booking_center_code: str | None = Field(
        default=None,
        description="Booking center code for the portfolio when available.",
        examples=["SG"],
    )


class FoundationPortfolioCatalogResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated through the gateway boundary.",
        examples=["corr_1"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway contract version for the Foundation catalog response.",
        examples=["v1"],
    )
    items: list[FoundationPortfolioCatalogItem] = Field(
        default_factory=list,
        description="Selector-ready portfolio entries available to the Foundation shell.",
    )


class FoundationPortfolioIdentity(BaseModel):
    portfolio_id: str = Field(
        description="Stable portfolio identifier for the current workspace.",
        examples=["PF_1001"],
    )
    display_name: str = Field(
        description="Advisor-facing portfolio name for the workspace header.",
        examples=["Alpha Growth"],
    )
    client_id: str | None = Field(
        default=None,
        description="Client identifier associated with the portfolio when available.",
        examples=["CIF_1001"],
    )
    base_currency: str = Field(
        description="Portfolio base currency code.",
        examples=["USD"],
    )
    booking_center_code: str | None = Field(
        default=None,
        description="Booking center code for the portfolio when available.",
        examples=["SG"],
    )


class FoundationPortfolioSummary(BaseModel):
    market_value_base: float = Field(
        description="Total market value of the portfolio in base currency.",
        examples=[1000.0],
    )
    total_cash_base: float = Field(
        description="Total cash value in base currency included in the portfolio snapshot.",
        examples=[100.0],
    )
    cash_weight_pct: float = Field(
        description="Cash share of total market value expressed in percentage points.",
        examples=[10.0],
    )
    position_count: int = Field(
        description="Number of baseline positions in the snapshot.",
        examples=[3],
    )


class FoundationAllocationBucket(BaseModel):
    asset_class: str = Field(
        description="Asset-class grouping label sourced from core enrichment.",
        examples=["Equity"],
    )
    position_count: int = Field(
        description="Number of positions in the allocation bucket.",
        examples=[2],
    )
    market_value_base: float | None = Field(
        default=None,
        description="Bucket market value in portfolio base currency.",
        examples=[900.0],
    )
    weight_pct: float | None = Field(
        default=None,
        description="Bucket weight as a percentage of total market value.",
        examples=[90.0],
    )


class FoundationTopPosition(BaseModel):
    security_id: str = Field(
        description="Stable security identifier for the holding.",
        examples=["EQ_1"],
    )
    display_name: str = Field(
        description="Advisor-facing instrument label for the holding.",
        examples=["Global Equity Fund"],
    )
    asset_class: str | None = Field(
        default=None,
        description="Asset-class label for the holding when available.",
        examples=["Equity"],
    )
    market_value_base: float | None = Field(
        default=None,
        description="Holding market value in portfolio base currency.",
        examples=[600.0],
    )
    weight_pct: float | None = Field(
        default=None,
        description="Holding weight as a percentage of total market value.",
        examples=[60.0],
    )


class FoundationPerformanceSummary(BaseModel):
    period: str = Field(
        description="Performance horizon used for the first-paint summary return.",
        examples=["YTD"],
    )
    return_pct: float | None = Field(
        default=None,
        description="Net portfolio return for the requested period in percentage points.",
        examples=[4.2],
    )


class FoundationRebalanceSummary(BaseModel):
    status: str = Field(
        description="Latest rebalance workflow status when a run is available.",
        examples=["PENDING_REVIEW"],
    )
    last_run_at_utc: str | None = Field(
        default=None,
        description="UTC timestamp for the latest rebalance run creation time.",
        examples=["2026-03-25T09:00:00Z"],
    )
    last_rebalance_run_id: str | None = Field(
        default=None,
        description="Latest rebalance run identifier when available.",
        examples=["rr_100"],
    )


class FoundationReportingReadiness(BaseModel):
    status: str = Field(
        description="Reporting readiness posture for the portfolio snapshot.",
        examples=["READY"],
    )
    generated_at_utc: str | None = Field(
        default=None,
        description="UTC timestamp of the reporting snapshot generation when available.",
        examples=["2026-03-25T10:00:00Z"],
    )
    row_count: int = Field(
        default=0,
        description="Number of rows returned by the reporting snapshot.",
        examples=[2],
    )


class FoundationWorkspaceReadiness(BaseModel):
    has_positions: bool = Field(
        description="Whether the portfolio snapshot currently contains baseline positions.",
        examples=[True],
    )
    reporting: FoundationReportingReadiness = Field(
        description="Reporting snapshot readiness for the Foundation workspace.",
    )


class FoundationWorkflowLaunchCue(BaseModel):
    key: str = Field(
        description="Stable workflow cue identifier.",
        examples=["performance"],
    )
    label: str = Field(
        description="Advisor-facing workflow label.",
        examples=["Open Performance"],
    )
    href: str = Field(
        description="Frontend route to the next strategic workspace.",
        examples=["/app/performance"],
    )


class FoundationEvidenceSummary(BaseModel):
    status: str = Field(
        description="Advisor-facing degradation status for the Foundation workspace boundary.",
        examples=["ready"],
    )
    summary: str = Field(
        description=(
            "Short explanation of whether the workspace is fully ready or partially degraded."
        ),
        examples=["Foundation workspace inputs are ready for advisor use."],
    )
    warning_count: int = Field(
        default=0,
        description="Number of workspace warnings carried alongside the response.",
        examples=[0],
    )
    partial_failure_count: int = Field(
        default=0,
        description="Number of upstream partial failures preserved in the response.",
        examples=[0],
    )
    affected_sources: list[str] = Field(
        default_factory=list,
        description="Unique upstream services contributing to the degraded evidence posture.",
        examples=[["lotus-performance", "lotus-report"]],
    )


class FoundationWorkspaceResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated through the gateway boundary.",
        examples=["corr_1"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway contract version for the Foundation workspace response.",
        examples=["v1"],
    )
    as_of_date: str = Field(
        description="Business date of the workspace snapshot in YYYY-MM-DD format.",
        examples=["2026-03-25"],
    )
    portfolio: FoundationPortfolioIdentity = Field(
        description="Portfolio identity block for the current workspace.",
    )
    summary: FoundationPortfolioSummary = Field(
        description="First-paint portfolio valuation summary for the Foundation workspace.",
    )
    allocations: list[FoundationAllocationBucket] = Field(
        default_factory=list,
        description="Allocation shape grouped by asset class.",
    )
    top_positions: list[FoundationTopPosition] = Field(
        default_factory=list,
        description="Largest holdings ranked by market value for quick portfolio inspection.",
    )
    performance: FoundationPerformanceSummary | None = Field(
        default=None,
        description="YTD performance snapshot when lotus-performance is available.",
    )
    rebalance: FoundationRebalanceSummary | None = Field(
        default=None,
        description="Latest rebalance workflow summary when lotus-manage is available.",
    )
    readiness: FoundationWorkspaceReadiness = Field(
        description="Readiness cues for holdings and reporting posture.",
    )
    workflow_cues: list[FoundationWorkflowLaunchCue] = Field(
        default_factory=list,
        description="Strategic next-step links into deeper product workspaces.",
    )
    evidence: FoundationEvidenceSummary = Field(
        description="Advisor-facing evidence posture for degraded-but-usable behavior.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Machine-readable workspace warnings preserved by gateway.",
        examples=[["FOUNDATION_REPORTING_UNAVAILABLE"]],
    )
    partial_failures: list[FoundationPartialFailure] = Field(
        default_factory=list,
        description="Upstream partial failures preserved for diagnostics and support review.",
    )
