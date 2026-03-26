from pydantic import BaseModel, Field


class FoundationPartialFailure(BaseModel):
    source_service: str
    error_code: str
    detail: str


class FoundationPortfolioCatalogItem(BaseModel):
    portfolio_id: str
    display_name: str
    base_currency: str
    client_id: str | None = None
    booking_center_code: str | None = None


class FoundationPortfolioCatalogResponse(BaseModel):
    correlation_id: str
    contract_version: str = Field(default="v1")
    items: list[FoundationPortfolioCatalogItem] = Field(default_factory=list)


class FoundationPortfolioIdentity(BaseModel):
    portfolio_id: str
    display_name: str
    client_id: str | None = None
    base_currency: str
    booking_center_code: str | None = None


class FoundationPortfolioSummary(BaseModel):
    market_value_base: float
    total_cash_base: float
    cash_weight_pct: float
    position_count: int


class FoundationAllocationBucket(BaseModel):
    asset_class: str
    position_count: int
    market_value_base: float | None = None
    weight_pct: float | None = None


class FoundationTopPosition(BaseModel):
    security_id: str
    instrument_name: str
    asset_class: str | None = None
    quantity: float
    market_value_base: float | None = None
    weight_pct: float | None = None


class FoundationPerformanceSummary(BaseModel):
    period: str
    return_pct: float | None = None


class FoundationRebalanceSummary(BaseModel):
    status: str
    last_run_at_utc: str | None = None
    last_rebalance_run_id: str | None = None


class FoundationReportingReadiness(BaseModel):
    status: str
    generated_at_utc: str | None = None
    row_count: int = 0


class FoundationWorkspaceReadiness(BaseModel):
    has_positions: bool
    reporting: FoundationReportingReadiness


class FoundationWorkflowLaunchCue(BaseModel):
    key: str
    label: str
    href: str


class FoundationWorkspaceResponse(BaseModel):
    correlation_id: str
    contract_version: str = Field(default="v1")
    as_of_date: str
    portfolio: FoundationPortfolioIdentity
    summary: FoundationPortfolioSummary
    allocations: list[FoundationAllocationBucket] = Field(default_factory=list)
    top_positions: list[FoundationTopPosition] = Field(default_factory=list)
    performance: FoundationPerformanceSummary | None = None
    rebalance: FoundationRebalanceSummary | None = None
    readiness: FoundationWorkspaceReadiness
    workflow_cues: list[FoundationWorkflowLaunchCue] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    partial_failures: list[FoundationPartialFailure] = Field(default_factory=list)
