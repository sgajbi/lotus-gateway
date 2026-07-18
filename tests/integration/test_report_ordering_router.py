from fastapi.testclient import TestClient

from app.contracts.report_ordering import WorkbenchReportOrderingResponse
from app.contracts.report_ordering_examples import REPORT_ORDERING_RESPONSE_EXAMPLE
from app.main import app

client = TestClient(app)


class StubReportOrderingService:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    async def get_ordering_options(self, **kwargs) -> WorkbenchReportOrderingResponse:
        self.calls.append(kwargs)
        return WorkbenchReportOrderingResponse.model_validate(REPORT_ORDERING_RESPONSE_EXAMPLE)


def _headers() -> dict[str, str]:
    return {
        "X-Actor-Id": "advisor-1",
        "X-Caller-Application": "lotus-workbench",
        "X-Tenant-Id": "tenant-sg",
        "X-Region": "APAC",
        "X-Role": "client_advisor",
        "X-Caller-Portfolio-Ids": "PB_SG_GLOBAL_BAL_001",
    }


def test_report_ordering_route_forwards_trusted_scope_context(monkeypatch) -> None:
    service = StubReportOrderingService()
    monkeypatch.setattr(
        "app.routers.reporting_ordering.report_ordering_service",
        lambda: service,
    )

    response = client.get(
        "/api/v1/report-ordering/options",
        params={"scopeType": "portfolio", "scopeId": "PB_SG_GLOBAL_BAL_001"},
        headers={**_headers(), "X-Correlation-Id": "corr-ordering"},
    )

    assert response.status_code == 200
    assert response.json() == REPORT_ORDERING_RESPONSE_EXAMPLE
    assert len(service.calls) == 1
    call = service.calls[0]
    assert call["selection"].scope_id == "PB_SG_GLOBAL_BAL_001"
    assert call["caller_headers"] == {
        "X-Actor-Id": "advisor-1",
        "X-Caller-Application": "lotus-workbench",
        "X-Tenant-Id": "tenant-sg",
        "X-Region": "APAC",
        "X-Role": "client_advisor",
        "X-Caller-Portfolio-Ids": "PB_SG_GLOBAL_BAL_001",
    }
    assert call["correlation_id"] == "corr-ordering"


def test_report_ordering_route_rejects_missing_required_caller_context(monkeypatch) -> None:
    service = StubReportOrderingService()
    monkeypatch.setattr(
        "app.routers.reporting_ordering.report_ordering_service",
        lambda: service,
    )

    response = client.get(
        "/api/v1/report-ordering/options",
        params={"scopeType": "portfolio", "scopeId": "PB_SG_GLOBAL_BAL_001"},
        headers={"X-Role": "client_advisor"},
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "missing_caller_context"
    assert service.calls == []


def test_report_ordering_route_rejects_incomplete_scope_pair(monkeypatch) -> None:
    service = StubReportOrderingService()
    monkeypatch.setattr(
        "app.routers.reporting_ordering.report_ordering_service",
        lambda: service,
    )

    response = client.get(
        "/api/v1/report-ordering/options",
        params={"scopeType": "portfolio"},
        headers=_headers(),
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_report_ordering_scope"
    assert service.calls == []


def test_report_ordering_openapi_is_business_safe_and_executable() -> None:
    operation = app.openapi()["paths"]["/api/v1/report-ordering/options"]["get"]
    parameters = {item["name"] for item in operation["parameters"]}
    example = operation["responses"]["200"]["content"]["application/json"]["example"]

    assert operation["summary"] == "Get report ordering options"
    assert "client distribution" in operation["description"]
    assert {"scopeType", "scopeId", "X-Caller-Portfolio-Ids"} <= parameters
    assert operation["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/WorkbenchReportOrderingResponse"
    }
    assert WorkbenchReportOrderingResponse.model_validate(example)
