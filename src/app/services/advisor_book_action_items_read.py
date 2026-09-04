"""Accumulation and counting primitives for the advisor-book action feed read."""

from datetime import date

from app.contracts.advisor_book_action_items import (
    AdvisorBookActionItemCoverageReason,
    AdvisorBookActionItemCoverageState,
    AdvisorBookActionItemsSource,
    AdvisorBookActionItemsSummary,
    AdvisorBookPortfolioActionItems,
)
from app.contracts.advisor_cockpit_action_models import AdvisorCockpitActionItem
from app.execution_budget import AnalyticsPollBudget, AnalyticsRequestDeadlineExceeded
from app.services.advisor_cockpit_access_policy import AdvisorCockpitCallerContext
from app.services.advisor_cockpit_service import AdvisorCockpitService

_MAX_ITEM_REASON_CODES = 3


class ActionFeedRead:
    """Accumulated source evidence from one bounded, budgeted feed read."""

    def __init__(self) -> None:
        self.actions: list[AdvisorCockpitActionItem] = []
        self.seen_action_ids: set[str] = set()
        self.source_stated_total: int | None = None
        self.inconsistent = False

    def absorb(self, items: list[AdvisorCockpitActionItem], total_count: int | None) -> None:
        for item in items:
            if item.action_item_id in self.seen_action_ids:
                # The same immutable action identity on two pages means the mutable
                # feed shifted underneath the read; keep one copy, stay partial.
                self.inconsistent = True
                continue
            self.seen_action_ids.add(item.action_item_id)
            self.actions.append(item)
        if total_count is not None:
            if self.source_stated_total is not None and self.source_stated_total != total_count:
                self.inconsistent = True
            self.source_stated_total = total_count


def count_actions(
    *,
    cohort: list[str],
    actions: list[AdvisorCockpitActionItem],
) -> tuple[list[AdvisorBookPortfolioActionItems], int, int]:
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
        AdvisorBookPortfolioActionItems(
            portfolio_id=portfolio_id,
            action_item_count=counts[portfolio_id],
            reason_codes=reason_codes[portfolio_id],
        )
        for portfolio_id in cohort
    ]
    return items, unassigned, outside_book


ActionFeedCoverage = tuple[AdvisorBookActionItemCoverageState, AdvisorBookActionItemCoverageReason]
FEED_COMPLETE: ActionFeedCoverage = ("complete", "action_feed_fully_read")
FEED_PARTIAL_BUDGET: ActionFeedCoverage = ("partial", "action_page_budget_reached")
FEED_PARTIAL_DEADLINE: ActionFeedCoverage = ("partial", "composition_deadline_reached")
FEED_PARTIAL_TOTAL_MISMATCH: ActionFeedCoverage = ("partial", "source_total_mismatch")
FEED_PARTIAL_INCONSISTENT: ActionFeedCoverage = ("partial", "source_pagination_inconsistent")
FEED_PARTIAL_TOTAL_NOT_STATED: ActionFeedCoverage = ("partial", "source_total_not_stated")

# Matches the typed AdvisorCockpitActionPage items bound; a larger request could make
# a legitimate source page fail projection.
ACTION_PAGE_SIZE = 64
# Bounded fan-in: at most this many source pages are read per request. A feed that is
# still not exhausted is reported as partial coverage, never silently truncated.
MAX_ACTION_PAGES = 5


async def read_action_feed(
    *,
    cockpit_service: AdvisorCockpitService,
    cockpit_caller: AdvisorCockpitCallerContext,
    correlation_id: str,
    budget: AnalyticsPollBudget,
) -> tuple[ActionFeedRead, ActionFeedCoverage]:
    """One bounded, budgeted read of the caller's Advise action feed."""

    read = ActionFeedRead()
    cursor: str | None = None
    for _ in range(MAX_ACTION_PAGES):
        if budget.is_expired:
            return read, FEED_PARTIAL_DEADLINE
        params: dict[str, object] = {"limit": ACTION_PAGE_SIZE}
        if cursor is not None:
            params["cursor"] = cursor
        try:
            envelope = await budget.run_request(
                lambda: cockpit_service.list_actions(
                    params=params,
                    caller_headers=cockpit_caller.upstream_headers(),
                    correlation_id=correlation_id,
                )
            )
        except AnalyticsRequestDeadlineExceeded:
            # Preserve what was already verified; the deadline never becomes zero.
            return read, FEED_PARTIAL_DEADLINE
        page = envelope.data
        read.absorb(page.items, page.total_count)
        if page.next_cursor == cursor and page.next_cursor is not None:
            # A cursor that does not advance would loop over the same page.
            read.inconsistent = True
            return read, FEED_PARTIAL_INCONSISTENT
        cursor = page.next_cursor
        if cursor is None:
            return read, _final_coverage(read)
    return read, (FEED_PARTIAL_INCONSISTENT if read.inconsistent else FEED_PARTIAL_BUDGET)


def _final_coverage(read: ActionFeedRead) -> ActionFeedCoverage:
    if read.inconsistent:
        return FEED_PARTIAL_INCONSISTENT
    # A missing cursor alone is not proof of a fully read feed: complete coverage
    # requires a source-stated total that matches the delivered items exactly.
    if read.source_stated_total is None:
        return FEED_PARTIAL_TOTAL_NOT_STATED
    if read.source_stated_total != len(read.actions):
        return FEED_PARTIAL_TOTAL_MISMATCH
    return FEED_COMPLETE


def summarize_action_read(
    *,
    cohort: list[str],
    read: ActionFeedRead,
    coverage: ActionFeedCoverage,
) -> tuple[list[AdvisorBookPortfolioActionItems], AdvisorBookActionItemsSummary]:
    """Intersect one feed read with the frozen cohort into the owned summary shape."""

    items, unassigned, outside_book = count_actions(cohort=cohort, actions=read.actions)
    coverage_state, coverage_reason = coverage
    summary = AdvisorBookActionItemsSummary(
        portfolio_count=len(cohort),
        portfolios_with_action_items=sum(1 for item in items if item.action_item_count),
        action_item_count=sum(item.action_item_count for item in items),
        unassigned_action_item_count=unassigned,
        outside_book_action_item_count=outside_book,
        source_stated_total=read.source_stated_total,
        coverage_state=coverage_state,
        coverage_reason=coverage_reason,
        state="supported",
    )
    return items, summary


def empty_action_items_summary() -> AdvisorBookActionItemsSummary:
    return AdvisorBookActionItemsSummary(
        portfolio_count=0,
        portfolios_with_action_items=0,
        action_item_count=0,
        unassigned_action_item_count=0,
        outside_book_action_item_count=0,
        source_stated_total=None,
        coverage_state="not_read",
        coverage_reason="empty_book_feed_not_read",
        state="empty",
    )


def action_items_source(*, membership_as_of_date: date) -> AdvisorBookActionItemsSource:
    return AdvisorBookActionItemsSource(
        source_service="lotus-advise",
        source_route="/advisory/cockpit/actions",
        membership_as_of_date=membership_as_of_date,
    )
