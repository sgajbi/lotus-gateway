import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers import portfolio as portfolio_router
from app.routers.portfolio import _portfolio_service

LOTUS_CORE_QUERY_CLIENT = "app.clients.lotus_core_query_client.LotusCoreQueryClient"


@pytest.fixture(autouse=True)
def clear_portfolio_router_cache():
    _portfolio_service().clear_upstream_cache()
    yield
    _portfolio_service().clear_upstream_cache()


@pytest.fixture(autouse=True)
def stub_portfolio_workspace_enrichments(monkeypatch):
    async def _analytics_reference(*args, **kwargs):
        return 200, {"performance_end_date": "2026-03-27"}

    async def _twr(*args, **kwargs):
        return 200, {
            "results_by_period": {
                "YTD": {
                    "portfolio": {
                        "summary": {
                            "period_return": {"base": 2.5},
                        }
                    }
                }
            }
        }

    async def _rebalance_runs(*args, **kwargs):
        return 200, {
            "items": [
                {
                    "status": "PENDING_REVIEW",
                    "created_at": "2026-03-27T12:00:00Z",
                    "rebalance_run_id": "rr_100",
                }
            ]
        }

    monkeypatch.setattr(
        f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_analytics_reference",
        _analytics_reference,
    )
    monkeypatch.setattr(
        "app.clients.lotus_analytics_client.LotusAnalyticsClient.get_twr_analytics",
        _twr,
    )
    monkeypatch.setattr("app.clients.dpm_client.DpmClient.list_runs", _rebalance_runs)


def test_portfolio_catalog_router(monkeypatch):
    async def _list_portfolios(*args, **kwargs):
        return 200, {"portfolios": [{"portfolio_id": "PF_1001", "base_currency": "USD"}]}

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.list_portfolios", _list_portfolios)
    client = TestClient(app)
    response = client.get("/api/v1/portfolio/portfolios")
    assert response.status_code == 200
    assert response.json()["items"][0]["portfolio_id"] == "PF_1001"


