from pydantic import BaseModel, Field


class PortfolioMoneySummary(BaseModel):
    portfolio_currency_amount: float | None = Field(
        default=None,
        description="Optional amount in portfolio currency when the upstream summary provides it.",
        examples=[26.0],
    )
    reporting_currency_amount: float = Field(
        description="Amount in the resolved reporting currency for the requested summary bucket.",
        examples=[26.0],
    )
    transaction_count: int = Field(
        description="Number of transactions contributing to the summarized amount.",
        examples=[2],
    )


class PortfolioIncomePeriodSummary(BaseModel):
    gross: PortfolioMoneySummary = Field(
        description="Gross income before withholding tax and other deductions.",
    )
    withholding_tax: PortfolioMoneySummary = Field(
        description="Withholding-tax amounts applied to the summarized income.",
    )
    other_deductions: PortfolioMoneySummary = Field(
        description="Other deductions applied to the summarized income.",
    )
    net: PortfolioMoneySummary = Field(
        description="Net income after taxes and deductions.",
    )


class PortfolioIncomeTypeSummary(BaseModel):
    income_type: str = Field(
        description="Canonical Lotus income type represented in the summary row.",
        examples=["DIVIDEND"],
    )
    requested_window: PortfolioIncomePeriodSummary = Field(
        description="Income totals for the requested reporting window.",
    )
    year_to_date: PortfolioIncomePeriodSummary = Field(
        description=(
            "Income totals from the start of the calendar year through the window end date."
        ),
    )


class PortfolioIncomeSummaryResponse(BaseModel):
    correlation_id: str = Field(
        description="Opaque correlation identifier for the income-summary response envelope.",
        examples=["corr-portfolio-income-summary"],
    )
    contract_version: str = Field(
        default="v1",
        description="Version of the gateway income-summary response contract.",
        examples=["v1"],
    )
    portfolio_id: str = Field(
        description="Portfolio identifier whose income summary is being returned.",
        examples=["PF_1001"],
    )
    reporting_currency: str = Field(
        description="Resolved reporting currency used for all summary amounts.",
        examples=["USD"],
    )
    window_start_date: str = Field(
        description="Inclusive start date for the requested reporting window.",
        examples=["2026-03-01"],
    )
    window_end_date: str = Field(
        description="Inclusive end date for the requested reporting window.",
        examples=["2026-03-27"],
    )
    totals_requested_window: PortfolioIncomePeriodSummary = Field(
        description="Portfolio-level income totals for the requested reporting window.",
    )
    totals_year_to_date: PortfolioIncomePeriodSummary = Field(
        description="Portfolio-level income totals from year start through the window end date.",
    )
    income_types: list[PortfolioIncomeTypeSummary] = Field(
        default_factory=list,
        description="Breakdown of income totals by canonical income type.",
        examples=[
            [
                {
                    "income_type": "DIVIDEND",
                    "requested_window": {
                        "gross": {"reporting_currency_amount": 42.0, "transaction_count": 2},
                        "withholding_tax": {
                            "reporting_currency_amount": 6.0,
                            "transaction_count": 2,
                        },
                        "other_deductions": {
                            "reporting_currency_amount": 0.0,
                            "transaction_count": 2,
                        },
                        "net": {"reporting_currency_amount": 36.0, "transaction_count": 2},
                    },
                    "year_to_date": {
                        "gross": {"reporting_currency_amount": 42.0, "transaction_count": 2},
                        "withholding_tax": {
                            "reporting_currency_amount": 6.0,
                            "transaction_count": 2,
                        },
                        "other_deductions": {
                            "reporting_currency_amount": 0.0,
                            "transaction_count": 2,
                        },
                        "net": {"reporting_currency_amount": 36.0, "transaction_count": 2},
                    },
                }
            ]
        ],
    )


class PortfolioActivityBucketSummary(BaseModel):
    bucket: str = Field(
        description="Canonical activity bucket represented in the summary row.",
        examples=["INFLOWS"],
    )
    requested_window: PortfolioMoneySummary = Field(
        description="Activity totals for the requested reporting window.",
    )
    year_to_date: PortfolioMoneySummary = Field(
        description="Activity totals from year start through the window end date.",
    )


class PortfolioActivitySummaryResponse(BaseModel):
    correlation_id: str = Field(
        description="Opaque correlation identifier for the activity-summary response envelope.",
        examples=["corr-portfolio-activity-summary"],
    )
    contract_version: str = Field(
        default="v1",
        description="Version of the gateway activity-summary response contract.",
        examples=["v1"],
    )
    portfolio_id: str = Field(
        description="Portfolio identifier whose activity summary is being returned.",
        examples=["PF_1001"],
    )
    reporting_currency: str = Field(
        description="Resolved reporting currency used for all activity summary amounts.",
        examples=["USD"],
    )
    window_start_date: str = Field(
        description="Inclusive start date for the requested activity window.",
        examples=["2026-03-01"],
    )
    window_end_date: str = Field(
        description="Inclusive end date for the requested activity window.",
        examples=["2026-03-27"],
    )
    buckets: list[PortfolioActivityBucketSummary] = Field(
        default_factory=list,
        description="Portfolio flow buckets for the requested window and year-to-date.",
        examples=[
            [
                {
                    "bucket": "INFLOWS",
                    "requested_window": {
                        "reporting_currency_amount": 100.0,
                        "transaction_count": 1,
                    },
                    "year_to_date": {
                        "reporting_currency_amount": 150.0,
                        "transaction_count": 2,
                    },
                }
            ]
        ],
    )
