from typing import Any

from fastapi.testclient import TestClient

from app.contracts.reporting_batch_preflight import ReportBatchPreflightResponse
from app.contracts.reporting_batch_preflight_examples import (
    REPORT_BATCH_PREFLIGHT_RESPONSE_EXAMPLE,
)
from app.main import app

client = TestClient(app)


class _StubPreflightService:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def preflight(self, **kwargs):
        self.calls.append(kwargs)

        payload = REPORT_BATCH_PREFLIGHT_RESPONSE_EXAMPLE.copy()
        payload["source_posture"] = dict(payload["source_posture"])
        payload["configuration_posture"] = dict(payload["configuration_posture"])
        payload["candidates"] = list(payload["candidates"])
        payload["request"] = kwargs["request"].model_dump(mode="json")
        payload["state"] = "ready"
        payload["reason_code"] = "preflight_ready"
        payload["message"] = "All requested portfolios are ready for report creation."
        payload["candidate_count"] = 1
        payload["ready_count"] = 1
        payload["partial_count"] = 0
        payload["permission_blocked_count"] = 0
        payload["candidates"] = payload["candidates"][:1]
        return ReportBatchPreflightResponse.model_validate(payload)


def _headers() -> dict[str, str]:
    return {
        "X-Actor-Id": "advisor-1",
        "X-Caller-Application": "lotus-workbench",
        "X-Tenant-Id": "tenant-sg",
        "X-Region": "APAC",
        "X-Booking-Center-Code": "SG",
        "X-Role": "ADVISOR",
        "X-Caller-Capabilities": "advisor.book.read",
        "X-Caller-Portfolio-Ids": "browser-authority-must-not-be-used",
    }


def _request() -> dict[str, object]:
    return {
        "selector_mode": "explicit_portfolio_list",
        "portfolio_ids": ["PB_SG_GLOBAL_BAL_001"],
        "as_of_date": "2026-04-22",
        "requested_output_formats": ["pdf"],
        "reporting_currency": "USD",
        "options": {"sections": ["OVERVIEW"]},
        "max_batch_size": 250,
    }


def test_report_batch_preflight_is_read_only_and_forwards_trusted_context(monkeypatch) -> None:
    service = _StubPreflightService()
    monkeypatch.setattr(
        "app.routers.reporting_batches.reporting_batch_preflight_service",
        lambda: service,
    )

    response = client.post(
        "/api/v1/report-batches/preflight",
        json=_request(),
        headers={**_headers(), "X-Correlation-Id": "corr-batch-preflight"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["contract_version"] == "report-batch-preflight.v1"
    assert body["candidates"][0]["portfolio_id"] == "PB_SG_GLOBAL_BAL_001"
    assert body["state"] == "ready"
    assert len(service.calls) == 1
    assert service.calls[0]["request"].portfolio_ids == [
        "PB_SG_GLOBAL_BAL_001",
    ]
    assert service.calls[0]["caller_headers"] == {
        "X-Actor-Id": "advisor-1",
        "X-Caller-Application": "lotus-workbench",
        "X-Tenant-Id": "tenant-sg",
        "X-Region": "APAC",
        "X-Booking-Center-Code": "SG",
        "X-Role": "ADVISOR",
        "X-Caller-Capabilities": "advisor.book.read",
    }
    assert service.calls[0]["correlation_id"] == "corr-batch-preflight"


def test_report_batch_preflight_openapi_is_typed_and_non_authoritative() -> None:
    operation = app.openapi()["paths"]["/api/v1/report-batches/preflight"]["post"]

    assert operation["summary"] == "Preflight report batch candidates"
    assert "non-authoritative" in operation["description"]
    assert operation["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ReportBatchPreflightResponse"
    }
    schema = app.openapi()["components"]["schemas"]["ReportBatchCandidatePreflight"]
    assert schema["properties"]["state"]["enum"] == [
        "ready",
        "partial",
        "stale",
        "permission_blocked",
        "unavailable",
    ]