def test_portfolio_workspace_router(monkeypatch):
    captured: dict[str, object] = {}

    async def _get_portfolio(*args, **kwargs):
        return 200, {"portfolio_id": "PF_1001", "base_currency": "USD", "status": "ACTIVE"}

    async def _query_aum(*args, **kwargs):
        return 200, {
            "resolved_as_of_date": "2026-03-27",
            "portfolios": [
                {"portfolio_id": "PF_1001", "aum_reporting_currency": 1000.0, "position_count": 2}
            ],
        }

    async def _support(*args, **kwargs):
        captured["support_as_of_date"] = kwargs.get("as_of_date")
        return 200, {"business_date": "2026-03-27", "publish_allowed": True}

    async def _readiness(*args, **kwargs):
        return 200, {
            "holdings": {"status": "READY", "reasons": []},
            "pricing": {
                "status": "PENDING",
                "reasons": [
                    {
                        "code": "pricing_not_published",
                        "detail": "Pricing has not yet been published for the business date.",
                    }
                ],
            },
            "transactions": {"status": "READY", "reasons": []},
            "reporting": {"status": "READY", "reasons": []},
            "blocking_reasons": [
                {
                    "code": "awaiting_pricing",
                    "detail": "Reporting remains blocked until pricing is published.",
                }
            ],
        }

    async def _cashflow(*args, **kwargs):
        return 200, {
            "as_of_date": "2026-03-27",
            "range_end_date": "2026-04-06",
            "total_net_cashflow": 0,
            "projection_days": 10,
            "include_projected": True,
            "points": [],
        }

    async def _cash_balances(*args, **kwargs):
        return 200, {
            "totals": {"cash_account_count": 1, "total_balance_reporting_currency": 100.0},
            "cash_accounts": [],
        }

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio", _get_portfolio)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_assets_under_management", _query_aum)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_support_overview", _support)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_readiness", _readiness)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_cashflow_projection", _cashflow)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_cash_balances", _cash_balances)

    client = TestClient(app)
    response = client.get(
        "/api/v1/portfolio/portfolios/PF_1001/workspace",
        params={"as_of_date": "2026-03-27"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["portfolio"]["portfolio_id"] == "PF_1001"
    assert body["summary"]["assets_under_management_base"] == 1000.0
    assert body["performance"]["period"] == "YTD"
    assert body["performance"]["return_pct"] == 2.5
    assert body["rebalance"]["status"] == "PENDING_REVIEW"
    assert captured["support_as_of_date"] == "2026-03-27"


def test_portfolio_readiness_router(monkeypatch):
    async def _get_portfolio(*args, **kwargs):
        return 200, {"portfolio_id": "PF_1001", "base_currency": "USD", "status": "ACTIVE"}

    async def _query_aum(*args, **kwargs):
        return 200, {
            "resolved_as_of_date": "2026-03-27",
            "portfolios": [
                {"portfolio_id": "PF_1001", "aum_reporting_currency": 1000.0, "position_count": 2}
            ],
        }

    async def _support(*args, **kwargs):
        return 200, {"business_date": "2026-03-27", "publish_allowed": True}

    async def _cashflow(*args, **kwargs):
        return 200, {
            "as_of_date": "2026-03-27",
            "range_end_date": "2026-04-06",
            "total_net_cashflow": 0,
            "projection_days": 10,
            "include_projected": True,
            "points": [],
        }

    async def _cash_balances(*args, **kwargs):
        return 200, {
            "totals": {"cash_account_count": 1, "total_balance_reporting_currency": 100.0},
            "cash_accounts": [],
        }

    async def _positions(*args, **kwargs):
        return 200, {
            "positions": [
                {
                    "security_id": "EQ_1",
                    "instrument_name": "Equity 1",
                    "quantity": 1,
                    "valuation": {"market_value_base": 1000.0},
                }
            ]
        }

    async def _allocation(*args, **kwargs):
        return 200, {
            "views": [{"dimension": "asset_class", "buckets": [{"dimension_value": "Equity"}]}]
        }

    async def _transactions(*args, **kwargs):
        return 200, {
            "total": 1,
            "skip": 0,
            "limit": 1,
            "transactions": [
                {
                    "transaction_id": "TX_1",
                    "transaction_date": "2026-03-27T00:00:00Z",
                    "transaction_type": "BUY",
                    "security_id": "EQ_1",
                    "instrument_id": "EQ_1",
                    "quantity": 1,
                }
            ],
        }

    async def _readiness(*args, **kwargs):
        return 200, {
            "holdings": {"status": "READY", "reasons": []},
            "pricing": {
                "status": "PENDING",
                "reasons": [
                    {
                        "code": "pricing_not_published",
                        "detail": "Pricing has not yet been published for the business date.",
                    }
                ],
            },
            "transactions": {"status": "READY", "reasons": []},
            "reporting": {"status": "READY", "reasons": []},
            "blocking_reasons": [
                {
                    "code": "awaiting_pricing",
                    "detail": "Reporting remains blocked until pricing is published.",
                }
            ],
        }

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio", _get_portfolio)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_assets_under_management", _query_aum)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_support_overview", _support)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_cashflow_projection", _cashflow)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_cash_balances", _cash_balances)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_readiness", _readiness)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_positions", _positions)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_asset_allocation", _allocation)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_transactions", _transactions)

    client = TestClient(app)
    response = client.get("/api/v1/portfolio/portfolios/PF_1001/readiness")
    assert response.status_code == 200
    body = response.json()
    assert body["indicators"][0]["key"] == "holdings"
    assert body["indicators"][0]["status"] == "Ready"
    assert body["pricing"]["status"] == "Pending"
    assert body["pricing"]["reasons"][0]["code"] == "pricing_not_published"
    assert body["blocking_reasons"][0]["code"] == "awaiting_pricing"


