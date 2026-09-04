"""Primary Advisor Book workspace composition.

Membership is resolved exactly once, then the frozen cohort is enriched concurrently —
Core bulk value facts and Advise action-item facts — under one elapsed composition
deadline. Each enrichment degrades independently into an explicit unavailable fact
block with a bounded reason; rows for the frozen cohort always survive. Only failing
to resolve membership itself is fatal.
"""

import asyncio
from datetime import date

from app.contracts.advisor_book import AdvisorBookProvenance
from app.contracts.advisor_book_workspace import (
    AdvisorBookWorkspaceResponse,
    AdvisorBookWorkspaceRow,
)
from app.execution_budget import (
    AnalyticsPollBudget,
    AnalyticsRequestDeadlineExceeded,
)
from app.services.advisor_book_access_policy import AdvisorBookCallerContext
from app.services.advisor_book_client_protocols import AdvisorBookValueClient
from app.services.advisor_book_provenance import membership_provenance, own_book_scope
from app.services.advisor_book_service import AdvisorBookService
from app.services.advisor_book_service_errors import AdvisorBookServiceError, source_incomplete
from app.services.advisor_book_workspace_facts import (
    AdviseScope,
    empty_action_facts,
    empty_value_facts,
    load_action_facts,
    load_value_facts,
)
from app.services.advisor_cockpit_service import AdvisorCockpitService


class AdvisorBookWorkspaceService:
    def __init__(
        self,
        *,
        membership_service: AdvisorBookService,
        value_client: AdvisorBookValueClient,
        cockpit_service: AdvisorCockpitService,
        composition_deadline_seconds: float,
    ) -> None:
        self._membership_service = membership_service
        self._value_client = value_client
        self._cockpit_service = cockpit_service
        self._composition_deadline_seconds = composition_deadline_seconds

    async def get_workspace(
        self,
        *,
        book_caller: AdvisorBookCallerContext,
        advise_scope: AdviseScope,
        as_of_date: date,
        reporting_currency: str,
        correlation_id: str,
    ) -> AdvisorBookWorkspaceResponse:
        budget = AnalyticsPollBudget.from_timeout(self._composition_deadline_seconds)
        cohort, provenance = await self._resolve_cohort(
            budget=budget,
            book_caller=book_caller,
            as_of_date=as_of_date,
            correlation_id=correlation_id,
        )
        if not cohort:
            return _empty_workspace(
                book_caller=book_caller,
                advise_scope=advise_scope,
                as_of_date=as_of_date,
                reporting_currency=reporting_currency,
                correlation_id=correlation_id,
                provenance=provenance,
            )
        return await self._composed_workspace(
            budget=budget,
            book_caller=book_caller,
            advise_scope=advise_scope,
            as_of_date=as_of_date,
            reporting_currency=reporting_currency,
            correlation_id=correlation_id,
            cohort=cohort,
            provenance=provenance,
        )

    async def _composed_workspace(
        self,
        *,
        budget: AnalyticsPollBudget,
        book_caller: AdvisorBookCallerContext,
        advise_scope: AdviseScope,
        as_of_date: date,
        reporting_currency: str,
        correlation_id: str,
        cohort: list[str],
        provenance: AdvisorBookProvenance | None,
    ) -> AdvisorBookWorkspaceResponse:
        (value_facts, value_items), (action_facts, action_items) = await asyncio.gather(
            load_value_facts(
                value_client=self._value_client,
                budget=budget,
                cohort=cohort,
                as_of_date=as_of_date,
                reporting_currency=reporting_currency,
                correlation_id=correlation_id,
            ),
            load_action_facts(
                cockpit_service=self._cockpit_service,
                budget=budget,
                cohort=cohort,
                advise_scope=advise_scope,
                as_of_date=as_of_date,
                correlation_id=correlation_id,
            ),
        )
        rows = [
            AdvisorBookWorkspaceRow(
                portfolio_id=portfolio_id,
                value=value_items.get(portfolio_id),
                action_items=action_items.get(portfolio_id),
            )
            for portfolio_id in cohort
        ]
        return AdvisorBookWorkspaceResponse(
            correlation_id=correlation_id,
            scope=own_book_scope(
                booking_center_code=book_caller.booking_center_code, as_of_date=as_of_date
            ),
            rows=rows,
            value_facts=value_facts,
            action_facts=action_facts,
            membership_provenance=provenance,
        )

    async def _resolve_cohort(
        self,
        *,
        budget: AnalyticsPollBudget,
        book_caller: AdvisorBookCallerContext,
        as_of_date: date,
        correlation_id: str,
    ) -> tuple[list[str], AdvisorBookProvenance | None]:
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
        if membership is None:
            return [], None
        if membership.supportability.state == "INCOMPLETE":
            raise source_incomplete()
        cohort = [member.portfolio_id for member in membership.members]
        return cohort, membership_provenance(membership)


def _empty_workspace(
    *,
    book_caller: AdvisorBookCallerContext,
    advise_scope: AdviseScope,
    as_of_date: date,
    reporting_currency: str,
    correlation_id: str,
    provenance: AdvisorBookProvenance | None,
) -> AdvisorBookWorkspaceResponse:
    return AdvisorBookWorkspaceResponse(
        correlation_id=correlation_id,
        scope=own_book_scope(
            booking_center_code=book_caller.booking_center_code, as_of_date=as_of_date
        ),
        rows=[],
        value_facts=empty_value_facts(as_of_date=as_of_date, reporting_currency=reporting_currency),
        action_facts=empty_action_facts(advise_scope=advise_scope, as_of_date=as_of_date),
        membership_provenance=provenance,
    )


def _composition_deadline_exhausted() -> AdvisorBookServiceError:
    return AdvisorBookServiceError(
        code="advisor_book_workspace_deadline_exhausted",
        message=(
            "The workspace composition deadline was exhausted before the membership "
            "cohort could be resolved."
        ),
        status_code=504,
    )
