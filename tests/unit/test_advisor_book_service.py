from datetime import date
from typing import Any

import pytest

from app.services.advisor_book_access_policy import AdvisorBookCallerContext
from app.services.advisor_book_service import (
    AdvisorBookQuery,
    AdvisorBookService,
    AdvisorBookServiceError,
)


class _MembershipClient:
    def __init__(self, *, status_code: int = 200, payload: dict[str, Any] | None = None):
        self.status_code = status_code
        self.payload = payload or {}
        self.calls: list[dict[str, Any]] = []

    async def get_portfolio_manager_book_memberships(self, **kwargs):
        self.calls.append(kwargs)
        return self.status_code, self.payload


def _caller(**overrides: str) -> AdvisorBookCallerContext:
    values = {
        "portfolio_manager_id": "PM_SG_001",
        "tenant_id": "tenant-sg",
        "region": "APAC",
        "booking_center_code": "Singapore",
        "role": "ADVISOR",
        "caller_application": "lotus-workbench",
    }
    values.update(overrides)
    return AdvisorBookCallerContext(**values)


def _member(
    portfolio_id: str,
    *,
    client_id: str = "CIF_SG_001",
    portfolio_type: str = "ADVISORY",
    booking_center_code: str = "Singapore",
    membership_source: str = "party_role_assignment",
) -> dict[str, object]:
    return {
        "portfolio_id": portfolio_id,
        "client_id": client_id,
        "booking_center_code": booking_center_code,
        "portfolio_type": portfolio_type,
        "status": "ACTIVE",
        "open_date": "2025-03-31",
        "close_date": None,
        "base_currency": "SGD",
        "source_record_id": f"portfolio:{portfolio_id}",
        "membership_source": membership_source,
        "role_type": "ADVISOR" if membership_source == "party_role_assignment" else None,
    }


def _payload(
    *,
    members: list[dict[str, object]] | None = None,
    tenant_id: str | None = "tenant-sg",
    portfolio_manager_id: str = "PM_SG_001",
    booking_center_code: str = "Singapore",
) -> dict[str, object]:
    resolved_members = members if members is not None else [_member("PB_SG_001")]
    return {
        "product_name": "PortfolioManagerBookMembership",
        "product_version": "v1",
        "portfolio_manager_id": portfolio_manager_id,
        "tenant_id": tenant_id,
        "generated_at": "2026-04-10T02:00:00Z",
        "as_of_date": "2026-04-10",
        "latest_evidence_timestamp": "2026-04-10T01:59:00Z",
        "snapshot_id": "pm_book_membership:2e7dfe0c",
        "content_hash": "sha256:0123456789abcdef",
        "data_quality_status": "ACCEPTED" if resolved_members else "MISSING",
        "source_evidence_current": bool(resolved_members),
        "freshness_status": "CURRENT" if resolved_members else "UNAVAILABLE",
        "booking_center_code": booking_center_code,
        "members": resolved_members,
        "supportability": {
            "state": "READY" if resolved_members else "INCOMPLETE",
            "reason": (
                "PM_BOOK_MEMBERSHIP_READY" if resolved_members else "PM_BOOK_MEMBERSHIP_EMPTY"
            ),
            "returned_portfolio_count": len(resolved_members),
            "filters_applied": ["portfolio_manager_id", "as_of_date"],
        },
        "lineage": {"source_system": "lotus-core"},
    }


@pytest.mark.asyncio
async def test_service_requests_authenticated_own_book_and_projects_governed_membership() -> None:
    client = _MembershipClient(payload=_payload())
    service = AdvisorBookService(membership_client=client)

    response = await service.get_advisor_book(
        caller=_caller(),
        query=AdvisorBookQuery(as_of_date=date(2026, 4, 10)),
        correlation_id="corr-book",
    )

    assert client.calls == [
        {
            "portfolio_manager_id": "PM_SG_001",
            "as_of_date": "2026-04-10",
            "booking_center_code": "Singapore",
            "portfolio_types": ["ADVISORY", "DISCRETIONARY"],
            "correlation_id": "corr-book",
        }
    ]
    assert response.scope.label == "My book"
    assert response.items[0].membership_basis == "governed_role_assignment"
    assert response.supportability.state == "ready"
    assert response.supportability.tenant_scope == "source_confirmed"


@pytest.mark.asyncio
async def test_service_filters_sorts_and_pages_source_memberships_deterministically() -> None:
    members = [
        _member("PB_003", client_id="CIF_002", portfolio_type="DISCRETIONARY"),
        _member("PB_001", client_id="CIF_001", portfolio_type="ADVISORY"),
        _member("PB_002", client_id="CIF_001", portfolio_type="ADVISORY"),
    ]
    service = AdvisorBookService(
        membership_client=_MembershipClient(payload=_payload(members=members))
    )

    response = await service.get_advisor_book(
        caller=_caller(),
        query=AdvisorBookQuery(
            as_of_date=date(2026, 4, 10),
            client_id="CIF_001",
            mandate_type="ADVISORY",
            sort_by="client_id",
            sort_order="desc",
            offset=1,
            limit=1,
        ),
        correlation_id="corr-page",
    )

    assert response.page.total_count == 2
    assert response.page.returned_count == 1
    assert [item.portfolio_id for item in response.items] == ["PB_001"]


