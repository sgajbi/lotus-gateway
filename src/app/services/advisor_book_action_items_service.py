"""Compose Advise-owned action-item counts for the trusted advisor-book cohort.

One bounded, paged read of the caller's Advise action feed is intersected with the
Core-owned membership cohort on portfolio identity. Gateway counts the items the source
returns — whatever their source status — and preserves their reason codes; it never
defines which statuses are "attention", never reinterprets action meaning, and never maps
the Core and Advise caller identities onto each other.

The whole composition (membership plus every action page) runs under one elapsed budget
reusing the existing AnalyticsPollBudget primitive: when the budget can no longer admit
another source call, already verified items are preserved and coverage is reported as an
explicit partial lower bound — a timeout never becomes zero action items.
"""

from datetime import date

from app.contracts.advisor_book import AdvisorBookProvenance
from app.contracts.advisor_book_action_items import (
    AdvisorBookActionItemCoverageReason,
    AdvisorBookActionItemCoverageState,
    AdvisorBookActionItemsResponse,
    AdvisorBookActionItemsSource,
    AdvisorBookActionItemsSummary,
)
from app.execution_budget import (
    AnalyticsPollBudget,
    AnalyticsRequestDeadlineExceeded,
)
from app.services.advisor_book_access_policy import AdvisorBookCallerContext
from app.services.advisor_book_action_items_read import (
    ActionFeedRead,
    count_actions,
)
from app.services.advisor_book_provenance import membership_provenance, own_book_scope
from app.services.advisor_book_service import AdvisorBookService
from app.services.advisor_book_service_errors import AdvisorBookServiceError, source_incomplete
from app.services.advisor_cockpit_access_policy import AdvisorCockpitCallerContext
from app.services.advisor_cockpit_service import AdvisorCockpitService

# Matches the typed AdvisorCockpitActionPage items bound; a larger request could make
# a legitimate source page fail projection.
_ACTION_PAGE_SIZE = 64
# Bounded fan-in: at most this many source pages are read per request. A feed that is
# still not exhausted is reported as partial coverage, never silently truncated.
_MAX_ACTION_PAGES = 5

_Coverage = tuple[AdvisorBookActionItemCoverageState, AdvisorBookActionItemCoverageReason]
_COMPLETE: _Coverage = ("complete", "action_feed_fully_read")
_PARTIAL_BUDGET: _Coverage = ("partial", "action_page_budget_reached")
_PARTIAL_DEADLINE: _Coverage = ("partial", "composition_deadline_reached")
_PARTIAL_TOTAL_MISMATCH: _Coverage = ("partial", "source_total_mismatch")
_PARTIAL_INCONSISTENT: _Coverage = ("partial", "source_pagination_inconsistent")
_PARTIAL_TOTAL_NOT_STATED: _Coverage = ("partial", "source_total_not_stated")


class AdvisorBookActionItemsService:
    def __init__(
        self,
        *,
        membership_service: AdvisorBookService,
        cockpit_service: AdvisorCockpitService,
        composition_deadline_seconds: float,
    ) -> None:
        self._membership_service = membership_service
        self._cockpit_service = cockpit_service
        self._composition_deadline_seconds = composition_deadline_seconds

    async def get_action_items(
        self,
        *,
        book_caller: AdvisorBookCallerContext,
        cockpit_caller: AdvisorCockpitCallerContext,
        as_of_date: date,
        correlation_id: str,
    ) -> AdvisorBookActionItemsResponse:
        budget = AnalyticsPollBudget.from_timeout(self._composition_deadline_seconds)
        try:
            membership = await budget.run_request(
                lambda: self._membership_service.load_membership_source(
                    caller=book_caller,
                    as_of_date=as_of_date,
                    correlation_id=correlation_id,
                )
            )
        except AnalyticsRequestDeadlineExceeded as exc:
            raise _composition_deadline_exhausted() from exc
        cohort: list[str] = []
        provenance: AdvisorBookProvenance | None = None
        if membership is not None:
            if membership.supportability.state == "INCOMPLETE":
                raise source_incomplete()
            cohort = [member.portfolio_id for member in membership.members]
            provenance = membership_provenance(membership)
        if not cohort:
            return _empty_response(
                book_caller=book_caller,
                as_of_date=as_of_date,
                correlation_id=correlation_id,
                membership_provenance=provenance,
            )

        read, coverage = await self._read_action_feed(
            cockpit_caller=cockpit_caller,
            correlation_id=correlation_id,
            budget=budget,
        )
        return _response_from_sources(
            book_caller=book_caller,
            as_of_date=as_of_date,
            correlation_id=correlation_id,
            cohort=cohort,
            read=read,
            coverage=coverage,
            membership_provenance=provenance,
        )

    async def _read_action_feed(
        self,
        *,
        cockpit_caller: AdvisorCockpitCallerContext,
        correlation_id: str,
        budget: AnalyticsPollBudget,
    ) -> tuple[ActionFeedRead, _Coverage]:
        read = ActionFeedRead()
        cursor: str | None = None
        for _ in range(_MAX_ACTION_PAGES):
            if budget.is_expired:
                return read, _PARTIAL_DEADLINE
            params: dict[str, object] = {"limit": _ACTION_PAGE_SIZE}
            if cursor is not None:
                params["cursor"] = cursor
            try:
                envelope = await budget.run_request(
                    lambda: self._cockpit_service.list_actions(
                        params=params,
                        caller_headers=cockpit_caller.upstream_headers(),
                        correlation_id=correlation_id,
                    )
                )
            except AnalyticsRequestDeadlineExceeded:
                # Preserve what was already verified; the deadline never becomes zero.
                return read, _PARTIAL_DEADLINE
            page = envelope.data
            read.absorb(page.items, page.total_count)
            if page.next_cursor == cursor and page.next_cursor is not None:
                # A cursor that does not advance would loop over the same page.
                read.inconsistent = True
                return read, _PARTIAL_INCONSISTENT
            cursor = page.next_cursor
            if cursor is None:
                return read, _final_coverage(read)
        return read, (_PARTIAL_INCONSISTENT if read.inconsistent else _PARTIAL_BUDGET)


