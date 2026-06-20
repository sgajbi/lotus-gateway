from pydantic import BaseModel, Field

from app.contracts.portfolio_core import PortfolioSummary


class PortfolioTopPosition(BaseModel):
    security_id: str = Field(
        description="Identifier of the ranked top holding.",
        examples=["EQ_1"],
    )
    instrument_name: str = Field(
        description="Advisor-facing instrument name for the ranked holding.",
        examples=["Equity 1"],
    )
    asset_class: str | None = Field(
        default=None,
        description="Asset class assigned to the ranked holding when available.",
        examples=["Equity"],
    )
    isin: str | None = Field(
        default=None,
        description="Optional ISIN associated with the ranked holding.",
        examples=["US1234567890"],
    )
    currency: str | None = Field(
        default=None,
        description="Trading or instrument currency of the ranked holding.",
        examples=["USD"],
    )
    quantity: float = Field(
        description="Held quantity of the ranked position.",
        examples=[10.0],
    )
    cost_basis_base: float | None = Field(
        default=None,
        description="Cost basis expressed in portfolio base currency.",
        examples=[500.0],
    )
    market_value_base: float | None = Field(
        default=None,
        description="Market value expressed in portfolio base currency.",
        examples=[700.0],
    )
    weight_pct: float | None = Field(
        default=None,
        description="Position weight as a percentage of portfolio assets under management.",
        examples=[70.0],
    )


class PortfolioPositionView(BaseModel):
    security_id: str = Field(
        description="Identifier of the position row.",
        examples=["EQ_1"],
    )
    instrument_name: str = Field(
        description="Advisor-facing instrument name for the position row.",
        examples=["Equity 1"],
    )
    asset_class: str | None = Field(
        default=None,
        description="Asset class assigned to the position when available.",
        examples=["Equity"],
    )
    isin: str | None = Field(
        default=None,
        description="Optional ISIN associated with the position.",
        examples=["US1234567890"],
    )
    currency: str | None = Field(
        default=None,
        description="Trading or instrument currency of the position.",
        examples=["USD"],
    )
    sector: str | None = Field(
        default=None,
        description="Optional sector classification for the position.",
        examples=["Technology"],
    )
    country_of_risk: str | None = Field(
        default=None,
        description="Optional country-of-risk classification for the position.",
        examples=["US"],
    )
    held_since_date: str | None = Field(
        default=None,
        description="Optional holding start date in YYYY-MM-DD format.",
        examples=["2025-12-31"],
    )
    quantity: float = Field(
        description="Held quantity of the position.",
        examples=[10.0],
    )
    market_price: float | None = Field(
        default=None,
        description="Current market price of the position when valuation is available.",
        examples=[70.0],
    )
    cost_basis_base: float | None = Field(
        default=None,
        description="Cost basis expressed in portfolio base currency.",
        examples=[500.0],
    )
    cost_basis_local: float | None = Field(
        default=None,
        description="Cost basis expressed in local or instrument currency when available.",
        examples=[500.0],
    )
    market_value_base: float | None = Field(
        default=None,
        description="Market value expressed in portfolio base currency.",
        examples=[700.0],
    )
    market_value_local: float | None = Field(
        default=None,
        description="Market value expressed in local or instrument currency when available.",
        examples=[700.0],
    )
    unrealized_gain_loss_base: float | None = Field(
        default=None,
        description="Unrealized gain or loss expressed in portfolio base currency.",
        examples=[200.0],
    )
    unrealized_gain_loss_local: float | None = Field(
        default=None,
        description=(
            "Unrealized gain or loss expressed in local or instrument currency when available."
        ),
        examples=[200.0],
    )
    weight_pct: float | None = Field(
        default=None,
        description="Position weight as a percentage of portfolio assets under management.",
        examples=[70.0],
    )
    reprocessing_status: str | None = Field(
        default=None,
        description="Optional upstream reprocessing or valuation status for the position row.",
        examples=["READY"],
    )


class PortfolioPositionBookResponse(BaseModel):
    correlation_id: str = Field(
        description="Opaque correlation identifier for the position-book response envelope.",
        examples=["corr-portfolio-positions"],
    )
    contract_version: str = Field(
        default="v1",
        description="Version of the gateway position-book response contract.",
        examples=["v1"],
    )
    portfolio_id: str = Field(
        description="Portfolio identifier whose position book is being returned.",
        examples=["PF_1001"],
    )
    as_of_date: str = Field(
        description="Resolved as-of date used for the position-book request.",
        examples=["2026-03-27"],
    )
    summary: PortfolioSummary = Field(
        description="Source-backed summary values used to frame the positions response.",
    )
    top_positions: list[PortfolioTopPosition] = Field(
        default_factory=list,
        description="Ranked top holdings derived from the returned position rows.",
        examples=[
            [
                {
                    "security_id": "EQ_1",
                    "instrument_name": "Equity 1",
                    "asset_class": "Equity",
                    "isin": "US1234567890",
                    "currency": "USD",
                    "quantity": 10.0,
                    "cost_basis_base": 320.0,
                    "market_value_base": 400.0,
                    "weight_pct": 40.0,
                }
            ]
        ],
    )
    positions: list[PortfolioPositionView] = Field(
        default_factory=list,
        description="Detailed position rows for the requested portfolio book.",
        examples=[
            [
                {
                    "security_id": "EQ_1",
                    "instrument_name": "Equity 1",
                    "asset_class": "Equity",
                    "isin": "US1234567890",
                    "currency": "USD",
                    "sector": "Technology",
                    "country_of_risk": "United States",
                    "held_since_date": "2025-12-31",
                    "quantity": 10.0,
                    "market_price": 40.0,
                    "cost_basis_base": 320.0,
                    "cost_basis_local": 320.0,
                    "market_value_base": 400.0,
                    "market_value_local": 400.0,
                    "unrealized_gain_loss_base": 80.0,
                    "unrealized_gain_loss_local": 80.0,
                    "weight_pct": 40.0,
                    "reprocessing_status": "READY",
                }
            ]
        ],
    )
