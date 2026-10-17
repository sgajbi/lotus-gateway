"""Portfolio360 admission through concrete optional producer transports."""

import asyncio
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.dpm_manage_request_authority import forward_dpm_manage_read_headers
from app.services.workbench_service_factory import build_workbench_service

ROUTE = "/api/v1/workbench/PF_SHARED/portfolio-360"
OVERVIEW_ROUTE = "/api/v1/workbench/PF_SHARED/overview"
CALLER = {
    "X-Actor-Id": "workbench-system",
    "X-Caller-Application": "lotus-workbench",
    "X-Tenant-Id": "tenant-a",
    "X-Region": "APAC",
    "X-Booking-Center-Code": "SG",
    "X-Role": "PORTFOLIO_MANAGER",
    "X-Correlation-Id": "portfolio360-proof",
}


@pytest.fixture
def producers(monkeypatch):
    requests = []
    failures = {}
    service = build_workbench_service()
    monkeypatch.setattr("app.routers.workbench_portfolio_360.workbench_service", lambda: service)
    monkeypatch.setattr("app.routers.workbench.workbench_service", lambda: service)
    monkeypatch.setattr(app.state, "is_draining", False, raising=False)

    async def portfolio(**kwargs):
        return 200, {"portfolio_id": kwargs["portfolio_id"], "base_currency": "USD"}

    async def support(**kwargs):
        return 200, {"business_date": "2026-04-10"}

    async def reference(**kwargs):
        return 200, {"performance_end_date": "2026-04-10"}

    async def snapshot(**kwargs):
        return 200, {
            "as_of_date": "2026-04-10",
            "sections": {
                "positions_baseline": [],
                "portfolio_totals": {"baseline_total_market_value_base": 1000},
                "instrument_enrichment": [],
            },
        }

    core = service._lotus_core_query_client
    monkeypatch.setattr(core, "get_portfolio", portfolio)
    monkeypatch.setattr(core, "get_support_overview", support)
    monkeypatch.setattr(core, "get_core_snapshot", snapshot)
    monkeypatch.setattr(core, "get_portfolio_analytics_reference", reference)

    async def respond(request):
        requests.append(request)
        await asyncio.sleep(0)
        tenant = request.headers.get("X-Tenant-Id")
        if request.url.path.startswith("/api/v1/rebalance"):
            if "manage" in failures:
                return httpx.Response(failures["manage"], json={"detail": "unavailable"})
            if tenant is None:
                return httpx.Response(422, json={"detail": "tenant required"})
            if request.url.path.endswith("/runs"):
                assert request.url.params["portfolio_id"] == "PF_SHARED"
                assert request.url.params["limit"] == "5"
                return httpx.Response(
                    200,
                    json={
                        "items": [
                            {
                                "rebalance_run_id": f"run-{tenant}",
                                "status": "PENDING_REVIEW",
                                "created_at": "2026-04-10T00:00:00Z",
                            }
                        ]
                    },
                )
            return httpx.Response(200, json={"supportability": {"state": "supported"}})
        if "performance" in failures:
            return httpx.Response(failures["performance"], json={"detail": "unavailable"})
        if tenant is None:
            return httpx.Response(401, json={"detail": "tenant required"})
        assert json.loads(request.content)["portfolio_id"] == "PF_SHARED"
        return httpx.Response(
            200,
            json={
                "results_by_period": {
                    "YTD": {
                        "portfolio_twr": {"net": {"summary": {"period_return": {"base": 2.5}}}},
                    }
                }
            },
        )

    original = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: original(**kwargs, transport=httpx.MockTransport(respond)),
    )
    return requests, failures, service, original


@pytest.fixture
def gateway_client(producers):
    with TestClient(app) as client:
        yield client


