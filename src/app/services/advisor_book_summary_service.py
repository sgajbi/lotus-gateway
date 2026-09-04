from datetime import date

from app.contracts.advisor_book_summary import AdvisorBookSummaryResponse
from app.services.advisor_book_access_policy import AdvisorBookCallerContext
from app.services.advisor_book_client_protocols import AdvisorBookValueClient
from app.services.advisor_book_provenance import membership_provenance, own_book_scope
from app.services.advisor_book_service import AdvisorBookService
from app.services.advisor_book_service_errors import source_incomplete
from app.services.advisor_book_source_contract import SourceAdvisorBookResponse
from app.services.advisor_book_value_facts import (
    empty_value_summary,
    load_and_validate_value_source,
    value_item,
    value_source_descriptor,
    value_summary,
)
from app.services.advisor_book_value_source_contract import SourceBulkSummaryResponse


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
        value_source = await load_and_validate_value_source(
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


def _response_from_sources(
    *,
    caller: AdvisorBookCallerContext,
    membership_source: SourceAdvisorBookResponse,
    value_source: SourceBulkSummaryResponse,
    correlation_id: str,
) -> AdvisorBookSummaryResponse:
    items = [value_item(member) for member in value_source.portfolios]
    covered_count = sum(item.state == "supported" for item in items)
    reporting_currency = (value_source.reporting_currency or "").strip().upper()
    return AdvisorBookSummaryResponse(
        correlation_id=correlation_id,
        scope=own_book_scope(
            booking_center_code=caller.booking_center_code,
            as_of_date=value_source.resolved_as_of_date,
        ),
        summary=value_summary(
            value_source=value_source,
            covered_count=covered_count,
            reporting_currency=reporting_currency,
        ),
        items=items,
        source=value_source_descriptor(
            resolved_as_of_date=value_source.resolved_as_of_date,
            reporting_currency=reporting_currency,
        ),
        membership_provenance=membership_provenance(membership_source),
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
        scope=own_book_scope(booking_center_code=caller.booking_center_code, as_of_date=as_of_date),
        summary=empty_value_summary(as_of_date=as_of_date, reporting_currency=reporting_currency),
        items=[],
        source=value_source_descriptor(
            resolved_as_of_date=as_of_date,
            reporting_currency=reporting_currency,
        ),
    )