def test_portfolio_readiness_router_preserves_upstream_bad_request(monkeypatch):
    async def _get_portfolio(*args, **kwargs):
        return 200, {"portfolio_id": "PF_1001", "base_currency": "USD", "status": "ACTIVE"}

    async def _query_aum(*args, **kwargs):
        return 200, {
            "resolved_as_of_date": "2026-03-27",
            "portfolios": [
                {"portfolio_id": "PF_1001", "aum_reporting_currency": 1000.0, "position_count": 2}
            ],
        }

    async def _support(*args, **kwargs):
        return 200, {"business_date": "2026-03-27", "publish_allowed": True}

    async def _cashflow(*args, **kwargs):
        return 200, {
            "as_of_date": "2026-03-27",
            "range_end_date": "2026-04-06",
            "total_net_cashflow": 0,
            "projection_days": 10,
            "include_projected": True,
            "points": [],
        }

    async def _cash_balances(*args, **kwargs):
        return 200, {
            "totals": {"cash_account_count": 1, "total_balance_reporting_currency": 100.0},
            "cash_accounts": [],
        }

    async def _readiness(*args, **kwargs):
        return 400, {"detail": "as_of_date must be YYYY-MM-DD"}

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio", _get_portfolio)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_assets_under_management", _query_aum)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_support_overview", _support)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_cashflow_projection", _cashflow)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_cash_balances", _cash_balances)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_readiness", _readiness)

    client = TestClient(app)
    response = client.get(
        "/api/v1/portfolio/portfolios/PF_1001/readiness",
        params={"as_of_date": "bad-date"},
    )

    assert response.status_code == 400
    assert "readiness rejected the request" in response.json()["detail"]


def test_portfolio_workspace_router_preserves_support_overview_bad_request(monkeypatch):
    async def _get_portfolio(*args, **kwargs):
        return 200, {"portfolio_id": "PF_1001", "base_currency": "USD", "status": "ACTIVE"}

    async def _query_aum(*args, **kwargs):
        return 200, {
            "resolved_as_of_date": "2026-03-27",
            "portfolios": [
                {"portfolio_id": "PF_1001", "aum_reporting_currency": 1000.0, "position_count": 2}
            ],
        }

    async def _support(*args, **kwargs):
        return 400, {"detail": "as_of_date must be YYYY-MM-DD"}

    async def _readiness(*args, **kwargs):
        return 200, {
            "holdings": {"status": "READY", "reasons": []},
            "pricing": {"status": "READY", "reasons": []},
            "transactions": {"status": "READY", "reasons": []},
            "reporting": {"status": "READY", "reasons": []},
            "blocking_reasons": [],
        }

    async def _cashflow(*args, **kwargs):
        return 200, {
            "as_of_date": "2026-03-27",
            "range_end_date": "2026-04-06",
            "total_net_cashflow": 0,
            "projection_days": 10,
            "include_projected": True,
            "points": [],
        }

    async def _cash_balances(*args, **kwargs):
        return 200, {
            "totals": {"cash_account_count": 1, "total_balance_reporting_currency": 100.0},
            "cash_accounts": [],
        }

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio", _get_portfolio)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_assets_under_management", _query_aum)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_support_overview", _support)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_readiness", _readiness)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_cashflow_projection", _cashflow)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_cash_balances", _cash_balances)

    client = TestClient(app)
    response = client.get(
        "/api/v1/portfolio/portfolios/PF_1001/workspace",
        params={"as_of_date": "bad-date"},
    )

    assert response.status_code == 400
    assert "support overview rejected the request" in response.json()["detail"]


