"""One owner for loading and admitting Core's bulk value source for a cohort."""

from datetime import date
from typing import Literal

from pydantic import ValidationError

from app.contracts.advisor_book_summary import (
    AdvisorBookValueItem,
    AdvisorBookValueSource,
    AdvisorBookValueSummary,
)
from app.services.advisor_book_client_protocols import AdvisorBookValueClient
from app.services.advisor_book_service_errors import (
    value_source_contract_invalid,
    value_source_unavailable,
)
from app.services.advisor_book_value_source_contract import (
    TRUSTWORTHY_MEMBER_COVERAGE_STATES,
    SourceBulkSummaryMember,
    SourceBulkSummaryResponse,
)


def validate_value_source(
    *,
    source: SourceBulkSummaryResponse,
    requested_portfolio_ids: list[str],
    requested_as_of_date: date,
    requested_reporting_currency: str,
) -> None:
    returned_ids = [member.portfolio_id for member in source.portfolios]
    if (
        source.requested_portfolio_ids != requested_portfolio_ids
        or returned_ids != requested_portfolio_ids
        or source.resolved_as_of_date != requested_as_of_date
        or (source.reporting_currency or "").strip().upper() != requested_reporting_currency
        or source.aggregate.portfolio_count != len(requested_portfolio_ids)
    ):
        raise value_source_contract_invalid()
    # Core resolves every member on the cohort basis; an older carry-forward
    # basis travels in snapshot_date, never in resolved_as_of_date. A member
    # resolved on a different date contradicts the admitted cohort.
    if any(member.resolved_as_of_date != requested_as_of_date for member in source.portfolios):
        raise value_source_contract_invalid()
    # Core's aggregate is fail-closed: COMPLETE asserts that every member is
    # trustworthy, so a COMPLETE aggregate over an untrustworthy member
    # contradicts its own member coverage evidence.
    if source.aggregate.coverage_state == "COMPLETE" and any(
        member.coverage_state not in TRUSTWORTHY_MEMBER_COVERAGE_STATES
        for member in source.portfolios
    ):
        raise value_source_contract_invalid()


async def load_and_validate_value_source(
    *,
    value_client: AdvisorBookValueClient,
    correlation_id: str,
    portfolio_ids: list[str],
    as_of_date: date,
    reporting_currency: str,
) -> SourceBulkSummaryResponse:
    value_source = await load_value_source(
        value_client=value_client,
        correlation_id=correlation_id,
        portfolio_ids=portfolio_ids,
        as_of_date=as_of_date,
        reporting_currency=reporting_currency,
    )
    validate_value_source(
        source=value_source,
        requested_portfolio_ids=portfolio_ids,
        requested_as_of_date=as_of_date,
        requested_reporting_currency=reporting_currency,
    )
    return value_source


async def load_value_source(
    *,
    value_client: AdvisorBookValueClient,
    correlation_id: str,
    portfolio_ids: list[str],
    as_of_date: date,
    reporting_currency: str,
) -> SourceBulkSummaryResponse:
    try:
        status_code, payload = await value_client.query_bulk_portfolio_summary(
            correlation_id=correlation_id,
            portfolio_ids=portfolio_ids,
            as_of_date=as_of_date.isoformat(),
            reporting_currency=reporting_currency,
        )
    except Exception as exc:
        raise value_source_unavailable() from exc
    if status_code != 200 or not isinstance(payload, dict):
        raise value_source_unavailable()
    try:
        return SourceBulkSummaryResponse.model_validate(payload)
    except ValidationError as exc:
        raise value_source_contract_invalid() from exc


def value_item(member: SourceBulkSummaryMember) -> AdvisorBookValueItem:
    totals = member.totals
    return AdvisorBookValueItem(
        portfolio_id=member.portfolio_id,
        total_value=totals.total_market_value_reporting_currency if totals else None,
        cash_value=totals.cash_balance_reporting_currency if totals else None,
        invested_value=totals.invested_market_value_reporting_currency if totals else None,
        valuation_as_of=member.resolved_as_of_date,
        snapshot_date=member.snapshot_date,
        coverage_state=member.coverage_state,
        coverage_reason=member.coverage_reason,
        state="supported" if totals is not None else "unavailable",
    )


def value_summary(
    *,
    value_source: SourceBulkSummaryResponse,
    covered_count: int,
    reporting_currency: str,
) -> AdvisorBookValueSummary:
    aggregate = value_source.aggregate
    postures: dict[
        str,
        tuple[
            Literal["supported", "partial", "unavailable"],
            Literal[
                "advisor_book_value_ready",
                "advisor_book_value_partial",
                "advisor_book_value_unavailable",
            ],
        ],
    ] = {
        "COMPLETE": ("supported", "advisor_book_value_ready"),
        "PARTIAL": ("partial", "advisor_book_value_partial"),
        "UNAVAILABLE": ("unavailable", "advisor_book_value_unavailable"),
    }
    state, reason_code = postures[aggregate.coverage_state]
    return AdvisorBookValueSummary(
        resolved_as_of_date=value_source.resolved_as_of_date,
        reporting_currency=reporting_currency,
        requested_portfolio_count=aggregate.portfolio_count,
        covered_portfolio_count=covered_count,
        total_value=(
            aggregate.totals.total_market_value_reporting_currency if aggregate.totals else None
        ),
        cash_value=(aggregate.totals.cash_balance_reporting_currency if aggregate.totals else None),
        invested_value=(
            aggregate.totals.invested_market_value_reporting_currency if aggregate.totals else None
        ),
        coverage_state=aggregate.coverage_state,
        coverage_reason=aggregate.coverage_reason,
        state=state,
        reason_code=reason_code,
    )


def empty_value_summary(*, as_of_date: date, reporting_currency: str) -> AdvisorBookValueSummary:
    return AdvisorBookValueSummary(
        resolved_as_of_date=as_of_date,
        reporting_currency=reporting_currency,
        requested_portfolio_count=0,
        covered_portfolio_count=0,
        coverage_state="COMPLETE",
        coverage_reason="empty_book_has_no_members_to_cover",
        state="empty",
        reason_code="advisor_book_empty",
    )


def value_source_descriptor(
    *, resolved_as_of_date: date, reporting_currency: str
) -> AdvisorBookValueSource:
    return AdvisorBookValueSource(
        source_service="lotus-core",
        source_route="/reporting/portfolio-summary/bulk-query",
        resolved_as_of_date=resolved_as_of_date,
        reporting_currency=reporting_currency,
    )
