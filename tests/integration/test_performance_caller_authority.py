"""Registered Gateway route -> concrete Performance HTTP adapter authority proof."""

import json
from datetime import date

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
def performance_transport(monkeypatch):
    requests = []
    service = build_performance_workspace_service(build_workbench_service())
    monkeypatch.setattr(
        "app.routers.workbench_performance.performance_workspace_service",
        lambda: service,
    )
    # Own the shared app flag for this lifespan, then restore its prior state.
    monkeypatch.setattr(app.state, "is_draining", False, raising=False)

    async def context(**kwargs):
        return workspace_context()

    def respond(request):
        requests.append(request)
        tenant = request.headers.get("X-Tenant-Id")
        if tenant not in {"tenant-a", "tenant-b"}:
            return httpx.Response(401, json={"detail": "tenant required before durable submission"})
        calculation = f"calc-{tenant}"
        if request.method == "POST":
            assert json.loads(request.content)["portfolio_id"] == "PF_SHARED"
            return httpx.Response(
                202,
                json={
                    "calculation_id": calculation,
                    "result_path": f"/performance/results/{calculation}",
                    "poll_after_seconds": 0.001,
                },
            )
        if calculation not in request.url.path:
            return httpx.Response(404, json={"detail": "Calculation not found"})
        if "/results/" in request.url.path:
            value = 3.25 if tenant == "tenant-a" else -1.5
            return httpx.Response(
                200,
                json={
                    "calculation_id": calculation,
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
