from dataclasses import dataclass
from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class ManageMandateConstraintsSource(BaseModel):
    model_config = ConfigDict(extra="ignore")

    cash_band_min_weight: float = 0.0
    cash_band_max_weight: float = 1.0
    single_position_max_weight: float | None = None
    issuer_max_weight: float | None = None
    sector_max_weight: float | None = None
    region_max_weight: float | None = None
    currency_max_weight: float | None = None
    turnover_budget: float | None = None
    max_tracking_error: float | None = None


class ManageMandateReviewPolicySource(BaseModel):
    model_config = ConfigDict(extra="ignore")

    review_frequency: str = "QUARTERLY"
    last_review_date: date | None = None
    next_review_due_date: date | None = None


class ManageMandateLineageSource(BaseModel):
    model_config = ConfigDict(extra="ignore")

    product_name: str
    product_version: str
    source_system: str = "lotus-core"
    source_record_id: str | None = None
    data_quality_status: str | None = None
    latest_evidence_timestamp: str | None = None


class ManageMandateSource(BaseModel):
    model_config = ConfigDict(extra="ignore")

    mandate_id: str
    portfolio_id: str
    mandate_version: str
    as_of_date: date
    risk_profile: str
    constraints: ManageMandateConstraintsSource
    review_policy: ManageMandateReviewPolicySource
    source_lineage: list[ManageMandateLineageSource] = Field(default_factory=list)


class ManageMandateHealthDimensionSource(BaseModel):
    model_config = ConfigDict(extra="ignore")

    dimension: str
    state: str
    reason_code: str
    measured_value: float | str | int | None = None
    threshold_value: float | str | int | None = None


class ManageMandateHealthSource(BaseModel):
    model_config = ConfigDict(extra="ignore")

    health_snapshot_id: str
    mandate_id: str
    portfolio_id: str
    as_of_date: date
    health_state: str
    dimension_scores: list[ManageMandateHealthDimensionSource] = Field(default_factory=list)

    def dimension(self, key: str) -> ManageMandateHealthDimensionSource | None:
        return next((item for item in self.dimension_scores if item.dimension == key), None)


@dataclass(frozen=True)
class WorkbenchCashMeasureSource:
    value: float
    as_of_date: date


@dataclass(frozen=True)
class RiskMandateSources:
    mandate: ManageMandateSource | None
    health: ManageMandateHealthSource | None
    cash: WorkbenchCashMeasureSource | None
    mandate_failure_reason: str | None = None
    health_failure_reason: str | None = None
    cash_failure_reason: str | None = None