def test_exact_admitted_authority_reaches_both_optional_producers(producers, gateway_client):
    requests, _, service, _ = producers
    response = gateway_client.get(
        ROUTE,
        headers={
            **CALLER,
            "X-Service-Identity": "browser-supplied",
            "X-Capabilities": "manage.write",
            "Authorization": "Bearer browser",
            "X-Unrelated": "private",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["performance_snapshot"]["return_pct"] == 2.5
    assert body["rebalance_snapshot"]["last_rebalance_run_id"] == "run-tenant-a"
    assert body["warnings"] == []
    assert body["partial_failures"] == []
    assert len(requests) == 3
    for request in requests:
        if request.url.path.startswith("/api/v1/rebalance"):
            assert request.method == "GET"
            expected = {
                key.lower(): CALLER[key]
                for key in (
                    "X-Actor-Id",
                    "X-Tenant-Id",
                    "X-Region",
                    "X-Role",
                    "X-Correlation-Id",
                )
            }
        else:
            expected = {key.lower(): value for key, value in CALLER.items()}
        assert {
            key: value
            for key, value in request.headers.items()
            if key.startswith("x-") and key not in {"x-request-id", "x-trace-id"}
        } == expected
        assert "authorization" not in request.headers
    assert service._analytics_client._caller_headers == {}
    assert forward_dpm_manage_read_headers({}) == {}


@pytest.mark.parametrize("caller_application", [None, " "], ids=["omitted", "blank"])
def test_optional_application_defaults_and_absent_booking_center_is_not_forwarded(
    producers, gateway_client, caller_application
):
    requests, _, _, _ = producers
    headers = {
        name: value
        for name, value in CALLER.items()
        if name not in {"X-Caller-Application", "X-Booking-Center-Code"}
    }
    if caller_application is not None:
        headers["X-Caller-Application"] = caller_application

    response = gateway_client.get(ROUTE, headers=headers)

    assert response.status_code == 200
    performance_request = next(
        request for request in requests if not request.url.path.startswith("/api/v1/rebalance")
    )
    assert performance_request.headers["X-Caller-Application"] == "lotus-gateway"
    assert "X-Booking-Center-Code" not in performance_request.headers
    assert all("X-Booking-Center-Code" not in request.headers for request in requests)


@pytest.mark.parametrize(
    "bad",
    [
        "missing-actor",
        "missing-tenant",
        "missing-region",
        "missing-role",
        "blank",
        "duplicate",
        "invalid-role",
    ],
)
def test_bad_authority_is_refused_before_any_optional_producer_io(producers, gateway_client, bad):
    requests, _, _, _ = producers
    headers = dict(CALLER)
    if bad.startswith("missing-"):
        header = {
            "missing-actor": "X-Actor-Id",
            "missing-tenant": "X-Tenant-Id",
            "missing-region": "X-Region",
            "missing-role": "X-Role",
        }[bad]
        headers.pop(header)
    elif bad == "blank":
        headers["X-Actor-Id"] = " "
    elif bad == "duplicate":
        headers = [*headers.items(), ("x-tenant-id", "tenant-b")]
    else:
        headers["X-Role"] = "bad role"

    response = gateway_client.get(ROUTE, headers=headers)

    assert response.status_code == 400
    assert requests == []


@pytest.mark.parametrize(
    ("producer", "status"), [("manage", 422), ("manage", 403), ("performance", 401)]
)
def test_optional_producer_refusals_remain_truthful_partial_failures(
    producers, gateway_client, producer, status
):
    _, failures, _, _ = producers
    failures[producer] = status

    response = gateway_client.get(ROUTE, headers=CALLER)

    assert response.status_code == 200
    body = response.json()
    assert body["overview"]["market_value_base"] == 1000
    failure = next(
        item for item in body["partial_failures"] if item["source_service"] == f"lotus-{producer}"
    )
    assert failure["error_code"] == f"HTTP_{status}"


@pytest.mark.asyncio
async def test_concurrent_authority_resets_and_overview_source_only_stays_compatible(producers):
    requests, _, service, original = producers
    async with original(
        transport=httpx.ASGITransport(app=app), base_url="http://gateway"
    ) as client:
        a, b = await asyncio.gather(
            *[
                client.get(
                    ROUTE,
                    headers={**CALLER, "X-Tenant-Id": tenant, "X-Correlation-Id": tenant},
                )
                for tenant in ("tenant-a", "tenant-b")
            ]
        )
        assert a.json()["rebalance_snapshot"]["last_rebalance_run_id"] == "run-tenant-a"
        assert b.json()["rebalance_snapshot"]["last_rebalance_run_id"] == "run-tenant-b"
        assert all(
            request.headers["X-Tenant-Id"] == request.headers["X-Correlation-Id"]
            for request in requests
        )
        count = len(requests)
        denied = await client.get(ROUTE)
        assert denied.status_code == 400
        source_only = await client.get(
            OVERVIEW_ROUTE,
            params={
                "include_performance_snapshot": False,
                "include_rebalance_snapshot": False,
            },
        )
        assert source_only.status_code == 200
        assert len(requests) == count
    assert service._analytics_client._caller_headers == {}
    assert forward_dpm_manage_read_headers({}) == {}


def test_openapi_declares_required_portfolio360_authority():
    operation = app.openapi()["paths"][ROUTE.replace("PF_SHARED", "{portfolio_id}")]["get"]
    headers = {
        parameter["name"]: parameter
        for parameter in operation["parameters"]
        if parameter["in"] == "header"
    }

    assert {"X-Actor-Id", "X-Tenant-Id", "X-Region", "X-Role"} <= headers.keys()
    assert all(
        headers[name]["required"] for name in ("X-Actor-Id", "X-Tenant-Id", "X-Region", "X-Role")
    )
    assert not headers["X-Caller-Application"]["required"]
    assert not headers["X-Booking-Center-Code"]["required"]
    assert headers["X-Caller-Application"]["schema"]["minLength"] == 0
    assert "pattern" not in headers["X-Caller-Application"]["schema"]
    for name in ("X-Actor-Id", "X-Tenant-Id", "X-Region", "X-Role"):
        assert headers[name]["schema"]["minLength"] == 1
        assert headers[name]["schema"]["pattern"]
    assert "lotus-gateway" in headers["X-Caller-Application"]["description"]
    assert "only when provided" in headers["X-Booking-Center-Code"]["description"]
    assert "lotus-gateway" in operation["description"]
    assert "optional performance and rebalance enrichments" in operation["description"]
    assert "400" in operation["responses"]


@pytest.mark.asyncio
async def test_manage_authority_scope_resets_when_portfolio360_service_raises(
    producers, monkeypatch
):
    _, _, service, original = producers

    async def fail(**kwargs):
        assert forward_dpm_manage_read_headers({})["X-Tenant-Id"] == "tenant-a"
        raise RuntimeError("controlled service failure")

    monkeypatch.setattr(service, "get_portfolio_360", fail)
    async with original(
        transport=httpx.ASGITransport(app=app), base_url="http://gateway"
    ) as client:
        with pytest.raises(RuntimeError, match="controlled service failure"):
            await client.get(ROUTE, headers=CALLER)
    assert forward_dpm_manage_read_headers({}) == {}
