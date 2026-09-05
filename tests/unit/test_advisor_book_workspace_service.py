import asyncio
from datetime import date
from decimal import Decimal
from typing import Any

import pytest
from fastapi import HTTPException

from app.contracts.advisor_cockpit_action_envelopes import (
    AdvisorCockpitActionPageEnvelopeResponse,
)
from app.contracts.advisor_cockpit_action_models import AdvisorCockpitActionPage
from app.services.advisor_book_service import AdvisorBookService, AdvisorBookServiceError
from app.services.advisor_book_workspace_facts import AdviseScopeUnavailable
from app.services.advisor_book_workspace_service import AdvisorBookWorkspaceService
from tests.support.advisor_book_fixtures import (
    MembershipClient,
    ValueClient,
    book_caller,
    bulk_payload,
    cockpit_caller,
    covered_member,
    membership_payload,
    uncovered_member,
)
from tests.support.advisor_cockpit_fixtures import advisor_action_item_payload


class _StubCockpitService:
    def __init__(
        self,
        pages: list[AdvisorCockpitActionPage] | None = None,
        page_delays: dict[int, float] | None = None,
    ) -> None:
        self.pages = pages or []
        self.page_delays = page_delays or {}
        self.calls: list[dict[str, Any]] = []
        self.error: HTTPException | None = None

    async def list_actions(
        self,
        *,
        params: dict[str, Any],
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> AdvisorCockpitActionPageEnvelopeResponse:
        call_index = len(self.calls)
        self.calls.append(
            {"params": params, "caller_headers": caller_headers, "correlation_id": correlation_id}
        )
        if self.error is not None:
            raise self.error
        delay = self.page_delays.get(call_index, 0.0)
        if delay:
            await asyncio.sleep(delay)
        page = self.pages[min(call_index, len(self.pages) - 1)]
        return AdvisorCockpitActionPageEnvelopeResponse(
            correlation_id=correlation_id,
            contract_version="v1",
            data=page,
        )


def _action_page(
    actions: list[dict[str, Any]],
    *,
    next_cursor: str | None = None,
    total_count: int | None = None,
) -> AdvisorCockpitActionPage:
    return AdvisorCockpitActionPage.model_validate(
        {
            "items": actions,
            "next_cursor": next_cursor,
            "page_size": 100,
            "total_count": total_count if total_count is not None else len(actions),
        }
    )


def _action(action_item_id: str, *, portfolio_id: str | None) -> dict[str, Any]:
    payload = advisor_action_item_payload(action_item_id=action_item_id)
    payload["portfolio_id"] = portfolio_id
    return payload


def _service(
    membership: dict[str, object],
    *,
    value_client: ValueClient | None = None,
    cockpit: _StubCockpitService | None = None,
    deadline_seconds: float = 10.0,
    membership_delay_seconds: float = 0.0,
) -> AdvisorBookWorkspaceService:
    return AdvisorBookWorkspaceService(
        membership_service=AdvisorBookService(
            membership_client=MembershipClient(
                payload=membership, delay_seconds=membership_delay_seconds
            )
        ),
        value_client=value_client or ValueClient(),
        cockpit_service=cockpit or _StubCockpitService(pages=[_action_page([])]),
        composition_deadline_seconds=deadline_seconds,
    )


async def _get(service: AdvisorBookWorkspaceService, correlation_id: str, *, advise_scope=None):
    return await service.get_workspace(
        book_caller=book_caller(),
        advise_scope=advise_scope if advise_scope is not None else cockpit_caller(),
        as_of_date=date(2026, 4, 10),
        reporting_currency="USD",
        correlation_id=correlation_id,
    )


@pytest.mark.asyncio
async def test_workspace_composes_dense_rows_from_one_frozen_cohort() -> None:
    value_client = ValueClient(
        payload=bulk_payload(
            ["PB_001", "PB_002"],
            [
                covered_member("PB_001", "600.00", "100.00"),
                covered_member("PB_002", "399.99", "50.00"),
            ],
        )
    )
    cockpit = _StubCockpitService(
        pages=[
            _action_page(
                [
                    _action("a1", portfolio_id="PB_001"),
                    _action("a2", portfolio_id="PB_001"),
                    _action("a3", portfolio_id=None),
                ],
                total_count=3,
            )
        ]
    )
    service = _service(
        membership_payload("PB_001", "PB_002"), value_client=value_client, cockpit=cockpit
    )

    response = await _get(service, "corr-workspace")

    assert [row.portfolio_id for row in response.rows] == ["PB_001", "PB_002"]
    assert response.rows[0].value is not None
    assert response.rows[0].value.total_value == Decimal("600.00")
    assert response.rows[0].action_items is not None
    assert response.rows[0].action_items.action_item_count == 2
    assert response.rows[1].value is not None
    assert response.rows[1].action_items is not None
    assert response.rows[1].action_items.action_item_count == 0
    assert response.value_facts.state == "stated"
    assert response.value_facts.summary is not None
    assert response.value_facts.summary.total_value == Decimal("999.99")
    assert response.action_facts.state == "stated"
    assert response.action_facts.summary is not None
    assert response.action_facts.summary.unassigned_action_item_count == 1
    assert response.action_facts.summary.coverage_state == "complete"
    assert response.membership_provenance is not None
    assert response.membership_provenance.freshness_status == "CURRENT"
    # The frozen cohort drives the value read: exactly the membership order.
    assert value_client.calls[0]["portfolio_ids"] == ["PB_001", "PB_002"]


@pytest.mark.asyncio
async def test_workspace_value_source_outage_degrades_only_the_value_fact() -> None:
    cockpit = _StubCockpitService(
        pages=[_action_page([_action("a1", portfolio_id="PB_001")], total_count=1)]
    )
    service = _service(
        membership_payload("PB_001"),
        value_client=ValueClient(status_code=503),
        cockpit=cockpit,
    )

    response = await _get(service, "corr-value-down")

    assert response.value_facts.state == "unavailable"
    assert response.value_facts.reason_code == "value_source_unavailable"
    assert response.value_facts.summary is None
    assert [row.portfolio_id for row in response.rows] == ["PB_001"]
    assert response.rows[0].value is None
    assert response.rows[0].action_items is not None
    assert response.rows[0].action_items.action_item_count == 1
    assert response.action_facts.state == "stated"


@pytest.mark.asyncio
async def test_workspace_value_contract_violation_is_named_not_masked() -> None:
    # The source echoes a different cohort than requested: contract-invalid, not outage.
    service = _service(
        membership_payload("PB_001"),
        value_client=ValueClient(
            payload=bulk_payload(["PB_OTHER"], [covered_member("PB_OTHER", "600.00", "100.00")])
        ),
        cockpit=_StubCockpitService(pages=[_action_page([])]),
    )

    response = await _get(service, "corr-value-contract")

    assert response.value_facts.state == "unavailable"
    assert response.value_facts.reason_code == "value_source_contract_invalid"
    assert response.rows[0].value is None
    assert response.action_facts.state == "stated"


@pytest.mark.asyncio
async def test_workspace_without_advise_scope_degrades_action_fact_without_source_read() -> None:
    cockpit = _StubCockpitService(pages=[_action_page([])])
    service = _service(
        membership_payload("PB_001"),
        value_client=ValueClient(
            payload=bulk_payload(["PB_001"], [covered_member("PB_001", "600.00", "100.00")])
        ),
        cockpit=cockpit,
    )

    response = await _get(
        service,
        "corr-no-advise-scope",
        advise_scope=AdviseScopeUnavailable("advise_scope_not_presented"),
    )

    assert response.action_facts.state == "unavailable"
    assert response.action_facts.reason_code == "advise_scope_not_presented"
    assert response.action_facts.summary is None
    assert cockpit.calls == []
    assert response.rows[0].action_items is None
    assert response.rows[0].value is not None
    assert response.value_facts.state == "stated"


@pytest.mark.asyncio
async def test_workspace_action_feed_failure_degrades_only_the_action_fact() -> None:
    cockpit = _StubCockpitService()
    cockpit.error = HTTPException(status_code=503, detail={"code": "advise_unavailable"})
    service = _service(
        membership_payload("PB_001"),
        value_client=ValueClient(
            payload=bulk_payload(["PB_001"], [covered_member("PB_001", "600.00", "100.00")])
        ),
        cockpit=cockpit,
    )

    response = await _get(service, "corr-feed-down")

    assert response.action_facts.state == "unavailable"
    assert response.action_facts.reason_code == "action_feed_unavailable"
    assert response.rows[0].action_items is None
    assert response.rows[0].value is not None
    assert response.value_facts.state == "stated"


@pytest.mark.asyncio
async def test_workspace_membership_deadline_exhaustion_is_fatal() -> None:
    service = _service(
        membership_payload("PB_001"),
        deadline_seconds=0.2,
        membership_delay_seconds=0.5,
    )

    with pytest.raises(AdvisorBookServiceError) as raised:
        await _get(service, "corr-membership-deadline")

    assert raised.value.status_code == 504
    assert raised.value.code == "advisor_book_workspace_deadline_exhausted"


@pytest.mark.asyncio
async def test_workspace_value_deadline_preserves_the_action_fact() -> None:
    cockpit = _StubCockpitService(
        pages=[_action_page([_action("a1", portfolio_id="PB_001")], total_count=1)]
    )
    service = _service(
        membership_payload("PB_001"),
        value_client=ValueClient(
            payload=bulk_payload(["PB_001"], [covered_member("PB_001", "600.00", "100.00")]),
            delay_seconds=0.6,
        ),
        cockpit=cockpit,
        deadline_seconds=0.3,
    )

    response = await _get(service, "corr-value-deadline")

    assert response.value_facts.state == "unavailable"
    assert response.value_facts.reason_code == "composition_deadline_reached"
    assert response.action_facts.state == "stated"
    assert response.rows[0].action_items is not None
    assert response.rows[0].action_items.action_item_count == 1


@pytest.mark.asyncio
async def test_workspace_untrustworthy_member_value_is_a_present_fact_not_a_missing_row() -> None:
    service = _service(
        membership_payload("PB_001", "PB_002"),
        value_client=ValueClient(
            payload=bulk_payload(
                ["PB_001", "PB_002"],
                [
                    covered_member("PB_001", "600.00", "100.00"),
                    uncovered_member("PB_002", "NO_SNAPSHOT"),
                ],
                aggregate_state="PARTIAL",
            )
        ),
        cockpit=_StubCockpitService(pages=[_action_page([])]),
    )

    response = await _get(service, "corr-partial-coverage")

    assert [row.portfolio_id for row in response.rows] == ["PB_001", "PB_002"]
    row = response.rows[1]
    assert row.value is not None
    assert row.value.state == "unavailable"
    assert row.value.total_value is None
    assert row.value.coverage_state == "NO_SNAPSHOT"
    assert response.value_facts.state == "stated"
    assert response.value_facts.summary is not None
    assert response.value_facts.summary.state == "partial"
    assert response.value_facts.summary.total_value is None


@pytest.mark.asyncio
async def test_workspace_partial_feed_read_stays_a_stated_lower_bound() -> None:
    # Terminal page, but the source-stated total exceeds the delivered items.
    cockpit = _StubCockpitService(
        pages=[_action_page([_action("a1", portfolio_id="PB_001")], total_count=5)]
    )
    service = _service(
        membership_payload("PB_001"),
        value_client=ValueClient(
            payload=bulk_payload(["PB_001"], [covered_member("PB_001", "600.00", "100.00")])
        ),
        cockpit=cockpit,
    )

    response = await _get(service, "corr-partial-feed")

    assert response.action_facts.state == "stated"
    assert response.action_facts.summary is not None
    assert response.action_facts.summary.coverage_state == "partial"
    assert response.action_facts.summary.coverage_reason == "source_total_mismatch"
    assert response.rows[0].action_items is not None
    assert response.rows[0].action_items.action_item_count == 1


@pytest.mark.asyncio
async def test_workspace_empty_book_states_empty_facts_with_provenance() -> None:
    service = _service(membership_payload())

    response = await _get(service, "corr-empty-book")

    assert response.rows == []
    assert response.value_facts.state == "stated"
    assert response.value_facts.summary is not None
    assert response.value_facts.summary.state == "empty"
    assert response.action_facts.state == "stated"
    assert response.action_facts.summary is not None
    assert response.action_facts.summary.state == "empty"
    assert response.action_facts.summary.coverage_state == "not_read"
    assert response.membership_provenance is not None


@pytest.mark.asyncio
async def test_workspace_empty_book_without_advise_scope_degrades_the_action_fact() -> None:
    service = _service(membership_payload())

    response = await _get(
        service,
        "corr-empty-no-scope",
        advise_scope=AdviseScopeUnavailable("advise_scope_not_advisor"),
    )

    assert response.rows == []
    assert response.value_facts.state == "stated"
    assert response.action_facts.state == "unavailable"
    assert response.action_facts.reason_code == "advise_scope_not_advisor"


@pytest.mark.asyncio
async def test_workspace_incomplete_membership_is_fatal() -> None:
    payload = membership_payload("PB_001")
    payload["supportability"] = {
        "state": "INCOMPLETE",
        "reason": "PM_BOOK_MEMBERSHIP_DEGRADED",
        "returned_portfolio_count": 1,
        "filters_applied": ["portfolio_manager_id", "as_of_date"],
    }
    service = _service(payload)

    with pytest.raises(AdvisorBookServiceError) as raised:
        await _get(service, "corr-incomplete")

    assert raised.value.code == "advisor_book_source_incomplete"


@pytest.mark.asyncio
async def test_workspace_refuses_a_member_resolved_off_the_cohort_date() -> None:
    # Core resolves every member on the cohort basis; a member resolved on a
    # different date is contradictory evidence, not a legitimate carry-forward.
    drifted = covered_member("PB_001", "600.00", "100.00")
    drifted["resolved_as_of_date"] = "2026-04-09"
    service = _service(
        membership_payload("PB_001"),
        value_client=ValueClient(payload=bulk_payload(["PB_001"], [drifted])),
        cockpit=_StubCockpitService(pages=[_action_page([_action("a1", portfolio_id="PB_001")])]),
    )

    response = await _get(service, "corr-member-date-drift")

    assert response.value_facts.state == "unavailable"
    assert response.value_facts.reason_code == "value_source_contract_invalid"
    assert [row.portfolio_id for row in response.rows] == ["PB_001"]
    assert response.rows[0].value is None
    assert response.rows[0].action_items is not None
    assert response.action_facts.state == "stated"


@pytest.mark.asyncio
async def test_workspace_refuses_a_complete_aggregate_contradicted_by_member_coverage() -> None:
    # Core's aggregate is fail-closed: COMPLETE over an untrustworthy member
    # contradicts its own member coverage evidence.
    service = _service(
        membership_payload("PB_001", "PB_002"),
        value_client=ValueClient(
            payload=bulk_payload(
                ["PB_001", "PB_002"],
                [
                    covered_member("PB_001", "600.00", "100.00"),
                    uncovered_member("PB_002", "NO_SNAPSHOT"),
                ],
                aggregate_state="COMPLETE",
            )
        ),
        cockpit=_StubCockpitService(pages=[_action_page([])]),
    )

    response = await _get(service, "corr-aggregate-contradiction")

    assert response.value_facts.state == "unavailable"
    assert response.value_facts.reason_code == "value_source_contract_invalid"
    assert [row.portfolio_id for row in response.rows] == ["PB_001", "PB_002"]
    assert response.rows[0].value is None
    assert response.action_facts.state == "stated"


@pytest.mark.asyncio
async def test_workspace_preserves_carry_forward_and_measured_zero_evidence() -> None:
    carried = covered_member("PB_001", "600.00", "100.00")
    carried["coverage_state"] = "CARRY_FORWARD"
    carried["coverage_reason"] = "latest_source_snapshot_precedes_as_of_date"
    carried["snapshot_date"] = "2026-04-05"
    measured_zero = covered_member("PB_002", "0.00", "0.00")
    measured_zero["coverage_state"] = "MEASURED_ZERO"
    measured_zero["coverage_reason"] = "loaded_snapshot_measures_zero_value"
    service = _service(
        membership_payload("PB_001", "PB_002"),
        value_client=ValueClient(
            payload=bulk_payload(["PB_001", "PB_002"], [carried, measured_zero])
        ),
        cockpit=_StubCockpitService(pages=[_action_page([])]),
    )

    response = await _get(service, "corr-carry-forward")

    assert response.value_facts.state == "stated"
    assert response.rows[0].value is not None
    assert response.rows[0].value.coverage_state == "CARRY_FORWARD"
    assert response.rows[0].value.snapshot_date == date(2026, 4, 5)
    assert response.rows[0].value.total_value == Decimal("600.00")
    assert response.rows[1].value is not None
    assert response.rows[1].value.coverage_state == "MEASURED_ZERO"
    assert response.rows[1].value.total_value == Decimal("0.00")
