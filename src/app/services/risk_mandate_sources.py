from dataclasses import dataclass
from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ManageMandateConstraintsSource(BaseModel):
    model_config = ConfigDict(extra="ignore")

    cash_band_min_weight: float | None = Field(  # monetary-float-allow
        default=None, ge=0, le=1
    )
    cash_band_max_weight: float | None = Field(  # monetary-float-allow
        default=None, ge=0, le=1
    )
    single_position_max_weight: float | None = Field(  # monetary-float-allow
        default=None, ge=0, le=1
    )
    issuer_max_weight: float | None = Field(  # monetary-float-allow
        default=None, ge=0, le=1
    )
    sector_max_weight: float | None = Field(  # monetary-float-allow
        default=None, ge=0, le=1
    )
    region_max_weight: float | None = Field(  # monetary-float-allow
        default=None, ge=0, le=1
    )
    currency_max_weight: float | None = Field(  # monetary-float-allow
        default=None, ge=0, le=1
    )
    turnover_budget: float | None = Field(  # monetary-float-allow
        default=None, ge=0, le=1
    )
    max_tracking_error: float | None = Field(  # monetary-float-allow
        default=None, ge=0, le=1
    )

    @model_validator(mode="after")
    def validate_cash_band(self) -> "ManageMandateConstraintsSource":
        if (
            self.cash_band_min_weight is not None
            and self.cash_band_max_weight is not None
            and self.cash_band_min_weight > self.cash_band_max_weight
        ):
            raise ValueError("cash mandate minimum must not exceed maximum")
        return self


class ManageMandateReviewPolicySource(BaseModel):
    model_config = ConfigDict(extra="ignore")

    review_frequency: str | None = None
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
    source_lineage: list[ManageMandateLineageSource] = Field(default_factory=list, max_length=32)


class ManageMandateHealthDimensionSource(BaseModel):
    model_config = ConfigDict(extra="ignore")

    dimension: str
    state: str
    reason_code: str
    measured_value: float | str | int | None = None  # monetary-float-allow
    threshold_value: float | str | int | None = None  # monetary-float-allow


class ManageMandateHealthSource(BaseModel):
    model_config = ConfigDict(extra="ignore")

    health_snapshot_id: str
    mandate_id: str
    portfolio_id: str
    as_of_date: date
    health_state: str
    dimension_scores: list[ManageMandateHealthDimensionSource] = Field(
        default_factory=list,
        max_length=32,
    )

    def dimension(self, key: str) -> ManageMandateHealthDimensionSource | None:
        return next((item for item in self.dimension_scores if item.dimension == key), None)


@dataclass(frozen=True)
class WorkbenchCashMeasureSource:
    value: float  # monetary-float-allow
    as_of_date: date


@dataclass(frozen=True)
class RiskMandateSources:
    mandate: ManageMandateSource | None
    health: ManageMandateHealthSource | None
    cash: WorkbenchCashMeasureSource | None
    mandate_failure_reason: str | None = None
    health_failure_reason: str | None = None
    cash_failure_reason: str | None = None
