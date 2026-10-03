from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

AllocationContributorType = Literal["direct_position", "look_through_component"]
LookThroughMode = Literal["direct_only", "prefer_look_through"]
AllocationValuationCoverageState = Literal[
    "COMPLETE", "MEASURED_ZERO", "CARRY_FORWARD", "LOADED_EMPTY", "PARTIAL", "UNAVAILABLE"
]
TRUSTED_ALLOCATION_VALUATION_COVERAGE_STATES = frozenset(
    {"COMPLETE", "MEASURED_ZERO", "CARRY_FORWARD", "LOADED_EMPTY"}
)
DEGRADED_ALLOCATION_VALUATION_COVERAGE_STATES = frozenset({"PARTIAL", "UNAVAILABLE"})


class SourceAllocationValuationCoverage(BaseModel):
    coverage_state: AllocationValuationCoverageState
    coverage_reason: str = Field(min_length=1, max_length=128)
    snapshot_row_count: int = Field(ge=0)
    expected_open_position_count: int = Field(ge=0)
    valued_position_count: int = Field(ge=0)
    unvalued_position_count: int = Field(ge=0)

    model_config = ConfigDict(extra="ignore")

    @model_validator(mode="after")
    def validate_count_coherence(self) -> "SourceAllocationValuationCoverage":
        observed_partition = self.valued_position_count + self.unvalued_position_count
        if observed_partition != self.snapshot_row_count:
            raise ValueError("valued and unvalued counts must partition snapshot rows")
        if self.coverage_state in {"COMPLETE", "MEASURED_ZERO", "CARRY_FORWARD"}:
            if self.unvalued_position_count != 0:
                raise ValueError(
                    "complete allocation valuation coverage cannot contain unvalued rows"
                )
            if self.snapshot_row_count == 0:
                raise ValueError("non-empty trusted allocation coverage requires snapshot rows")
            if self.snapshot_row_count < self.expected_open_position_count:
                raise ValueError("trusted allocation coverage cannot omit expected open positions")
        if self.coverage_state == "LOADED_EMPTY" and any(
            (
                self.snapshot_row_count,
                self.expected_open_position_count,
                self.valued_position_count,
                self.unvalued_position_count,
            )
        ):
            raise ValueError("loaded-empty allocation coverage requires zero counts")
        if self.coverage_state == "UNAVAILABLE" and any(
            (self.snapshot_row_count, self.valued_position_count, self.unvalued_position_count)
        ):
            raise ValueError("unavailable allocation coverage cannot contain observed rows")
        return self


