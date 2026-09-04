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
from app.contracts.advisor_book_action_items import AdvisorBookActionItemsResponse
from app.execution_budget import (
    AnalyticsPollBudget,
    AnalyticsRequestDeadlineExceeded,
)
from app.services.advisor_book_access_policy import AdvisorBookCallerContext
from app.services.advisor_book_action_items_read import (
    action_items_source,
    empty_action_items_summary,
    read_action_feed,
    summarize_action_read,
)
from app.services.advisor_book_provenance import membership_provenance, own_book_scope
from app.services.advisor_book_service import AdvisorBookService
from app.services.advisor_book_service_errors import AdvisorBookServiceError, source_incomplete
from app.services.advisor_cockpit_access_policy import AdvisorCockpitCallerContext
from app.services.advisor_cockpit_service import AdvisorCockpitService


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

        read, coverage = await read_action_feed(
            cockpit_service=self._cockpit_service,
            cockpit_caller=cockpit_caller,
            correlation_id=correlation_id,
            budget=budget,
        )
        items, summary = summarize_action_read(cohort=cohort, read=read, coverage=coverage)
        return AdvisorBookActionItemsResponse(
            correlation_id=correlation_id,
            scope=own_book_scope(
                booking_center_code=book_caller.booking_center_code, as_of_date=as_of_date
            ),
            summary=summary,
            items=items,
            source=action_items_source(membership_as_of_date=as_of_date),
            membership_provenance=provenance,
        )


def _composition_deadline_exhausted() -> AdvisorBookServiceError:
    return AdvisorBookServiceError(
        code="advisor_book_action_items_deadline_exhausted",
        message=(
            "The action-items composition deadline was exhausted before the membership "
            "cohort could be resolved."
        ),
        status_code=504,
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
        summary=empty_action_items_summary(),
        items=[],
        source=action_items_source(membership_as_of_date=as_of_date),
        membership_provenance=membership_provenance,
    )
