from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

PortfolioLookThroughMode = Literal["direct_only", "prefer_look_through"]
PortfolioAllocationValuationCoverageState = Literal[
    "COMPLETE",
    "MEASURED_ZERO",
    "CARRY_FORWARD",
    "LOADED_EMPTY",
    "PARTIAL",
    "UNAVAILABLE",
]

__all__ = [
    "PortfolioAllocationContributor",
    "PortfolioAllocationCalculationLineage",
    "PortfolioAllocationLookThroughCapability",
    "PortfolioAllocationNumericOutputPolicy",
    "PortfolioAllocationValuationCoverage",
    "PortfolioLookThroughMode",
]


class _StrictPortfolioAllocationModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PortfolioAllocationContributor(_StrictPortfolioAllocationModel):
    contributor_type: Literal["direct_position", "look_through_component"] = Field(
        description=(
            "Source-owned contributor posture: direct_position for a booked holding or "
            "look_through_component for a decomposed exposure."
        ),
        examples=["look_through_component"],
    )
    portfolio_id: str = Field(
        description="Portfolio that owns the booked position.",
        examples=["PB_SG_GLOBAL_BAL_001"],
    )
    security_id: str = Field(
        description="Contributing security identifier; component security for look-through rows.",
        examples=["ETF_US_EQUITY_001"],
    )
    booked_security_id: str = Field(
        description="Booked parent-position security; equal to security_id for direct rows.",
        examples=["FUND_GLOBAL_001"],
    )
    source_snapshot_id: int = Field(
        description="Exact Core daily-position snapshot used for the booked value.",
        examples=[101],
    )
    component_record_id: int | None = Field(
        default=None,
        description="Core look-through component record; null for direct positions.",
        examples=[501],
    )
    component_weight: Decimal | None = Field(
        default=None,
        description="Source-owned parent-to-component weight; null for direct positions.",
        examples=["0.600000"],
    )
    component_effective_from: date | None = Field(
        default=None,
        description="Inclusive effective date of the source component record.",
        examples=["2026-01-01"],
    )
    component_effective_to: date | None = Field(
        default=None,
        description="Inclusive expiry date of the source component record, when present.",
        examples=["2026-12-31"],
    )
    component_source_system: str | None = Field(
        default=None,
        description="Source system that supplied the component record, when available.",
        examples=["fund-master"],
    )
    component_source_record_id: str | None = Field(
        default=None,
        description="Source-system component record identity, when available.",
        examples=["FUND_GLOBAL_001-ETF_US_EQUITY_001"],
    )
    market_value_reporting_currency: Decimal | None = Field(
        ...,
        description=(
            "Signed source contribution value in the effective reporting currency, or null "
            "when Core reports unavailable or unusable valuation."
        ),
        examples=["600.00"],
    )
    bucket_weight: Decimal | None = Field(
        default=None,
        description=(
            "Signed source contribution divided by the bucket value; null when the bucket nets "
            "to zero."
        ),
        examples=["0.600000"],
    )


class PortfolioAllocationLookThroughCapability(_StrictPortfolioAllocationModel):
    requested_mode: PortfolioLookThroughMode = Field(
        description="Look-through mode requested by the consumer for the allocation query.",
        examples=["prefer_look_through"],
    )
    effective_mode: PortfolioLookThroughMode = Field(
        description="Look-through mode actually applied by the upstream allocation service.",
        examples=["direct_only"],
    )
    applied: bool = Field(
        description="Whether the requested look-through expansion was applied in the response.",
        examples=[False],
    )
    supported: bool = Field(
        default=False,
        description="Whether Core had source-owned look-through decomposition available.",
        examples=[True],
    )
    decomposed_position_count: int = Field(
        default=0,
        description="Number of parent positions decomposed by Core.",
        examples=[2],
    )
    limitation_reason: str | None = Field(
        default=None,
        description="Source explanation when look-through was unavailable or only partial.",
        examples=["Remaining positions stayed at direct-holding level."],
    )


