"""Registered Gateway route -> concrete Performance HTTP adapter authority proof."""

import json
from copy import deepcopy
from dataclasses import replace
from datetime import date
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from app.contracts.workbench import (
    WorkbenchOverviewResponse,
    WorkbenchOverviewSummary,
    WorkbenchPortfolioSummary,
)
from app.main import app
from app.services.performance_workspace_context import WorkspaceRequestContext
from app.services.workbench_service_factory import (
    build_performance_workspace_service,
    build_workbench_service,
)

ROUTE = "/api/v1/workbench/PF_SHARED/performance/summary?period=YTD"
CALLER = {"X-Actor-Id": "advisor", "X-Tenant-Id": "tenant-a", "X-Region": "APAC"}
PROTECTED_ROUTES = [
    ROUTE,
    "/api/v1/workbench/PF_SHARED/performance/details",
    "/api/v1/workbench/PF_SHARED/performance/horizon-comparison",
    "/api/v1/workbench/PF_SHARED/performance/attribution-trend",
    "/api/v1/workbench/PF_SHARED/performance/advisor-brief",
    "/api/v1/workbench/PF_SHARED/performance/evidence/artifacts/calc/request.json",
    "/api/v1/portfolio/portfolios/PF_SHARED/performance-snapshot",
]


def workspace_context():
    return WorkspaceRequestContext(
        overview=WorkbenchOverviewResponse(
            correlation_id="fixture",
            contract_version="v1",
            as_of_date="2026-04-10",
            portfolio=WorkbenchPortfolioSummary(
                portfolio_id="PF_SHARED",
                client_id="client",
                base_currency="USD",
                booking_center_code="SG",
            ),
            overview=WorkbenchOverviewSummary(
                market_value_base=1000,
                cash_weight_pct=5,
                position_count=2,
            ),
        ),
        warnings=[],
        partial_failures=[],
        report_end_date="2026-04-10",
        report_start_date=date(2026, 1, 1),
        effective_period="YTD",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        requested_chart_frequency_supported=True,
        requested_contribution_dimension_supported=True,
        requested_attribution_dimension_supported=True,
        segment="2026-01-01:2026-04-10",
        benchmark_code=None,
        benchmark_catalog_result=(200, {}),
        requested_as_of_date=None,
        requested_reporting_currency=None,
        reporting_currency="USD",
    )


@pytest.fixture
def performance_transport(monkeypatch, request):
    requests = []
    peer_sources = {}
    qualification = getattr(
        request,
        "param",
        {"calculation_supportability": {"state": "ready", "freshness_bucket": "fresh"}},
    )
    service = build_performance_workspace_service(build_workbench_service())
    monkeypatch.setattr(
        "app.routers.workbench_performance.performance_workspace_service",
        lambda: service,
    )
    monkeypatch.setattr(
        "app.routers.workbench_performance_details.performance_workspace_service",
        lambda: service,
    )
    # Own the shared app flag for this lifespan, then restore its prior state.
    monkeypatch.setattr(app.state, "is_draining", False, raising=False)

    async def context(**kwargs):
        if source := qualification.get("source_response"):
            history = source["calculation_supportability"]["history_coverage"]
            return replace(
                workspace_context(),
                report_start_date=date.fromisoformat(history["requested_start_date"]),
                report_end_date=history["requested_end_date"],
                effective_period=next(iter(source["results_by_period"])),
                benchmark_code="BMK_CONTROL" if qualification.get("peer_responses") else None,
            )
        return workspace_context()

    def respond(request):
        requests.append(request)
        tenant = request.headers.get("X-Tenant-Id")
        if tenant not in {"tenant-a", "tenant-b"}:
            return httpx.Response(401, json={"detail": "tenant required before durable submission"})
        calculation = f"calc-{tenant}"
        if request.method == "POST":
            assert json.loads(request.content)["portfolio_id"] == "PF_SHARED"
            if peers := qualification.get("peer_responses"):
                role = request.url.path.rsplit("/", 1)[-1]
                calculation = f"{calculation}-{role}"
                peer_sources[calculation] = peers[role]
            return httpx.Response(
                202,
                json={
                    "calculation_id": calculation,
                    "result_path": f"/performance/results/{calculation}",
                    "poll_after_seconds": 0.001,
                },
            )
        if peer_sources:
            calculation = request.url.path.rsplit("/", 1)[-1]
        if calculation not in request.url.path:
            return httpx.Response(404, json={"detail": "Calculation not found"})
        if "/results/" in request.url.path:
            if source := peer_sources.get(calculation) or qualification.get("source_response"):
                response = deepcopy(source)
                # Controlled transport identities match this registered-route request.
                response.update(calculation_id=calculation, portfolio_id="PF_SHARED")
                if qualification.get("peer_responses"):
                    for period in response["results_by_period"].values():
                        period["benchmark"] = {"benchmark_id": "BMK_CONTROL"}
                return httpx.Response(200, json=response)
            value = 3.25 if tenant == "tenant-a" else -1.5
            return httpx.Response(
                200,
                json={
                    "calculation_id": calculation,
                    **qualification,
                    "results_by_period": {
                        "YTD": {
                            "portfolio_twr": {
                                "net": {"summary": {"period_return": {"base": value}}}
                            },
                        }
                    },
                },
            )
        return httpx.Response(
            200,
            json={
                "calculation_id": calculation,
                "status": "complete",
                "stages": [],
                "artifacts": {},
                "upstream_snapshots": [
                    {
                        "upstream_endpoint": "portfolio_timeseries",
                        "source_identifier": "PF_SHARED",
                        "as_of_date": "2026-04-10",
                        "retrieval_status": "200",
                    }
                ],
            },
        )

    original_client = httpx.AsyncClient
    monkeypatch.setattr(service, "_build_workspace_request_context", context)
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: original_client(
            **kwargs,
            transport=httpx.MockTransport(respond),
        ),
    )
    yield requests
    service.clear_upstream_cache()


