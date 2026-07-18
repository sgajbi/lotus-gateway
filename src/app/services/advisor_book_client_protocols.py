from typing import Any, Protocol


class AdvisorBookMembershipClient(Protocol):
    async def get_portfolio_manager_book_memberships(
        self,
        *,
        portfolio_manager_id: str,
        as_of_date: str,
        booking_center_code: str,
        portfolio_types: list[str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...
