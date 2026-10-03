from decimal import Decimal

from pydantic import Field

from app.contracts.portfolio_allocation import (
    PortfolioAllocationCalculationLineage,
    PortfolioAllocationContributor,
    PortfolioAllocationLookThroughCapability,
    PortfolioAllocationValuationCoverage,
    _StrictPortfolioAllocationModel,
)
from app.contracts.portfolio_core import PortfolioSummary


class PortfolioAllocationBucket(_StrictPortfolioAllocationModel):
    bucket: str = Field(
        description="Bucket label within the requested allocation dimension.",
        examples=["Equity"],
    )
    position_count: int = Field(
        description="Count of positions contributing to the allocation bucket.",
        examples=[1],
    )
    market_value_base: float | None = Field(
        default=None,
        description="Bucket market value expressed in portfolio base currency.",
        examples=[700.0],
    )
    market_value_reporting_currency: Decimal | None = Field(
        ...,
        description=(
            "Exact bucket value in effective reporting currency, or null when source valuation "
            "coverage does not support the bucket value."
        ),
        examples=["700.123"],
    )
    weight_pct: float | None = Field(
        default=None,
        description="Bucket weight as a percentage of portfolio assets under management.",
        examples=[70.0],
    )
    contributor_count: int = Field(
        default=0,
        description="Total source contributor rows included in this allocation bucket.",
        examples=[2],
    )
    contributors: list[PortfolioAllocationContributor] = Field(
        default_factory=list,
        description=(
            "Bounded source-owned contributor lineage ordered by Core. Direct positions and "
            "look-through components are preserved without Gateway recalculation."
        ),
    )
    contributors_truncated: bool = Field(
        default=False,
        description="Whether Core omitted contributors beyond the requested per-bucket limit.",
        examples=[False],
    )
    omitted_market_value_reporting_currency: Decimal | None = Field(
        ...,
        description=(
            "Exact signed source value omitted from bounded contributors; it reconciles the "
            "bucket with retained contributor values; null when the bucket value is unknown."
        ),
        examples=["0.00"],
    )


class PortfolioAllocationView(_StrictPortfolioAllocationModel):
    dimension: str = Field(
        description="Allocation dimension represented by the current view.",
        examples=["asset_class"],
    )
    total_market_value_reporting_currency: Decimal | None = Field(
        ...,
        description=(
            "Exact total represented by this source view, or null when Core reports incomplete "
            "valuation coverage."
        ),
        examples=["1000.00"],
    )
    buckets: list[PortfolioAllocationBucket] = Field(
        default_factory=list,
        description="Allocation buckets returned for the requested dimension.",
        examples=[
            [
                {
                    "bucket": "Asia",
                    "position_count": 3,
                    "market_value_base": 420000.0,
                    "weight_pct": 42.0,
                }
            ]
        ],
    )


class PortfolioAllocationResponse(_StrictPortfolioAllocationModel):
    correlation_id: str = Field(
        description="Opaque correlation identifier for the allocation response envelope.",
        examples=["corr-portfolio-allocation"],
    )
    contract_version: str = Field(
        default="v1",
        description="Version of the gateway allocation response contract.",
        examples=["v1"],
    )
    portfolio_id: str = Field(
        description="Portfolio identifier whose allocation views are being returned.",
        examples=["PF_1001"],
    )
    as_of_date: str = Field(
        description="Resolved as-of date used for the allocation query inputs.",
        examples=["2026-03-27"],
    )
    reporting_currency: str | None = Field(
        default=None,
        description=(
            "Reporting currency used for the allocation response when restatement is applied."
        ),
        examples=["USD"],
    )
    total_market_value_reporting_currency: Decimal | None = Field(
        ...,
        description=(
            "Core-owned full-scope allocation total in reporting currency, or null when the "
            "full-scope denominator is not trustworthy."
        ),
        examples=["1000.00"],
    )
    valuation_coverage: PortfolioAllocationValuationCoverage = Field(
        description=(
            "Core-owned valuation qualification that distinguishes unavailable valuation from "
            "a genuine measured zero."
        )
    )
    calculation_lineage: PortfolioAllocationCalculationLineage = Field(
        description=(
            "Core-owned deterministic lineage binding allocation inputs, policy, and output."
        )
    )
    look_through: PortfolioAllocationLookThroughCapability | None = Field(
        default=None,
        description=(
            "Look-through capability and effective mode returned by the "
            "upstream allocation service."
        ),
        examples=[
            {
                "requested_mode": "prefer_look_through",
                "effective_mode": "direct_only",
                "applied": False,
                "supported": False,
                "decomposed_position_count": 0,
                "limitation_reason": "Look-through components were not available.",
            }
        ],
    )
    summary: PortfolioSummary = Field(
        description="Source-backed summary values used to frame the allocation response.",
        examples=[
            {
                "assets_under_management_base": 1000.0,
                "invested_market_value_base": 900.0,
                "cash_market_value_base": 100.0,
                "cash_weight_pct": 10.0,
                "position_count": 3,
                "cash_balance_count": 1,
            }
        ],
    )
    views: list[PortfolioAllocationView] = Field(
        default_factory=list,
        description="Allocation views returned for the supported reporting dimensions.",
        examples=[
            [
                {
                    "dimension": "region",
                    "buckets": [
                        {
                            "bucket": "Asia",
                            "position_count": 1,
                            "market_value_base": 700.0,
                            "weight_pct": 70.0,
                        }
                    ],
                }
            ]
        ],
    )
