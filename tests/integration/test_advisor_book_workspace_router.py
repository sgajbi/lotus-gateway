from fastapi.testclient import TestClient

from app.contracts.advisor_book_workspace import AdvisorBookWorkspaceResponse
from app.contracts.advisor_book_workspace_examples import (
    ADVISOR_BOOK_WORKSPACE_RESPONSE_EXAMPLE,
)
from app.main import app
from app.services.advisor_book_service import AdvisorBookServiceError
from app.services.advisor_book_workspace_facts import AdviseScopeUnavailable
from app.services.advisor_cockpit_access_policy import AdvisorCockpitCallerContext

client = TestClient(app)


class _WorkspaceService:
    def __init__(self, *, error: Exception | None = None) -> None:
        self.error = error
        self.calls: list[dict[str, object]] = []

    async def get_workspace(self, **kwargs) -> AdvisorBookWorkspaceResponse:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return AdvisorBookWorkspaceResponse.model_validate(ADVISOR_BOOK_WORKSPACE_RESPONSE_EXAMPLE)


def _install(monkeypatch, service: _WorkspaceService) -> None:
    monkeypatch.setattr(
        "app.routers.advisor_book_workspace_route.advisor_book_workspace_service",
        lambda: service,
    )


def _book_headers(**overrides: str) -> dict[str, str]:
    headers = {
        "X-Actor-Id": "PM_SG_001",
        "X-Caller-Application": "lotus-workbench",
        "X-Tenant-Id": "tenant-sg",
        "X-Region": "APAC",
        "X-Booking-Center-Code": "Singapore",
        "X-Role": "ADVISOR",
        "X-Caller-Capabilities": "advisor.book.read",
        "X-Correlation-Id": "corr-advisor-book-workspace",
    }
    headers.update(overrides)
    return headers


def _dual_scope_headers(**overrides: str) -> dict[str, str]:
    headers = _book_headers(
        **{
            "X-Caller-Capabilities": "advisor.book.read,advisory.advisor_cockpit.read",
            "X-Legal-Entity-Code": "SG01",
            "X-Principal-Status": "ACTIVE",
            "X-Authorized-Advisor-Id": "PM_SG_001",
        }
    )
    headers.update(overrides)
    return headers


_PARAMS = {"asOfDate": "2026-04-10", "reportingCurrency": "usd"}


def test_workspace_route_composes_with_an_admitted_advisor_advise_scope(monkeypatch) -> None:
    service = _WorkspaceService()
    _install(monkeypatch, service)

    response = client.get(
        "/api/v1/advisor-book/workspace", params=_PARAMS, headers=_dual_scope_headers()
    )

    assert response.status_code == 200
    assert response.json() == ADVISOR_BOOK_WORKSPACE_RESPONSE_EXAMPLE
    call = service.calls[0]
    assert call["book_caller"].portfolio_manager_id == "PM_SG_001"
    assert isinstance(call["advise_scope"], AdvisorCockpitCallerContext)
    assert call["advise_scope"].authorized_advisor_id == "PM_SG_001"
    assert call["as_of_date"].isoformat() == "2026-04-10"
    assert call["reporting_currency"] == "USD"
    assert call["correlation_id"] == "corr-advisor-book-workspace"


def test_workspace_route_degrades_when_no_advise_scope_is_presented(monkeypatch) -> None:
    service = _WorkspaceService()
    _install(monkeypatch, service)

    response = client.get("/api/v1/advisor-book/workspace", params=_PARAMS, headers=_book_headers())

    assert response.status_code == 200
    assert service.calls[0]["advise_scope"] == AdviseScopeUnavailable("advise_scope_not_presented")


def test_workspace_route_degrades_an_invalid_advise_context(monkeypatch) -> None:
    service = _WorkspaceService()
    _install(monkeypatch, service)

    # Advise context partially presented (principal status without legal entity).
    response = client.get(
        "/api/v1/advisor-book/workspace",
        params=_PARAMS,
        headers=_book_headers(**{"X-Principal-Status": "ACTIVE"}),
    )

    assert response.status_code == 200
    assert service.calls[0]["advise_scope"] == AdviseScopeUnavailable("advise_scope_invalid")


