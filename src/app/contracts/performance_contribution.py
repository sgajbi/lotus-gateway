from pydantic import BaseModel, Field

__all__ = [
    "ContributionLevelView",
    "ContributionPositionView",
    "ContributionRowView",
    "ContributionSmoothingEvidenceView",
    "ContributionSourceEconomicsEvidenceView",
    "ContributionSummaryView",
]


class ContributionRowView(BaseModel):
    key_label: str
    contribution_pct: float
    weight_avg_pct: float | None = None
    total_return_pct: float | None = None
    local_contribution_pct: float | None = None
    fx_contribution_pct: float | None = None
    is_other: bool = False


class ContributionPositionView(BaseModel):
    position_id: str
    contribution_pct: float
    weight_avg_pct: float | None = None
    total_return_pct: float | None = None
    local_contribution_pct: float | None = None
    fx_contribution_pct: float | None = None


class ContributionLevelView(BaseModel):
    level: int
    name: str
    rows: list[ContributionRowView] = Field(default_factory=list)
    total_contribution_pct: float | None = None
    total_weight_avg_pct: float | None = None
    total_portfolio_return_pct: float | None = None


class ContributionSmoothingEvidenceView(BaseModel):
    status: str | None = None
    reason_codes: list[str] = Field(default_factory=list)
    raw_contribution_pct: float | None = None
    final_contribution_pct: float | None = None
    linked_return_pct: float | None = None
    smoothing_residual_pct: float | None = None


class ContributionSourceEconomicsEvidenceView(BaseModel):
    status: str | None = None
    reason_codes: list[str] = Field(default_factory=list)
    source_contracts: list[str] = Field(default_factory=list)
    available_economics: list[str] = Field(default_factory=list)
    unsupported_economics: list[str] = Field(default_factory=list)
    degraded_economics: list[str] = Field(default_factory=list)
    source_snapshot_count: int | None = None


class ContributionSummaryView(BaseModel):
    metric_basis: str
    weighting_scheme: str | None = None
    portfolio_contribution_pct: float | None = None
    total_portfolio_return_pct: float | None = None
    coverage_mv_pct: float | None = None
    portfolio_local_contribution_pct: float | None = None
    portfolio_fx_contribution_pct: float | None = None
    position_rows: list[ContributionPositionView] = Field(default_factory=list)
    levels: list[ContributionLevelView] = Field(default_factory=list)
    smoothing_evidence: ContributionSmoothingEvidenceView | None = None
    source_economics_evidence: ContributionSourceEconomicsEvidenceView | None = None
