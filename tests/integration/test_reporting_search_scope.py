"""The report-job search is fenced by the admitted caller scope: a filter can
only narrow within it, a conflict is refused before any source call, and a
source result outside the fence is refused rather than published."""

import copy

from fastapi.testclient import TestClient

from app.contracts.reporting_query_examples import REPORT_JOB_LIST_RESPONSE_EXAMPLE
from app.main import app

_LIST_CLIENT = "app.clients.reporting_client.ReportingClient.list_report_jobs"

_HEADERS = {
    "X-Actor-Id": "ops-123",
    "X-Tenant-Id": "tenant-sg",
    "X-Region": "APAC",
}


def _install(monkeypatch, payload):
    captured: dict[str, object] = {}

    async def _mock_list(self, *, filters, caller_headers, correlation_id):
        captured["filters"] = filters
        return 200, copy.deepcopy(payload)

    monkeypatch.setattr(_LIST_CLIENT, _mock_list)
    return captured


def test_search_always_sends_the_admitted_fence_upstream(monkeypatch):
    captured = _install(monkeypatch, REPORT_JOB_LIST_RESPONSE_EXAMPLE)

    client = TestClient(app)
    response = client.get("/api/v1/report-jobs?status=accepted", headers=_HEADERS)

    assert response.status_code == 200
    assert captured["filters"]["tenantId"] == "tenant-sg"
    assert captured["filters"]["region"] == "APAC"


def test_search_accepts_a_filter_matching_the_admitted_fence(monkeypatch):
    captured = _install(monkeypatch, REPORT_JOB_LIST_RESPONSE_EXAMPLE)

    client = TestClient(app)
    response = client.get("/api/v1/report-jobs?tenantId=tenant-sg&region=APAC", headers=_HEADERS)

    assert response.status_code == 200
    assert captured["filters"]["tenantId"] == "tenant-sg"


def test_search_refuses_a_conflicting_tenant_filter_before_any_source_call(monkeypatch):
    captured = _install(monkeypatch, REPORT_JOB_LIST_RESPONSE_EXAMPLE)

    client = TestClient(app)
    response = client.get("/api/v1/report-jobs?tenantId=tenant-b", headers=_HEADERS)

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "report_job_tenant_scope_ambiguous"
    assert "filters" not in captured


def test_search_refuses_a_conflicting_region_filter_before_any_source_call(monkeypatch):
    captured = _install(monkeypatch, REPORT_JOB_LIST_RESPONSE_EXAMPLE)

    client = TestClient(app)
    response = client.get("/api/v1/report-jobs?region=EMEA", headers=_HEADERS)

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "report_job_region_scope_ambiguous"
    assert "filters" not in captured


def test_search_refuses_a_source_row_outside_the_admitted_tenant(monkeypatch):
    payload = copy.deepcopy(REPORT_JOB_LIST_RESPONSE_EXAMPLE)
    payload["items"][0]["tenantId"] = "tenant-b"
    _install(monkeypatch, payload)

    client = TestClient(app)
    response = client.get("/api/v1/report-jobs?status=accepted", headers=_HEADERS)

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "report_job_source_scope_violation"


def test_search_refuses_an_applied_filter_echo_outside_the_admitted_tenant(monkeypatch):
    payload = copy.deepcopy(REPORT_JOB_LIST_RESPONSE_EXAMPLE)
    payload["appliedFilters"]["tenantId"] = "tenant-b"
    _install(monkeypatch, payload)

    client = TestClient(app)
    response = client.get("/api/v1/report-jobs?status=accepted", headers=_HEADERS)

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "report_job_source_scope_violation"
