from fastapi.testclient import TestClient

from app.contracts.advisor_book import AdvisorBookResponse
from app.contracts.advisor_book_attention import AdvisorBookAttentionResponse
from app.contracts.advisor_book_attention_examples import (
    ADVISOR_BOOK_ATTENTION_RESPONSE_EXAMPLE,
)
from app.contracts.advisor_book_examples import ADVISOR_BOOK_RESPONSE_EXAMPLE
from app.contracts.advisor_book_summary import AdvisorBookSummaryResponse
from app.contracts.advisor_book_summary_examples import ADVISOR_BOOK_SUMMARY_RESPONSE_EXAMPLE
from app.main import app
from app.services.advisor_book_service import AdvisorBookServiceError

client = TestClient(app)


class _AdvisorBookService:
    def __init__(self, *, error: AdvisorBookServiceError | None = None) -> None:
        self.error = error
        self.calls: list[dict[str, object]] = []

    async def get_advisor_book(self, **kwargs) -> AdvisorBookResponse:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return AdvisorBookResponse.model_validate(ADVISOR_BOOK_RESPONSE_EXAMPLE)


class _AdvisorBookSummaryService:
    def __init__(self, *, error: AdvisorBookServiceError | None = None) -> None:
        self.error = error
        self.calls: list[dict[str, object]] = []

    async def get_value_summary(self, **kwargs) -> AdvisorBookSummaryResponse:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return AdvisorBookSummaryResponse.model_validate(ADVISOR_BOOK_SUMMARY_RESPONSE_EXAMPLE)


def _headers(**overrides: str) -> dict[str, str]:
    headers = {
        "X-Actor-Id": "PM_SG_001",
        "X-Caller-Application": "lotus-workbench",
        "X-Tenant-Id": "tenant-sg",
        "X-Region": "APAC",
        "X-Booking-Center-Code": "Singapore",
        "X-Role": "ADVISOR",
        "X-Caller-Capabilities": "advisor.book.read",
        "X-Correlation-Id": "corr-advisor-book",
    }
    headers.update(overrides)
    return headers


def test_advisor_book_route_derives_own_book_scope_from_trusted_headers(monkeypatch) -> None:
    service = _AdvisorBookService()
    monkeypatch.setattr("app.routers.advisor_book.advisor_book_service", lambda: service)

    response = client.get(
        "/api/v1/advisor-book/portfolios",
        params={
            "asOfDate": "2026-04-10",
            "clientId": " CIF_SG_001 ",
            "mandateType": "ADVISORY",
            "sortBy": "client_id",
            "sortOrder": "desc",
            "offset": 5,
            "limit": 10,
        },
        headers=_headers(),
    )

    assert response.status_code == 200
    assert response.json() == ADVISOR_BOOK_RESPONSE_EXAMPLE
    assert len(service.calls) == 1
    call = service.calls[0]
    assert call["caller"].portfolio_manager_id == "PM_SG_001"
    assert call["caller"].tenant_id == "tenant-sg"
    assert call["query"].client_id == "CIF_SG_001"
    assert call["query"].mandate_type == "ADVISORY"
    assert call["query"].sort_by == "client_id"
    assert call["query"].offset == 5
    assert call["correlation_id"] == "corr-advisor-book"


def test_advisor_book_route_rejects_missing_trusted_context_before_service(monkeypatch) -> None:
    service = _AdvisorBookService()
    monkeypatch.setattr("app.routers.advisor_book.advisor_book_service", lambda: service)

    response = client.get(
        "/api/v1/advisor-book/portfolios",
        params={"asOfDate": "2026-04-10"},
        headers={"X-Actor-Id": "PM_SG_001"},
    )

    assert response.status_code == 400
    assert response.json()["code"] == "advisor_book_caller_context_missing"
    assert service.calls == []


def test_advisor_book_route_requires_exact_role_and_capability(monkeypatch) -> None:
    service = _AdvisorBookService()
    monkeypatch.setattr("app.routers.advisor_book.advisor_book_service", lambda: service)

    response = client.get(
        "/api/v1/advisor-book/portfolios",
        params={"asOfDate": "2026-04-10"},
        headers=_headers(**{"X-Caller-Capabilities": "advisor.book.read.all"}),
    )

    assert response.status_code == 403
    assert response.json()["code"] == "advisor_book_access_denied"
    assert service.calls == []


