from pydantic import BaseModel, Field

from app.contracts.portfolio_common import PortfolioPartialFailure
from app.contracts.portfolio_core import PortfolioSummary
from app.contracts.portfolio_holdings import PortfolioCashBalance


class PortfolioCashflowPoint(BaseModel):
    projection_date: str = Field(
        description="Projected business date represented by the forward cashflow point.",
        examples=["2026-03-28"],
    )
    net_cashflow_base: float = Field(
        description="Net projected cashflow for the point date, expressed in base currency.",
        examples=[25.0],
    )
    projected_cumulative_cashflow_base: float = Field(
        description=(
            "Running cumulative projected cashflow through the point date, expressed in "
            "base currency."
        ),
        examples=[125.0],
    )


class PortfolioCashflowOutlook(BaseModel):
    as_of_date: str = Field(
        description="As-of date used to resolve the projected cashflow path.",
        examples=["2026-03-27"],
    )
    range_end_date: str = Field(
        description="Inclusive end date of the projected cashflow horizon.",
        examples=["2026-04-26"],
    )
    total_net_cashflow_base: float = Field(
        description=(
            "Net projected cashflow across the full returned horizon, expressed in base currency."
        ),
        examples=[125.0],
    )
    projection_days: int = Field(
        description="Number of forward projection days covered by the returned liquidity path.",
        examples=[30],
    )
    include_projected: bool = Field(
        description="Whether projected events were included when generating the liquidity path.",
        examples=[True],
    )
    notes: str | None = Field(
        default=None,
        description="Optional upstream note or caveat associated with the projected cashflow path.",
        examples=["Projection includes booked and projected settlement events."],
    )
    upcoming_points: list[PortfolioCashflowPoint] = Field(
        default_factory=list,
        description="Ordered forward cashflow points spanning the returned liquidity horizon.",
    )


class PortfolioLiquidityResponse(BaseModel):
    correlation_id: str = Field(
        description="Opaque correlation identifier for the liquidity response envelope.",
        examples=["corr-portfolio-liquidity"],
    )
    contract_version: str = Field(
        default="v1",
        description="Version of the gateway portfolio liquidity response contract.",
        examples=["v1"],
    )
    portfolio_id: str = Field(
        description="Portfolio identifier whose liquidity snapshot is being returned.",
        examples=["PF_1001"],
    )
    as_of_date: str = Field(
        description="Resolved as-of date used for the liquidity summary and cash balances.",
        examples=["2026-03-27"],
    )
    summary: PortfolioSummary = Field(
        description="Source-backed summary values used to frame available and invested liquidity.",
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
    cash_balances: list[PortfolioCashBalance] = Field(
        default_factory=list,
        description=(
            "Published cash balance rows for the requested portfolio and reporting currency."
        ),
        examples=[
            [
                {
                    "security_id": "CASH_USD",
                    "instrument_name": "USD Cash",
                    "currency": "USD",
                    "quantity": 100.0,
                    "market_value_base": 100.0,
                    "weight_pct": 10.0,
                }
            ]
        ],
    )
    cashflow_outlook: PortfolioCashflowOutlook | None = Field(
        default=None,
        description="Projected liquidity path when forward cashflow evidence is available.",
        examples=[
            {
                "as_of_date": "2026-03-27",
                "range_end_date": "2026-04-06",
                "total_net_cashflow_base": -25.0,
                "projection_days": 10,
                "include_projected": True,
                "notes": [],
                "upcoming_points": [
                    {
                        "projection_date": "2026-03-28",
                        "net_cashflow_base": -25.0,
                        "projected_cumulative_cashflow_base": -25.0,
                    }
                ],
            }
        ],
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Gateway warning codes describing degraded but still usable liquidity output.",
        examples=[["PORTFOLIO_CASHFLOW_UNAVAILABLE"]],
    )
    partial_failures: list[PortfolioPartialFailure] = Field(
        default_factory=list,
        description=(
            "Upstream source failures preserved when optional liquidity sections are unavailable."
        ),
        examples=[
            [
                {
                    "source_service": "lotus-core",
                    "error_code": "PORTFOLIO_CASHFLOW_UNAVAILABLE",
                    "detail": "cashflow temporarily unavailable",
                }
            ]
        ],
    )


class PortfolioProjectedCashflowResponse(BaseModel):
    correlation_id: str = Field(
        description="Opaque correlation identifier for the projected-cashflow response envelope.",
        examples=["corr-portfolio-projected-cashflow"],
    )
    contract_version: str = Field(
        default="v1",
        description="Version of the gateway projected-cashflow response contract.",
        examples=["v1"],
    )
    portfolio_id: str = Field(
        description="Portfolio identifier whose forward cashflow projection is being returned.",
        examples=["PF_1001"],
    )
    as_of_date: str = Field(
        description="Resolved projection as-of date used for the projected cashflow request.",
        examples=["2026-03-27"],
    )
    cashflow_outlook: PortfolioCashflowOutlook | None = Field(
        default=None,
        description="Forward projected cashflow path for the requested horizon when available.",
        examples=[
            {
                "as_of_date": "2026-03-27",
                "range_end_date": "2026-04-26",
                "total_net_cashflow_base": 125.0,
                "projection_days": 30,
                "include_projected": False,
                "notes": None,
                "upcoming_points": [
                    {
                        "projection_date": "2026-03-28",
                        "net_cashflow_base": 25.0,
                        "projected_cumulative_cashflow_base": 25.0,
                    }
                ],
            }
        ],
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Gateway warning codes describing degraded projected-cashflow output.",
        examples=[["PORTFOLIO_PROJECTED_CASHFLOW_UNAVAILABLE"]],
    )
    partial_failures: list[PortfolioPartialFailure] = Field(
        default_factory=list,
        description=(
            "Upstream source failures preserved when projected cashflow cannot be returned."
        ),
        examples=[
            [
                {
                    "source_service": "lotus-core",
                    "error_code": "PORTFOLIO_PROJECTED_CASHFLOW_UNAVAILABLE",
                    "detail": "projected cashflow unavailable",
                }
            ]
        ],
    )
