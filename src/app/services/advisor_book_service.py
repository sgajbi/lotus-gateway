from dataclasses import dataclass
from datetime import date
from typing import Literal

from app.contracts.advisor_book import (
    AdvisorBookMandateType,
    AdvisorBookPage,
    AdvisorBookPortfolio,
    AdvisorBookProvenance,
    AdvisorBookResponse,
    AdvisorBookScope,
)
from app.services.advisor_book_access_policy import AdvisorBookCallerContext
from app.services.advisor_book_client_protocols import AdvisorBookMembershipClient
from app.services.advisor_book_membership_source import load_advisor_book_source
from app.services.advisor_book_service_errors import (
    AdvisorBookServiceError,
)
from app.services.advisor_book_service_errors import (
    portfolio_selection_inactive as _portfolio_selection_inactive,
)
from app.services.advisor_book_service_errors import (
    portfolio_selection_unavailable as _portfolio_selection_unavailable,
)
from app.services.advisor_book_service_errors import (
    source_contract_invalid as _source_contract_invalid,
)
from app.services.advisor_book_service_errors import (
    source_incomplete as _source_incomplete,
)
from app.services.advisor_book_service_errors import (
    tenant_scope_unverified as _tenant_scope_unverified,
)
from app.services.advisor_book_source_contract import (
    SourceAdvisorBookMember,
    SourceAdvisorBookResponse,
)
from app.services.advisor_book_supportability import (
    advisor_book_supportability,
    empty_advisor_book_supportability,
)

AdvisorBookSortField = Literal["portfolio_id", "client_id", "mandate_type"]
AdvisorBookSortOrder = Literal["asc", "desc"]

_SUPPORTED_PORTFOLIO_TYPES: tuple[AdvisorBookMandateType, ...] = (
    "ADVISORY",
    "DISCRETIONARY",
)
_SUPPORTED_PORTFOLIO_TYPE_BY_SOURCE_VALUE: dict[str, AdvisorBookMandateType] = {
    value: value for value in _SUPPORTED_PORTFOLIO_TYPES
}

__all__ = [
    "AdvisorBookQuery",
    "AdvisorBookService",
    "AdvisorBookServiceError",
    "ResolvedAdvisorBookSelection",
]


@dataclass(frozen=True)
class AdvisorBookQuery:
    as_of_date: date
    client_id: str | None = None
    mandate_type: AdvisorBookMandateType | None = None
    sort_by: AdvisorBookSortField = "portfolio_id"
    sort_order: AdvisorBookSortOrder = "asc"
    offset: int = 0
    limit: int = 25


@dataclass(frozen=True)
class ResolvedAdvisorBookSelection:
    tenant_id: str
    portfolios: tuple[AdvisorBookPortfolio, ...]


class AdvisorBookService:
    def __init__(self, *, membership_client: AdvisorBookMembershipClient) -> None:
        self._membership_client = membership_client

    async def get_advisor_book(
        self,
        *,
        caller: AdvisorBookCallerContext,
        query: AdvisorBookQuery,
        correlation_id: str,
    ) -> AdvisorBookResponse:
        source = await self._load_source(
            caller=caller,
            as_of_date=query.as_of_date,
            include_inactive=False,
            correlation_id=correlation_id,
        )
        if source is None:
            return _empty_response(caller=caller, query=query, correlation_id=correlation_id)
        return _project_response(
            source=source,
            caller=caller,
            query=query,
            correlation_id=correlation_id,
        )

    async def resolve_portfolios(
        self,
        *,
        caller: AdvisorBookCallerContext,
        as_of_date: date,
        portfolio_ids: tuple[str, ...],
        correlation_id: str,
    ) -> ResolvedAdvisorBookSelection:
        source = await self._load_source(
            caller=caller,
            as_of_date=as_of_date,
            include_inactive=True,
            correlation_id=correlation_id,
        )
        if source is None:
            raise _portfolio_selection_unavailable()
        if source.tenant_id is None:
            raise _tenant_scope_unverified()
        if source.supportability.state == "INCOMPLETE":
            raise _source_incomplete()

        members_by_id = {member.portfolio_id: member for member in source.members}
        unavailable_ids = sorted(set(portfolio_ids).difference(members_by_id))
        if unavailable_ids:
            raise _portfolio_selection_unavailable()

        selected = tuple(_portfolio(members_by_id[portfolio_id]) for portfolio_id in portfolio_ids)
        if any(portfolio.status.strip().upper() != "ACTIVE" for portfolio in selected):
            raise _portfolio_selection_inactive()
        return ResolvedAdvisorBookSelection(
            tenant_id=source.tenant_id,
            portfolios=selected,
        )

    async def load_membership_source(
        self,
        *,
        caller: AdvisorBookCallerContext,
        as_of_date: date,
        correlation_id: str,
        include_inactive: bool = False,
    ) -> SourceAdvisorBookResponse | None:
        """Load the validated own-book source for sibling read compositions."""

        return await self._load_source(
            caller=caller,
            as_of_date=as_of_date,
            include_inactive=include_inactive,
            correlation_id=correlation_id,
        )

    async def _load_source(
        self,
        *,
        caller: AdvisorBookCallerContext,
        as_of_date: date,
        include_inactive: bool,
        correlation_id: str,
    ) -> SourceAdvisorBookResponse | None:
        return await load_advisor_book_source(
            membership_client=self._membership_client,
            caller=caller,
            as_of_date=as_of_date,
            include_inactive=include_inactive,
            portfolio_types=_SUPPORTED_PORTFOLIO_TYPES,
            correlation_id=correlation_id,
        )


