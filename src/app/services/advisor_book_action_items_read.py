"""Accumulation and counting primitives for the advisor-book action feed read."""

from app.contracts.advisor_book_action_items import AdvisorBookPortfolioActionItems
from app.contracts.advisor_cockpit_action_models import AdvisorCockpitActionItem

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
