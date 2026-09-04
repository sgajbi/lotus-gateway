import asyncio
from datetime import date
from typing import Any

import pytest
from fastapi import HTTPException

from app.contracts.advisor_cockpit_action_envelopes import (
    AdvisorCockpitActionPageEnvelopeResponse,
)
from app.contracts.advisor_cockpit_action_models import AdvisorCockpitActionPage
from app.services.advisor_book_access_policy import AdvisorBookCallerContext
from app.services.advisor_book_action_items_service import AdvisorBookActionItemsService
from app.services.advisor_book_service import AdvisorBookService, AdvisorBookServiceError
from app.services.advisor_cockpit_access_policy import AdvisorCockpitCallerContext
from tests.support.advisor_cockpit_fixtures import advisor_action_item_payload


class _MembershipClient:
    def __init__(self, payload: dict[str, Any] | None = None, delay_seconds: float = 0.0) -> None:
        self.payload = payload or {}
        self.delay_seconds = delay_seconds

    async def get_portfolio_manager_book_memberships(self, **kwargs: Any):
        if self.delay_seconds:
            await asyncio.sleep(self.delay_seconds)
        return 200, self.payload


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


def _book_caller() -> AdvisorBookCallerContext:
    return AdvisorBookCallerContext(
        portfolio_manager_id="PM_SG_001",
        tenant_id="tenant-sg",
        region="APAC",
        booking_center_code="Singapore",
        role="ADVISOR",
        caller_application="lotus-workbench",
    )


def _cockpit_caller() -> AdvisorCockpitCallerContext:
    return AdvisorCockpitCallerContext(
        actor_id="advisor_sg_001",
        caller_application="lotus-workbench",
        tenant_id="tenant-sg",
        region="APAC",
        booking_center_code="Singapore",
        legal_entity_code="SG01",
        role="ADVISOR",
        capabilities=frozenset({"advisory.advisor_cockpit.read"}),
        principal_status="ACTIVE",
        authorized_advisor_id="advisor_sg_001",
        authorized_portfolio_id=None,
    )


def _member(portfolio_id: str) -> dict[str, object]:
    return {
        "portfolio_id": portfolio_id,
        "client_id": f"CIF_{portfolio_id}",
        "booking_center_code": "Singapore",
        "portfolio_type": "ADVISORY",
        "status": "ACTIVE",
        "open_date": "2025-03-31",
        "close_date": None,
        "base_currency": "USD",
        "source_record_id": f"portfolio:{portfolio_id}",
        "membership_source": "party_role_assignment",
        "role_type": "ADVISOR",
    }


def _membership_payload(*portfolio_ids: str) -> dict[str, object]:
    members = [_member(portfolio_id) for portfolio_id in portfolio_ids]
    return {
        "product_name": "PortfolioManagerBookMembership",
        "product_version": "v1",
        "portfolio_manager_id": "PM_SG_001",
        "tenant_id": "tenant-sg",
        "generated_at": "2026-04-10T02:00:00Z",
        "as_of_date": "2026-04-10",
        "latest_evidence_timestamp": "2026-04-10T01:59:00Z",
        "snapshot_id": "pm_book_membership:2e7dfe0c",
        "content_hash": "sha256:0123456789abcdef",
        "data_quality_status": "ACCEPTED",
        "source_evidence_current": True,
        "freshness_status": "CURRENT",
        "booking_center_code": "Singapore",
        "members": members,
        "supportability": {
            "state": "READY",
            "reason": "PM_BOOK_MEMBERSHIP_READY",
            "returned_portfolio_count": len(members),
            "filters_applied": ["portfolio_manager_id", "as_of_date"],
        },
        "lineage": {"source_system": "lotus-core"},
    }


