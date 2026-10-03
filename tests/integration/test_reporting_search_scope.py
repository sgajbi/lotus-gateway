"""The report-job search is fenced by the admitted caller scope: a filter can
only narrow within it, a conflict is refused before any source call, and a
source result outside the fence is refused rather than published."""

import copy

import pytest
from fastapi.testclient import TestClient

from app.contracts.reporting_query_examples import REPORT_JOB_LIST_RESPONSE_EXAMPLE
from app.main import app

_LIST_CLIENT = "app.clients.reporting_client.ReportingClient.list_report_jobs"

_HEADERS = {
    "X-Actor-Id": "ops-123",
    "X-Tenant-Id": "tenant-sg",
    "X-Region": "APAC",
}


@pytest.fixture
def client():
    with TestClient(app) as owned_client:
        yield owned_client


def _install(monkeypatch, payload):
    captured: dict[str, object] = {}

    async def _mock_list(self, *, filters, caller_headers, correlation_id):
        captured["filters"] = filters
        return 200, copy.deepcopy(payload)

    monkeypatch.setattr(_LIST_CLIENT, _mock_list)
    return captured


def test_search_always_sends_the_admitted_fence_upstream(monkeypatch, client):
    captured = _install(monkeypatch, REPORT_JOB_LIST_RESPONSE_EXAMPLE)

    response = client.get("/api/v1/report-jobs?status=accepted", headers=_HEADERS)

    assert response.status_code == 200
    assert captured["filters"]["tenantId"] == "tenant-sg"
    assert captured["filters"]["region"] == "APAC"


def test_search_accepts_a_filter_matching_the_admitted_fence(monkeypatch, client):
    captured = _install(monkeypatch, REPORT_JOB_LIST_RESPONSE_EXAMPLE)

    response = client.get("/api/v1/report-jobs?tenantId=tenant-sg&region=APAC", headers=_HEADERS)

    assert response.status_code == 200
    assert captured["filters"]["tenantId"] == "tenant-sg"


def test_search_refuses_a_conflicting_tenant_filter_before_any_source_call(monkeypatch, client):
    captured = _install(monkeypatch, REPORT_JOB_LIST_RESPONSE_EXAMPLE)

    response = client.get("/api/v1/report-jobs?tenantId=tenant-b", headers=_HEADERS)

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "report_job_tenant_scope_ambiguous"
    assert "filters" not in captured


def test_search_refuses_a_conflicting_region_filter_before_any_source_call(monkeypatch, client):
    captured = _install(monkeypatch, REPORT_JOB_LIST_RESPONSE_EXAMPLE)

    response = client.get("/api/v1/report-jobs?region=EMEA", headers=_HEADERS)

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "report_job_region_scope_ambiguous"
    assert "filters" not in captured


def test_search_refuses_a_source_row_outside_the_admitted_tenant(monkeypatch, client):
    payload = copy.deepcopy(REPORT_JOB_LIST_RESPONSE_EXAMPLE)
    payload["items"][0]["tenantId"] = "tenant-b"
    _install(monkeypatch, payload)

    response = client.get("/api/v1/report-jobs?status=accepted", headers=_HEADERS)

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "report_job_source_scope_violation"


def test_search_refuses_an_applied_filter_echo_outside_the_admitted_tenant(monkeypatch, client):
    payload = copy.deepcopy(REPORT_JOB_LIST_RESPONSE_EXAMPLE)
    payload["appliedFilters"]["tenantId"] = "tenant-b"
    _install(monkeypatch, payload)

    response = client.get("/api/v1/report-jobs?status=accepted", headers=_HEADERS)

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "report_job_source_scope_violation"


@pytest.mark.parametrize(
    "scope",
    [
        {"portfolio_ids": ["PRIVATE-OTHER"]},
        {},
        {"portfolio_ids": None},
        {"portfolio_ids": "PB_SG_GLOBAL_BAL_001"},
        {"portfolio_ids": []},
        {"portfolio_ids": ["PB_SG_GLOBAL_BAL_001", 1]},
        {"portfolio_ids": ["PB_SG_GLOBAL_BAL_001", " "]},
    ],
)
def test_portfolio_search_refuses_unrelated_or_malformed_row_scope(monkeypatch, client, scope):
    payload = copy.deepcopy(REPORT_JOB_LIST_RESPONSE_EXAMPLE)
    payload["items"][0]["portfolioScope"] = scope
    captured = _install(monkeypatch, payload)
    response = client.get("/api/v1/report-jobs?portfolioId=PB_SG_GLOBAL_BAL_001", headers=_HEADERS)
    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "report_job_source_scope_violation"
    assert "PRIVATE-OTHER" not in response.text
    assert "rjob_" not in response.text
    assert captured["filters"]["portfolioId"] == "PB_SG_GLOBAL_BAL_001"


@pytest.mark.parametrize("echo", [None, "", "PRIVATE-OTHER"])
def test_portfolio_search_requires_matching_applied_filter(monkeypatch, client, echo):
    payload = copy.deepcopy(REPORT_JOB_LIST_RESPONSE_EXAMPLE)
    payload["appliedFilters"]["portfolioId"] = echo
    _install(monkeypatch, payload)
    response = client.get("/api/v1/report-jobs?portfolioId=PB_SG_GLOBAL_BAL_001", headers=_HEADERS)
    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "report_job_source_scope_violation"
    assert "PRIVATE-OTHER" not in response.text


@pytest.mark.parametrize("count", [-1, 0, 2, True, "1", 1.5])
def test_search_refuses_inconsistent_or_malformed_count(monkeypatch, client, count):
    payload = copy.deepcopy(REPORT_JOB_LIST_RESPONSE_EXAMPLE)
    payload["count"] = count
    _install(monkeypatch, payload)
    response = client.get("/api/v1/report-jobs?portfolioId=PB_SG_GLOBAL_BAL_001", headers=_HEADERS)
    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "report_job_source_contract_invalid"
    assert "rjob_" not in response.text


@pytest.mark.parametrize("mode", ["single", "multi", "empty", "no_portfolio_filter"])
def test_search_preserves_valid_neighbors(monkeypatch, client, mode):
    payload = copy.deepcopy(REPORT_JOB_LIST_RESPONSE_EXAMPLE)
    route = "/api/v1/report-jobs?portfolioId=PB_SG_GLOBAL_BAL_001"
    if mode == "multi":
        payload["items"][0]["portfolioScope"]["portfolio_ids"].append("PB_SG_GLOBAL_BAL_002")
    elif mode == "empty":
        payload.update(count=0, items=[])
    elif mode == "no_portfolio_filter":
        route = "/api/v1/report-jobs?status=accepted"
        payload["appliedFilters"].pop("portfolioId")
        payload["items"][0]["portfolioScope"] = {"portfolio_ids": ["PB_SG_GLOBAL_BAL_002"]}
    _install(monkeypatch, payload)
    response = client.get(route, headers=_HEADERS)
    assert response.status_code == 200
    assert response.json()["count"] == len(payload["items"])
    assert [row["portfolioScope"] for row in response.json()["items"]] == [
        row["portfolioScope"] for row in payload["items"]
    ]
