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

    async def query_assets_under_management(self, **kwargs: Any):
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


def _value_payload(
    requested_ids: list[str],
    returned_ids: list[str],
) -> dict[str, object]:
    return {
        "scope_type": "portfolio_list",
        "scope": {"portfolio_ids": requested_ids},
        "resolved_as_of_date": "2026-04-10",
        "reporting_currency": "USD",
        "totals": {
            "portfolio_count": len(returned_ids),
            "position_count": 21,
            "aum_reporting_currency": "999.99",
        },
        "portfolios": [
            {
                "portfolio_id": portfolio_id,
                "aum_reporting_currency": str(index * 100),
                "position_count": index,
            }
            for index, portfolio_id in enumerate(returned_ids, start=1)
        ],
    }


@pytest.mark.asyncio
async def test_summary_uses_one_core_scope_read_and_source_total() -> None:
    membership_client = _MembershipClient(payload=_membership_payload("PB_001", "PB_002"))
    value_client = _ValueClient(payload=_value_payload(["PB_001", "PB_002"], ["PB_001", "PB_002"]))
    service = AdvisorBookSummaryService(
        membership_service=AdvisorBookService(membership_client=membership_client),
        value_client=value_client,
    )

    response = await service.get_value_summary(
        caller=_caller(),
        as_of_date=date(2026, 4, 10),
        reporting_currency="usd",
        correlation_id="corr-summary",
    )

    assert response.summary.state == "supported"
    assert response.summary.total_value == Decimal("999.99")
    assert response.summary.covered_portfolio_count == 2
    assert [item.portfolio_id for item in response.items] == ["PB_001", "PB_002"]
    assert value_client.calls == [
        {
            "correlation_id": "corr-summary",
            "portfolio_ids": ["PB_001", "PB_002"],
            "as_of_date": "2026-04-10",
            "reporting_currency": "USD",
        }
    ]


@pytest.mark.asyncio
async def test_summary_marks_missing_source_rows_partial_without_zero_substitution() -> None:
    value_client = _ValueClient(payload=_value_payload(["PB_001", "PB_002"], ["PB_001"]))
    service = AdvisorBookSummaryService(
        membership_service=AdvisorBookService(
            membership_client=_MembershipClient(payload=_membership_payload("PB_001", "PB_002"))
        ),
        value_client=value_client,
    )

    response = await service.get_value_summary(
        caller=_caller(),
        as_of_date=date(2026, 4, 10),
        reporting_currency="USD",
        correlation_id="corr-partial-summary",
    )

    assert response.summary.state == "partial"
    assert response.summary.total_value is None
    assert response.items[1].state == "unavailable"
    assert response.items[1].total_value is None
    assert response.items[1].reason_code == "advisor_book_value_not_covered"


@pytest.mark.asyncio
async def test_summary_keeps_ambiguous_zero_source_rows_out_of_confident_coverage() -> None:
    payload = _value_payload(["PB_001", "PB_002"], ["PB_001", "PB_002"])
    portfolios = payload["portfolios"]
    assert isinstance(portfolios, list)
    portfolios[1]["aum_reporting_currency"] = "0"
    portfolios[1]["position_count"] = 0
    payload["totals"]["aum_reporting_currency"] = "0"
    value_client = _ValueClient(payload=payload)
    service = AdvisorBookSummaryService(
        membership_service=AdvisorBookService(
            membership_client=_MembershipClient(payload=_membership_payload("PB_001", "PB_002"))
        ),
        value_client=value_client,
    )

    response = await service.get_value_summary(
        caller=_caller(),
        as_of_date=date(2026, 4, 10),
        reporting_currency="USD",
        correlation_id="corr-ambiguous-zero-summary",
    )

    assert response.summary.state == "partial"
    assert response.summary.covered_portfolio_count == 1
    assert response.summary.total_value is None
    assert response.items[0].state == "supported"
    assert response.items[1].state == "unavailable"
    assert response.items[1].total_value is None
    assert response.items[1].position_count is None
    assert response.items[1].reason_code == "advisor_book_value_coverage_ambiguous"


@pytest.mark.asyncio
async def test_summary_returns_empty_without_fabricating_a_value_read() -> None:
    value_client = _ValueClient()
    service = AdvisorBookSummaryService(
        membership_service=AdvisorBookService(
            membership_client=_MembershipClient(payload=_membership_payload())
        ),
        value_client=value_client,
    )

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


@pytest.mark.asyncio
async def test_summary_rejects_mismatched_source_scope() -> None:
    value_client = _ValueClient(payload=_value_payload(["PB_002", "PB_001"], ["PB_001", "PB_002"]))
    service = AdvisorBookSummaryService(
        membership_service=AdvisorBookService(
            membership_client=_MembershipClient(payload=_membership_payload("PB_001", "PB_002"))
        ),
        value_client=value_client,
    )

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
    service = AdvisorBookSummaryService(
        membership_service=AdvisorBookService(
            membership_client=_MembershipClient(payload=_membership_payload("PB_001"))
        ),
        value_client=_ValueClient(status_code=503),
    )

    with pytest.raises(AdvisorBookServiceError) as raised:
        await service.get_value_summary(
            caller=_caller(),
            as_of_date=date(2026, 4, 10),
            reporting_currency="USD",
            correlation_id="corr-unavailable-summary",
        )

    assert raised.value.code == "advisor_book_value_source_unavailable"
    assert raised.value.status_code == 502
