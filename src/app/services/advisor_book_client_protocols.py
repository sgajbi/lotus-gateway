from typing import Any, Protocol


class AdvisorBookMembershipClient(Protocol):
    async def get_portfolio_manager_book_memberships(
        self,
        *,
        portfolio_manager_id: str,
        as_of_date: str,
        booking_center_code: str,
        portfolio_types: list[str],
        include_inactive: bool = False,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class AdvisorBookValueClient(Protocol):
    async def query_bulk_portfolio_summary(
        self,
        *,
        correlation_id: str,
        portfolio_ids: list[str],
        as_of_date: str | None = None,
        reporting_currency: str | None = None,
    ) -> tuple[int, dict[str, Any]]: ...
