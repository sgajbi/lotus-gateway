from datetime import date
from typing import Final, Literal

from pydantic import ValidationError

from app.contracts.advisor_book import AdvisorBookProvenance, AdvisorBookScope
from app.contracts.advisor_book_summary import (
    AdvisorBookSummaryResponse,
    AdvisorBookValueItem,
    AdvisorBookValueSource,
    AdvisorBookValueSummary,
)
from app.services.advisor_book_access_policy import AdvisorBookCallerContext
from app.services.advisor_book_client_protocols import AdvisorBookValueClient
from app.services.advisor_book_service import AdvisorBookService
from app.services.advisor_book_service_errors import (
    source_incomplete,
    value_source_contract_invalid,
    value_source_unavailable,
)
from app.services.advisor_book_source_contract import SourceAdvisorBookResponse
from app.services.advisor_book_value_source_contract import (
    SourceBulkSummaryMember,
    SourceBulkSummaryResponse,
)

_SOURCE_ROUTE: Final[Literal["/reporting/portfolio-summary/bulk-query"]] = (
    "/reporting/portfolio-summary/bulk-query"
)


class AdvisorBookSummaryService:
    def __init__(
        self,
        *,
        membership_service: AdvisorBookService,
        value_client: AdvisorBookValueClient,
    ) -> None:
        self._membership_service = membership_service
        self._value_client = value_client

    async def get_value_summary(
        self,
        *,
        caller: AdvisorBookCallerContext,
        as_of_date: date,
        reporting_currency: str,
        correlation_id: str,
    ) -> AdvisorBookSummaryResponse:
        normalized_reporting_currency = reporting_currency.strip().upper()
        source = await self._membership_service.load_membership_source(
            caller=caller,
            as_of_date=as_of_date,
            correlation_id=correlation_id,
        )
        if source is None:
            return _empty_response(
                caller=caller,
                as_of_date=as_of_date,
                reporting_currency=normalized_reporting_currency,
                correlation_id=correlation_id,
            )
        if source.supportability.state == "INCOMPLETE":
            raise source_incomplete()
        if not source.members:
            return _empty_response(
                caller=caller,
                as_of_date=as_of_date,
                reporting_currency=normalized_reporting_currency,
                correlation_id=correlation_id,
            )

        portfolio_ids = [member.portfolio_id for member in source.members]
        value_source = await _load_and_validate_value_source(
            value_client=self._value_client,
            correlation_id=correlation_id,
            portfolio_ids=portfolio_ids,
            as_of_date=as_of_date,
            reporting_currency=normalized_reporting_currency,
        )
        return _response_from_sources(
            caller=caller,
            membership_source=source,
            value_source=value_source,
            correlation_id=correlation_id,
        )


def _validate_value_source(
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


async def _load_and_validate_value_source(
    *,
    value_client: AdvisorBookValueClient,
    correlation_id: str,
    portfolio_ids: list[str],
    as_of_date: date,
    reporting_currency: str,
) -> SourceBulkSummaryResponse:
    value_source = await _load_value_source(
        value_client=value_client,
        correlation_id=correlation_id,
        portfolio_ids=portfolio_ids,
        as_of_date=as_of_date,
        reporting_currency=reporting_currency,
    )
    _validate_value_source(
        source=value_source,
        requested_portfolio_ids=portfolio_ids,
        requested_as_of_date=as_of_date,
        requested_reporting_currency=reporting_currency,
    )
    return value_source


async def _load_value_source(
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


def _response_from_sources(
    *,
    caller: AdvisorBookCallerContext,
    membership_source: SourceAdvisorBookResponse,
    value_source: SourceBulkSummaryResponse,
    correlation_id: str,
) -> AdvisorBookSummaryResponse:
    items = [_value_item(member) for member in value_source.portfolios]
    covered_count = sum(item.state == "supported" for item in items)
    reporting_currency = (value_source.reporting_currency or "").strip().upper()
    return AdvisorBookSummaryResponse(
        correlation_id=correlation_id,
        scope=_scope(caller=caller, as_of_date=value_source.resolved_as_of_date),
        summary=_value_summary(
            value_source=value_source,
            covered_count=covered_count,
            reporting_currency=reporting_currency,
        ),
        items=items,
        source=AdvisorBookValueSource(
            source_service="lotus-core",
            source_route=_SOURCE_ROUTE,
            resolved_as_of_date=value_source.resolved_as_of_date,
            reporting_currency=reporting_currency,
        ),
        membership_provenance=_membership_provenance(membership_source),
    )


def _value_summary(
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


def _value_item(member: SourceBulkSummaryMember) -> AdvisorBookValueItem:
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


def _empty_response(
    *,
    caller: AdvisorBookCallerContext,
    as_of_date: date,
    reporting_currency: str,
    correlation_id: str,
) -> AdvisorBookSummaryResponse:
    return AdvisorBookSummaryResponse(
        correlation_id=correlation_id,
        scope=_scope(caller=caller, as_of_date=as_of_date),
        summary=AdvisorBookValueSummary(
            resolved_as_of_date=as_of_date,
            reporting_currency=reporting_currency,
            requested_portfolio_count=0,
            covered_portfolio_count=0,
            coverage_state="COMPLETE",
            coverage_reason="empty_book_has_no_members_to_cover",
            state="empty",
            reason_code="advisor_book_empty",
        ),
        items=[],
        source=AdvisorBookValueSource(
            source_service="lotus-core",
            source_route=_SOURCE_ROUTE,
            resolved_as_of_date=as_of_date,
            reporting_currency=reporting_currency,
        ),
    )


def _scope(*, caller: AdvisorBookCallerContext, as_of_date: date) -> AdvisorBookScope:
    return AdvisorBookScope(
        kind="own_book",
        label="My book",
        as_of_date=as_of_date,
        booking_center_code=caller.booking_center_code,
    )


def _membership_provenance(source: SourceAdvisorBookResponse) -> AdvisorBookProvenance:
    return AdvisorBookProvenance(
        product_name=source.product_name,
        product_version=source.product_version,
        generated_at=source.generated_at,
        latest_evidence_timestamp=source.latest_evidence_timestamp,
        freshness_status=source.freshness_status,
        data_quality_status=source.data_quality_status,
        source_evidence_current=source.source_evidence_current,
        snapshot_id=source.snapshot_id,
        content_hash=source.content_hash,
        lineage=source.lineage,
    )
