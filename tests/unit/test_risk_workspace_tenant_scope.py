import httpx
import pytest
from fastapi.testclient import TestClient

from app.clients.lotus_analytics_client import LotusAnalyticsClient
from app.main import app
from app.services.risk_workspace_service import RiskWorkspaceService


def test_risk_client_and_cache_are_bound_to_the_admitted_tenant_per_request() -> None:
    shared_client = LotusAnalyticsClient(base_url="http://risk.test", timeout_seconds=1)
    shared_service = RiskWorkspaceService(shared_client)

    singapore = shared_service.with_caller_headers({"X-Tenant-Id": "tenant-sg"})
    hong_kong = shared_service.with_caller_headers({"X-Tenant-Id": "tenant-hk"})

    assert shared_client._caller_headers == {}
    assert singapore._risk_client._caller_headers == {"X-Tenant-Id": "tenant-sg"}
    assert hong_kong._risk_client._caller_headers == {"X-Tenant-Id": "tenant-hk"}
    assert singapore._cache._entries is hong_kong._cache._entries
    assert singapore._cache._scope != hong_kong._cache._scope


@pytest.mark.asyncio
async def test_drawdown_transport_and_cache_are_tenant_scoped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/analytics/risk/drawdown"
        calls.append(request.headers["X-Tenant-Id"])
        return httpx.Response(503, json={"detail": "source unavailable"})

    original_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: original_client(**kwargs, transport=httpx.MockTransport(respond)),
    )
    service = RiskWorkspaceService(LotusAnalyticsClient("http://risk.test", 1, max_retries=0))
    request = dict(
        portfolio_id="PF_SHARED",
        correlation_id="corr-risk-cache",
        period="YTD",
        detail_basis="NET",
        benchmark_code=None,
        as_of_date="2026-04-10",
        reporting_currency="USD",
        include_underwater_series=False,
    )

    sg = service.with_caller_headers({"X-Tenant-Id": "tenant-sg"})
    hk = service.with_caller_headers({"X-Tenant-Id": "tenant-hk"})
    first = await sg.get_drawdown(**request)
    second = await hk.get_drawdown(**request)
    replay = await sg.get_drawdown(**request)

    assert first.state == second.state == "unavailable"
    assert first.metadata.cache_status == second.metadata.cache_status == "miss"
    assert replay.metadata.cache_status == "hit"
    assert calls == ["tenant-sg", "tenant-hk"]


@pytest.mark.parametrize(
    "module",
    ["summary", "concentration", "drawdown", "rolling", "attribution"],
)
@pytest.mark.parametrize(
    "headers,expected_status",
    [({}, 422), ({"X-Tenant-Id": "   "}, 422), ({"X-Tenant-Id": "t" * 129}, 422)],
)
def test_stateful_risk_route_refuses_unusable_tenant_before_upstream(
    monkeypatch: pytest.MonkeyPatch,
    module: str,
    headers: dict[str, str],
    expected_status: int,
) -> None:
    def unexpected_upstream() -> None:
        raise AssertionError("Risk upstream must not be called without admitted tenant")

    monkeypatch.setattr(
        "app.services.workbench_service_provider.risk_workspace_service",
        unexpected_upstream,
    )
    request_headers = dict(headers)
    if module == "summary":
        request_headers.update({"X-Actor-Id": "actor-1", "X-Region": "APAC"})
    response = TestClient(app).get(
        f"/api/v1/workbench/PF_1/risk/{module}",
        headers=request_headers,
    )
    # Summary's pre-existing caller-context dependency reports missing or blank
    # tenant as 400; overlong values reach the constrained Risk header schema.
    caller_context_refusal = module == "summary" and (
        not headers or not headers["X-Tenant-Id"].strip()
    )
    assert response.status_code == (400 if caller_context_refusal else expected_status)


def test_stateful_risk_route_refuses_repeated_tenant_before_upstream(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected_upstream() -> None:
        raise AssertionError("Risk upstream must not be called with ambiguous tenant")

    monkeypatch.setattr(
        "app.services.workbench_service_provider.risk_workspace_service",
        unexpected_upstream,
    )
    response = TestClient(app).get(
        "/api/v1/workbench/PF_1/risk/concentration",
        headers=[("X-Tenant-Id", "tenant-sg"), ("X-Tenant-Id", "tenant-hk")],
    )
    assert response.status_code == 400


def test_openapi_requires_tenant_on_every_stateful_risk_surface() -> None:
    paths = app.openapi()["paths"]
    for module in ("summary", "concentration", "drawdown", "rolling", "attribution"):
        route = paths[f"/api/v1/workbench/{{portfolio_id}}/risk/{module}"]["get"]
        tenant_parameters = [
            item
            for item in route["parameters"]
            if item["in"] == "header" and item["name"] == "X-Tenant-Id"
        ]
        assert len(tenant_parameters) == 1
        assert tenant_parameters[0]["required"] is True
        assert tenant_parameters[0]["schema"]["pattern"] == r"\S"
        assert tenant_parameters[0]["schema"]["minLength"] == 1
        assert tenant_parameters[0]["schema"]["maxLength"] == 128