def _action(
    action_item_id: str,
    *,
    portfolio_id: str | None,
    reason_codes: list[str] | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    payload = advisor_action_item_payload(action_item_id=action_item_id)
    payload["portfolio_id"] = portfolio_id
    if reason_codes is not None:
        payload["reason_codes"] = reason_codes
    if status is not None:
        payload["status"] = status
    return payload


def _page(
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


def _service(
    membership_payload: dict[str, object],
    cockpit: _StubCockpitService,
    *,
    deadline_seconds: float = 10.0,
    membership_delay_seconds: float = 0.0,
) -> AdvisorBookActionItemsService:
    return AdvisorBookActionItemsService(
        membership_service=AdvisorBookService(
            membership_client=_MembershipClient(
                payload=membership_payload,
                delay_seconds=membership_delay_seconds,
            )
        ),
        cockpit_service=cockpit,
        composition_deadline_seconds=deadline_seconds,
    )


async def _get(service: AdvisorBookActionItemsService, correlation_id: str):
    return await service.get_action_items(
        book_caller=_book_caller(),
        cockpit_caller=_cockpit_caller(),
        as_of_date=date(2026, 4, 10),
        correlation_id=correlation_id,
    )


@pytest.mark.asyncio
async def test_action_items_count_source_items_per_cohort_member() -> None:
    cockpit = _StubCockpitService(
        pages=[
            _page(
                [
                    _action("a1", portfolio_id="PB_001", reason_codes=["PROPOSAL_READY", "X1"]),
                    _action("a2", portfolio_id="PB_001", reason_codes=["PROPOSAL_READY", "X2"]),
                    _action("a3", portfolio_id=None, reason_codes=["CLIENT_LEVEL"]),
                    _action("a4", portfolio_id="PB_OUTSIDE", reason_codes=["OTHER_BOOK"]),
                ],
                total_count=4,
            )
        ]
    )
    service = _service(_membership_payload("PB_001", "PB_002"), cockpit)

    response = await _get(service, "corr-action-items")

    assert response.summary.state == "supported"
    assert response.summary.portfolio_count == 2
    assert response.summary.portfolios_with_action_items == 1
    assert response.summary.action_item_count == 2
    assert response.summary.unassigned_action_item_count == 1
    assert response.summary.outside_book_action_item_count == 1
    assert response.summary.source_stated_total == 4
    assert response.summary.coverage_state == "complete"
    assert [item.portfolio_id for item in response.items] == ["PB_001", "PB_002"]
    assert response.items[0].action_item_count == 2
    assert response.items[0].reason_codes == ["PROPOSAL_READY", "X1", "X2"]
    assert response.items[1].action_item_count == 0
    assert response.source.action_evidence_basis == "current_state"
    assert response.source.membership_as_of_date == date(2026, 4, 10)
    assert cockpit.calls[0]["params"] == {"limit": 64}
    assert cockpit.calls[0]["caller_headers"]["X-Authorized-Advisor-Id"] == "advisor_sg_001"


@pytest.mark.asyncio
async def test_action_items_do_not_define_which_source_statuses_count() -> None:
    cockpit = _StubCockpitService(
        pages=[
            _page(
                [
                    _action("a1", portfolio_id="PB_001", status="PENDING_REVIEW"),
                    _action("a2", portfolio_id="PB_001", status="COMPLETED"),
                    _action("a3", portfolio_id="PB_001", status="SUPERSEDED"),
                ],
                total_count=3,
            )
        ]
    )
    service = _service(_membership_payload("PB_001"), cockpit)

    response = await _get(service, "corr-status-faithful")

    # Gateway counts what the source returned; actionable meaning stays with Advise.
    assert response.items[0].action_item_count == 3
    assert response.summary.coverage_state == "complete"


@pytest.mark.asyncio
async def test_action_items_follow_source_cursors_until_the_feed_ends() -> None:
    cockpit = _StubCockpitService(
        pages=[
            _page([_action("a1", portfolio_id="PB_001")], next_cursor="a1", total_count=2),
            _page([_action("a2", portfolio_id="PB_001")], total_count=2),
        ]
    )
    service = _service(_membership_payload("PB_001"), cockpit)

    response = await _get(service, "corr-pages")

    assert response.summary.action_item_count == 2
    assert response.summary.coverage_state == "complete"
    assert len(cockpit.calls) == 2
    assert cockpit.calls[1]["params"] == {"limit": 64, "cursor": "a1"}


@pytest.mark.asyncio
async def test_action_items_report_partial_at_the_page_budget() -> None:
    cockpit = _StubCockpitService(
        pages=[
            _page(
                [_action(f"a{index}", portfolio_id="PB_001")],
                next_cursor=f"c{index}",
                total_count=999,
            )
            for index in range(6)
        ]
    )
    service = _service(_membership_payload("PB_001"), cockpit)

    response = await _get(service, "corr-budget")

    assert len(cockpit.calls) == 5
    assert response.summary.coverage_state == "partial"
    assert response.summary.coverage_reason == "action_page_budget_reached"
    assert response.summary.action_item_count == 5


@pytest.mark.asyncio
async def test_action_items_preserve_verified_items_when_the_deadline_stops_paging() -> None:
    cockpit = _StubCockpitService(
        pages=[
            _page([_action("a1", portfolio_id="PB_001")], next_cursor="a1", total_count=3),
            _page([_action("a2", portfolio_id="PB_001")], next_cursor="a2", total_count=3),
            _page([_action("a3", portfolio_id="PB_001")], total_count=3),
        ],
        page_delays={1: 0.5},
    )
    service = _service(_membership_payload("PB_001"), cockpit, deadline_seconds=0.3)

    response = await _get(service, "corr-deadline-adversarial")

    # Page 1 succeeded; page 2 consumed the remaining budget; later pages not admitted.
    assert len(cockpit.calls) == 2
    assert response.summary.coverage_state == "partial"
    assert response.summary.coverage_reason == "composition_deadline_reached"
    assert response.summary.action_item_count == 1
    assert response.items[0].action_item_count == 1


@pytest.mark.asyncio
async def test_action_items_fail_closed_when_membership_exhausts_the_deadline() -> None:
    cockpit = _StubCockpitService()
    service = _service(
        _membership_payload("PB_001"),
        cockpit,
        deadline_seconds=0.05,
        membership_delay_seconds=0.5,
    )

    with pytest.raises(AdvisorBookServiceError) as raised:
        await _get(service, "corr-membership-deadline")

    assert raised.value.code == "advisor_book_action_items_deadline_exhausted"
    assert raised.value.status_code == 504
    assert cockpit.calls == []


@pytest.mark.asyncio
async def test_action_items_report_partial_when_source_total_exceeds_collected() -> None:
    cockpit = _StubCockpitService(
        pages=[_page([_action("a1", portfolio_id="PB_001")], total_count=7)]
    )
    service = _service(_membership_payload("PB_001"), cockpit)

    response = await _get(service, "corr-total-over")

    assert response.summary.coverage_state == "partial"
    assert response.summary.coverage_reason == "source_total_mismatch"
    assert response.summary.source_stated_total == 7


@pytest.mark.asyncio
async def test_action_items_report_partial_when_source_total_undercounts_collected() -> None:
    cockpit = _StubCockpitService(
        pages=[
            _page(
                [
                    _action("a1", portfolio_id="PB_001"),
                    _action("a2", portfolio_id="PB_001"),
                ],
                total_count=1,
            )
        ]
    )
    service = _service(_membership_payload("PB_001"), cockpit)

    response = await _get(service, "corr-total-under")

    assert response.summary.coverage_state == "partial"
    assert response.summary.coverage_reason == "source_total_mismatch"
    assert response.summary.action_item_count == 2


@pytest.mark.asyncio
async def test_action_items_report_inconsistent_when_the_stated_total_drifts() -> None:
    cockpit = _StubCockpitService(
        pages=[
            _page([_action("a1", portfolio_id="PB_001")], next_cursor="a1", total_count=2),
            _page([_action("a2", portfolio_id="PB_001")], total_count=5),
        ]
    )
    service = _service(_membership_payload("PB_001"), cockpit)

    response = await _get(service, "corr-total-drift")

    assert response.summary.coverage_state == "partial"
    assert response.summary.coverage_reason == "source_pagination_inconsistent"


@pytest.mark.asyncio
async def test_action_items_deduplicate_repeated_identities_and_stay_partial() -> None:
    cockpit = _StubCockpitService(
        pages=[
            _page([_action("a1", portfolio_id="PB_001")], next_cursor="a1", total_count=2),
            _page([_action("a1", portfolio_id="PB_001")], total_count=2),
        ]
    )
    service = _service(_membership_payload("PB_001"), cockpit)

    response = await _get(service, "corr-duplicate-identity")

    assert response.summary.action_item_count == 1
    assert response.summary.coverage_state == "partial"
    assert response.summary.coverage_reason == "source_pagination_inconsistent"


@pytest.mark.asyncio
async def test_action_items_stop_on_a_cursor_that_does_not_advance() -> None:
    cockpit = _StubCockpitService(
        pages=[
            _page([_action("a1", portfolio_id="PB_001")], next_cursor="stuck", total_count=9),
            _page([_action("a2", portfolio_id="PB_001")], next_cursor="stuck", total_count=9),
        ]
    )
    service = _service(_membership_payload("PB_001"), cockpit)

    response = await _get(service, "corr-stuck-cursor")

    assert len(cockpit.calls) == 2
    assert response.summary.coverage_state == "partial"
    assert response.summary.coverage_reason == "source_pagination_inconsistent"


@pytest.mark.asyncio
async def test_action_items_empty_book_never_reads_the_action_feed() -> None:
    cockpit = _StubCockpitService()
    service = _service(_membership_payload(), cockpit)

    response = await _get(service, "corr-empty")

    assert response.summary.state == "empty"
    assert response.summary.coverage_state == "not_read"
    assert response.summary.coverage_reason == "empty_book_feed_not_read"
    assert response.items == []
    assert cockpit.calls == []


@pytest.mark.asyncio
async def test_action_items_fail_closed_on_incomplete_membership() -> None:
    payload = _membership_payload("PB_001")
    payload["supportability"] = {
        "state": "INCOMPLETE",
        "reason": "PM_BOOK_MEMBERSHIP_INCOMPLETE",
        "returned_portfolio_count": 0,
        "filters_applied": [],
    }
    service = _service(payload, _StubCockpitService())

    with pytest.raises(AdvisorBookServiceError):
        await _get(service, "corr-incomplete")


@pytest.mark.asyncio
async def test_action_items_propagate_the_source_action_failure() -> None:
    cockpit = _StubCockpitService()
    cockpit.error = HTTPException(status_code=502, detail={"code": "advise_unavailable"})
    service = _service(_membership_payload("PB_001"), cockpit)

    with pytest.raises(HTTPException) as raised:
        await _get(service, "corr-source-down")

    assert raised.value.status_code == 502


def test_action_items_page_size_stays_within_the_typed_source_page_bound() -> None:
    from app.services.advisor_book_action_items_read import ACTION_PAGE_SIZE

    items_bound = AdvisorCockpitActionPage.model_json_schema()["properties"]["items"]["maxItems"]
    assert ACTION_PAGE_SIZE <= items_bound


@pytest.mark.asyncio
async def test_action_items_report_partial_when_the_source_states_no_total() -> None:
    cockpit = _StubCockpitService(
        pages=[
            AdvisorCockpitActionPage.model_validate(
                {
                    "items": [_action("a1", portfolio_id="PB_001")],
                    "next_cursor": None,
                    "page_size": 100,
                    "total_count": None,
                }
            )
        ]
    )
    service = _service(_membership_payload("PB_001"), cockpit)

    response = await _get(service, "corr-total-not-stated")

    assert response.summary.coverage_state == "partial"
    assert response.summary.coverage_reason == "source_total_not_stated"
    assert response.summary.source_stated_total is None
    assert response.summary.action_item_count == 1


@pytest.mark.asyncio
async def test_action_items_preserve_core_membership_provenance() -> None:
    cockpit = _StubCockpitService(
        pages=[_page([_action("a1", portfolio_id="PB_001")], total_count=1)]
    )
    service = _service(_membership_payload("PB_001"), cockpit)

    response = await _get(service, "corr-provenance")

    assert response.membership_provenance is not None
    assert response.membership_provenance.freshness_status == "CURRENT"
    assert response.membership_provenance.source_evidence_current is True
    assert response.membership_provenance.snapshot_id == "pm_book_membership:2e7dfe0c"
