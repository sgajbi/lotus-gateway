from pydantic import BaseModel, Field


class FoundationPortfolioCatalogItem(BaseModel):
    portfolio_id: str = Field(
        description="Stable portfolio identifier used to open the Foundation workspace.",
        examples=["PF_1001"],
    )
    display_name: str = Field(
        description="Advisor-facing portfolio label shown in selectors and page headers.",
        examples=["Alpha Growth"],
    )
    base_currency: str = Field(
        description="Portfolio base currency code.",
        examples=["USD"],
    )
    client_id: str | None = Field(
        default=None,
        description="Client identifier associated with the portfolio when available.",
        examples=["CIF_1001"],
    )
    booking_center_code: str | None = Field(
        default=None,
        description="Booking center code for the portfolio when available.",
        examples=["SG"],
    )


class FoundationPortfolioCatalogResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated through the gateway boundary.",
        examples=["corr_1"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway contract version for the Foundation catalog response.",
        examples=["v1"],
    )
    items: list[FoundationPortfolioCatalogItem] = Field(
        default_factory=list,
        description="Selector-ready portfolio entries available to the Foundation shell.",
        examples=[
            [
                {
                    "portfolio_id": "PF_1001",
                    "display_name": "Alpha Growth",
                    "base_currency": "USD",
                    "client_id": "CIF_1001",
                    "booking_center_code": "SG",
                }
            ]
        ],
    )
