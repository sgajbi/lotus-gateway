from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.contracts.advisor_book import AdvisorBookProvenance, AdvisorBookScope


class AdvisorBookValueItem(BaseModel):
    portfolio_id: str = Field(
        description="Portfolio identifier from the trusted Core book membership cohort.",
        examples=["PB_SG_GLOBAL_BAL_001"],
    )
    total_value: Decimal | None = Field(
        default=None,
        description=(
            "Core-reported total portfolio value in the requested reporting currency. Null when "
            "the source did not return a value for this entitled portfolio."
        ),
        examples=[1250000.50],
    )
    position_count: int | None = Field(
        default=None,
        ge=0,
        description="Core-reported non-zero position count when the value fact is supported.",
        examples=[12],
    )
    state: Literal["supported", "unavailable"] = Field(
        description="Whether Core returned a complete value fact for this portfolio.",
        examples=["supported"],
    )
    reason_code: Literal[
        "advisor_book_value_ready",
        "advisor_book_value_not_covered",
    ] = Field(
        description="Bounded reason for the per-portfolio value state.",
        examples=["advisor_book_value_ready"],
    )


class AdvisorBookValueSummary(BaseModel):
    resolved_as_of_date: date = Field(
        description="Core-resolved business date for all value facts in this response.",
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
        description="Number of trusted portfolios with a returned Core value fact.",
        examples=[2],
    )
    total_value: Decimal | None = Field(
        default=None,
        description=(
            "Core-reported aggregate value when every trusted portfolio is covered. Null for "
            "partial or unavailable coverage; Gateway never sums partial rows or substitutes zero."
        ),
        examples=[2500000.75],
    )
    state: Literal["supported", "partial", "empty"] = Field(
        description="Book-level value coverage posture.",
        examples=["supported"],
    )
    reason_code: Literal[
        "advisor_book_value_ready",
        "advisor_book_value_partial",
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
    source_route: Literal["/reporting/assets-under-management/query"] = Field(
        description="Core route family that owns the bounded multi-portfolio value contract.",
        examples=["/reporting/assets-under-management/query"],
    )
    resolved_as_of_date: date = Field(
        description="As-of date resolved by Core for the value read.",
        examples=["2026-04-10"],
    )
    reporting_currency: str = Field(
        description="Reporting currency resolved by Core for the value read.",
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
