from datetime import date
from decimal import Decimal
from typing import Any

import pytest

from app.services.advisor_book_access_policy import AdvisorBookCallerContext
from app.services.advisor_book_service import AdvisorBookService, AdvisorBookServiceError
from app.services.advisor_book_summary_service import AdvisorBookSummaryService


class _MembershipClient:
    def __init__(self, payload: dict[str, Any] | None = None) -> None:
        self.payload = payload or {}
        self.calls: list[dict[str, Any]] = []

    async def get_portfolio_manager_book_memberships(self, **kwargs: Any):
        self.calls.append(kwargs)
        return 200, self.payload


class _ValueClient:
    def __init__(self, *, status_code: int = 200, payload: dict[str, Any] | None = None) -> None:
        self.status_code = status_code
        self.payload = payload or {}
        self.calls: list[dict[str, Any]] = []

    async def query_bulk_portfolio_summary(self, **kwargs: Any):
        self.calls.append(kwargs)
        return self.status_code, self.payload


def _caller() -> AdvisorBookCallerContext:
    return AdvisorBookCallerContext(
        portfolio_manager_id="PM_SG_001",
        tenant_id="tenant-sg",
        region="APAC",
        booking_center_code="Singapore",
        role="ADVISOR",
        caller_application="lotus-workbench",
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


def _covered_member(portfolio_id: str, total: str, cash: str) -> dict[str, object]:
    invested = str(Decimal(total) - Decimal(cash))
    return {
        "portfolio_id": portfolio_id,
        "booking_center_code": "Singapore",
        "client_id": f"CIF_{portfolio_id}",
        "portfolio_currency": "USD",
        "reporting_currency": "USD",
        "resolved_as_of_date": "2026-04-10",
        "coverage_state": "COMPLETE",
        "coverage_reason": "snapshot_rows_complete",
        "snapshot_date": "2026-04-10",
        "snapshot_row_count": 12,
        "expected_open_position_count": 12,
        "totals": {
            "total_market_value_portfolio_currency": total,
            "total_market_value_reporting_currency": total,
            "cash_balance_portfolio_currency": cash,
            "cash_balance_reporting_currency": cash,
            "invested_market_value_portfolio_currency": invested,
            "invested_market_value_reporting_currency": invested,
        },
    }


def _uncovered_member(portfolio_id: str, coverage_state: str) -> dict[str, object]:
    return {
        "portfolio_id": portfolio_id,
        "booking_center_code": None,
        "client_id": None,
        "portfolio_currency": None,
        "reporting_currency": "USD",
        "resolved_as_of_date": "2026-04-10",
        "coverage_state": coverage_state,
        "coverage_reason": "no_snapshot_rows_for_as_of_date",
        "snapshot_date": None,
        "snapshot_row_count": 0,
        "expected_open_position_count": 3,
        "totals": None,
    }


def _bulk_payload(
    requested_ids: list[str],
    members: list[dict[str, object]],
    *,
    aggregate_state: str = "COMPLETE",
) -> dict[str, object]:
    covered = [member for member in members if member.get("totals") is not None]
    aggregate_totals = None
    if aggregate_state == "COMPLETE":
        aggregate_totals = {
            "total_market_value_portfolio_currency": None,
            "total_market_value_reporting_currency": str(
                sum(
                    Decimal(str(m["totals"]["total_market_value_reporting_currency"]))
                    for m in covered
                )  # type: ignore[index]
            ),
            "cash_balance_portfolio_currency": None,
            "cash_balance_reporting_currency": str(
                sum(Decimal(str(m["totals"]["cash_balance_reporting_currency"])) for m in covered)  # type: ignore[index]
            ),
            "invested_market_value_portfolio_currency": None,
            "invested_market_value_reporting_currency": str(
                sum(
                    Decimal(str(m["totals"]["invested_market_value_reporting_currency"]))  # type: ignore[index]
                    for m in covered
                )
            ),
        }
    return {
        "contract_version": "portfolio-summary-bulk-v1",
        "requested_portfolio_ids": requested_ids,
        "resolved_as_of_date": "2026-04-10",
        "reporting_currency": "USD",
        "portfolios": members,
        "aggregate": {
            "portfolio_count": len(requested_ids),
            "coverage_state": aggregate_state,
            "coverage_reason": (
                "all_members_covered"
                if aggregate_state == "COMPLETE"
                else "member_coverage_incomplete"
            ),
            "totals": aggregate_totals,
        },
    }


def _service(
    membership_payload: dict[str, object],
    value_client: _ValueClient,
) -> AdvisorBookSummaryService:
    return AdvisorBookSummaryService(
        membership_service=AdvisorBookService(
            membership_client=_MembershipClient(payload=membership_payload)
        ),
        value_client=value_client,
    )


@pytest.mark.asyncio
async def test_summary_uses_one_bulk_read_and_source_owned_aggregate() -> None:
    value_client = _ValueClient(
        payload=_bulk_payload(
            ["PB_001", "PB_002"],
            [
                _covered_member("PB_001", "600.00", "100.00"),
                _covered_member("PB_002", "399.99", "50.00"),
            ],
        )
    )
    service = _service(_membership_payload("PB_001", "PB_002"), value_client)

    response = await service.get_value_summary(
        caller=_caller(),
        as_of_date=date(2026, 4, 10),
        reporting_currency="usd",
        correlation_id="corr-summary",
    )

    assert response.summary.state == "supported"
    assert response.summary.total_value == Decimal("999.99")
    assert response.summary.cash_value == Decimal("150.00")
    assert response.summary.invested_value == Decimal("849.99")
    assert response.summary.coverage_state == "COMPLETE"
    assert response.summary.covered_portfolio_count == 2
    assert [item.portfolio_id for item in response.items] == ["PB_001", "PB_002"]
    assert response.items[0].cash_value == Decimal("100.00")
    assert response.items[0].valuation_as_of == date(2026, 4, 10)
    assert response.source.source_route == "/reporting/portfolio-summary/bulk-query"
    assert value_client.calls == [
        {
            "correlation_id": "corr-summary",
            "portfolio_ids": ["PB_001", "PB_002"],
            "as_of_date": "2026-04-10",
            "reporting_currency": "USD",
        }
    ]


@pytest.mark.asyncio
async def test_summary_preserves_source_partial_coverage_without_zero_substitution() -> None:
    value_client = _ValueClient(
        payload=_bulk_payload(
            ["PB_001", "PB_002"],
            [
                _covered_member("PB_001", "600.00", "100.00"),
                _uncovered_member("PB_002", "NO_SNAPSHOT"),
            ],
            aggregate_state="PARTIAL",
        )
    )
    service = _service(_membership_payload("PB_001", "PB_002"), value_client)

    response = await service.get_value_summary(
        caller=_caller(),
        as_of_date=date(2026, 4, 10),
        reporting_currency="USD",
        correlation_id="corr-partial-summary",
    )

    assert response.summary.state == "partial"
    assert response.summary.total_value is None
    assert response.summary.cash_value is None
    assert response.summary.coverage_state == "PARTIAL"
    assert response.summary.covered_portfolio_count == 1
    assert response.items[1].state == "unavailable"
    assert response.items[1].total_value is None
    assert response.items[1].coverage_state == "NO_SNAPSHOT"
    assert response.items[1].coverage_reason == "no_snapshot_rows_for_as_of_date"


@pytest.mark.asyncio
async def test_summary_reports_measured_zero_as_a_business_fact() -> None:
    empty_member = _covered_member("PB_002", "0.00", "0.00")
    empty_member["coverage_state"] = "MEASURED_ZERO"
    empty_member["coverage_reason"] = "snapshot_measured_zero"
    value_client = _ValueClient(
        payload=_bulk_payload(
            ["PB_001", "PB_002"],
            [_covered_member("PB_001", "600.00", "100.00"), empty_member],
        )
    )
    service = _service(_membership_payload("PB_001", "PB_002"), value_client)

    response = await service.get_value_summary(
        caller=_caller(),
        as_of_date=date(2026, 4, 10),
        reporting_currency="USD",
        correlation_id="corr-measured-zero-summary",
    )

    assert response.summary.state == "supported"
    assert response.summary.covered_portfolio_count == 2
    assert response.items[1].state == "supported"
    assert response.items[1].total_value == Decimal("0.00")
    assert response.items[1].coverage_state == "MEASURED_ZERO"


@pytest.mark.asyncio
async def test_summary_rejects_totals_that_contradict_source_coverage() -> None:
    contradiction = _uncovered_member("PB_002", "NO_SNAPSHOT")
    contradiction["totals"] = _covered_member("PB_002", "1.00", "1.00")["totals"]
    value_client = _ValueClient(
        payload=_bulk_payload(
            ["PB_001", "PB_002"],
            [_covered_member("PB_001", "600.00", "100.00"), contradiction],
            aggregate_state="PARTIAL",
        )
    )
    service = _service(_membership_payload("PB_001", "PB_002"), value_client)

    with pytest.raises(AdvisorBookServiceError) as raised:
        await service.get_value_summary(
            caller=_caller(),
            as_of_date=date(2026, 4, 10),
            reporting_currency="USD",
            correlation_id="corr-contradiction-summary",
        )

    assert raised.value.code == "advisor_book_value_source_contract_invalid"


@pytest.mark.asyncio
async def test_summary_returns_empty_without_fabricating_a_value_read() -> None:
    value_client = _ValueClient()
    service = _service(_membership_payload(), value_client)

    response = await service.get_value_summary(
        caller=_caller(),
        as_of_date=date(2026, 4, 10),
        reporting_currency="usd",
        correlation_id="corr-empty-summary",
    )

    assert response.summary.state == "empty"
    assert response.summary.reporting_currency == "USD"
    assert response.summary.total_value is None
    assert response.items == []
    assert value_client.calls == []


@pytest.mark.parametrize(
    "mutate",
    (
        pytest.param(
            lambda payload: payload.update({"requested_portfolio_ids": ["PB_002", "PB_001"]}),
            id="reordered-request-echo",
        ),
        pytest.param(
            lambda payload: payload["portfolios"].pop(),
            id="missing-member-item",
        ),
        pytest.param(
            lambda payload: payload.update({"resolved_as_of_date": "2026-04-11"}),
            id="different-as-of",
        ),
        pytest.param(
            lambda payload: payload.update({"reporting_currency": "SGD"}),
            id="different-currency",
        ),
    ),
)
@pytest.mark.asyncio
async def test_summary_rejects_source_identity_drift(mutate) -> None:
    payload = _bulk_payload(
        ["PB_001", "PB_002"],
        [
            _covered_member("PB_001", "600.00", "100.00"),
            _covered_member("PB_002", "399.99", "50.00"),
        ],
    )
    mutate(payload)
    service = _service(_membership_payload("PB_001", "PB_002"), _ValueClient(payload=payload))

    with pytest.raises(AdvisorBookServiceError) as raised:
        await service.get_value_summary(
            caller=_caller(),
            as_of_date=date(2026, 4, 10),
            reporting_currency="USD",
            correlation_id="corr-mismatch-summary",
        )

    assert raised.value.code == "advisor_book_value_source_contract_invalid"
    assert raised.value.status_code == 502


@pytest.mark.asyncio
async def test_summary_maps_core_failure_to_product_safe_error() -> None:
    service = _service(_membership_payload("PB_001"), _ValueClient(status_code=503))

    with pytest.raises(AdvisorBookServiceError) as raised:
        await service.get_value_summary(
            caller=_caller(),
            as_of_date=date(2026, 4, 10),
            reporting_currency="USD",
            correlation_id="corr-unavailable-summary",
        )

    assert raised.value.code == "advisor_book_value_source_unavailable"
