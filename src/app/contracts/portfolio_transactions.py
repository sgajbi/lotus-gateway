from pydantic import BaseModel, Field


class PortfolioTransactionView(BaseModel):
    transaction_id: str = Field(
        description="Identifier of the transaction row.",
        examples=["TX_1"],
    )
    transaction_date: str = Field(
        description="Booked transaction date or timestamp for the ledger row.",
        examples=["2026-03-27T09:30:00Z"],
    )
    settlement_date: str | None = Field(
        default=None,
        description="Optional settlement date for the transaction row.",
        examples=["2026-03-29"],
    )
    transaction_type: str = Field(
        description="Canonical transaction type returned by the source ledger.",
        examples=["BUY"],
    )
    component_type: str | None = Field(
        default=None,
        description=(
            "Optional source-owned component role for linked or multi-row economic events. "
            "FX cash-settlement components use FX_CASH_SETTLEMENT_BUY or "
            "FX_CASH_SETTLEMENT_SELL."
        ),
        examples=["FX_CASH_SETTLEMENT_BUY"],
    )
    security_id: str = Field(
        description="Security identifier associated with the transaction row.",
        examples=["EQ_1"],
    )
    instrument_id: str = Field(
        description="Instrument identifier associated with the transaction row.",
        examples=["INST_EQ_1"],
    )
    quantity: float = Field(
        description="Transaction quantity for the ledger row.",
        examples=[10.0],
    )
    price: float | None = Field(
        default=None,
        description="Booked transaction price when available.",
        examples=[70.0],
    )
    gross_amount: float | None = Field(
        default=None,
        description="Gross transaction amount when available.",
        examples=[700.0],
    )
    currency: str | None = Field(
        default=None,
        description="Currency associated with the transaction row when available.",
        examples=["USD"],
    )
    net_cost_base: float | None = Field(
        default=None,
        description="Net cost expressed in portfolio base currency when available.",
        examples=[700.0],
    )
    realized_gain_loss_base: float | None = Field(
        default=None,
        description="Realized gain or loss expressed in portfolio base currency when available.",
        examples=[15.0],
    )
    settlement_status: str | None = Field(
        default=None,
        description=(
            "Optional source-owned settlement lifecycle status for an FX cash-settlement "
            "component. It is omitted when the source does not report an applicable "
            "settlement lifecycle."
        ),
        examples=["PENDING"],
    )
    source_system: str | None = Field(
        default=None,
        description="Optional upstream source system associated with the transaction row.",
        examples=["lotus-core"],
    )
    cash_entry_mode: str | None = Field(
        default=None,
        description="Optional cash-entry mode associated with the transaction row.",
        examples=["BOOKED"],
    )
    economic_event_id: str | None = Field(
        default=None,
        description="Optional economic event identifier linking related transaction rows.",
        examples=["EVT-2026-0001"],
    )
    linked_transaction_group_id: str | None = Field(
        default=None,
        description="Optional linked transaction group identifier for multi-row events.",
        examples=["LTG-2026-0001"],
    )
    fx_contract_id: str | None = Field(
        default=None,
        description="Optional FX contract identifier associated with the transaction row.",
        examples=["FXC-2026-0001"],
    )
    swap_event_id: str | None = Field(
        default=None,
        description="Optional FX swap event identifier associated with the transaction row.",
        examples=["FXSWAP-2026-0001"],
    )
    near_leg_group_id: str | None = Field(
        default=None,
        description=(
            "Optional FX swap near-leg group identifier associated with the transaction row."
        ),
        examples=["FXSWAP-2026-0001-NEAR"],
    )
    far_leg_group_id: str | None = Field(
        default=None,
        description=(
            "Optional FX swap far-leg group identifier associated with the transaction row."
        ),
        examples=["FXSWAP-2026-0001-FAR"],
    )


class PortfolioTransactionLedgerResponse(BaseModel):
    correlation_id: str = Field(
        description="Opaque correlation identifier for the transaction-ledger response envelope.",
        examples=["corr-portfolio-transactions"],
    )
    contract_version: str = Field(
        default="v1",
        description="Version of the gateway transaction-ledger response contract.",
        examples=["v1"],
    )
    portfolio_id: str = Field(
        description="Portfolio identifier whose transaction ledger is being returned.",
        examples=["PF_1001"],
    )
    as_of_date: str | None = Field(
        default=None,
        description=(
            "Resolved as-of date used for booked transaction state when "
            "provided by source or caller."
        ),
        examples=["2026-03-27"],
    )
    include_projected: bool = Field(
        description="Whether future-dated projected transactions are included in the result set.",
        examples=[False],
    )
    total: int = Field(
        description="Total number of matching transactions before paging is applied.",
        examples=[125],
    )
    skip: int = Field(
        description="Number of matching rows skipped before the current page.",
        examples=[0],
    )
    limit: int = Field(
        description="Maximum number of matching rows requested for the current page.",
        examples=[50],
    )
    transactions: list[PortfolioTransactionView] = Field(
        default_factory=list,
        description="Transaction rows returned for the current filter and paging window.",
        examples=[
            [
                {
                    "transaction_id": "TX_1",
                    "transaction_date": "2026-03-27T00:00:00Z",
                    "settlement_date": "2026-03-31",
                    "transaction_type": "BUY",
                    "component_type": "FX_CONTRACT_OPEN",
                    "security_id": "EQ_1",
                    "instrument_id": "INST_EQ_1",
                    "quantity": 1.0,
                    "currency": "USD",
                    "linked_transaction_group_id": "LTG-2026-0001",
                    "fx_contract_id": "FXC-2026-0001",
                    "swap_event_id": "FXSWAP-2026-0001",
                    "near_leg_group_id": "FXSWAP-2026-0001-NEAR",
                    "far_leg_group_id": "FXSWAP-2026-0001-FAR",
                }
            ]
        ],
    )