_HISTORY_RESPONSES = json.loads(
    (
        Path(__file__).parents[1] / "fixtures" / "performance-history-source-responses.json"
    ).read_text(encoding="utf-8")
)


# Deliberately controlled history-only variants; no new producer arithmetic is asserted.
_GAP_RESPONSES = {}
for _gap, _day in (
    ("leading", "2026-01-05"),
    ("interior", "2026-01-07"),
    ("trailing", "2026-01-09"),
):
    _source = deepcopy(_HISTORY_RESPONSES["unknown"])
    _history = _source["calculation_supportability"]["history_coverage"]
    _history.update(
        status="partial",
        calendar_basis="natural_days",
        missing_required_observation_dates_sample=[_day],
        reason_codes=[f"{_gap}_history_missing"],
    )
    if _gap == "leading":
        _history.update(covered_start_date="2026-01-06", effective_start_date="2026-01-06")
    if _gap == "trailing":
        _history.update(covered_end_date="2026-01-08", effective_end_date="2026-01-08")
    _GAP_RESPONSES[_gap] = _source


@pytest.mark.parametrize("surface", ["summary", "details"])
@pytest.mark.parametrize(
    "performance_transport,source",
    [({"source_response": source}, source) for source in _GAP_RESPONSES.values()],
    ids=list(_GAP_RESPONSES),
    indirect=["performance_transport"],
)
def test_public_gap_qualification_retains_source_dates_without_zero_filling(
    performance_transport, source, surface
):
    with TestClient(app) as client:
        response = client.get(f"/api/v1/workbench/PF_SHARED/performance/{surface}", headers=CALLER)
    assert response.status_code == 200
    items = response.json()["evidence_view"]["source_supportability"]
    assert items
    assert all(
        item["history_coverage"] == source["calculation_supportability"]["history_coverage"]
        and item["state"] == "partial"
        for item in items
    )