@pytest.mark.asyncio
async def test_service_reports_filter_empty_without_claiming_source_book_is_empty() -> None:
    service = AdvisorBookService(membership_client=_MembershipClient(payload=_payload()))

    response = await service.get_advisor_book(
        caller=_caller(),
        query=AdvisorBookQuery(as_of_date=date(2026, 4, 10), client_id="CIF_UNKNOWN"),
        correlation_id="corr-filter",
    )

    assert response.items == []
    assert response.supportability.reason_code == "advisor_book_filter_empty"
    assert response.provenance is not None


@pytest.mark.asyncio
async def test_service_marks_null_source_tenant_as_degraded_not_certified() -> None:
    service = AdvisorBookService(
        membership_client=_MembershipClient(payload=_payload(tenant_id=None))
    )

    response = await service.get_advisor_book(
        caller=_caller(),
        query=AdvisorBookQuery(as_of_date=date(2026, 4, 10)),
        correlation_id="corr-tenant",
    )

    assert response.supportability.state == "degraded"
    assert response.supportability.reason_code == "advisor_book_tenant_scope_not_reported"
    assert response.supportability.tenant_scope == "trusted_context_only"


@pytest.mark.asyncio
async def test_service_marks_legacy_advisor_projection_as_degraded() -> None:
    payload = _payload(members=[_member("PB_001", membership_source="legacy_advisor_projection")])
    service = AdvisorBookService(membership_client=_MembershipClient(payload=payload))

    response = await service.get_advisor_book(
        caller=_caller(),
        query=AdvisorBookQuery(as_of_date=date(2026, 4, 10)),
        correlation_id="corr-legacy",
    )

    assert response.items[0].membership_basis == "legacy_advisor_projection"
    assert response.supportability.state == "degraded"
    assert response.supportability.reason_code == "advisor_book_legacy_projection"


@pytest.mark.asyncio
async def test_service_translates_source_not_found_to_explicit_empty_book() -> None:
    service = AdvisorBookService(membership_client=_MembershipClient(status_code=404))

    response = await service.get_advisor_book(
        caller=_caller(),
        query=AdvisorBookQuery(as_of_date=date(2026, 4, 10)),
        correlation_id="corr-empty",
    )

    assert response.items == []
    assert response.supportability.reason_code == "advisor_book_empty"
    assert response.provenance is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        _payload(portfolio_manager_id="PM_OTHER"),
        _payload(booking_center_code="Zurich"),
        _payload(members=[_member("PB_001", booking_center_code="Zurich")]),
        _payload(members=[_member("PB_DUPLICATE"), _member("PB_DUPLICATE")]),
    ],
)
async def test_service_fails_closed_on_cross_scope_or_duplicate_source_rows(
    payload: dict[str, object],
) -> None:
    service = AdvisorBookService(membership_client=_MembershipClient(payload=payload))

    with pytest.raises(AdvisorBookServiceError) as raised:
        await service.get_advisor_book(
            caller=_caller(),
            query=AdvisorBookQuery(as_of_date=date(2026, 4, 10)),
            correlation_id="corr-invalid",
        )

    assert raised.value.code == "advisor_book_source_contract_invalid"
    assert raised.value.status_code == 502


@pytest.mark.asyncio
async def test_service_rejects_cross_tenant_source_response() -> None:
    service = AdvisorBookService(
        membership_client=_MembershipClient(payload=_payload(tenant_id="tenant-other"))
    )

    with pytest.raises(AdvisorBookServiceError) as raised:
        await service.get_advisor_book(
            caller=_caller(),
            query=AdvisorBookQuery(as_of_date=date(2026, 4, 10)),
            correlation_id="corr-cross-tenant",
        )

    assert raised.value.code == "advisor_book_tenant_scope_mismatch"
    assert raised.value.status_code == 403


@pytest.mark.asyncio
@pytest.mark.parametrize("status_code", [400, 401, 403, 500, 503])
async def test_service_returns_product_safe_error_for_source_failures(status_code: int) -> None:
    service = AdvisorBookService(membership_client=_MembershipClient(status_code=status_code))

    with pytest.raises(AdvisorBookServiceError) as raised:
        await service.get_advisor_book(
            caller=_caller(),
            query=AdvisorBookQuery(as_of_date=date(2026, 4, 10)),
            correlation_id="corr-upstream",
        )

    assert raised.value.code == "advisor_book_source_unavailable"
    assert raised.value.status_code == 502
    assert "Core" not in raised.value.message
