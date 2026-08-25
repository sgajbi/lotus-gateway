from datetime import date

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
    SourceAdvisorBookValuePortfolio,
    SourceAdvisorBookValueResponse,
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
    source: SourceAdvisorBookValueResponse,
    requested_portfolio_ids: list[str],
    requested_as_of_date: date,
    requested_reporting_currency: str,
) -> None:
    if (
        source.resolved_as_of_date != requested_as_of_date
        or source.reporting_currency.strip().upper() != requested_reporting_currency.strip().upper()
        or source.scope_type != "portfolio_list"
        or source.scope.portfolio_ids != requested_portfolio_ids
        or source.totals.portfolio_count != len(source.portfolios)
        or len({portfolio.portfolio_id for portfolio in source.portfolios})
        != len(source.portfolios)
        or any(
            portfolio.portfolio_id not in requested_portfolio_ids for portfolio in source.portfolios
        )
    ):
        raise value_source_contract_invalid()


async def _load_and_validate_value_source(
    *,
    value_client: AdvisorBookValueClient,
    correlation_id: str,
    portfolio_ids: list[str],
    as_of_date: date,
    reporting_currency: str,
) -> SourceAdvisorBookValueResponse:
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
) -> SourceAdvisorBookValueResponse:
    try:
        status_code, payload = await value_client.query_assets_under_management(
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
        return SourceAdvisorBookValueResponse.model_validate(payload)
    except ValidationError as exc:
        raise value_source_contract_invalid() from exc


def _response_from_sources(
    *,
    caller: AdvisorBookCallerContext,
    membership_source: SourceAdvisorBookResponse,
    value_source: SourceAdvisorBookValueResponse,
    correlation_id: str,
) -> AdvisorBookSummaryResponse:
    value_by_id = {portfolio.portfolio_id: portfolio for portfolio in value_source.portfolios}
    items = _value_items(membership_source=membership_source, value_by_id=value_by_id)
    covered_count = sum(item.state == "supported" for item in items)
    all_covered = covered_count == len(membership_source.members)
    return AdvisorBookSummaryResponse(
        correlation_id=correlation_id,
        scope=_scope(caller=caller, as_of_date=value_source.resolved_as_of_date),
        summary=AdvisorBookValueSummary(
            resolved_as_of_date=value_source.resolved_as_of_date,
            reporting_currency=value_source.reporting_currency,
            requested_portfolio_count=len(membership_source.members),
            covered_portfolio_count=covered_count,
            total_value=value_source.totals.aum_reporting_currency if all_covered else None,
            state="supported" if all_covered else "partial",
            reason_code=(
                "advisor_book_value_ready" if all_covered else "advisor_book_value_partial"
            ),
        ),
        items=items,
        source=AdvisorBookValueSource(
            source_service="lotus-core",
            source_route="/reporting/assets-under-management/query",
            resolved_as_of_date=value_source.resolved_as_of_date,
            reporting_currency=value_source.reporting_currency,
        ),
        membership_provenance=_membership_provenance(membership_source),
    )


def _value_items(
    *,
    membership_source: SourceAdvisorBookResponse,
    value_by_id: dict[str, SourceAdvisorBookValuePortfolio],
) -> list[AdvisorBookValueItem]:
    items: list[AdvisorBookValueItem] = []
    for member in membership_source.members:
        value = value_by_id.get(member.portfolio_id)
        if value is None:
            items.append(
                AdvisorBookValueItem(
                    portfolio_id=member.portfolio_id,
                    state="unavailable",
                    reason_code="advisor_book_value_not_covered",
                )
            )
        elif _is_ambiguous_zero(value):
            items.append(
                AdvisorBookValueItem(
                    portfolio_id=value.portfolio_id,
                    state="unavailable",
                    reason_code="advisor_book_value_coverage_ambiguous",
                )
            )
        else:
            items.append(
                AdvisorBookValueItem(
                    portfolio_id=value.portfolio_id,
                    total_value=value.aum_reporting_currency,
                    position_count=value.position_count,
                    state="supported",
                    reason_code="advisor_book_value_ready",
                )
            )
    return items


def _is_ambiguous_zero(value: SourceAdvisorBookValuePortfolio) -> bool:
    """Keep Core's indistinguishable no-snapshot zero out of confident coverage."""

    return value.aum_reporting_currency == 0 and value.position_count == 0


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
            state="empty",
            reason_code="advisor_book_empty",
        ),
        items=[],
        source=AdvisorBookValueSource(
            source_service="lotus-core",
            source_route="/reporting/assets-under-management/query",
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
