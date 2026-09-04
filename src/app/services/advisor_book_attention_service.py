"""Compose Advise-owned attention counts for the trusted advisor-book cohort.

One bounded, paged read of the caller's Advise action feed is intersected with the
Core-owned membership cohort on portfolio identity. Gateway counts source-owned items
and preserves their reason codes; it never reinterprets action status, priority, or
business meaning, and never maps the Core and Advise caller identities onto each other.
"""

from datetime import date

from app.contracts.advisor_book import AdvisorBookScope
from app.contracts.advisor_book_attention import (
    AdvisorBookAttentionResponse,
    AdvisorBookAttentionSource,
    AdvisorBookAttentionSummary,
    AdvisorBookPortfolioAttention,
)
from app.contracts.advisor_cockpit_action_models import AdvisorCockpitActionItem
from app.services.advisor_book_access_policy import AdvisorBookCallerContext
from app.services.advisor_book_service import AdvisorBookService
from app.services.advisor_book_service_errors import source_incomplete
from app.services.advisor_cockpit_access_policy import AdvisorCockpitCallerContext
from app.services.advisor_cockpit_service import AdvisorCockpitService

# Matches the typed AdvisorCockpitActionPage items bound; a larger request could make
# a legitimate source page fail projection.
_ACTION_PAGE_SIZE = 64
# Bounded fan-in: at most this many source pages are read per request. A feed that is
# still not exhausted is reported as partial coverage, never silently truncated.
_MAX_ACTION_PAGES = 5
_MAX_ITEM_REASON_CODES = 3


class AdvisorBookAttentionService:
    def __init__(
        self,
        *,
        membership_service: AdvisorBookService,
        cockpit_service: AdvisorCockpitService,
    ) -> None:
        self._membership_service = membership_service
        self._cockpit_service = cockpit_service

    async def get_attention(
        self,
        *,
        book_caller: AdvisorBookCallerContext,
        cockpit_caller: AdvisorCockpitCallerContext,
        as_of_date: date,
        correlation_id: str,
    ) -> AdvisorBookAttentionResponse:
        membership = await self._membership_service.load_membership_source(
            caller=book_caller,
            as_of_date=as_of_date,
            correlation_id=correlation_id,
        )
        cohort: list[str] = []
        if membership is not None:
            if membership.supportability.state == "INCOMPLETE":
                raise source_incomplete()
            cohort = [member.portfolio_id for member in membership.members]
        if not cohort:
            return _empty_response(
                book_caller=book_caller,
                as_of_date=as_of_date,
                correlation_id=correlation_id,
            )

        actions, source_stated_total, fully_read = await self._load_actions(
            cockpit_caller=cockpit_caller,
            correlation_id=correlation_id,
        )
        return _response_from_sources(
            book_caller=book_caller,
            as_of_date=as_of_date,
            correlation_id=correlation_id,
            cohort=cohort,
            actions=actions,
            source_stated_total=source_stated_total,
            fully_read=fully_read,
        )

    async def _load_actions(
        self,
        *,
        cockpit_caller: AdvisorCockpitCallerContext,
        correlation_id: str,
    ) -> tuple[list[AdvisorCockpitActionItem], int | None, bool]:
        actions: list[AdvisorCockpitActionItem] = []
        source_stated_total: int | None = None
        cursor: str | None = None
        for _ in range(_MAX_ACTION_PAGES):
            params: dict[str, object] = {"limit": _ACTION_PAGE_SIZE}
            if cursor is not None:
                params["cursor"] = cursor
            envelope = await self._cockpit_service.list_actions(
                params=params,
                caller_headers=cockpit_caller.upstream_headers(),
                correlation_id=correlation_id,
            )
            page = envelope.data
            actions.extend(page.items)
            if page.total_count is not None:
                source_stated_total = page.total_count
            cursor = page.next_cursor
            if cursor is None:
                return actions, source_stated_total, True
        return actions, source_stated_total, False


def _count_actions(
    *,
    cohort: list[str],
    actions: list[AdvisorCockpitActionItem],
) -> tuple[list[AdvisorBookPortfolioAttention], int, int]:
    counts: dict[str, int] = {portfolio_id: 0 for portfolio_id in cohort}
    reason_codes: dict[str, list[str]] = {portfolio_id: [] for portfolio_id in cohort}
    unassigned = 0
    outside_book = 0
    for action in actions:
        portfolio_id = action.portfolio_id
        if portfolio_id is None:
            unassigned += 1
        elif portfolio_id in counts:
            counts[portfolio_id] += 1
            codes = reason_codes[portfolio_id]
            for code in action.reason_codes:
                if code not in codes and len(codes) < _MAX_ITEM_REASON_CODES:
                    codes.append(code)
        else:
            outside_book += 1
    items = [
        AdvisorBookPortfolioAttention(
            portfolio_id=portfolio_id,
            action_count=counts[portfolio_id],
            reason_codes=reason_codes[portfolio_id],
        )
        for portfolio_id in cohort
    ]
    return items, unassigned, outside_book


def _response_from_sources(
    *,
    book_caller: AdvisorBookCallerContext,
    as_of_date: date,
    correlation_id: str,
    cohort: list[str],
    actions: list[AdvisorCockpitActionItem],
    source_stated_total: int | None,
    fully_read: bool,
) -> AdvisorBookAttentionResponse:
    items, unassigned, outside_book = _count_actions(cohort=cohort, actions=actions)
    return AdvisorBookAttentionResponse(
        correlation_id=correlation_id,
        scope=_scope(book_caller=book_caller, as_of_date=as_of_date),
        summary=AdvisorBookAttentionSummary(
            portfolio_count=len(cohort),
            portfolios_with_actions=sum(1 for item in items if item.action_count),
            action_count=sum(item.action_count for item in items),
            unassigned_action_count=unassigned,
            outside_book_action_count=outside_book,
            source_stated_total=source_stated_total,
            coverage_state="complete" if fully_read else "partial",
            coverage_reason=(
                "action_feed_fully_read" if fully_read else "action_page_budget_reached"
            ),
            state="supported",
        ),
        items=items,
        source=_source(as_of_date=as_of_date),
    )


def _empty_response(
    *,
    book_caller: AdvisorBookCallerContext,
    as_of_date: date,
    correlation_id: str,
) -> AdvisorBookAttentionResponse:
    return AdvisorBookAttentionResponse(
        correlation_id=correlation_id,
        scope=_scope(book_caller=book_caller, as_of_date=as_of_date),
        summary=AdvisorBookAttentionSummary(
            portfolio_count=0,
            portfolios_with_actions=0,
            action_count=0,
            unassigned_action_count=0,
            outside_book_action_count=0,
            source_stated_total=None,
            coverage_state="not_read",
            coverage_reason="empty_book_feed_not_read",
            state="empty",
        ),
        items=[],
        source=_source(as_of_date=as_of_date),
    )


def _scope(*, book_caller: AdvisorBookCallerContext, as_of_date: date) -> AdvisorBookScope:
    return AdvisorBookScope(
        kind="own_book",
        label="My book",
        as_of_date=as_of_date,
        booking_center_code=book_caller.booking_center_code,
    )


def _source(*, as_of_date: date) -> AdvisorBookAttentionSource:
    return AdvisorBookAttentionSource(
        source_service="lotus-advise",
        source_route="/advisory/cockpit/actions",
        membership_as_of_date=as_of_date,
    )