def test_portfolio_workflow_router(monkeypatch):
    async def _get_portfolio(*args, **kwargs):
        return 200, {"portfolio_id": "PF_1001", "base_currency": "USD", "status": "ACTIVE"}

    async def _query_aum(*args, **kwargs):
        return 200, {
            "resolved_as_of_date": "2026-03-27",
            "portfolios": [
                {"portfolio_id": "PF_1001", "aum_reporting_currency": 1000.0, "position_count": 2}
            ],
        }

    async def _support(*args, **kwargs):
        return 200, {"business_date": "2026-03-27", "publish_allowed": True}

    async def _cashflow(*args, **kwargs):
        return 200, {
            "as_of_date": "2026-03-27",
            "range_end_date": "2026-04-06",
            "total_net_cashflow": 0,
            "projection_days": 10,
            "include_projected": True,
            "points": [],
        }

    async def _cash_balances(*args, **kwargs):
        return 200, {
            "totals": {"cash_account_count": 1, "total_balance_reporting_currency": 100.0},
            "cash_accounts": [],
        }

    async def _transactions(*args, **kwargs):
        return 200, {
            "total": 1,
            "skip": 0,
            "limit": 1,
            "transactions": [
                {
                    "transaction_id": "TX_1",
                    "transaction_date": "2026-03-27T00:00:00Z",
                    "transaction_type": "BUY",
                    "security_id": "EQ_1",
                    "instrument_id": "EQ_1",
                    "quantity": 1,
                }
            ],
        }

    async def _readiness(*args, **kwargs):
        return 200, {
            "holdings": {"status": "READY", "reasons": []},
            "pricing": {"status": "READY", "reasons": []},
            "transactions": {"status": "READY", "reasons": []},
            "reporting": {"status": "READY", "reasons": []},
            "blocking_reasons": [],
        }

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio", _get_portfolio)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_assets_under_management", _query_aum)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_support_overview", _support)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_cashflow_projection", _cashflow)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_cash_balances", _cash_balances)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_readiness", _readiness)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_transactions", _transactions)

    client = TestClient(app)
    response = client.get("/api/v1/portfolio/portfolios/PF_1001/workflow")
    assert response.status_code == 200
    assert response.json()["actions"][0]["title"] == "Review performance"


def test_portfolio_insights_router(monkeypatch):
    async def _get_portfolio(*args, **kwargs):
        return 200, {"portfolio_id": "PF_1001", "base_currency": "USD", "status": "ACTIVE"}

    async def _query_aum(*args, **kwargs):
        return 200, {
            "resolved_as_of_date": "2026-03-27",
            "portfolios": [
                {"portfolio_id": "PF_1001", "aum_reporting_currency": 1000.0, "position_count": 1}
            ],
        }

    async def _support(*args, **kwargs):
        return 200, {"business_date": "2026-03-27", "publish_allowed": True}

    async def _cashflow(*args, **kwargs):
        return 200, {
            "as_of_date": "2026-03-27",
            "range_end_date": "2026-04-06",
            "total_net_cashflow": 0,
            "projection_days": 10,
            "include_projected": True,
            "points": [],
        }

    async def _cash_balances(*args, **kwargs):
        return 200, {
            "totals": {"cash_account_count": 1, "total_balance_reporting_currency": 100.0},
            "cash_accounts": [],
        }

    async def _positions(*args, **kwargs):
        return 200, {
            "positions": [
                {
                    "security_id": "EQ_1",
                    "instrument_name": "Equity 1",
                    "quantity": 1,
                    "weight": 0.25,
                    "valuation": {"market_value_base": 1000.0},
                }
            ]
        }

    async def _allocation(*args, **kwargs):
        return 200, {
            "views": [{"dimension": "asset_class", "buckets": [{"dimension_value": "Equity"}]}]
        }

    async def _transactions(*args, **kwargs):
        return 200, {
            "total": 1,
            "skip": 0,
            "limit": 50,
            "transactions": [
                {
                    "transaction_id": "TX_1",
                    "transaction_date": "2026-03-27T00:00:00Z",
                    "transaction_type": "BUY",
                    "security_id": "EQ_1",
                    "instrument_id": "EQ_1",
                    "quantity": 1,
                }
            ],
        }

    async def _activity_summary(*args, **kwargs):
        return 200, {
            "reporting_currency": "USD",
            "totals": {
                "buckets": [
                    {
                        "bucket": "OUTFLOWS",
                        "requested_window": {
                            "transaction_count": 1,
                            "amount_reporting_currency": -100.0,
                        },
                        "year_to_date": {
                            "transaction_count": 1,
                            "amount_reporting_currency": -100.0,
                        },
                    }
                ]
            },
        }

    async def _readiness(*args, **kwargs):
        return 200, {
            "holdings": {"status": "READY", "reasons": []},
            "pricing": {"status": "READY", "reasons": []},
            "transactions": {"status": "READY", "reasons": []},
            "reporting": {"status": "READY", "reasons": []},
            "blocking_reasons": [],
        }

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio", _get_portfolio)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_assets_under_management", _query_aum)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_support_overview", _support)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_cashflow_projection", _cashflow)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_cash_balances", _cash_balances)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_readiness", _readiness)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_positions", _positions)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_asset_allocation", _allocation)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_transactions", _transactions)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_activity_summary", _activity_summary)

    client = TestClient(app)
    response = client.get("/api/v1/portfolio/portfolios/PF_1001/insights")
    assert response.status_code == 200
    body = response.json()
    assert body["portfolio_id"] == "PF_1001"
    assert {item["key"] for item in body["insights"]} == {
        "equity-concentration-high",
        "net-outflows-window",
    }
    assert body["exception_summaries"] == []