class PortfolioAllocationValuationCoverage(_StrictPortfolioAllocationModel):
    coverage_state: PortfolioAllocationValuationCoverageState = Field(
        description="Core-owned allocation valuation coverage classification.",
        examples=["PARTIAL"],
    )
    coverage_reason: str = Field(
        min_length=1,
        max_length=128,
        description="Bounded Core-owned reason for the valuation coverage classification.",
        examples=["market_value_missing"],
    )
    snapshot_row_count: int = Field(
        ge=0,
        description="Latest open-position snapshot rows observed by Core.",
        examples=[2],
    )
    expected_open_position_count: int = Field(
        ge=0,
        description="Expected open source positions used by Core to assess coverage.",
        examples=[2],
    )
    valued_position_count: int = Field(
        ge=0,
        description="Observed rows with usable valuation status and a monetary value.",
        examples=[1],
    )
    unvalued_position_count: int = Field(
        ge=0,
        description="Observed rows with missing value or unusable valuation status.",
        examples=[1],
    )


class PortfolioAllocationNumericOutputPolicy(_StrictPortfolioAllocationModel):
    name: str = Field(
        min_length=1,
        description="Stable Core-owned numeric output policy name.",
        examples=["allocation-output"],
    )
    version: str = Field(
        min_length=1,
        description="Exact Core-owned numeric output policy version.",
        examples=["1.0.0"],
    )
    precision: int = Field(
        ge=1,
        description="Maximum decimal digits accepted at the Core output boundary.",
        examples=[18],
    )
    scale: int = Field(
        ge=0,
        description="Maximum fractional decimal digits accepted at the Core output boundary.",
        examples=[10],
    )
    working_precision: int = Field(
        ge=1,
        description="Decimal precision used for Core intermediate arithmetic.",
        examples=[64],
    )
    rounding: str = Field(
        min_length=1,
        description="Explicit decimal rounding mode used at the Core output boundary.",
        examples=["ROUND_HALF_EVEN"],
    )

    @field_validator("name", "version", "rounding")
    @classmethod
    def require_nonblank_identity(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("numeric-output policy identity fields must be nonblank")
        return value

    @model_validator(mode="after")
    def validate_numeric_shape(self) -> "PortfolioAllocationNumericOutputPolicy":
        if self.scale > self.precision:
            raise ValueError("numeric-output policy scale cannot exceed precision")
        if self.working_precision < self.precision:
            raise ValueError("numeric-output working precision cannot be below output precision")
        return self


class PortfolioAllocationCalculationLineage(_StrictPortfolioAllocationModel):
    algorithm_id: str = Field(
        min_length=1,
        description="Stable Core-owned allocation algorithm identity.",
        examples=["PORTFOLIO_ALLOCATION"],
    )
    algorithm_version: int = Field(
        ge=1,
        description="Exact Core allocation algorithm version.",
        examples=[1],
    )
    intermediate_precision: int = Field(
        ge=1,
        description="Decimal precision used by Core during allocation calculation.",
        examples=[28],
    )
    input_content_hash: str = Field(
        pattern=r"^[0-9a-f]{64}$",
        description="Core SHA-256 identity for normalized allocation inputs.",
        examples=["a" * 64],
    )
    calculation_content_hash: str = Field(
        pattern=r"^[0-9a-f]{64}$",
        description="Core SHA-256 identity for the allocation calculation policy.",
        examples=["b" * 64],
    )
    output_content_hash: str = Field(
        pattern=r"^[0-9a-f]{64}$",
        description="Core SHA-256 identity binding the returned allocation output.",
        examples=["c" * 64],
    )
    numeric_output_policy: PortfolioAllocationNumericOutputPolicy | None = Field(
        default=None,
        description="Core-owned numeric output boundary when the calculation applies one.",
    )

    @field_validator("algorithm_id")
    @classmethod
    def require_nonblank_algorithm_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("allocation algorithm identity must be nonblank")
        return value