def _final_coverage(read: ActionFeedRead) -> _Coverage:
    if read.inconsistent:
        return _PARTIAL_INCONSISTENT
    # A missing cursor alone is not proof of a fully read feed: complete coverage
    # requires a source-stated total that matches the delivered items exactly.
    if read.source_stated_total is None:
        return _PARTIAL_TOTAL_NOT_STATED
    if read.source_stated_total != len(read.actions):
        return _PARTIAL_TOTAL_MISMATCH
    return _COMPLETE


def _composition_deadline_exhausted() -> AdvisorBookServiceError:
    return AdvisorBookServiceError(
        code="advisor_book_action_items_deadline_exhausted",
        message=(
            "The action-items composition deadline was exhausted before the membership "
            "cohort could be resolved."
        ),
        status_code=504,
    )


def _response_from_sources(
    *,
    book_caller: AdvisorBookCallerContext,
    as_of_date: date,
    correlation_id: str,
    cohort: list[str],
    read: ActionFeedRead,
    coverage: _Coverage,
    membership_provenance: AdvisorBookProvenance | None,
) -> AdvisorBookActionItemsResponse:
    items, unassigned, outside_book = count_actions(cohort=cohort, actions=read.actions)
    coverage_state, coverage_reason = coverage
    return AdvisorBookActionItemsResponse(
        correlation_id=correlation_id,
        scope=own_book_scope(
            booking_center_code=book_caller.booking_center_code, as_of_date=as_of_date
        ),
        summary=AdvisorBookActionItemsSummary(
            portfolio_count=len(cohort),
            portfolios_with_action_items=sum(1 for item in items if item.action_item_count),
            action_item_count=sum(item.action_item_count for item in items),
            unassigned_action_item_count=unassigned,
            outside_book_action_item_count=outside_book,
            source_stated_total=read.source_stated_total,
            coverage_state=coverage_state,
            coverage_reason=coverage_reason,
            state="supported",
        ),
        items=items,
        source=_source(as_of_date=as_of_date),
        membership_provenance=membership_provenance,
    )


def _empty_response(
    *,
    book_caller: AdvisorBookCallerContext,
    as_of_date: date,
    correlation_id: str,
    membership_provenance: AdvisorBookProvenance | None,
) -> AdvisorBookActionItemsResponse:
    return AdvisorBookActionItemsResponse(
        correlation_id=correlation_id,
        scope=own_book_scope(
            booking_center_code=book_caller.booking_center_code, as_of_date=as_of_date
        ),
        summary=AdvisorBookActionItemsSummary(
            portfolio_count=0,
            portfolios_with_action_items=0,
            action_item_count=0,
            unassigned_action_item_count=0,
            outside_book_action_item_count=0,
            source_stated_total=None,
            coverage_state="not_read",
            coverage_reason="empty_book_feed_not_read",
            state="empty",
        ),
        items=[],
        source=_source(as_of_date=as_of_date),
        membership_provenance=membership_provenance,
    )


def _source(*, as_of_date: date) -> AdvisorBookActionItemsSource:
    return AdvisorBookActionItemsSource(
        source_service="lotus-advise",
        source_route="/advisory/cockpit/actions",
        membership_as_of_date=as_of_date,
    )
