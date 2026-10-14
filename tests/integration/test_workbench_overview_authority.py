"""Legacy overview admission through concrete optional producer transports."""

import asyncio
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.dpm_manage_request_authority import forward_dpm_manage_read_headers
from app.services.workbench_service_factory import build_workbench_service

ROUTE = "/api/v1/workbench/PF_SHARED/overview"
CALLER = {
    "X-Actor-Id": "advisor",
    "X-Tenant-Id": "tenant-a",
    "X-Region": "APAC",
    "X-Role": "PORTFOLIO_MANAGER",
    "X-Correlation-Id": "overview-proof",
}


@pytest.fixture
def producers(monkeypatch):
    requests = []
    failures = {}
    service = build_workbench_service()
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
            return httpx.Response(200, json={})
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
        lambda **kwargs: original(
            **kwargs,
            transport=httpx.MockTransport(respond),
        ),
    )
    return requests, failures, service, original


@pytest.fixture
def gateway_client(producers):
    with TestClient(app) as client:
        yield client


@pytest.mark.parametrize(
    "performance,manage", [(True, True), (True, False), (False, True), (False, False)]
)
def test_conditional_authority_and_exact_producer_headers(
    producers, gateway_client, performance, manage
):
    requests, _, service, _ = producers
    headers = {
        **CALLER,
        "X-Service-Identity": "evil",
        "X-Capabilities": "manage.write",
        "Authorization": "Bearer browser",
        "X-Unrelated": "private",
    }
    response = gateway_client.get(
        ROUTE,
        params={
            "include_performance_snapshot": performance,
            "include_rebalance_snapshot": manage,
        },
        headers=headers if performance or manage else {},
    )
    assert response.status_code == 200
    body = response.json()
    assert (body["performance_snapshot"] is not None) is performance
    assert (body["rebalance_snapshot"] is not None) is manage
    if manage:
        assert body["rebalance_snapshot"]["last_rebalance_run_id"] == "run-tenant-a"
        assert body["rebalance_snapshot"]["recent_runs"][0]["rebalance_run_id"] == "run-tenant-a"
    assert len(requests) == int(performance) + 2 * int(manage)
    for request in requests:
        expected = {key.lower(): value for key, value in CALLER.items()}
        if request.url.path.startswith("/api/v1/rebalance"):
            assert request.method == "GET"
        else:
            expected["x-caller-application"] = "lotus-gateway"
        assert {
            key: value
            for key, value in request.headers.items()
            if key.startswith("x-") and key not in {"x-request-id", "x-trace-id"}
        } == expected
        assert "authorization" not in request.headers
    assert service._analytics_client._caller_headers == {}
    assert forward_dpm_manage_read_headers({}) == {}


@pytest.mark.parametrize("performance,manage", [(True, True), (True, False), (False, True)])
@pytest.mark.parametrize("bad", ["missing", "blank", "duplicate", "invalid-manage"])
def test_bad_optional_authority_refused_before_producer_io(
    producers, gateway_client, performance, manage, bad
):
    requests, _, _, _ = producers
    headers = dict(CALLER)
    if bad == "missing":
        headers.pop("X-Tenant-Id")
    elif bad == "blank":
        headers["X-Actor-Id"] = " "
    elif bad == "duplicate":
        headers = [*headers.items(), ("x-tenant-id", "tenant-b")]
    elif manage:
        headers["X-Role"] = "bad role"
    else:
        headers["X-Region"] = " "
    response = gateway_client.get(
        ROUTE,
        params={
            "include_performance_snapshot": performance,
            "include_rebalance_snapshot": manage,
        },
        headers=headers,
    )
    assert response.status_code == 400
    assert requests == []


@pytest.mark.parametrize(
    "producer,status", [("manage", 422), ("manage", 403), ("performance", 401)]
)
def test_producer_refusals_remain_partial_failures(producers, gateway_client, producer, status):
    _, failures, _, _ = producers
    failures[producer] = status
    response = gateway_client.get(ROUTE, headers=CALLER)
    assert response.status_code == 200
    body = response.json()
    assert body["overview"]["market_value_base"] == 1000
    assert {"source_service": f"lotus-{producer}", "error_code": f"HTTP_{status}"}.items() <= next(
        failure.items()
        for failure in body["partial_failures"]
        if failure["source_service"] == f"lotus-{producer}"
    )


@pytest.mark.asyncio
async def test_concurrent_tenants_and_request_reset(producers):
    requests, _, service, original = producers
    async with original(
        transport=httpx.ASGITransport(app=app), base_url="http://gateway"
    ) as client:
        a, b = await asyncio.gather(
            *[
                client.get(
                    ROUTE, headers={**CALLER, "X-Tenant-Id": tenant, "X-Correlation-Id": tenant}
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
            ROUTE,
            params={
                "include_performance_snapshot": False,
                "include_rebalance_snapshot": False,
            },
        )
        assert source_only.status_code == 200
        assert len(requests) == count
    assert service._analytics_client._caller_headers == {}
    assert forward_dpm_manage_read_headers({}) == {}


def test_openapi_conditional_context_is_optional_on_source_only_reads():
    operation = app.openapi()["paths"][ROUTE.replace("PF_SHARED", "{portfolio_id}")]["get"]
    headers = {
        parameter["name"]: parameter
        for parameter in operation["parameters"]
        if parameter["in"] == "header"
    }
    assert {"X-Actor-Id", "X-Tenant-Id", "X-Region", "X-Role"} <= headers.keys()
    assert all(not parameter["required"] for parameter in headers.values())
    assert "include_performance_snapshot=true" in operation["description"]
    assert "include_rebalance_snapshot=true" in operation["description"]
    assert "400" in operation["responses"]


@pytest.mark.parametrize(
    "performance,manage,omitted",
    [
        (True, False, "X-Role"),
        (False, True, "X-Region"),
    ],
)
def test_each_enrichment_uses_only_its_existing_required_context(
    producers,
    gateway_client,
    performance,
    manage,
    omitted,
):
    requests, _, _, _ = producers
    headers = {key: value for key, value in CALLER.items() if key != omitted}
    response = gateway_client.get(
        ROUTE,
        headers=headers,
        params={
            "include_performance_snapshot": performance,
            "include_rebalance_snapshot": manage,
        },
    )
    assert response.status_code == 200
    assert requests
    assert all(omitted not in request.headers for request in requests)


def test_source_only_ignores_optional_enrichment_authority(producers, gateway_client):
    requests, _, _, _ = producers
    response = gateway_client.get(
        ROUTE,
        headers=[
            ("X-Actor-Id", " "),
            ("X-Tenant-Id", "tenant-a"),
            ("X-Tenant-Id", "tenant-b"),
        ],
        params={"include_performance_snapshot": False, "include_rebalance_snapshot": False},
    )
    assert response.status_code == 200
    assert requests == []


@pytest.mark.asyncio
async def test_manage_scope_resets_when_service_raises(producers, monkeypatch):
    _, _, service, original = producers

    async def fail(**kwargs):
        assert forward_dpm_manage_read_headers({})["X-Tenant-Id"] == "tenant-a"
        raise RuntimeError("controlled service failure")

    monkeypatch.setattr(service, "get_workbench_overview", fail)
    async with original(
        transport=httpx.ASGITransport(app=app), base_url="http://gateway"
    ) as client:
        with pytest.raises(RuntimeError, match="controlled service failure"):
            await client.get(ROUTE, headers=CALLER, params={"include_performance_snapshot": False})
    assert forward_dpm_manage_read_headers({}) == {}