@pytest.mark.parametrize(
    "performance_transport",
    [
        {
            "source_response": _HISTORY_RESPONSES["complete"],
            "peer_responses": {
                "workspace-summary": _HISTORY_RESPONSES["complete"],
                "contribution": _HISTORY_RESPONSES["partial"],
                "attribution": _HISTORY_RESPONSES["unknown"],
            },
        }
    ],
    indirect=True,
)
def test_public_details_preserve_divergent_peer_calculations(performance_transport):
    with TestClient(app) as client:
        response = client.get("/api/v1/workbench/PF_SHARED/performance/details", headers=CALLER)
    assert response.status_code == 200
    evidence = response.json()["evidence_view"]
    items = {item["calculation_role"]: item for item in evidence["source_supportability"]}
    assert set(items) == {"workspace_summary", "contribution", "attribution"}
    for role, case in (
        ("workspace_summary", "complete"),
        ("contribution", "partial"),
        ("attribution", "unknown"),
    ):
        assert (
            items[role]["history_coverage"]
            == (_HISTORY_RESPONSES[case]["calculation_supportability"]["history_coverage"])
        )
    assert len({item["calculation_id"] for item in items.values()}) == 3
    assert evidence["state"] == "partial"


@pytest.mark.parametrize("surface", ["summary", "details"])
@pytest.mark.parametrize(
    "performance_transport",
    [
        {"calculation_supportability": {"state": "ready", "history_coverage": value}}
        for value in ({}, [], {"status": "complete"}, "complete")
    ],
    indirect=["performance_transport"],
)
def test_malformed_history_public_response_is_unverified_not_http500(
    performance_transport, surface
):
    with TestClient(app) as client:
        response = client.get(f"/api/v1/workbench/PF_SHARED/performance/{surface}", headers=CALLER)
    assert response.status_code == 200
    body = response.json()
    items = body["evidence_view"]["source_supportability"]
    assert items
    assert all(item["state"] == "partial" and item["history_coverage"] is None for item in items)
    assert all("missing or invalid" in item["reason"] for item in items)
    assert body["evidence_view"]["state"] != "supported"


@pytest.mark.parametrize("surface", ["summary", "details"])
@pytest.mark.parametrize(
    "performance_transport,source",
    [
        ({"source_response": _HISTORY_RESPONSES[case]}, _HISTORY_RESPONSES[case])
        for case in ("complete", "partial", "unknown")
    ],
    indirect=["performance_transport"],
)
def test_registered_history_survives_unchanged_async_http_adapter(
    performance_transport, source, surface
):
    headers = {**CALLER, "X-Correlation-Id": "history-source-preservation"}
    with TestClient(app) as client:
        response = client.get(f"/api/v1/workbench/PF_SHARED/performance/{surface}", headers=headers)
    assert response.status_code == 200
    body = response.json()
    item = next(
        item
        for item in body["evidence_view"]["source_supportability"]
        if item["calculation_role"] == "workspace_summary"
    )
    assert item["history_coverage"] == source["calculation_supportability"]["history_coverage"]
    assert item["calculation_id"] == "calc-tenant-a"
    assert item["period_keys"] == list(source["results_by_period"])
    assert item["metric_basis"] == "NET"
    assert item["state"] == (
        "supported" if source["calculation_supportability"]["state"] == "ready" else "partial"
    )
    if surface == "summary":
        assert body["net_performance"]["portfolio_return_pct"] == 5.0
    assert performance_transport
    for request in performance_transport:
        assert request.headers["X-Tenant-Id"] == "tenant-a"
        assert request.headers["X-Actor-Id"] == "advisor"
        assert request.headers["X-Correlation-Id"] == "history-source-preservation"


