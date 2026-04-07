from typing import Any, Literal

from pydantic import BaseModel, Field

from app.contracts.workbench import WorkbenchPartialFailure

RiskModuleState = Literal["ready", "partial", "unavailable", "blocked"]
RiskSupportabilityState = Literal["ready", "partial", "unavailable", "blocked"]


class WorkbenchRiskSupportabilityItem(BaseModel):
    key: str
    label: str
    state: RiskSupportabilityState
    reason: str | None = None
    source_service: str | None = None


class WorkbenchRiskMetadata(BaseModel):
    generated_at: str
    input_mode: Literal["stateful", "simulation"] = "stateful"
    methodology_version: str | None = None
    cache_status: Literal["hit", "miss", "bypass"] | None = None


class WorkbenchRiskMetric(BaseModel):
    key: str
    label: str
    value: float | None = None
    state: RiskModuleState = "ready"
    reason: str | None = None
    details: dict[str, Any] | None = None


class WorkbenchRiskPeriodResult(BaseModel):
    key: str
    label: str
    start_date: str
    end_date: str
    metrics: list[WorkbenchRiskMetric] = Field(default_factory=list)


class WorkbenchRiskSummaryPayload(BaseModel):
    periods: list[WorkbenchRiskPeriodResult] = Field(default_factory=list)


class WorkbenchConcentrationRiskProxy(BaseModel):
    hhi_current: float
    hhi_proposed: float
    hhi_delta: float


class WorkbenchSinglePositionConcentration(BaseModel):
    top_position_weight_current: float
    top_position_weight_proposed: float
    top_position_weight_delta: float
    top_n_cumulative_weight_current: float
    top_n_cumulative_weight_proposed: float
    top_n_cumulative_weight_delta: float
    top_n: int


class WorkbenchIssuerConcentration(BaseModel):
    hhi_current: float
    hhi_proposed: float
    hhi_delta: float
    top_issuer_weight_current: float
    top_issuer_weight_proposed: float
    top_issuer_weight_delta: float
    coverage_status: str
    covered_position_count_current: int
    covered_position_count_proposed: int
    total_position_count_current: int
    total_position_count_proposed: int
    note: str | None = None


class WorkbenchRiskConcentrationPayload(BaseModel):
    risk_proxy: WorkbenchConcentrationRiskProxy
    single_position_concentration: WorkbenchSinglePositionConcentration
    issuer_concentration: WorkbenchIssuerConcentration
    valuation_context: dict[str, Any] | None = None
    risk_metadata: dict[str, Any] | None = None


class WorkbenchRiskModuleEnvelope(BaseModel):
    correlation_id: str
    contract_version: str = "risk-workspace.v1"
    portfolio_id: str
    period: str
    as_of_date: str
    benchmark_code: str | None = None
    source_service: str = "lotus-risk"
    state: RiskModuleState
    payload: dict[str, Any] | None = None
    supportability: list[WorkbenchRiskSupportabilityItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    partial_failures: list[WorkbenchPartialFailure] = Field(default_factory=list)
    metadata: WorkbenchRiskMetadata


class WorkbenchRiskSummaryResponse(WorkbenchRiskModuleEnvelope):
    payload: WorkbenchRiskSummaryPayload | None = None


class WorkbenchRiskConcentrationResponse(WorkbenchRiskModuleEnvelope):
    payload: WorkbenchRiskConcentrationPayload | None = None
