from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

PortfolioLookThroughMode = Literal["direct_only", "prefer_look_through"]

__all__ = [
    "PortfolioAllocationContributor",
    "PortfolioAllocationLookThroughCapability",
    "PortfolioLookThroughMode",
]


class PortfolioAllocationContributor(BaseModel):
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
    market_value_reporting_currency: Decimal = Field(
        description="Signed source contribution value in the effective reporting currency.",
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


class PortfolioAllocationLookThroughCapability(BaseModel):
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
