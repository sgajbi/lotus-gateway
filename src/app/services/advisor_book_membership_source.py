from datetime import date
from typing import Sequence

from pydantic import ValidationError

from app.contracts.advisor_book import AdvisorBookMandateType
from app.services.advisor_book_access_policy import AdvisorBookCallerContext
from app.services.advisor_book_client_protocols import AdvisorBookMembershipClient
from app.services.advisor_book_service_errors import (
    AdvisorBookServiceError,
    source_contract_invalid,
    source_unavailable,
)
from app.services.advisor_book_source_contract import SourceAdvisorBookResponse


async def load_advisor_book_source(
    *,
    membership_client: AdvisorBookMembershipClient,
    caller: AdvisorBookCallerContext,
    as_of_date: date,
    include_inactive: bool,
    portfolio_types: Sequence[AdvisorBookMandateType],
    correlation_id: str,
) -> SourceAdvisorBookResponse | None:
    try:
        status_code, payload = await membership_client.get_portfolio_manager_book_memberships(
            portfolio_manager_id=caller.portfolio_manager_id,
            as_of_date=as_of_date.isoformat(),
            booking_center_code=caller.booking_center_code,
            portfolio_types=list(portfolio_types),
            include_inactive=include_inactive,
            correlation_id=correlation_id,
        )
    except Exception as exc:
        raise source_unavailable() from exc

    if status_code == 404:
        return None
    if status_code != 200:
        raise source_unavailable()

    try:
        source = SourceAdvisorBookResponse.model_validate(payload)
    except ValidationError as exc:
        raise source_contract_invalid() from exc
    _validate_source_scope(
        source=source,
        caller=caller,
        as_of_date=as_of_date,
        portfolio_types=portfolio_types,
    )
    return source


def _validate_source_scope(
    *,
    source: SourceAdvisorBookResponse,
    caller: AdvisorBookCallerContext,
    as_of_date: date,
    portfolio_types: Sequence[AdvisorBookMandateType],
) -> None:
    supported_portfolio_types = {value.upper() for value in portfolio_types}
    if (
        source.portfolio_manager_id != caller.portfolio_manager_id
        or source.booking_center_code != caller.booking_center_code
        or source.as_of_date != as_of_date
        or source.supportability.returned_portfolio_count != len(source.members)
        or any(
            member.booking_center_code != caller.booking_center_code for member in source.members
        )
        or any(
            member.portfolio_type.strip().upper() not in supported_portfolio_types
            for member in source.members
        )
        or len({member.portfolio_id for member in source.members}) != len(source.members)
    ):
        raise source_contract_invalid()
    if source.tenant_id is not None and source.tenant_id != caller.tenant_id:
        raise AdvisorBookServiceError(
            code="advisor_book_tenant_scope_mismatch",
            message="Advisor-book access is not available for this tenant scope.",
            status_code=403,
        )
