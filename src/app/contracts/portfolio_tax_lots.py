from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

PORTFOLIO_TAX_LOT_RESPONSE_EXAMPLE: dict[str, Any] = {
    "correlation_id": "corr-portfolio-tax-lots",
    "contract_version": "v1",
    "portfolio_id": "PF_1001",
    "security_id": "US0378331005",
    "lots": [
        {
            "lot_id": "LOT-TXN-2026-0001",
            "source_transaction_id": "TXN-2026-0001",
            "portfolio_id": "PF_1001",
            "instrument_id": "AAPL",
            "security_id": "US0378331005",
            "acquisition_date": "2026-02-28",
            "original_quantity": "100.0",
            "open_quantity": "75.0",
            "lot_cost_local": "15005.5",
            "lot_cost_base": "15005.5",
            "accrued_interest_paid_local": "0.0",
            "economic_event_id": "EVT-2026-00987",
            "linked_transaction_group_id": "LTG-2026-00456",
            "calculation_policy_id": "BUY_DEFAULT_POLICY",
            "calculation_policy_version": "1.0.0",
            "source_system": "OMS_PRIMARY",
        }
    ],
}


class PortfolioTaxLot(BaseModel):
    """Source-faithful current BUY lot fields exposed by the Gateway."""

    lot_id: str = Field(description="Stable source lot identifier.", examples=["LOT-TXN-2026-0001"])
    source_transaction_id: str = Field(
        description="Source transaction that created the lot.", examples=["TXN-2026-0001"]
    )
    portfolio_id: str = Field(description="Portfolio owning the lot.", examples=["PF_1001"])
    instrument_id: str = Field(description="Instrument identifier for the lot.", examples=["AAPL"])
    security_id: str = Field(
        description="Security identifier for the lot.", examples=["US0378331005"]
    )
    acquisition_date: date = Field(
        description="Source acquisition date for the lot.", examples=["2026-02-28"]
    )
    original_quantity: Decimal = Field(
        description="Original acquired quantity as reported by Core.", examples=["100.0"]
    )
    open_quantity: Decimal = Field(
        description="Current open quantity as reported by Core.", examples=["100.0"]
    )
    lot_cost_local: Decimal = Field(
        description="Lot cost in the source trade/local currency; not a reporting-currency value.",
        examples=["15005.5"],
    )
    lot_cost_base: Decimal = Field(
        description="Lot cost in the portfolio base currency; not restated by Gateway.",
        examples=["15005.5"],
    )
    accrued_interest_paid_local: Decimal = Field(
        description="Accrued interest paid at acquisition in local currency.", examples=["1250.0"]
    )
    economic_event_id: str | None = Field(
        default=None, description="Source economic event identifier.", examples=["EVT-2026-00987"]
    )
    linked_transaction_group_id: str | None = Field(
        default=None,
        description="Source linked transaction group identifier.",
        examples=["LTG-2026-00456"],
    )
    calculation_policy_id: str | None = Field(
        default=None,
        description="Source BUY calculation policy identifier.",
        examples=["BUY_DEFAULT_POLICY"],
    )
    calculation_policy_version: str | None = Field(
        default=None, description="Source BUY calculation policy version.", examples=["1.0.0"]
    )
    source_system: str | None = Field(
        default=None,
        description="Source system for the transaction record.",
        examples=["OMS_PRIMARY"],
    )

    model_config = ConfigDict(extra="forbid")


class PortfolioTaxLotResponse(BaseModel):
    """Typed Gateway envelope for one portfolio/security lot drill-down."""

    correlation_id: str = Field(
        description="Correlation identifier propagated through the Gateway request.",
        examples=["corr-portfolio-tax-lots"],
    )
    contract_version: str = Field(
        default="v1", description="Gateway contract version for the lot response.", examples=["v1"]
    )
    portfolio_id: str = Field(
        description="Portfolio requested by the caller.", examples=["PF_1001"]
    )
    security_id: str = Field(
        description="Security requested by the caller.", examples=["US0378331005"]
    )
    lots: list[PortfolioTaxLot] = Field(
        default_factory=list,
        description=(
            "Current source BUY lots for the exact portfolio/security key. Gateway does not "
            "calculate holding period, valuation, unrealized P&L, or reporting-currency values."
        ),
    )

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": PORTFOLIO_TAX_LOT_RESPONSE_EXAMPLE},
    )