class SourceNumericOutputPolicyLineage(BaseModel):
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    precision: int = Field(ge=1)
    scale: int = Field(ge=0)
    working_precision: int = Field(ge=1)
    rounding: str = Field(min_length=1)

    model_config = ConfigDict(extra="ignore")

    @field_validator("name", "version", "rounding")
    @classmethod
    def require_nonblank_identity(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("numeric-output policy identity fields must be nonblank")
        return value

    @model_validator(mode="after")
    def validate_numeric_shape(self) -> "SourceNumericOutputPolicyLineage":
        if self.scale > self.precision:
            raise ValueError("numeric-output policy scale cannot exceed precision")
        if self.working_precision < self.precision:
            raise ValueError("numeric-output working precision cannot be below output precision")
        return self


class SourceCalculationLineage(BaseModel):
    algorithm_id: str = Field(min_length=1)
    algorithm_version: int = Field(ge=1)
    intermediate_precision: int = Field(ge=1)
    input_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    calculation_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    output_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    numeric_output_policy: SourceNumericOutputPolicyLineage | None = None

    model_config = ConfigDict(extra="ignore")

    @field_validator("algorithm_id")
    @classmethod
    def require_nonblank_algorithm_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("allocation algorithm identity must be nonblank")
        return value


class SourceAllocationEvidence(BaseModel):
    total_market_value_reporting_currency: Decimal | None
    valuation_coverage: SourceAllocationValuationCoverage
    calculation_lineage: SourceCalculationLineage

    model_config = ConfigDict(extra="ignore")

    @model_validator(mode="after")
    def validate_total_matches_valuation_coverage(self) -> "SourceAllocationEvidence":
        coverage_state = self.valuation_coverage.coverage_state
        has_known_total = self.total_market_value_reporting_currency is not None
        if coverage_state in DEGRADED_ALLOCATION_VALUATION_COVERAGE_STATES and has_known_total:
            raise ValueError("degraded allocation valuation coverage requires an unknown total")
        if coverage_state in TRUSTED_ALLOCATION_VALUATION_COVERAGE_STATES and not has_known_total:
            raise ValueError("trusted allocation valuation coverage requires a known total")
        if coverage_state in {"MEASURED_ZERO", "LOADED_EMPTY"} and (
            self.total_market_value_reporting_currency != Decimal("0")
        ):
            raise ValueError("zero allocation valuation coverage requires a zero total")
        return self


class SourceAllocationContributor(BaseModel):
    contributor_type: AllocationContributorType
    portfolio_id: str
    security_id: str
    booked_security_id: str
    source_snapshot_id: int
    component_record_id: int | None
    component_weight: Decimal | None
    component_effective_from: date | None
    component_effective_to: date | None
    component_source_system: str | None
    component_source_record_id: str | None
    market_value_reporting_currency: Decimal | None
    bucket_weight: Decimal | None

    model_config = ConfigDict(extra="ignore")


class SourceAllocationBucket(BaseModel):
    dimension_value: str
    market_value_reporting_currency: Decimal | None
    weight: Decimal | None
    position_count: int = Field(ge=0)
    contributor_count: int = Field(ge=0)
    contributors: list[SourceAllocationContributor]
    contributors_truncated: bool
    omitted_market_value_reporting_currency: Decimal | None

    model_config = ConfigDict(extra="ignore")

    @model_validator(mode="after")
    def validate_contributor_reconciliation(self) -> "SourceAllocationBucket":
        if len(self.contributors) > self.contributor_count:
            raise ValueError("contributors cannot exceed contributor_count")
        if not self.contributors_truncated and len(self.contributors) != self.contributor_count:
            raise ValueError("untruncated contributors must contain every source row")
        bucket_value_known = self.market_value_reporting_currency is not None
        residual_known = self.omitted_market_value_reporting_currency is not None
        if bucket_value_known != residual_known:
            raise ValueError("bucket value and omitted residual must share null qualification")
        bucket_weight_denominator_known = (
            self.market_value_reporting_currency is not None
            and self.market_value_reporting_currency != Decimal("0")
        )
        if any(
            (contributor.bucket_weight is not None) != bucket_weight_denominator_known
            for contributor in self.contributors
        ):
            raise ValueError(
                "contributor bucket weights require a known nonzero bucket denominator"
            )
        if bucket_value_known and residual_known:
            bucket_value = self.market_value_reporting_currency
            omitted_residual = self.omitted_market_value_reporting_currency
            if bucket_value is None or omitted_residual is None:
                raise ValueError("known bucket qualification requires numeric values")
            retained_values = [item.market_value_reporting_currency for item in self.contributors]
            if any(value is None for value in retained_values):
                raise ValueError("known bucket value cannot contain unknown contributor value")
            retained_value = sum(
                (value for value in retained_values if value is not None),
                Decimal("0"),
            )
            if retained_value + omitted_residual != bucket_value:
                raise ValueError("contributors and omitted residual must reconcile to bucket value")
        return self


class SourceAllocationView(BaseModel):
    dimension: str
    total_market_value_reporting_currency: Decimal | None
    buckets: list[SourceAllocationBucket]

    model_config = ConfigDict(extra="ignore")


class SourceAllocationLookThrough(BaseModel):
    requested_mode: LookThroughMode
    applied_mode: LookThroughMode
    supported: bool
    decomposed_position_count: int = Field(ge=0)
    limitation_reason: str | None

    model_config = ConfigDict(extra="ignore")


class SourceAllocationScope(BaseModel):
    portfolio_id: str = Field(min_length=1)

    model_config = ConfigDict(extra="ignore")

    @field_validator("portfolio_id")
    @classmethod
    def require_nonblank_portfolio_id(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("allocation scope portfolio_id must be nonblank")
        return normalized


def _validate_coverage_view_content(
    views: list[SourceAllocationView],
    coverage_state: AllocationValuationCoverageState,
    total_market_value_reporting_currency: Decimal | None,
) -> None:
    buckets = [bucket for view in views for bucket in view.buckets]
    if coverage_state in DEGRADED_ALLOCATION_VALUATION_COVERAGE_STATES and any(
        bucket.weight is not None for bucket in buckets
    ):
        raise ValueError("degraded allocation valuation coverage requires unknown weights")
    if coverage_state in {"COMPLETE", "MEASURED_ZERO", "CARRY_FORWARD"} and any(
        bucket.market_value_reporting_currency is None for bucket in buckets
    ):
        raise ValueError("trusted allocation valuation coverage requires known bucket values")
    trusted_weight_denominator_known = (
        coverage_state in {"COMPLETE", "MEASURED_ZERO", "CARRY_FORWARD"}
        and total_market_value_reporting_currency is not None
        and total_market_value_reporting_currency != Decimal("0")
    )
    if coverage_state in TRUSTED_ALLOCATION_VALUATION_COVERAGE_STATES and any(
        (bucket.weight is not None) != trusted_weight_denominator_known for bucket in buckets
    ):
        raise ValueError(
            "trusted allocation bucket weights require a known nonzero portfolio denominator"
        )
    if coverage_state in {"LOADED_EMPTY", "UNAVAILABLE"} and buckets:
        raise ValueError("empty allocation coverage cannot contain buckets")
    if coverage_state in TRUSTED_ALLOCATION_VALUATION_COVERAGE_STATES and any(
        sum(
            (bucket.market_value_reporting_currency or Decimal("0") for bucket in view.buckets),
            Decimal("0"),
        )
        != view.total_market_value_reporting_currency
        for view in views
    ):
        raise ValueError("allocation view buckets must reconcile to the declared total")


def _validate_contributor_portfolios(
    views: list[SourceAllocationView],
    portfolio_id: str,
) -> None:
    if any(
        contributor.portfolio_id != portfolio_id
        for view in views
        for bucket in view.buckets
        for contributor in bucket.contributors
    ):
        raise ValueError("allocation contributors must match the source portfolio scope")


class SourceAllocationPayload(SourceAllocationEvidence):
    scope_type: Literal["portfolio"]
    scope: SourceAllocationScope
    resolved_as_of_date: date
    reporting_currency: str = Field(pattern=r"^[A-Z]{3}$")
    look_through: SourceAllocationLookThrough | None = None
    views: list[SourceAllocationView] | None = None

    @field_validator("reporting_currency", mode="before")
    @classmethod
    def normalize_reporting_currency(cls, value: object) -> object:
        return value.strip().upper() if isinstance(value, str) else value

    @model_validator(mode="after")
    def validate_view_totals_match_evidence(self) -> "SourceAllocationPayload":
        views = self.views or []
        expected_total = self.total_market_value_reporting_currency
        if any(view.total_market_value_reporting_currency != expected_total for view in views):
            raise ValueError("allocation view totals must match full-scope source evidence")
        _validate_coverage_view_content(
            views,
            self.valuation_coverage.coverage_state,
            self.total_market_value_reporting_currency,
        )
        _validate_contributor_portfolios(views, self.scope.portfolio_id)
        return self


__all__ = [
    "AllocationValuationCoverageState",
    "LookThroughMode",
    "SourceAllocationEvidence",
    "SourceAllocationBucket",
    "SourceAllocationContributor",
    "SourceAllocationLookThrough",
    "SourceAllocationPayload",
    "SourceAllocationScope",
    "SourceAllocationValuationCoverage",
    "SourceAllocationView",
]