def test_workspace_route_degrades_a_missing_cockpit_capability(monkeypatch) -> None:
    service = _WorkspaceService()
    _install(monkeypatch, service)

    response = client.get(
        "/api/v1/advisor-book/workspace",
        params=_PARAMS,
        headers=_dual_scope_headers(**{"X-Caller-Capabilities": "advisor.book.read"}),
    )

    assert response.status_code == 200
    assert service.calls[0]["advise_scope"] == AdviseScopeUnavailable("advise_scope_invalid")


def test_workspace_route_degrades_a_portfolio_scoped_advise_entitlement(monkeypatch) -> None:
    service = _WorkspaceService()
    _install(monkeypatch, service)

    response = client.get(
        "/api/v1/advisor-book/workspace",
        params=_PARAMS,
        headers=_dual_scope_headers(**{"X-Authorized-Portfolio-Id": "PB_SG_GLOBAL_BAL_001"}),
    )

    assert response.status_code == 200
    assert service.calls[0]["advise_scope"] == AdviseScopeUnavailable("advise_scope_not_advisor")


def test_workspace_route_degrades_an_unscoped_supervisory_principal(monkeypatch) -> None:
    service = _WorkspaceService()
    _install(monkeypatch, service)

    # A portfolio-manager principal reads the book, but without an advisor-scoped
    # Advise entitlement the action feed could be wider than one advisor's book.
    headers = _dual_scope_headers(**{"X-Role": "PORTFOLIO_MANAGER"})
    headers.pop("X-Authorized-Advisor-Id")
    response = client.get("/api/v1/advisor-book/workspace", params=_PARAMS, headers=headers)

    assert response.status_code == 200
    assert service.calls[0]["advise_scope"] == AdviseScopeUnavailable("advise_scope_not_advisor")
    assert service.calls[0]["book_caller"].role == "PORTFOLIO_MANAGER"


def test_workspace_route_requires_trusted_book_context(monkeypatch) -> None:
    service = _WorkspaceService()
    _install(monkeypatch, service)

    headers = _book_headers()
    headers.pop("X-Actor-Id")
    response = client.get("/api/v1/advisor-book/workspace", params=_PARAMS, headers=headers)

    assert response.status_code == 400
    assert response.json()["code"] == "advisor_book_caller_context_missing"
    assert service.calls == []


def test_workspace_route_rejects_an_invalid_reporting_currency(monkeypatch) -> None:
    service = _WorkspaceService()
    _install(monkeypatch, service)

    response = client.get(
        "/api/v1/advisor-book/workspace",
        params={"asOfDate": "2026-04-10", "reportingCurrency": "US1"},
        headers=_dual_scope_headers(),
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "advisor_book_reporting_currency_invalid"
    assert service.calls == []


def test_workspace_route_keeps_the_error_envelope_for_service_errors(monkeypatch) -> None:
    service = _WorkspaceService(
        error=AdvisorBookServiceError(
            code="advisor_book_workspace_deadline_exhausted",
            message="The workspace composition deadline was exhausted.",
            status_code=504,
        )
    )
    _install(monkeypatch, service)

    response = client.get(
        "/api/v1/advisor-book/workspace", params=_PARAMS, headers=_dual_scope_headers()
    )

    assert response.status_code == 504
    body = response.json()
    assert body["code"] == "advisor_book_workspace_deadline_exhausted"
    assert body["correlation_id"] == "corr-advisor-book-workspace"


def test_workspace_route_maps_a_membership_outage_to_the_bounded_502(monkeypatch) -> None:
    from fastapi import HTTPException

    service = _WorkspaceService(
        error=HTTPException(status_code=503, detail={"code": "core_unavailable"})
    )
    _install(monkeypatch, service)

    response = client.get(
        "/api/v1/advisor-book/workspace", params=_PARAMS, headers=_dual_scope_headers()
    )

    assert response.status_code == 502
    assert response.json()["code"] == "advisor_book_workspace_source_unavailable"


def test_workspace_openapi_is_typed_and_explicit() -> None:
    operation = app.openapi()["paths"]["/api/v1/advisor-book/workspace"]["get"]
    parameters = {item["name"] for item in operation["parameters"]}
    example = operation["responses"]["200"]["content"]["application/json"]["example"]

    assert {"asOfDate", "reportingCurrency", "X-Actor-Id", "X-Authorized-Advisor-Id"} <= parameters
    assert "resolved exactly once" in operation["description"]
    assert "never removes a row" in operation["description"]
    assert operation["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/AdvisorBookWorkspaceResponse"
    }
    assert AdvisorBookWorkspaceResponse.model_validate(example)