@pytest.mark.parametrize(
    "performance_transport,expected",
    [
        ({}, "partial"),
        ({"calculation_supportability": None}, "partial"),
        ({"calculation_supportability": []}, "partial"),
        ({"calculation_supportability": {}}, "partial"),
        ({"calculation_supportability": {"state": ""}}, "partial"),
        (
            {"calculation_supportability": {"state": "unrecognized", "reason": "PRIVATE-MARKER"}},
            "partial",
        ),
        ({"calculation_supportability": {"state": 1}}, "partial"),
        (
            {"calculation_supportability": {"state": "ready", "freshness_bucket": "fresh"}},
            "supported",
        ),
        (
            {
                "metadata": {
                    "calculation_supportability": {"state": "ready", "freshness_bucket": "fresh"}
                }
            },
            "supported",
        ),
        (
            {"calculation_supportability": {"state": "blocked", "reason": "source_quality_issue"}},
            "partial",
        ),
        (
            {"calculation_supportability": {"state": "stale", "reason": "source_quality_issue"}},
            "partial",
        ),
        (
            {
                "calculation_supportability": {
                    "state": "unavailable",
                    "reason": "source_quality_issue",
                }
            },
            "unavailable",
        ),
    ],
    indirect=["performance_transport"],
)
@pytest.mark.parametrize(
    "route", [ROUTE, "/api/v1/workbench/PF_SHARED/performance/details?period=YTD"]
)
def test_completed_current_calculation_requires_explicit_qualification(
    performance_transport, expected, route
):
    with TestClient(app) as client:
        response = client.get(route, headers=CALLER)
    assert response.status_code == 200
    body = response.json()
    evidence = body["evidence_view"]
    assert evidence["state"] == expected, (evidence["reason"], evidence["source_supportability"])
    assert body["capabilities"]["evidence"]["state"] == expected
    if route == ROUTE:
        assert body["net_performance"]["portfolio_return_pct"] == 3.25
    assert evidence["input_freshness"]["performance"] == "fresh"
    assert evidence["source_supportability"]
    assert all(item["history_coverage"] is None for item in evidence["source_supportability"])
    assert evidence["calculations"][0]["execution_status"] == "complete"
    assert evidence["calculations"][0]["lineage_status"] == "complete"
    assert evidence["calculations"][0]["upstream_snapshots"][0]["as_of_date"] == "2026-04-10"
    assert "PRIVATE-MARKER" not in response.text
    if expected != "supported":
        assert evidence["reason"] == evidence["source_supportability"][0]["reason"]
        assert evidence["limitations"] == [evidence["reason"]]
        assert body["capabilities"]["evidence"]["reason"] == evidence["reason"]


def test_summary_carries_admitted_authority_through_async_evidence_and_cache(performance_transport):
    with TestClient(app) as client:
        for tenant, expected in (("tenant-a", 3.25), ("tenant-b", -1.5), ("tenant-a", 3.25)):
            response = client.get(ROUTE, headers={**CALLER, "X-Tenant-Id": tenant})
            assert response.status_code == 200
            body = response.json()
            assert body["net_performance"]["portfolio_return_pct"] == expected
            assert body["evidence_view"]["calculations"][0]["calculation_id"] == f"calc-{tenant}"
            assert body["partial_failures"] == []
    posts = [r for r in performance_transport if r.method == "POST"]
    assert [r.headers["X-Tenant-Id"] for r in posts] == ["tenant-a", "tenant-b"]
    assert all(r.headers["X-Actor-Id"] == "advisor" for r in performance_transport)
    assert any("/executions/" in r.url.path for r in performance_transport)
    assert any("/lineage/" in r.url.path for r in performance_transport)


@pytest.mark.parametrize("tenant", [None, "", "   "])
@pytest.mark.parametrize("route", PROTECTED_ROUTES)
def test_summary_refuses_missing_authority_before_any_io(performance_transport, tenant, route):
    headers = {k: v for k, v in CALLER.items() if k != "X-Tenant-Id"}
    if tenant is not None:
        headers["X-Tenant-Id"] = tenant
    with TestClient(app) as client:
        response = client.get(route, headers=headers)
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "missing_caller_context"
    assert performance_transport == []


def test_ambiguous_tenant_is_refused_before_io(performance_transport):
    with TestClient(app) as client:
        response = client.get(
            ROUTE,
            headers=[
                *CALLER.items(),
                ("X-Tenant-Id", "tenant-b"),
            ],
        )
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "ambiguous_caller_context"
    assert performance_transport == []


def test_served_performance_contract_has_one_required_context_definition():
    schema = app.openapi()
    paths = [
        path
        for path in schema["paths"]
        if (path.startswith("/api/v1/workbench/") and "/performance/" in path)
        or path.endswith("/performance-snapshot")
    ]
    for path in paths:
        for operation in schema["paths"][path].values():
            parameters = [p for p in operation["parameters"] if p["in"] == "header"]
            names = [p["name"] for p in parameters]
            assert len(names) == len(set(names)), path
            by_name = {p["name"]: p for p in parameters}
            for name in ("X-Actor-Id", "X-Tenant-Id", "X-Region"):
                assert by_name[name]["required"] is True, (path, name)
                assert by_name[name]["schema"]["pattern"] == r".*\S.*"