def _project_response(
    *,
    source: SourceAdvisorBookResponse,
    caller: AdvisorBookCallerContext,
    query: AdvisorBookQuery,
    correlation_id: str,
) -> AdvisorBookResponse:
    filtered = [member for member in source.members if _matches(member, query)]
    ordered = sorted(
        filtered,
        key=lambda member: (_sort_value(member, query.sort_by), member.portfolio_id),
        reverse=query.sort_order == "desc",
    )
    page_members = ordered[query.offset : query.offset + query.limit]
    return AdvisorBookResponse(
        correlation_id=correlation_id,
        scope=_scope(caller, query),
        page=AdvisorBookPage(
            total_count=len(filtered),
            offset=query.offset,
            limit=query.limit,
            returned_count=len(page_members),
            sort_by=query.sort_by,
            sort_order=query.sort_order,
        ),
        items=[_portfolio(member) for member in page_members],
        supportability=advisor_book_supportability(source=source, filtered_count=len(filtered)),
        provenance=AdvisorBookProvenance(
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
        ),
    )


def _matches(member: SourceAdvisorBookMember, query: AdvisorBookQuery) -> bool:
    mandate_type = _canonical_portfolio_type(member.portfolio_type)
    return (query.client_id is None or member.client_id == query.client_id) and (
        query.mandate_type is None or mandate_type == query.mandate_type
    )


def _sort_value(member: SourceAdvisorBookMember, sort_by: AdvisorBookSortField) -> str:
    if sort_by == "client_id":
        return member.client_id
    if sort_by == "mandate_type":
        return _canonical_portfolio_type(member.portfolio_type) or member.portfolio_type
    return member.portfolio_id


def _portfolio(member: SourceAdvisorBookMember) -> AdvisorBookPortfolio:
    mandate_type = _canonical_portfolio_type(member.portfolio_type)
    if mandate_type is None:
        raise _source_contract_invalid()
    return AdvisorBookPortfolio(
        portfolio_id=member.portfolio_id,
        display_name=member.portfolio_id,
        client_id=member.client_id,
        base_currency=member.base_currency,
        booking_center_code=member.booking_center_code,
        mandate_type=mandate_type,
        status=member.status,
        opened_on=member.open_date,
        closed_on=member.close_date,
        membership_source="PortfolioManagerBookMembership:v1",
        membership_reference=member.source_record_id,
        membership_basis=(
            "governed_role_assignment"
            if member.membership_source == "party_role_assignment"
            else "legacy_advisor_projection"
        ),
    )


def _canonical_portfolio_type(value: str) -> AdvisorBookMandateType | None:
    return _SUPPORTED_PORTFOLIO_TYPE_BY_SOURCE_VALUE.get(value.strip().upper())


def _empty_response(
    *,
    caller: AdvisorBookCallerContext,
    query: AdvisorBookQuery,
    correlation_id: str,
) -> AdvisorBookResponse:
    return AdvisorBookResponse(
        correlation_id=correlation_id,
        scope=_scope(caller, query),
        page=AdvisorBookPage(
            total_count=0,
            offset=query.offset,
            limit=query.limit,
            returned_count=0,
            sort_by=query.sort_by,
            sort_order=query.sort_order,
        ),
        items=[],
        supportability=empty_advisor_book_supportability(),
        provenance=None,
    )


def _scope(caller: AdvisorBookCallerContext, query: AdvisorBookQuery) -> AdvisorBookScope:
    return AdvisorBookScope(
        kind="own_book",
        label="My book",
        as_of_date=query.as_of_date,
        booking_center_code=caller.booking_center_code,
    )
