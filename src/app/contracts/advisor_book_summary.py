from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.contracts.advisor_book import AdvisorBookProvenance, AdvisorBookScope

AdvisorBookMemberCoverageState = Literal[
    "COMPLETE",
    "MEASURED_ZERO",
    "CARRY_FORWARD",
    "LOADED_EMPTY",
    "NO_SNAPSHOT",
    "PARTIAL",
    "FX_UNAVAILABLE",
    "INVALID_PORTFOLIO",
]
AdvisorBookAggregateCoverageState = Literal["COMPLETE", "PARTIAL", "UNAVAILABLE"]


class AdvisorBookValueItem(BaseModel):
    portfolio_id: str = Field(
        description="Portfolio identifier from the trusted Core book membership cohort.",
        examples=["PB_SG_GLOBAL_BAL_001"],
    )
    total_value: Decimal | None = Field(
        default=None,
        description=(
            "Core-reported total portfolio value in the requested reporting currency. Null "
            "whenever the source coverage state is not trustworthy; Gateway never substitutes "
            "zero."
        ),
        examples=[1250000.50],
    )
    cash_value: Decimal | None = Field(
        default=None,
        description=(
            "Core-reported cash balance in the requested reporting currency; null whenever the "
            "source coverage state is not trustworthy."
        ),
        examples=[100000.00],
    )
    invested_value: Decimal | None = Field(
        default=None,
        description=(
            "Core-reported invested market value in the requested reporting currency; null "
            "whenever the source coverage state is not trustworthy."
        ),
        examples=[1150000.50],
    )
    valuation_as_of: date | None = Field(
        default=None,
        description="Effective as-of date Core resolved for this member's value facts.",
        examples=["2026-04-10"],
    )
    snapshot_date: date | None = Field(
        default=None,
        description=(
            "Latest source snapshot date Core used or observed for this member. Earlier than "
            "valuation_as_of for carried-forward coverage."
        ),
        examples=["2026-04-10"],
    )
    coverage_state: AdvisorBookMemberCoverageState = Field(
        description=(
            "Source-owned coverage state preserved from lotus-core. Value facts are populated "
            "only for COMPLETE, MEASURED_ZERO, and CARRY_FORWARD members."
        ),
        examples=["COMPLETE"],
    )
    coverage_reason: str = Field(
        description="Source-owned machine-readable explanation for the coverage state.",
        examples=["snapshot_rows_complete"],
    )
    state: Literal["supported", "unavailable"] = Field(
        description=(
            "Whether Core stated trustworthy value facts for this portfolio. MEASURED_ZERO is "
            "supported: an empty portfolio is a business fact, not missing data."
        ),
        examples=["supported"],
    )


class AdvisorBookValueSummary(BaseModel):
    resolved_as_of_date: date = Field(
        description="Effective as-of date Core resolved for the bounded cohort read.",
        examples=["2026-04-10"],
    )
    reporting_currency: str = Field(
        description="Core-resolved currency for all supported value facts.",
        examples=["USD"],
    )
    requested_portfolio_count: int = Field(
        ge=0,
        description="Number of active portfolios in the trusted membership cohort.",
        examples=[2],
    )
    covered_portfolio_count: int = Field(
        ge=0,
        description="Number of trusted portfolios with trustworthy Core value facts.",
        examples=[2],
    )
    total_value: Decimal | None = Field(
        default=None,
        description=(
            "Core's fail-closed cohort total in the reporting currency. Null unless every "
            "trusted portfolio is covered; Gateway never sums partial rows or substitutes zero."
        ),
        examples=[2500000.75],
    )
    cash_value: Decimal | None = Field(
        default=None,
        description=(
            "Core's fail-closed cohort cash total in the reporting currency; null unless every "
            "trusted portfolio is covered."
        ),
        examples=[200000.00],
    )
    invested_value: Decimal | None = Field(
        default=None,
        description=(
            "Core's fail-closed cohort invested total in the reporting currency; null unless "
            "every trusted portfolio is covered."
        ),
        examples=[2300000.75],
    )
    coverage_state: AdvisorBookAggregateCoverageState = Field(
        description="Source-owned aggregate coverage posture across the requested cohort.",
        examples=["COMPLETE"],
    )
    coverage_reason: str = Field(
        description="Source-owned explanation for the aggregate coverage posture.",
        examples=["all_members_covered"],
    )
    state: Literal["supported", "partial", "unavailable", "empty"] = Field(
        description="Book-level value coverage posture.",
        examples=["supported"],
    )
    reason_code: Literal[
        "advisor_book_value_ready",
        "advisor_book_value_partial",
        "advisor_book_value_unavailable",
        "advisor_book_empty",
    ] = Field(
        description="Bounded reason for the book-level value coverage posture.",
        examples=["advisor_book_value_ready"],
    )


class AdvisorBookValueSource(BaseModel):
    source_service: Literal["lotus-core"] = Field(
        description="Service that owns the value facts.",
        examples=["lotus-core"],
    )
    source_route: Literal["/reporting/portfolio-summary/bulk-query"] = Field(
        description=(
            "Core route that owns the bounded cohort value contract (portfolio-summary-bulk-v1)."
        ),
        examples=["/reporting/portfolio-summary/bulk-query"],
    )
    source_contract_version: Literal["portfolio-summary-bulk-v1"] = Field(
        default="portfolio-summary-bulk-v1",
        description="Versioned source contract this summary preserves.",
        examples=["portfolio-summary-bulk-v1"],
    )
    resolved_as_of_date: date = Field(
        description="Effective as-of date Core resolved for the cohort read.",
        examples=["2026-04-10"],
    )
    reporting_currency: str = Field(
        description="Reporting currency resolved by Core for the cohort read.",
        examples=["USD"],
    )


class AdvisorBookSummaryResponse(BaseModel):
    correlation_id: str = Field(
        description="Opaque request correlation identifier.",
        examples=["corr-advisor-book-summary-001"],
    )
    contract_version: Literal["v1"] = Field(
        default="v1",
        description="Version of the Gateway advisor-book value summary contract.",
        examples=["v1"],
    )
    scope: AdvisorBookScope
    summary: AdvisorBookValueSummary
    items: list[AdvisorBookValueItem] = Field(
        default_factory=list,
        description="Value facts in the stable order of the trusted membership cohort.",
    )
    source: AdvisorBookValueSource
    membership_provenance: AdvisorBookProvenance | None = Field(
        default=None,
        description="Core membership provenance retained for the trusted book scope.",
    )
