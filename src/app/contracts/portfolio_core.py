from pydantic import BaseModel, Field


class PortfolioIdentity(BaseModel):
    portfolio_id: str = Field(
        description="Canonical Lotus portfolio identifier.",
        examples=["PF_1001"],
    )
    display_name: str = Field(
        description="Advisor-facing portfolio display label.",
        examples=["PF_1001"],
    )
    client_id: str | None = Field(
        default=None,
        description="Optional client or CIF identifier associated with the portfolio.",
        examples=["CIF_1"],
    )
    base_currency: str = Field(
        description="Base currency assigned to the portfolio.",
        examples=["USD"],
    )
    booking_center_code: str | None = Field(
        default=None,
        description="Optional booking-center code for the portfolio record.",
        examples=["SGPB"],
    )


class PortfolioSummary(BaseModel):
    assets_under_management_base: float = Field(
        description="Total assets under management for the portfolio, expressed in base currency.",
        examples=[1000.0],
    )
    invested_market_value_base: float = Field(
        description="Invested market value excluding cash, expressed in base currency.",
        examples=[900.0],
    )
    cash_market_value_base: float = Field(
        description="Total cash market value, expressed in base currency.",
        examples=[100.0],
    )
    cash_weight_pct: float = Field(
        description="Cash weight as a percentage of total assets under management.",
        examples=[10.0],
    )
    position_count: int = Field(
        description="Count of position rows included in the resolved portfolio snapshot.",
        examples=[3],
    )
    cash_balance_count: int = Field(
        description="Count of cash balance rows included in the resolved portfolio snapshot.",
        examples=[1],
    )