def test_advisor_book_route_returns_product_safe_source_error(monkeypatch) -> None:
    service = _AdvisorBookService(
        error=AdvisorBookServiceError(
            code="advisor_book_source_unavailable",
            message="Advisor-book information is temporarily unavailable.",
            status_code=502,
        )
    )
    monkeypatch.setattr("app.routers.advisor_book.advisor_book_service", lambda: service)

    response = client.get(
        "/api/v1/advisor-book/portfolios",
        params={"asOfDate": "2026-04-10"},
        headers=_headers(),
    )

    assert response.status_code == 502
    assert response.json() == {
        "code": "advisor_book_source_unavailable",
        "message": "Advisor-book information is temporarily unavailable.",
        "correlation_id": "corr-advisor-book",
    }


def test_advisor_book_route_rejects_blank_filter() -> None:
    response = client.get(
        "/api/v1/advisor-book/portfolios",
        params={"asOfDate": "2026-04-10", "clientId": "   "},
        headers=_headers(),
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "advisor_book_filter_invalid"


def test_advisor_book_openapi_exposes_bounded_own_book_contract() -> None:
    operation = app.openapi()["paths"]["/api/v1/advisor-book/portfolios"]["get"]
    parameters = {item["name"] for item in operation["parameters"]}
    example = operation["responses"]["200"]["content"]["application/json"]["example"]

    assert operation["summary"] == "Get my advisor book"
    assert "another advisor's book" in operation["description"]
    assert "advisorId" not in parameters
    assert {
        "asOfDate",
        "clientId",
        "mandateType",
        "sortBy",
        "sortOrder",
        "offset",
        "limit",
        "X-Actor-Id",
        "X-Tenant-Id",
        "X-Caller-Capabilities",
    } <= parameters
    assert operation["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/AdvisorBookResponse"
    }
    assert AdvisorBookResponse.model_validate(example)


def test_advisor_book_summary_route_preserves_trusted_scope_and_currency(monkeypatch) -> None:
    service = _AdvisorBookSummaryService()
    monkeypatch.setattr("app.routers.advisor_book.advisor_book_summary_service", lambda: service)

    response = client.get(
        "/api/v1/advisor-book/summary",
        params={"asOfDate": "2026-04-10", "reportingCurrency": "usd"},
        headers=_headers(),
    )

    assert response.status_code == 200
    assert response.json() == ADVISOR_BOOK_SUMMARY_RESPONSE_EXAMPLE
    assert len(service.calls) == 1
    assert service.calls[0]["reporting_currency"] == "USD"
    assert service.calls[0]["caller"].portfolio_manager_id == "PM_SG_001"


def test_advisor_book_summary_route_rejects_invalid_currency_before_service(monkeypatch) -> None:
    service = _AdvisorBookSummaryService()
    monkeypatch.setattr("app.routers.advisor_book.advisor_book_summary_service", lambda: service)

    response = client.get(
        "/api/v1/advisor-book/summary",
        params={"asOfDate": "2026-04-10", "reportingCurrency": "US1"},
        headers=_headers(),
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "advisor_book_reporting_currency_invalid"
    assert service.calls == []


def test_advisor_book_summary_openapi_is_typed_and_explicit() -> None:
    operation = app.openapi()["paths"]["/api/v1/advisor-book/summary"]["get"]
    parameters = {item["name"] for item in operation["parameters"]}
    example = operation["responses"]["200"]["content"]["application/json"]["example"]

    assert {"asOfDate", "reportingCurrency", "X-Actor-Id", "X-Tenant-Id"} <= parameters
    assert "one bounded Core AUM scope read" in operation["description"]
    assert "does not certify every value fact as current" in operation["description"]
    assert operation["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/AdvisorBookSummaryResponse"
    }
    assert AdvisorBookSummaryResponse.model_validate(example)


class _AdvisorBookAttentionService:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    async def get_attention(self, **kwargs) -> AdvisorBookAttentionResponse:
        self.calls.append(kwargs)
        return AdvisorBookAttentionResponse.model_validate(ADVISOR_BOOK_ATTENTION_RESPONSE_EXAMPLE)


def _attention_headers(**overrides: str) -> dict[str, str]:
    headers = _headers(
        **{
            "X-Caller-Capabilities": "advisor.book.read,advisory.advisor_cockpit.read",
            "X-Legal-Entity-Code": "SG01",
            "X-Principal-Status": "ACTIVE",
            "X-Authorized-Advisor-Id": "PM_SG_001",
        }
    )
    headers.update(overrides)
    return headers


def test_advisor_book_attention_route_requires_both_admitted_scopes(monkeypatch) -> None:
    service = _AdvisorBookAttentionService()
    monkeypatch.setattr(
        "app.routers.advisor_book_attention_route.advisor_book_attention_service",
        lambda: service,
    )

    response = client.get(
        "/api/v1/advisor-book/attention?asOfDate=2026-04-10",
        headers=_attention_headers(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["action_count"] == 2
    assert body["source"]["source_service"] == "lotus-advise"
    assert service.calls[0]["as_of_date"].isoformat() == "2026-04-10"
    assert service.calls[0]["book_caller"].portfolio_manager_id == "PM_SG_001"
    assert service.calls[0]["cockpit_caller"].authorized_advisor_id == "PM_SG_001"


def test_advisor_book_attention_route_rejects_missing_cockpit_capability(monkeypatch) -> None:
    service = _AdvisorBookAttentionService()
    monkeypatch.setattr(
        "app.routers.advisor_book_attention_route.advisor_book_attention_service",
        lambda: service,
    )

    response = client.get(
        "/api/v1/advisor-book/attention?asOfDate=2026-04-10",
        headers=_attention_headers(
            **{"X-Caller-Capabilities": "advisor.book.read"},
        ),
    )

    assert response.status_code == 403
    assert response.json()["code"] == "advisor_cockpit_access_denied"
    assert response.json()["correlation_id"]
    assert service.calls == []


def test_advisor_book_attention_route_rejects_missing_cockpit_context(monkeypatch) -> None:
    service = _AdvisorBookAttentionService()
    monkeypatch.setattr(
        "app.routers.advisor_book_attention_route.advisor_book_attention_service",
        lambda: service,
    )

    response = client.get(
        "/api/v1/advisor-book/attention?asOfDate=2026-04-10",
        headers=_headers(),
    )

    assert response.status_code in (400, 403)
    assert service.calls == []


def test_advisor_book_attention_route_rejects_portfolio_scoped_advise_entitlement(
    monkeypatch,
) -> None:
    service = _AdvisorBookAttentionService()
    monkeypatch.setattr(
        "app.routers.advisor_book_attention_route.advisor_book_attention_service",
        lambda: service,
    )

    response = client.get(
        "/api/v1/advisor-book/attention?asOfDate=2026-04-10",
        headers=_attention_headers(
            **{"X-Authorized-Portfolio-Id": "PB_SG_GLOBAL_BAL_001"},
        ),
    )

    assert response.status_code == 403
    assert response.json()["code"] == "advisor_book_attention_requires_advisor_scope"
    assert service.calls == []


def test_advisor_book_attention_route_wraps_source_failures_in_the_book_envelope(
    monkeypatch,
) -> None:
    from fastapi import HTTPException

    class _FailingAttentionService:
        async def get_attention(self, **kwargs):
            raise HTTPException(
                status_code=502,
                detail={
                    "code": "advisor_cockpit_upstream_invalid",
                    "message": "lotus-advise returned an unsafe cockpit payload.",
                },
            )

    monkeypatch.setattr(
        "app.routers.advisor_book_attention_route.advisor_book_attention_service",
        lambda: _FailingAttentionService(),
    )

    response = client.get(
        "/api/v1/advisor-book/attention?asOfDate=2026-04-10",
        headers=_attention_headers(),
    )

    assert response.status_code == 502
    body = response.json()
    assert body["code"] == "advisor_cockpit_upstream_invalid"
    assert body["message"]
    assert body["correlation_id"]
