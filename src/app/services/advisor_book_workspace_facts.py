"""Independent fact-block loaders for the Advisor Book workspace composition.

Each loader turns one source read for the frozen cohort into a typed fact block plus
per-member facts, and degrades on its own failure into an explicit unavailable block
with a bounded reason — it never raises for a source failure and never invents data.
"""

from dataclasses import dataclass
from datetime import date
from typing import Literal

from fastapi import HTTPException

from app.contracts.advisor_book_action_items import AdvisorBookPortfolioActionItems
from app.contracts.advisor_book_summary import AdvisorBookValueItem
from app.contracts.advisor_book_workspace import (
    AdvisorBookWorkspaceActionFacts,
    AdvisorBookWorkspaceActionReason,
    AdvisorBookWorkspaceValueFacts,
    AdvisorBookWorkspaceValueReason,
)
from app.execution_budget import (
    AnalyticsPollBudget,
    AnalyticsRequestDeadlineExceeded,
)
from app.services.advisor_book_action_items_read import (
    action_items_source,
    empty_action_items_summary,
    read_action_feed,
    summarize_action_read,
)
from app.services.advisor_book_client_protocols import AdvisorBookValueClient
from app.services.advisor_book_service_errors import AdvisorBookServiceError
from app.services.advisor_book_value_facts import (
    empty_value_summary,
    load_and_validate_value_source,
    value_item,
    value_source_descriptor,
    value_summary,
)
from app.services.advisor_cockpit_access_policy import AdvisorCockpitCallerContext
from app.services.advisor_cockpit_service import AdvisorCockpitService


@dataclass(frozen=True)
class AdviseScopeUnavailable:
    """The caller presented no usable Advise advisor scope for the action fact."""

    reason_code: Literal[
        "advise_scope_not_presented",
        "advise_scope_invalid",
        "advise_scope_not_advisor",
    ]


AdviseScope = AdvisorCockpitCallerContext | AdviseScopeUnavailable

ValueFactsResult = tuple[AdvisorBookWorkspaceValueFacts, dict[str, AdvisorBookValueItem]]
ActionFactsResult = tuple[
    AdvisorBookWorkspaceActionFacts, dict[str, AdvisorBookPortfolioActionItems]
]


async def load_value_facts(
    *,
    value_client: AdvisorBookValueClient,
    budget: AnalyticsPollBudget,
    cohort: list[str],
    as_of_date: date,
    reporting_currency: str,
    correlation_id: str,
) -> ValueFactsResult:
    try:
        value_source = await budget.run_request(
            lambda: load_and_validate_value_source(
                value_client=value_client,
                correlation_id=correlation_id,
                portfolio_ids=cohort,
                as_of_date=as_of_date,
                reporting_currency=reporting_currency,
            )
        )
    except AnalyticsRequestDeadlineExceeded:
        return _value_unavailable("composition_deadline_reached"), {}
    except AdvisorBookServiceError as exc:
        reason: AdvisorBookWorkspaceValueReason = (
            "value_source_contract_invalid"
            if exc.code == "advisor_book_value_source_contract_invalid"
            else "value_source_unavailable"
        )
        return _value_unavailable(reason), {}
    items = {member.portfolio_id: value_item(member) for member in value_source.portfolios}
    covered_count = sum(item.state == "supported" for item in items.values())
    resolved_currency = (value_source.reporting_currency or "").strip().upper()
    facts = AdvisorBookWorkspaceValueFacts(
        state="stated",
        reason_code="value_facts_stated",
        summary=value_summary(
            value_source=value_source,
            covered_count=covered_count,
            reporting_currency=resolved_currency,
        ),
        source=value_source_descriptor(
            resolved_as_of_date=value_source.resolved_as_of_date,
            reporting_currency=resolved_currency,
        ),
    )
    return facts, items


async def load_action_facts(
    *,
    cockpit_service: AdvisorCockpitService,
    budget: AnalyticsPollBudget,
    cohort: list[str],
    advise_scope: AdviseScope,
    as_of_date: date,
    correlation_id: str,
) -> ActionFactsResult:
    if isinstance(advise_scope, AdviseScopeUnavailable):
        return _action_unavailable(advise_scope.reason_code), {}
    try:
        read, coverage = await read_action_feed(
            cockpit_service=cockpit_service,
            cockpit_caller=advise_scope,
            correlation_id=correlation_id,
            budget=budget,
        )
    except HTTPException:
        # Any feed failure — outage or a source-refused read — degrades only this
        # fact block; the value composition and the cohort rows still stand.
        return _action_unavailable("action_feed_unavailable"), {}
    items, summary = summarize_action_read(cohort=cohort, read=read, coverage=coverage)
    facts = AdvisorBookWorkspaceActionFacts(
        state="stated",
        reason_code="action_facts_stated",
        summary=summary,
        source=action_items_source(membership_as_of_date=as_of_date),
    )
    return facts, {item.portfolio_id: item for item in items}


def empty_value_facts(
    *, as_of_date: date, reporting_currency: str
) -> AdvisorBookWorkspaceValueFacts:
    return AdvisorBookWorkspaceValueFacts(
        state="stated",
        reason_code="value_facts_stated",
        summary=empty_value_summary(as_of_date=as_of_date, reporting_currency=reporting_currency),
        source=value_source_descriptor(
            resolved_as_of_date=as_of_date,
            reporting_currency=reporting_currency,
        ),
    )


def empty_action_facts(
    *, advise_scope: AdviseScope, as_of_date: date
) -> AdvisorBookWorkspaceActionFacts:
    if isinstance(advise_scope, AdviseScopeUnavailable):
        return _action_unavailable(advise_scope.reason_code)
    return AdvisorBookWorkspaceActionFacts(
        state="stated",
        reason_code="action_facts_stated",
        summary=empty_action_items_summary(),
        source=action_items_source(membership_as_of_date=as_of_date),
    )


def _value_unavailable(reason: AdvisorBookWorkspaceValueReason) -> AdvisorBookWorkspaceValueFacts:
    return AdvisorBookWorkspaceValueFacts(state="unavailable", reason_code=reason)


def _action_unavailable(
    reason: AdvisorBookWorkspaceActionReason,
) -> AdvisorBookWorkspaceActionFacts:
    return AdvisorBookWorkspaceActionFacts(state="unavailable", reason_code=reason)
