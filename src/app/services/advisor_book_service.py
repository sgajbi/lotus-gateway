from dataclasses import dataclass
from datetime import date
from typing import Literal

from pydantic import ValidationError

from app.contracts.advisor_book import (
    AdvisorBookPage,
    AdvisorBookPortfolio,
    AdvisorBookProvenance,
    AdvisorBookResponse,
    AdvisorBookScope,
)
from app.services.advisor_book_access_policy import AdvisorBookCallerContext
from app.services.advisor_book_client_protocols import AdvisorBookMembershipClient
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
AdvisorBookMandateType = Literal["ADVISORY", "DISCRETIONARY"]

_SUPPORTED_PORTFOLIO_TYPES = ["ADVISORY", "DISCRETIONARY"]


@dataclass(frozen=True)
class AdvisorBookQuery:
    as_of_date: date
    client_id: str | None = None
    mandate_type: AdvisorBookMandateType | None = None
    sort_by: AdvisorBookSortField = "portfolio_id"
    sort_order: AdvisorBookSortOrder = "asc"
    offset: int = 0
    limit: int = 25


class AdvisorBookServiceError(RuntimeError):
    def __init__(self, *, code: str, message: str, status_code: int):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


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
        try:
            (
                status_code,
                payload,
            ) = await self._membership_client.get_portfolio_manager_book_memberships(
                portfolio_manager_id=caller.portfolio_manager_id,
                as_of_date=query.as_of_date.isoformat(),
                booking_center_code=caller.booking_center_code,
                portfolio_types=_SUPPORTED_PORTFOLIO_TYPES,
                correlation_id=correlation_id,
            )
        except Exception as exc:
            raise _source_unavailable() from exc

        if status_code == 404:
            return _empty_response(caller=caller, query=query, correlation_id=correlation_id)
        if status_code != 200:
            raise _source_unavailable()

        try:
            source = SourceAdvisorBookResponse.model_validate(payload)
        except ValidationError as exc:
            raise _source_contract_invalid() from exc
        _validate_source_scope(source=source, caller=caller, query=query)
        return _project_response(
            source=source,
            caller=caller,
            query=query,
            correlation_id=correlation_id,
        )


def _validate_source_scope(
    *,
    source: SourceAdvisorBookResponse,
    caller: AdvisorBookCallerContext,
    query: AdvisorBookQuery,
) -> None:
    if (
        source.portfolio_manager_id != caller.portfolio_manager_id
        or source.booking_center_code != caller.booking_center_code
        or source.as_of_date != query.as_of_date
        or source.supportability.returned_portfolio_count != len(source.members)
        or any(
            member.booking_center_code != caller.booking_center_code for member in source.members
        )
        or len({member.portfolio_id for member in source.members}) != len(source.members)
    ):
        raise _source_contract_invalid()
    if source.tenant_id is not None and source.tenant_id != caller.tenant_id:
        raise AdvisorBookServiceError(
            code="advisor_book_tenant_scope_mismatch",
            message="Advisor-book access is not available for this tenant scope.",
            status_code=403,
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
    return (query.client_id is None or member.client_id == query.client_id) and (
        query.mandate_type is None or member.portfolio_type == query.mandate_type
    )


def _sort_value(member: SourceAdvisorBookMember, sort_by: AdvisorBookSortField) -> str:
    if sort_by == "client_id":
        return member.client_id
    if sort_by == "mandate_type":
        return member.portfolio_type
    return member.portfolio_id


def _portfolio(member: SourceAdvisorBookMember) -> AdvisorBookPortfolio:
    return AdvisorBookPortfolio(
        portfolio_id=member.portfolio_id,
        display_name=member.portfolio_id,
        client_id=member.client_id,
        base_currency=member.base_currency,
        booking_center_code=member.booking_center_code,
        mandate_type=member.portfolio_type,
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


def _source_unavailable() -> AdvisorBookServiceError:
    return AdvisorBookServiceError(
        code="advisor_book_source_unavailable",
        message="Advisor-book information is temporarily unavailable.",
        status_code=502,
    )


def _source_contract_invalid() -> AdvisorBookServiceError:
    return AdvisorBookServiceError(
        code="advisor_book_source_contract_invalid",
        message="Advisor-book information could not be safely verified.",
        status_code=502,
    )
