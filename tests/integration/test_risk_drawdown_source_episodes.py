"""Registered Gateway replay of retained actual Risk HTTP responses.

Only the upstream transport is substituted; routing, tenant binding, service,
cache, mapper and public serialization execute normally. This is not live Risk
or browser proof. Fixture provenance is retained with the unmodified responses.
"""

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.clients.lotus_analytics_client import LotusAnalyticsClient
from app.main import app
from app.services.risk_workspace_service import RiskWorkspaceService

_SOURCE_RECEIPT = json.loads(
    (Path(__file__).parents[1] / "fixtures" / "risk-drawdown-source-responses.json").read_text(
        encoding="utf-8"
    )
)
_SOURCE_CASES = _SOURCE_RECEIPT["cases"]
_PATH = (
    "/api/v1/workbench/REVIEW-RELATIVE/risk/drawdown"
    "?period=YTD&detail_basis=NET&as_of_date=2026-01-07"
    "&reporting_currency=USD&benchmark_code=REVIEW-BENCHMARK"
    "&include_underwater_series=true"
)


@pytest.mark.parametrize("case", _SOURCE_CASES, ids=lambda case: case["case"])
def test_registered_drawdown_preserves_actual_source_episodes_and_tenant_cache(
    monkeypatch: pytest.MonkeyPatch, case: dict[str, Any]
) -> None:
    source = deepcopy(case["response"])
    source_as_of = source["scope"]["as_of_date"]
    calls: list[str] = []

    async def source_response(self: Any, payload: Any, correlation_id: str) -> tuple[int, Any]:
        calls.append(self._caller_headers["X-Tenant-Id"])
        assert payload["input_mode"] == "stateful"
        return 200, deepcopy(source)

    monkeypatch.setattr(LotusAnalyticsClient, "post_risk_drawdown", source_response)
    shared_service = RiskWorkspaceService(LotusAnalyticsClient("http://risk.test", 1))
    monkeypatch.setattr(
        "app.services.workbench_service_provider.risk_workspace_service", lambda: shared_service
    )
    with TestClient(app, raise_server_exceptions=False) as client:
        responses = [
            client.get(
                _PATH.replace("2026-01-07", source_as_of),
                headers={"X-Tenant-Id": tenant, "X-Correlation-Id": "drawdown-source-replay"},
            )
            for tenant in ("tenant-sg", "tenant-hk", "tenant-sg")
        ]
    assert [response.status_code for response in responses] == [200, 200, 200]
    assert calls == ["tenant-sg", "tenant-hk"]
    assert [response.json()["metadata"]["cache_status"] for response in responses] == [
        "miss",
        "miss",
        "hit",
    ]
    original = source["results"]["YTD"]
    for response in responses:
        body = response.json()
        assert body["portfolio_id"] == "REVIEW-RELATIVE"
        assert body["benchmark_code"] == "REVIEW-BENCHMARK"
        assert body["as_of_date"] == source_as_of
        assert body["detail_basis"] == "NET"
        assert body["correlation_id"] == "drawdown-source-replay"
        mapped = body["payload"]["periods"][0]
        assert mapped["key"] == "YTD"
        for field in (
            "start_date",
            "end_date",
            "portfolio_observation_count",
            "benchmark_observation_count",
            "summary",
            "relative_to_benchmark",
            "relative_to_benchmark_context",
            "underwater_series",
        ):
            assert mapped[field] == original[field]
        assert mapped["episodes"] == sorted(
            original["episodes"], key=lambda episode: episode["depth"]
        )
        assert body["metadata"]["methodology_version"] == source["metadata"]["methodology_version"]
        quality = {item["key"]: item for item in body["supportability"]}["source_calculation"]
        source_quality = source["metadata"]["calculation_supportability"]
        assert quality["state"] == ("ready" if source_quality["state"] == "ready" else "partial")
        assert source_quality["reason"] in quality["reason"]
        expected_partial = (
            source_quality["state"] != "ready" or original["relative_to_benchmark"] is None
        )
        assert body["state"] == ("partial" if expected_partial else "ready")
        assert body["partial_failures"] == []
    assert source == case["response"]


@pytest.mark.parametrize("headers", [{}, {"X-Tenant-Id": " "}])
def test_drawdown_refuses_missing_tenant_before_source(
    monkeypatch: pytest.MonkeyPatch, headers: dict[str, str]
) -> None:
    def unexpected_source() -> None:
        raise AssertionError("No source service before tenant admission")

    monkeypatch.setattr(
        "app.services.workbench_service_provider.risk_workspace_service", unexpected_source
    )
    with TestClient(app) as client:
        response = client.get(_PATH, headers=headers)
    assert response.status_code == 422


def test_drawdown_keeps_source_unavailable_distinct_from_unknown_episode_timing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def unavailable(self: Any, payload: Any, correlation_id: str) -> tuple[int, Any]:
        return 503, {"detail": "source unavailable"}

    monkeypatch.setattr(LotusAnalyticsClient, "post_risk_drawdown", unavailable)
    service = RiskWorkspaceService(LotusAnalyticsClient("http://risk.test", 1))
    monkeypatch.setattr(
        "app.services.workbench_service_provider.risk_workspace_service", lambda: service
    )
    with TestClient(app) as client:
        response = client.get(_PATH, headers={"X-Tenant-Id": "tenant-sg"})
    assert response.status_code == 200
    body = response.json()
    assert body["state"] == "unavailable"
    assert body["payload"] is None
    assert body["warnings"] == ["RISK_DRAWDOWN_UNAVAILABLE"]
