from fastapi.testclient import TestClient

from app.main import app


def test_foundation_portfolio_catalog_router(monkeypatch):
    async def _list_portfolios(*args, **kwargs):
        return 200, {
            "items": [
                {
                    "id": "PF_2002",
                    "label": "Income",
                },
                {
                    "id": "PF_1001",
                    "label": "Alpha Growth",
                },
            ]
        }

    monkeypatch.setattr(
        "app.clients.lotus_core_query_client.LotusCoreQueryClient.get_portfolio_lookups",
        _list_portfolios,
    )

    client = TestClient(app)
    response = client.get("/api/v1/foundation/portfolios")
    assert response.status_code == 200
    body = response.json()
    assert [item["portfolio_id"] for item in body["items"]] == ["PF_1001", "PF_2002"]
    assert body["items"][0]["display_name"] == "Alpha Growth"


def test_foundation_workspace_router_success(monkeypatch):
    async def _core_snapshot(*args, **kwargs):
        return 200, {
            "portfolio": {
                "portfolio_id": "PF_1001",
                "portfolio_name": "Alpha Growth",
                "base_currency": "USD",
                "booking_center": "SG",
                "cif_id": "CIF_1001",
            },
            "metadata": {"as_of_date": "2026-03-25"},
            "sections": {
                "positions_baseline": [
                    {"security_id": "EQ_1", "market_value_base": 600.0},
                    {"security_id": "FI_1", "market_value_base": 300.0},
                ],
                "portfolio_totals": {
                    "baseline_total_market_value_base": 1000.0,
                    "baseline_total_cash_base": 100.0,
                },
                "instrument_enrichment": [
                    {"security_id": "EQ_1", "asset_class": "Equity"},
                    {"security_id": "FI_1", "asset_class": "Fixed Income"},
                ],
            },
        }

    async def _performance(*args, **kwargs):
        return 200, {"resultsByPeriod": {"YTD": {"net_cumulative_return": 2.5}}}

    async def _rebalance(*args, **kwargs):
        return 200, {
            "items": [
                {
                    "rebalance_run_id": "rr_100",
                    "status": "PENDING_REVIEW",
                    "created_at": "2026-03-25T09:00:00Z",
                }
            ]
        }

    async def _reporting(*args, **kwargs):
        return 200, {
            "generatedAt": "2026-03-25T10:00:00Z",
            "rows": [{"metric": "market_value_base"}, {"metric": "return_ytd_pct"}],
        }

    monkeypatch.setattr(
        "app.clients.lotus_core_query_client.LotusCoreQueryClient.get_core_snapshot",
        _core_snapshot,
    )
    monkeypatch.setattr(
        "app.clients.lotus_analytics_client.LotusAnalyticsClient.get_stateful_twr", _performance
    )
    monkeypatch.setattr("app.clients.dpm_client.DpmClient.list_runs", _rebalance)
    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.get_portfolio_snapshot", _reporting
    )

    client = TestClient(app)
    response = client.get("/api/v1/foundation/portfolios/PF_1001/workspace")
    assert response.status_code == 200
    body = response.json()
    assert body["portfolio"]["display_name"] == "Alpha Growth"
    assert body["summary"]["position_count"] == 2
    assert body["allocations"][0]["asset_class"] == "Equity"
    assert body["performance"]["period"] == "YTD"
    assert body["rebalance"]["status"] == "PENDING_REVIEW"
    assert body["readiness"]["reporting"]["status"] == "READY"
    assert body["evidence"]["status"] == "ready"
    assert body["evidence"]["partial_failure_count"] == 0
    assert len(body["workflow_cues"]) == 3


def test_foundation_workspace_router_partial_failure(monkeypatch):
    async def _core_snapshot(*args, **kwargs):
        return 200, {
            "portfolio": {"portfolio_id": "PF_1001", "base_currency": "USD"},
            "metadata": {"as_of_date": "2026-03-25"},
            "sections": {
                "positions_baseline": [{"security_id": "EQ_1", "market_value_base": 750.0}],
                "portfolio_totals": {
                    "baseline_total_market_value_base": 1000.0,
                    "baseline_total_cash_base": 250.0,
                },
                "instrument_enrichment": [{"security_id": "EQ_1", "asset_class": "Equity"}],
            },
        }

    async def _performance(*args, **kwargs):
        return 503, {"detail": "paused"}

    async def _rebalance(*args, **kwargs):
        return 200, {"items": []}

    async def _reporting(*args, **kwargs):
        return 503, {"detail": "report unavailable"}

    monkeypatch.setattr(
        "app.clients.lotus_core_query_client.LotusCoreQueryClient.get_core_snapshot",
        _core_snapshot,
    )
    monkeypatch.setattr(
        "app.clients.lotus_analytics_client.LotusAnalyticsClient.get_stateful_twr", _performance
    )
    monkeypatch.setattr("app.clients.dpm_client.DpmClient.list_runs", _rebalance)
    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.get_portfolio_snapshot", _reporting
    )

    client = TestClient(app)
    response = client.get("/api/v1/foundation/portfolios/PF_1001/workspace")
    assert response.status_code == 200
    body = response.json()
    assert body["performance"] is None
    assert body["readiness"]["reporting"]["status"] == "UNAVAILABLE"
    assert body["warnings"] == [
        "FOUNDATION_PERFORMANCE_UNAVAILABLE",
        "FOUNDATION_REPORTING_UNAVAILABLE",
    ]
    assert len(body["partial_failures"]) == 2
    assert body["evidence"]["status"] == "partial"
    assert body["evidence"]["warning_count"] == 2
    assert body["evidence"]["partial_failure_count"] == 2
    assert body["evidence"]["affected_sources"] == ["lotus-performance", "lotus-report"]