def test_portfolio_book_router(monkeypatch):
    captured: dict[str, object] = {}

    async def _get_portfolio(*args, **kwargs):
        return 200, {"portfolio_id": "PF_1001", "base_currency": "USD"}

    async def _query_aum(*args, **kwargs):
        return 200, {
            "resolved_as_of_date": "2026-03-27",
            "portfolios": [
                {"portfolio_id": "PF_1001", "aum_reporting_currency": 1000.0, "position_count": 2}
            ],
        }

    async def _positions(*args, **kwargs):
        captured["include_projected"] = kwargs.get("include_projected")
        return 200, {
            "positions": [
                {
                    "security_id": "EQ_1",
                    "instrument_name": "Equity 1",
                    "quantity": 1,
                    "valuation": {"market_value_base": 1000.0},
                }
            ]
        }

    async def _allocation(*args, **kwargs):
        return 200, {"views": [{"dimension": "asset_class", "buckets": []}]}

    async def _cash_balances(*args, **kwargs):
        return 200, {
            "totals": {"cash_account_count": 0, "total_balance_reporting_currency": 0},
            "cash_accounts": [],
        }

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio", _get_portfolio)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_assets_under_management", _query_aum)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_positions", _positions)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_asset_allocation", _allocation)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_cash_balances", _cash_balances)

    client = TestClient(app)
    response = client.get(
        "/api/v1/portfolio/portfolios/PF_1001/book",
        params={"as_of_date": "2026-03-27", "include_projected": "true"},
    )
    assert response.status_code == 200
    assert response.json()["positions"][0]["security_id"] == "EQ_1"
    assert captured["include_projected"] is True


def test_portfolio_transactions_router(monkeypatch):
    captured: dict[str, object] = {}

    async def _transactions(*args, **kwargs):
        captured.update(kwargs)
        return 200, {
            "total": 1,
            "skip": 0,
            "limit": 50,
            "transactions": [
                {
                    "transaction_id": "TX_1",
                    "transaction_date": "2026-03-27T00:00:00Z",
                    "transaction_type": "BUY",
                    "security_id": "EQ_1",
                    "instrument_id": "EQ_1",
                    "quantity": 1,
                }
            ],
        }

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_transactions", _transactions)
    client = TestClient(app)
    response = client.get(
        "/api/v1/portfolio/portfolios/PF_1001/transactions",
        params={
            "as_of_date": "2026-03-27",
            "include_projected": "true",
            "transaction_type": "BUY",
            "security_id": "EQ_1",
            "start_date": "2026-03-01",
            "end_date": "2026-03-27",
            "skip": 5,
            "limit": 25,
        },
    )
    assert response.status_code == 200
    assert response.json()["transactions"][0]["transaction_id"] == "TX_1"
    assert captured["as_of_date"] == "2026-03-27"
    assert captured["include_projected"] is True
    assert captured["transaction_type"] == "BUY"
    assert captured["security_id"] == "EQ_1"
    assert captured["start_date"] == "2026-03-01"
    assert captured["end_date"] == "2026-03-27"
    assert captured["skip"] == 5
    assert captured["limit"] == 25


