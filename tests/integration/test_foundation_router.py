from fastapi.testclient import TestClient

from app.main import app

LOTUS_CORE_QUERY_CLIENT = "app.clients.lotus_core_query_client.LotusCoreQueryClient"


def test_foundation_portfolio_catalog_router(monkeypatch):
    async def _list_portfolios(*args, **kwargs):
        return 200, {
            "portfolios": [
                {
                    "portfolio_id": "PF_2002",
                    "base_currency": "EUR",
                    "client_id": "CIF_2002",
                },
                {
                    "portfolio_id": "PF_1001",
                    "base_currency": "USD",
                    "client_id": "CIF_1001",
                },
            ]
        }

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.list_portfolios", _list_portfolios)

    client = TestClient(app)
    response = client.get("/api/v1/foundation/portfolios")
    assert response.status_code == 200
    body = response.json()
    assert [item["portfolio_id"] for item in body["items"]] == ["PF_1001", "PF_2002"]
    assert body["items"][0]["display_name"] == "PF_1001"


def test_foundation_workspace_router_success(monkeypatch):
    async def _get_portfolio(*args, **kwargs):
        return 200, {
            "portfolio_id": "PF_1001",
            "base_currency": "USD",
            "booking_center_code": "SG",
            "client_id": "CIF_1001",
            "status": "ACTIVE",
            "portfolio_type": "ADVISORY",
            "risk_exposure": "MODERATE",
        }

    async def _get_positions(*args, **kwargs):
        return 200, {
            "positions": [
                {
                    "security_id": "EQ_1",
                    "instrument_name": "Equity 1",
                    "asset_class": "Equity",
                    "quantity": 10,
                    "cost_basis": 600.0,
                    "valuation": {"market_value_base": 600.0},
                    "weight": 0.60,
                },
                {
                    "security_id": "FI_1",
                    "instrument_name": "Bond 1",
                    "asset_class": "Fixed Income",
                    "quantity": 4,
                    "cost_basis": 300.0,
                    "valuation": {"market_value_base": 300.0},
                    "weight": 0.30,
                },
                {
                    "security_id": "CASH_USD",
                    "instrument_name": "US Dollar Cash",
                    "asset_class": "Cash",
                    "quantity": 100,
                    "cost_basis": 100.0,
                    "valuation": {"market_value_base": 100.0},
                    "weight": 0.10,
                },
            ]
        }

    async def _core_snapshot(*args, **kwargs):
        return 200, {
            "as_of_date": "2026-03-25",
            "sections": {
                "portfolio_totals": {"baseline_total_market_value_base": 1000.0},
                "positions_baseline": [],
                "instrument_enrichment": [],
            },
        }

    async def _transactions(*args, **kwargs):
        return 200, {
            "transactions": [
                {
                    "transaction_id": "TX_1",
                    "transaction_date": "2026-03-24T10:00:00Z",
                    "transaction_type": "BUY",
                    "security_id": "EQ_1",
                    "instrument_id": "EQ_1",
                    "quantity": 10,
                    "price": 60.0,
                    "gross_transaction_amount": 600.0,
                    "currency": "USD",
                }
            ]
        }

    async def _cashflow(*args, **kwargs):
        return 200, {
            "as_of_date": "2026-03-25",
            "range_end_date": "2026-04-04",
            "total_net_cashflow": -25.0,
            "projection_days": 10,
            "include_projected": True,
            "points": [
                {
                    "projection_date": "2026-03-26",
                    "net_cashflow": -25.0,
                    "projected_cumulative_cashflow": -25.0,
                }
            ],
        }

    async def _performance(*args, **kwargs):
        return 200, {
            "results_by_period": {
                "YTD": {"portfolio": {"summary": {"period_return": {"base": 2.5}}}}
            }
        }

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

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio", _get_portfolio)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_positions", _get_positions)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_core_snapshot", _core_snapshot)
    monkeypatch.setattr(
        f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_transactions",
        _transactions,
    )
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_cashflow_projection", _cashflow)
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
    assert body["portfolio"]["display_name"] == "PF_1001"
    assert body["profile"]["status"] == "ACTIVE"
    assert body["summary"]["position_count"] == 3
    assert {bucket["asset_class"] for bucket in body["allocations"]} == {
        "Cash",
        "Equity",
        "Fixed Income",
    }
    assert body["positions"][0]["security_id"] == "EQ_1"
    assert body["recent_transactions"][0]["transaction_id"] == "TX_1"
    assert body["cashflow_outlook"]["total_net_cashflow_base"] == -25.0
    assert body["performance"]["period"] == "YTD"
    assert body["rebalance"]["status"] == "PENDING_REVIEW"
    assert body["readiness"]["reporting"]["status"] == "READY"
    assert len(body["workflow_cues"]) == 3


def test_foundation_workspace_router_partial_failure(monkeypatch):
    async def _get_portfolio(*args, **kwargs):
        return 200, {
            "portfolio_id": "PF_1001",
            "base_currency": "USD",
            "booking_center_code": "SG",
            "client_id": "CIF_1001",
        }

    async def _get_positions(*args, **kwargs):
        return 200, {
            "positions": [
                {
                    "security_id": "EQ_1",
                    "instrument_name": "Equity 1",
                    "asset_class": "Equity",
                    "quantity": 5,
                }
            ]
        }

    async def _core_snapshot(*args, **kwargs):
        return 200, {
            "as_of_date": "2026-03-25",
            "sections": {
                "portfolio_totals": {"baseline_total_market_value_base": 1000.0},
                "positions_baseline": [],
                "instrument_enrichment": [],
            },
        }

    async def _transactions(*args, **kwargs):
        return 503, {"detail": "transactions unavailable"}

    async def _cashflow(*args, **kwargs):
        return 503, {"detail": "cashflow unavailable"}

    async def _performance(*args, **kwargs):
        return 503, {"detail": "paused"}

    async def _rebalance(*args, **kwargs):
        return 200, {"items": []}

    async def _reporting(*args, **kwargs):
        return 503, {"detail": "report unavailable"}

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio", _get_portfolio)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_positions", _get_positions)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_core_snapshot", _core_snapshot)
    monkeypatch.setattr(
        f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_transactions",
        _transactions,
    )
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_cashflow_projection", _cashflow)
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
    assert body["recent_transactions"] == []
    assert body["cashflow_outlook"] is None
    assert body["top_positions"][0]["security_id"] == "EQ_1"
    assert body["warnings"] == [
        "FOUNDATION_TRANSACTIONS_UNAVAILABLE",
        "FOUNDATION_CASHFLOW_UNAVAILABLE",
        "FOUNDATION_PERFORMANCE_UNAVAILABLE",
        "FOUNDATION_REPORTING_UNAVAILABLE",
    ]
    assert len(body["partial_failures"]) == 4
