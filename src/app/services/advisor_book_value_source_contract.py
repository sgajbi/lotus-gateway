"""Typed projection of lotus-core's `portfolio-summary-bulk-v1` contract.

Source truth: lotus-core `POST /reporting/portfolio-summary/bulk-query`. Totals are
populated only for COMPLETE, MEASURED_ZERO, or CARRY_FORWARD members, and the cohort
aggregate is fail-closed (null totals unless every member is trustworthy). Gateway
preserves those coverage semantics without reinterpretation.
"""

from datetime import date
from decimal import Decimal
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

SourceBulkMemberCoverageState = Literal[
    "COMPLETE",
    "MEASURED_ZERO",
    "CARRY_FORWARD",
    "LOADED_EMPTY",
    "NO_SNAPSHOT",
    "PARTIAL",
    "FX_UNAVAILABLE",
    "INVALID_PORTFOLIO",
]
SourceBulkAggregateCoverageState = Literal["COMPLETE", "PARTIAL", "UNAVAILABLE"]

TRUSTWORTHY_MEMBER_COVERAGE_STATES: frozenset[str] = frozenset(
    {"COMPLETE", "MEASURED_ZERO", "CARRY_FORWARD"}
)


class SourceBulkSummaryTotals(BaseModel):
    model_config = ConfigDict(extra="ignore")

    total_market_value_reporting_currency: Decimal
    cash_balance_reporting_currency: Decimal
    invested_market_value_reporting_currency: Decimal


class SourceBulkSummaryMember(BaseModel):
    model_config = ConfigDict(extra="ignore")

    portfolio_id: str
    resolved_as_of_date: date
    coverage_state: SourceBulkMemberCoverageState
    coverage_reason: str
    snapshot_date: date | None = None
    totals: SourceBulkSummaryTotals | None = None

    @model_validator(mode="after")
    def validate_totals_match_coverage(self) -> Self:
        trustworthy = self.coverage_state in TRUSTWORTHY_MEMBER_COVERAGE_STATES
        if trustworthy and self.totals is None:
            raise ValueError("a trustworthy member must carry source totals")
        if not trustworthy and self.totals is not None:
            raise ValueError("an untrustworthy member must not carry totals")
        return self


class SourceBulkAggregateTotals(BaseModel):
    model_config = ConfigDict(extra="ignore")

    total_market_value_reporting_currency: Decimal
    cash_balance_reporting_currency: Decimal
    invested_market_value_reporting_currency: Decimal


class SourceBulkSummaryAggregate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    portfolio_count: int = Field(ge=0)
    coverage_state: SourceBulkAggregateCoverageState
    coverage_reason: str
    totals: SourceBulkAggregateTotals | None = None

    @model_validator(mode="after")
    def validate_totals_match_coverage(self) -> Self:
        if self.coverage_state == "COMPLETE" and self.totals is None:
            raise ValueError("a complete aggregate must carry source totals")
        if self.coverage_state != "COMPLETE" and self.totals is not None:
            raise ValueError("a partial or unavailable aggregate must not carry totals")
        return self


class SourceBulkSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    contract_version: Literal["portfolio-summary-bulk-v1"]
    requested_portfolio_ids: list[str]
    resolved_as_of_date: date
    reporting_currency: str | None = None
    portfolios: list[SourceBulkSummaryMember]
    aggregate: SourceBulkSummaryAggregate