def test_portfolio_liquidity_router(monkeypatch):
    captured: dict[str, object] = {}

    async def _query_aum(*args, **kwargs):
        captured["aum_reporting_currency"] = kwargs.get("reporting_currency")
        return 200, {
            "resolved_as_of_date": "2026-03-27",
            "portfolios": [
                {"portfolio_id": "PF_1001", "aum_reporting_currency": 1000.0, "position_count": 2}
            ],
        }

    async def _cash_balances(*args, **kwargs):
        captured["cash_reporting_currency"] = kwargs.get("reporting_currency")
        return 200, {
            "totals": {"cash_account_count": 1, "total_balance_reporting_currency": 100.0},
            "cash_accounts": [
                {
                    "security_id": "CASH_USD",
                    "instrument_name": "USD Cash",
                    "account_currency": "USD",
                    "balance_account_currency": 100.0,
                    "balance_reporting_currency": 100.0,
                }
            ],
        }

    async def _cashflow(*args, **kwargs):
        return 200, {
            "as_of_date": "2026-03-27",
            "range_end_date": "2026-04-06",
            "total_net_cashflow": 0,
            "projection_days": 10,
            "include_projected": True,
            "points": [],
        }

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_assets_under_management", _query_aum)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_cash_balances", _cash_balances)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_cashflow_projection", _cashflow)

    client = TestClient(app)
    response = client.get(
        "/api/v1/portfolio/portfolios/PF_1001/liquidity",
        params={"as_of_date": "2026-03-27", "reporting_currency": "USD"},
    )
    assert response.status_code == 200
    assert response.json()["cash_balances"][0]["security_id"] == "CASH_USD"
    assert captured["aum_reporting_currency"] == "USD"
    assert captured["cash_reporting_currency"] == "USD"


def test_portfolio_projected_cashflow_router(monkeypatch):
    captured: dict[str, object] = {}

    async def _cashflow(*args, **kwargs):
        captured.update(kwargs)
        return 200, {
            "as_of_date": "2026-03-27",
            "range_end_date": "2026-04-26",
            "total_net_cashflow": 125.0,
            "projection_days": 30,
            "include_projected": True,
            "points": [
                {
                    "projection_date": "2026-03-28",
                    "net_cashflow": 25.0,
                    "projected_cumulative_cashflow": 25.0,
                }
            ],
        }

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_cashflow_projection", _cashflow)

    client = TestClient(app)
    response = client.get(
        "/api/v1/portfolio/portfolios/PF_1001/projected-cashflow",
        params={
            "as_of_date": "2026-03-27",
            "horizon_days": 30,
            "include_projected": "false",
        },
    )
    assert response.status_code == 200
    assert response.json()["cashflow_outlook"]["projection_days"] == 30
    assert captured["horizon_days"] == 30
    assert captured["as_of_date"] == "2026-03-27"
    assert captured["include_projected"] is False


def test_portfolio_allocations_router(monkeypatch):
    captured: dict[str, object] = {}

    async def _query_aum(*args, **kwargs):
        return 200, {
            "resolved_as_of_date": "2026-03-27",
            "portfolios": [
                {"portfolio_id": "PF_1001", "aum_reporting_currency": 1000.0, "position_count": 2}
            ],
        }

    async def _cash_balances(*args, **kwargs):
        return 200, {
            "totals": {"cash_account_count": 0, "total_balance_reporting_currency": 0},
            "cash_accounts": [],
        }

    async def _allocation(*args, **kwargs):
        captured["reporting_currency"] = kwargs.get("reporting_currency")
        captured["look_through_mode"] = kwargs.get("look_through_mode")
        return 200, {
            "reporting_currency": "USD",
            "look_through": {
                "requested_mode": "full",
                "effective_mode": "direct_only",
                "applied": False,
            },
            "views": [
                {
                    "dimension": "region",
                    "buckets": [{"dimension_value": "Equity", "position_count": 1, "weight": 0.7}],
                }
            ],
        }

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_assets_under_management", _query_aum)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_cash_balances", _cash_balances)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_asset_allocation", _allocation)

    client = TestClient(app)
    response = client.get(
        "/api/v1/portfolio/portfolios/PF_1001/allocations",
        params={
            "as_of_date": "2026-03-27",
            "reporting_currency": "USD",
            "look_through_mode": "full",
        },
    )
    assert response.status_code == 200
    assert response.json()["views"][0]["dimension"] == "region"
    assert captured["reporting_currency"] == "USD"
    assert captured["look_through_mode"] == "full"


def test_portfolio_positions_router(monkeypatch):
    captured: dict[str, object] = {}

    async def _query_aum(*args, **kwargs):
        return 200, {
            "resolved_as_of_date": "2026-03-27",
            "portfolios": [
                {"portfolio_id": "PF_1001", "aum_reporting_currency": 1000.0, "position_count": 2}
            ],
        }

    async def _cash_balances(*args, **kwargs):
        return 200, {
            "totals": {"cash_account_count": 0, "total_balance_reporting_currency": 0},
            "cash_accounts": [],
        }

    async def _positions(*args, **kwargs):
        captured["include_projected"] = kwargs.get("include_projected")
        captured["reporting_currency"] = kwargs.get("reporting_currency")
        return 200, {
            "positions": [
                {
                    "security_id": "EQ_1",
                    "instrument_name": "Equity 1",
                    "quantity": 1,
                    "valuation": {"market_value_base": 1000.0},
                }
            ]
        }

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_assets_under_management", _query_aum)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_cash_balances", _cash_balances)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_positions", _positions)

    client = TestClient(app)
    response = client.get(
        "/api/v1/portfolio/portfolios/PF_1001/positions",
        params={
            "as_of_date": "2026-03-27",
            "include_projected": "true",
            "reporting_currency": "USD",
        },
    )
    assert response.status_code == 200
    assert response.json()["positions"][0]["security_id"] == "EQ_1"
    assert captured["include_projected"] is True
    assert captured["reporting_currency"] == "USD"


def test_portfolio_income_summary_router(monkeypatch):
    captured: dict[str, object] = {}

    async def _income_summary(*args, **kwargs):
        captured.update(kwargs)
        return 200, {
            "reporting_currency": "USD",
            "totals": {
                "requested_window": {
                    "transaction_count": 1,
                    "gross_amount_reporting_currency": 20.0,
                    "withholding_tax_reporting_currency": 2.0,
                    "other_deductions_reporting_currency": 0.0,
                    "net_amount_reporting_currency": 18.0,
                },
                "year_to_date": {
                    "transaction_count": 2,
                    "gross_amount_reporting_currency": 40.0,
                    "withholding_tax_reporting_currency": 4.0,
                    "other_deductions_reporting_currency": 0.0,
                    "net_amount_reporting_currency": 36.0,
                },
            },
            "portfolios": [
                {
                    "income_types": [
                        {
                            "income_type": "DIVIDEND",
                            "requested_window": {
                                "transaction_count": 1,
                                "gross_amount_reporting_currency": 20.0,
                                "withholding_tax_reporting_currency": 2.0,
                                "other_deductions_reporting_currency": 0.0,
                                "net_amount_reporting_currency": 18.0,
                            },
                            "year_to_date": {
                                "transaction_count": 2,
                                "gross_amount_reporting_currency": 40.0,
                                "withholding_tax_reporting_currency": 4.0,
                                "other_deductions_reporting_currency": 0.0,
                                "net_amount_reporting_currency": 36.0,
                            },
                        }
                    ]
                }
            ],
        }

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_income_summary", _income_summary)
    client = TestClient(app)
    response = client.get(
        "/api/v1/portfolio/portfolios/PF_1001/income-summary",
        params={
            "as_of_date": "2026-03-27",
            "start_date": "2026-03-01",
            "end_date": "2026-03-27",
            "reporting_currency": "USD",
        },
    )
    assert response.status_code == 200
    assert response.json()["income_types"][0]["income_type"] == "DIVIDEND"
    assert captured["reporting_currency"] == "USD"
    assert captured["start_date"] == "2026-03-01"
    assert captured["end_date"] == "2026-03-27"


def test_portfolio_activity_summary_router(monkeypatch):
    captured: dict[str, object] = {}

    async def _activity_summary(*args, **kwargs):
        captured.update(kwargs)
        return 200, {
            "reporting_currency": "USD",
            "totals": {
                "buckets": [
                    {
                        "bucket": "INFLOWS",
                        "requested_window": {
                            "transaction_count": 1,
                            "amount_reporting_currency": 100.0,
                        },
                        "year_to_date": {
                            "transaction_count": 2,
                            "amount_reporting_currency": 150.0,
                        },
                    }
                ]
            },
        }

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_activity_summary", _activity_summary)
    client = TestClient(app)
    response = client.get(
        "/api/v1/portfolio/portfolios/PF_1001/activity-summary",
        params={
            "as_of_date": "2026-03-27",
            "start_date": "2026-03-01",
            "end_date": "2026-03-27",
            "reporting_currency": "USD",
        },
    )
    assert response.status_code == 200
    assert response.json()["buckets"][0]["bucket"] == "INFLOWS"
    assert captured["reporting_currency"] == "USD"
    assert captured["start_date"] == "2026-03-01"
    assert captured["end_date"] == "2026-03-27"


def test_portfolio_performance_snapshot_router(monkeypatch):
    captured: dict[str, object] = {}

    async def _snapshot(*args, **kwargs):
        captured.update(kwargs)
        return {
            "correlation_id": "corr-performance",
            "contract_version": "v1",
            "portfolio_id": "PF_1001",
            "as_of_date": "2026-03-27",
            "period": "EXPLICIT",
            "benchmark_code": "BMK_GLOBAL_BALANCED_60_40",
            "portfolio_return_pct": 15.1,
            "benchmark_return_pct": 14.72,
            "excess_return_pct": 0.38,
            "sparkline": [
                {
                    "as_of_date": "2026-01-31",
                    "portfolio_return_pct": 2.0,
                    "benchmark_return_pct": 1.8,
                    "excess_return_pct": 0.2,
                }
            ],
            "unavailable": None,
            "warnings": [],
            "partial_failures": [],
        }

    monkeypatch.setattr(
        portfolio_router._performance_workspace_service(),
        "get_portfolio_performance_snapshot",
        _snapshot,
    )
    client = TestClient(app)
    response = client.get(
        "/api/v1/portfolio/portfolios/PF_1001/performance-snapshot",
        params={
            "period": "EXPLICIT",
            "chart_frequency": "quarterly",
            "detail_basis": "GROSS",
            "benchmark_code": "BMK_GLOBAL_BALANCED_60_40",
            "explicit_start_date": "2026-01-01",
            "explicit_end_date": "2026-03-27",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["portfolio_return_pct"] == 15.1
    assert body["benchmark_return_pct"] == 14.72
    assert body["excess_return_pct"] == 0.38
    assert body["sparkline"][0]["as_of_date"] == "2026-01-31"
    assert captured["portfolio_id"] == "PF_1001"
    assert captured["period"] == "EXPLICIT"
    assert captured["chart_frequency"] == "quarterly"
    assert captured["detail_basis"] == "GROSS"
    assert captured["benchmark_code"] == "BMK_GLOBAL_BALANCED_60_40"
    assert captured["explicit_start_date"] == "2026-01-01"
    assert captured["explicit_end_date"] == "2026-03-27"
