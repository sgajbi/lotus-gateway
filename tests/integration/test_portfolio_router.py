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
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_cash_balances", _cash_balances)

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
    assert captured["support_as_of_date"] is None


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
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_cash_balances", _cash_balances)
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
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_cash_balances", _cash_balances)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_readiness", _readiness)

    client = TestClient(app)
    response = client.get(
        "/api/v1/portfolio/portfolios/PF_1001/readiness",
        params={"as_of_date": "bad-date"},
    )

    assert response.status_code == 400
    assert "readiness rejected the request" in response.json()["detail"]


def test_portfolio_workspace_router_preserves_support_overview_partial_failure(monkeypatch):
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
        return 503, {"detail": "support overview unavailable"}

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
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_cash_balances", _cash_balances)

    client = TestClient(app)
    response = client.get(
        "/api/v1/portfolio/portfolios/PF_1001/workspace",
        params={"as_of_date": "bad-date"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["operations"] is None
    assert "PORTFOLIO_SUPPORT_OVERVIEW_UNAVAILABLE" in body["warnings"]
    assert body["partial_failures"][0]["error_code"] == "PORTFOLIO_SUPPORT_OVERVIEW_UNAVAILABLE"
    assert body["partial_failures"][0]["detail"] == "support overview unavailable"


def test_portfolio_workflow_router(monkeypatch):
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
        captured["workflow_transaction_limit"] = kwargs.get("limit")
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
        captured["workflow_readiness_as_of_date"] = kwargs.get("as_of_date")
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
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_cash_balances", _cash_balances)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_readiness", _readiness)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_transactions", _transactions)

    client = TestClient(app)
    response = client.get(
        "/api/v1/portfolio/portfolios/PF_1001/workflow",
        params={"as_of_date": "2026-03-27"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["correlation_id"]
    assert body["contract_version"] == "v1"
    assert body["as_of_date"] == "2026-03-27"
    assert body["actions"][0] == {
        "sequence": 1,
        "title": "Review performance",
        "impact": (
            "Review portfolio return, benchmark context, and contribution once the book is valued."
        ),
        "target": "Target: Performance workflow for this portfolio",
        "href": "/performance?portfolioId=PF_1001",
        "cta_label": "Performance",
        "recommended": True,
    }
    assert body["actions"][1]["title"] == "Review holdings"
    assert body["actions"][2]["title"] == "Review transactions"
    assert captured == {
        "workflow_transaction_limit": 1,
        "workflow_readiness_as_of_date": "2026-03-27",
    }


def test_portfolio_workflow_router_returns_empty_portfolio_setup_sequence(monkeypatch):
    async def _get_portfolio(*args, **kwargs):
        return 200, {"portfolio_id": "PF_EMPTY", "base_currency": "USD", "status": "ACTIVE"}

    async def _query_aum(*args, **kwargs):
        return 200, {
            "resolved_as_of_date": "2026-03-27",
            "portfolios": [
                {
                    "portfolio_id": "PF_EMPTY",
                    "aum_reporting_currency": 0.0,
                    "position_count": 0,
                }
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
            "totals": {"cash_account_count": 0, "total_balance_reporting_currency": 0.0},
            "cash_accounts": [],
        }

    async def _transactions(*args, **kwargs):
        return 200, {"total": 0, "skip": 0, "limit": 1, "transactions": []}

    async def _readiness(*args, **kwargs):
        return 200, {
            "holdings": {"status": "MISSING", "reasons": []},
            "pricing": {"status": "PENDING", "reasons": []},
            "transactions": {"status": "MISSING", "reasons": []},
            "reporting": {"status": "MISSING", "reasons": []},
            "blocking_reasons": [],
        }

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio", _get_portfolio)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_assets_under_management", _query_aum)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_support_overview", _support)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_cashflow_projection", _cashflow)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_cash_balances", _cash_balances)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_readiness", _readiness)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_transactions", _transactions)

    client = TestClient(app)
    response = client.get("/api/v1/portfolio/portfolios/PF_EMPTY/workflow")
    assert response.status_code == 200
    body = response.json()
    assert [action["title"] for action in body["actions"]] == [
        "Fund portfolio",
        "Book first trade",
        "Publish pricing",
        "Review holdings",
        "Open performance",
    ]
    assert [action["sequence"] for action in body["actions"]] == [1, 2, 3, 4, 5]
    assert [action["recommended"] for action in body["actions"]] == [
        True,
        False,
        False,
        False,
        False,
    ]


def test_portfolio_insights_router(monkeypatch):
    captured: dict[str, object] = {}
    transaction_calls: list[dict[str, object]] = []

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
        transaction_calls.append(
            {
                "as_of_date": kwargs.get("as_of_date"),
                "start_date": kwargs.get("start_date"),
                "end_date": kwargs.get("end_date"),
                "skip": kwargs.get("skip"),
                "limit": kwargs.get("limit"),
                "include_projected": kwargs.get("include_projected"),
                "sort_by": kwargs.get("sort_by"),
                "sort_order": kwargs.get("sort_order"),
            }
        )
        return 200, {
            "reporting_currency": "USD",
            "total": 2,
            "skip": 0,
            "limit": kwargs["limit"],
            "transactions": [
                {
                    "transaction_id": "TX_1",
                    "transaction_date": "2026-03-27T00:00:00Z",
                    "transaction_type": "BUY",
                    "security_id": "EQ_1",
                    "instrument_id": "EQ_1",
                    "quantity": 1,
                },
                {
                    "transaction_id": "TX_OUT_1",
                    "transaction_date": "2026-03-12T00:00:00Z",
                    "transaction_type": "WITHDRAWAL",
                    "security_id": "CASH_USD",
                    "instrument_id": "CASH_USD",
                    "quantity": 0,
                    "gross_transaction_amount": 100.0,
                    "gross_transaction_amount_reporting_currency": 100.0,
                },
            ],
        }

    async def _readiness(*args, **kwargs):
        captured["insights_readiness_as_of_date"] = kwargs.get("as_of_date")
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
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_cash_balances", _cash_balances)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_readiness", _readiness)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_positions", _positions)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_asset_allocation", _allocation)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_transactions", _transactions)
    portfolio_router._portfolio_service().clear_upstream_cache()

    client = TestClient(app)
    response = client.get(
        "/api/v1/portfolio/portfolios/PF_1001/insights",
        params={"as_of_date": "2026-03-27"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["correlation_id"]
    assert body["contract_version"] == "v1"
    assert body["portfolio_id"] == "PF_1001"
    assert body["as_of_date"] == "2026-03-27"
    assert body["insights"][0] == {
        "key": "equity-concentration-high",
        "title": "Large position dominates portfolio risk",
        "detail": (
            "One holding has become large enough to dominate current portfolio "
            "concentration. Open Risk to review concentration pressure."
        ),
        "severity": "warning",
        "href": "/risk?portfolioId=PF_1001",
    }
    assert "equity-concentration-high" in {item["key"] for item in body["insights"]}
    assert body["exception_summaries"] == []
    assert transaction_calls == [
        {
            "as_of_date": "2026-03-27",
            "start_date": None,
            "end_date": None,
            "skip": 0,
            "limit": 1,
            "include_projected": False,
            "sort_by": "transaction_date",
            "sort_order": "desc",
        },
        {
            "as_of_date": "2026-03-27",
            "start_date": "2026-01-01",
            "end_date": "2026-03-27",
            "skip": 0,
            "limit": 500,
            "include_projected": False,
            "sort_by": "transaction_date",
            "sort_order": "asc",
        },
    ]
    assert captured == {"insights_readiness_as_of_date": "2026-03-27"}


def test_portfolio_insights_router_returns_blocked_exception_summaries(monkeypatch):
    async def _get_portfolio(*args, **kwargs):
        return 200, {"portfolio_id": "PF_1001", "base_currency": "USD", "status": "ACTIVE"}

    async def _query_aum(*args, **kwargs):
        return 200, {
            "resolved_as_of_date": "2026-03-27",
            "portfolios": [
                {"portfolio_id": "PF_1001", "aum_reporting_currency": 0.0, "position_count": 0}
            ],
        }

    async def _support(*args, **kwargs):
        return 200, {
            "business_date": "2026-03-27",
            "publish_allowed": False,
            "controls_blocking": True,
        }

    async def _cashflow(*args, **kwargs):
        return 503, {"detail": "cashflow temporarily unavailable"}

    async def _cash_balances(*args, **kwargs):
        return 200, {
            "totals": {"cash_account_count": 0, "total_balance_reporting_currency": 0.0},
            "cash_accounts": [],
        }

    async def _positions(*args, **kwargs):
        return 200, {"positions": []}

    async def _allocation(*args, **kwargs):
        return 200, {"views": []}

    async def _transactions(*args, **kwargs):
        return 200, {
            "reporting_currency": "USD",
            "total": 0,
            "skip": 0,
            "limit": kwargs["limit"],
            "transactions": [],
        }

    async def _readiness(*args, **kwargs):
        return 200, {
            "holdings": {"status": "MISSING", "reasons": []},
            "pricing": {"status": "PENDING", "reasons": []},
            "transactions": {"status": "MISSING", "reasons": []},
            "reporting": {"status": "MISSING", "reasons": []},
            "blocking_reasons": [],
        }

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio", _get_portfolio)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_assets_under_management", _query_aum)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_support_overview", _support)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_cashflow_projection", _cashflow)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_cash_balances", _cash_balances)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_readiness", _readiness)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_positions", _positions)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_asset_allocation", _allocation)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_transactions", _transactions)
    portfolio_router._portfolio_service().clear_upstream_cache()

    client = TestClient(app)
    response = client.get("/api/v1/portfolio/portfolios/PF_1001/insights")
    assert response.status_code == 200
    body = response.json()
    assert [item["key"] for item in body["insights"]] == [
        "no-holdings-booked",
        "no-cash-funding",
        "pricing-not-published",
        "reporting-unavailable",
    ]
    assert [item["key"] for item in body["exception_summaries"]] == [
        "holdings",
        "pricing",
        "transactions",
        "reporting",
        "controls_blocking",
        "partial_failure_PORTFOLIO_CASHFLOW_UNAVAILABLE",
    ]


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
        captured["positions_reporting_currency"] = kwargs.get("reporting_currency")
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
        captured["allocation_reporting_currency"] = kwargs.get("reporting_currency")
        return 200, {"views": [{"dimension": "asset_class", "buckets": []}]}

    async def _cash_balances(*args, **kwargs):
        captured["cash_reporting_currency"] = kwargs.get("reporting_currency")
        return 200, {
            "totals": {"cash_account_count": 0, "total_balance_reporting_currency": 0},
            "cash_accounts": [],
        }

    async def _cashflow(*args, **kwargs):
        raise AssertionError("book endpoint should not request projected cashflow")

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio", _get_portfolio)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_assets_under_management", _query_aum)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_positions", _positions)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_asset_allocation", _allocation)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_cash_balances", _cash_balances)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_cashflow_projection", _cashflow)

    portfolio_router._portfolio_service().clear_upstream_cache()
    client = TestClient(app)
    response = client.get(
        "/api/v1/portfolio/portfolios/PF_1001/book",
        params={
            "as_of_date": "2026-03-27",
            "include_projected": "true",
            "reporting_currency": "USD",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["as_of_date"] == "2026-03-27"
    assert body["portfolio"]["portfolio_id"] == "PF_1001"
    assert body["summary"]["assets_under_management_base"] == 1000.0
    assert body["positions"][0]["security_id"] == "EQ_1"
    assert body["allocation_views"][0]["dimension"] == "asset_class"
    assert body["cash_balances"] == []
    assert captured["include_projected"] is True
    assert captured["positions_reporting_currency"] == "USD"
    assert captured["allocation_reporting_currency"] == "USD"
    assert captured["cash_reporting_currency"] == "USD"


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
                    "component_type": "FX_CONTRACT_OPEN",
                    "security_id": "EQ_1",
                    "instrument_id": "INST_EQ_1",
                    "quantity": 1,
                    "linked_transaction_group_id": "LTG-2026-0001",
                    "fx_contract_id": "FXC-2026-0001",
                    "swap_event_id": "FXSWAP-2026-0001",
                    "near_leg_group_id": "FXSWAP-2026-0001-NEAR",
                    "far_leg_group_id": "FXSWAP-2026-0001-FAR",
                }
            ],
        }

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_transactions", _transactions)
    portfolio_router._portfolio_service().clear_upstream_cache()
    client = TestClient(app)
    response = client.get(
        "/api/v1/portfolio/portfolios/PF_1001/transactions",
        params={
            "as_of_date": "2026-03-27",
            "include_projected": "true",
            "transaction_type": "BUY",
            "security_id": "EQ_1",
            "instrument_id": "INST_EQ_1",
            "component_type": "TRADE",
            "linked_transaction_group_id": "LTG-2026-0001",
            "fx_contract_id": "FXC-2026-0001",
            "swap_event_id": "FXSWAP-2026-0001",
            "near_leg_group_id": "FXSWAP-2026-0001-NEAR",
            "far_leg_group_id": "FXSWAP-2026-0001-FAR",
            "start_date": "2026-03-01",
            "end_date": "2026-03-27",
            "skip": 5,
            "limit": 25,
            "sort_by": "settlement_date",
            "sort_order": "asc",
        },
    )
    assert response.status_code == 200
    transaction = response.json()["transactions"][0]
    assert transaction["transaction_id"] == "TX_1"
    assert transaction["component_type"] == "FX_CONTRACT_OPEN"
    assert transaction["instrument_id"] == "INST_EQ_1"
    assert transaction["linked_transaction_group_id"] == "LTG-2026-0001"
    assert transaction["fx_contract_id"] == "FXC-2026-0001"
    assert transaction["swap_event_id"] == "FXSWAP-2026-0001"
    assert transaction["near_leg_group_id"] == "FXSWAP-2026-0001-NEAR"
    assert transaction["far_leg_group_id"] == "FXSWAP-2026-0001-FAR"
    assert captured["as_of_date"] == "2026-03-27"
    assert captured["include_projected"] is True
    assert captured["transaction_type"] == "BUY"
    assert captured["security_id"] == "EQ_1"
    assert captured["instrument_id"] == "INST_EQ_1"
    assert captured["component_type"] == "TRADE"
    assert captured["linked_transaction_group_id"] == "LTG-2026-0001"
    assert captured["fx_contract_id"] == "FXC-2026-0001"
    assert captured["swap_event_id"] == "FXSWAP-2026-0001"
    assert captured["near_leg_group_id"] == "FXSWAP-2026-0001-NEAR"
    assert captured["far_leg_group_id"] == "FXSWAP-2026-0001-FAR"
    assert captured["start_date"] == "2026-03-01"
    assert captured["end_date"] == "2026-03-27"
    assert captured["skip"] == 5
    assert captured["limit"] == 25
    assert captured["sort_by"] == "settlement_date"
    assert captured["sort_order"] == "asc"


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
        captured["cashflow_as_of_date"] = kwargs.get("as_of_date")
        captured["cashflow_horizon_days"] = kwargs.get("horizon_days")
        captured["cashflow_include_projected"] = kwargs.get("include_projected")
        return 200, {
            "as_of_date": "2026-03-27",
            "range_end_date": "2026-04-06",
            "total_net_cashflow": 0,
            "projection_days": 10,
            "include_projected": True,
            "points": [],
        }

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_assets_under_management", _query_aum)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_cash_balances", _cash_balances)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_cashflow_projection", _cashflow)

    client = TestClient(app)
    response = client.get(
        "/api/v1/portfolio/portfolios/PF_1001/liquidity",
        params={"as_of_date": "2026-03-27", "reporting_currency": "USD"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["as_of_date"] == "2026-03-27"
    assert body["summary"]["assets_under_management_base"] == 1000.0
    assert body["cash_balances"][0]["security_id"] == "CASH_USD"
    assert body["cashflow_outlook"]["projection_days"] == 10
    assert captured["aum_reporting_currency"] == "USD"
    assert captured["cash_reporting_currency"] == "USD"
    assert captured["cashflow_as_of_date"] == "2026-03-27"
    assert captured["cashflow_horizon_days"] == 10
    assert captured["cashflow_include_projected"] is True


def test_portfolio_liquidity_router_preserves_partial_failure(monkeypatch):
    async def _query_aum(*args, **kwargs):
        return 200, {
            "resolved_as_of_date": "2026-03-27",
            "portfolios": [
                {"portfolio_id": "PF_1001", "aum_reporting_currency": 1000.0, "position_count": 2}
            ],
        }

    async def _cash_balances(*args, **kwargs):
        return 200, {
            "totals": {"cash_account_count": 1, "total_balance_reporting_currency": 100.0},
            "cash_accounts": [],
        }

    async def _cashflow(*args, **kwargs):
        return 503, {"detail": "cashflow temporarily unavailable"}

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_assets_under_management", _query_aum)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_cash_balances", _cash_balances)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_cashflow_projection", _cashflow)

    client = TestClient(app)
    response = client.get("/api/v1/portfolio/portfolios/PF_1001/liquidity")
    assert response.status_code == 200
    body = response.json()
    assert body["cashflow_outlook"] is None
    assert "PORTFOLIO_CASHFLOW_UNAVAILABLE" in body["warnings"]
    assert body["partial_failures"][0]["error_code"] == "PORTFOLIO_CASHFLOW_UNAVAILABLE"


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
    body = response.json()
    assert body["as_of_date"] == "2026-03-27"
    assert body["cashflow_outlook"]["projection_days"] == 30
    assert body["cashflow_outlook"]["include_projected"] is True
    assert captured["horizon_days"] == 30
    assert captured["as_of_date"] == "2026-03-27"
    assert captured["include_projected"] is False


def test_portfolio_projected_cashflow_router_preserves_partial_failure(monkeypatch):
    async def _cashflow(*args, **kwargs):
        return 503, {"detail": "cashflow temporarily unavailable"}

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_cashflow_projection", _cashflow)

    client = TestClient(app)
    response = client.get("/api/v1/portfolio/portfolios/PF_1001/projected-cashflow")
    assert response.status_code == 200
    body = response.json()
    assert body["cashflow_outlook"] is None
    assert "PORTFOLIO_CASHFLOW_UNAVAILABLE" in body["warnings"]
    assert body["partial_failures"][0]["error_code"] == "PORTFOLIO_CASHFLOW_UNAVAILABLE"


def test_portfolio_allocations_router(monkeypatch):
    captured: dict[str, object] = {}

    async def _query_aum(*args, **kwargs):
        return 200, {
            "resolved_as_of_date": "2026-03-27",
            "portfolios": [
                {"portfolio_id": "PF_1001", "aum_reporting_currency": 1000.0, "position_count": 2}
            ],
        }

    async def _positions(*args, **kwargs):
        captured["positions_reporting_currency"] = kwargs.get("reporting_currency")
        return 200, {
            "positions": [
                {
                    "security_id": "CASH_USD",
                    "instrument_name": "USD Cash",
                    "asset_class": "Cash",
                    "quantity": 100.0,
                    "valuation": {"market_value_base": 100.0},
                }
            ]
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
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_positions", _positions)
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
    body = response.json()
    assert body["as_of_date"] == "2026-03-27"
    assert body["reporting_currency"] == "USD"
    assert body["look_through"]["requested_mode"] == "full"
    assert body["look_through"]["effective_mode"] == "direct_only"
    assert body["views"][0]["dimension"] == "region"
    assert body["summary"]["cash_market_value_base"] == 100.0
    assert captured["reporting_currency"] == "USD"
    assert captured["positions_reporting_currency"] == "USD"
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
                },
                {
                    "security_id": "CASH_USD",
                    "instrument_name": "USD Cash",
                    "asset_class": "Cash",
                    "quantity": 100.0,
                    "valuation": {"market_value_base": 100.0},
                },
            ]
        }

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_assets_under_management", _query_aum)
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
    body = response.json()
    assert body["as_of_date"] == "2026-03-27"
    assert body["positions"][0]["security_id"] == "EQ_1"
    assert body["top_positions"][0]["security_id"] == "EQ_1"
    assert body["summary"]["cash_market_value_base"] == 100.0
    assert captured["include_projected"] is True
    assert captured["reporting_currency"] == "USD"


def test_portfolio_income_summary_router(monkeypatch):
    captured: list[dict[str, object]] = []

    async def _transactions(*args, **kwargs):
        captured.append(dict(kwargs))
        return 200, {
            "reporting_currency": "USD",
            "total": 2,
            "skip": kwargs["skip"],
            "limit": kwargs["limit"],
            "transactions": [
                {
                    "transaction_id": "TX_DIV_REQ",
                    "transaction_date": "2026-03-20T09:30:00Z",
                    "transaction_type": "DIVIDEND",
                    "security_id": "EQ_1",
                    "instrument_id": "EQ_1",
                    "quantity": 0,
                    "gross_transaction_amount": 20.0,
                    "gross_transaction_amount_reporting_currency": 20.0,
                    "withholding_tax_amount": 2.0,
                    "withholding_tax_amount_reporting_currency": 2.0,
                    "other_interest_deductions_amount": 0.0,
                    "other_interest_deductions_amount_reporting_currency": 0.0,
                    "currency": "USD",
                },
                {
                    "transaction_id": "TX_DIV_YTD",
                    "transaction_date": "2026-02-20T09:30:00Z",
                    "transaction_type": "DIVIDEND",
                    "security_id": "EQ_1",
                    "instrument_id": "EQ_1",
                    "quantity": 0,
                    "gross_transaction_amount": 20.0,
                    "gross_transaction_amount_reporting_currency": 20.0,
                    "withholding_tax_amount": 2.0,
                    "withholding_tax_amount_reporting_currency": 2.0,
                    "other_interest_deductions_amount": 0.0,
                    "other_interest_deductions_amount_reporting_currency": 0.0,
                    "currency": "USD",
                },
            ],
        }

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_transactions", _transactions)
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
    body = response.json()
    assert body["reporting_currency"] == "USD"
    assert body["window_start_date"] == "2026-03-01"
    assert body["window_end_date"] == "2026-03-27"
    assert body["income_types"][0]["income_type"] == "DIVIDEND"
    assert body["totals_requested_window"]["net"]["reporting_currency_amount"] == 18.0
    assert body["totals_year_to_date"]["net"]["reporting_currency_amount"] == 36.0
    assert captured[0]["reporting_currency"] == "USD"
    assert captured[0]["start_date"] == "2026-01-01"
    assert captured[0]["end_date"] == "2026-03-27"


def test_portfolio_activity_summary_router(monkeypatch):
    captured: list[dict[str, object]] = []

    async def _transactions(*args, **kwargs):
        captured.append(dict(kwargs))
        return 200, {
            "reporting_currency": "USD",
            "total": 2,
            "skip": kwargs["skip"],
            "limit": kwargs["limit"],
            "transactions": [
                {
                    "transaction_id": "TX_DEP_REQ",
                    "transaction_date": "2026-03-20T09:30:00Z",
                    "transaction_type": "DEPOSIT",
                    "security_id": "CASH_USD",
                    "instrument_id": "CASH_USD",
                    "quantity": 0,
                    "gross_transaction_amount": 100.0,
                    "gross_transaction_amount_reporting_currency": 100.0,
                    "currency": "USD",
                },
                {
                    "transaction_id": "TX_DEP_YTD",
                    "transaction_date": "2026-02-20T09:30:00Z",
                    "transaction_type": "TRANSFER_IN",
                    "security_id": "CASH_USD",
                    "instrument_id": "CASH_USD",
                    "quantity": 0,
                    "gross_transaction_amount": 50.0,
                    "gross_transaction_amount_reporting_currency": 50.0,
                    "currency": "USD",
                },
            ],
        }

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_transactions", _transactions)
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
    body = response.json()
    assert body["reporting_currency"] == "USD"
    assert body["window_start_date"] == "2026-03-01"
    assert body["window_end_date"] == "2026-03-27"
    assert body["buckets"][0]["bucket"] == "INFLOWS"
    assert body["buckets"][0]["requested_window"]["reporting_currency_amount"] == 100.0
    assert body["buckets"][0]["year_to_date"]["reporting_currency_amount"] == 150.0
    assert captured[0]["reporting_currency"] == "USD"
    assert captured[0]["start_date"] == "2026-01-01"
    assert captured[0]["end_date"] == "2026-03-27"


def test_portfolio_performance_snapshot_router(monkeypatch):
    captured: dict[str, object] = {}

    async def _snapshot(*args, **kwargs):
        captured.update(kwargs)
        return {
            "correlation_id": "corr-performance",
            "contract_version": "v1",
            "portfolio_id": "PF_1001",
            "as_of_date": "2026-03-27",
            "report_start_date": "2026-01-01",
            "report_end_date": "2026-03-27",
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
    assert body["report_start_date"] == "2026-01-01"
    assert body["report_end_date"] == "2026-03-27"
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


def test_portfolio_performance_snapshot_router_preserves_unavailable_state(monkeypatch):
    async def _snapshot(*args, **kwargs):
        return {
            "correlation_id": "corr-performance-unavailable",
            "contract_version": "v1",
            "portfolio_id": "PF_1001",
            "as_of_date": "2026-03-27",
            "report_start_date": "2026-01-01",
            "report_end_date": "2026-03-27",
            "period": "YTD",
            "benchmark_code": None,
            "portfolio_return_pct": None,
            "benchmark_return_pct": None,
            "excess_return_pct": None,
            "sparkline": [],
            "unavailable": {
                "title": "Performance data unavailable",
                "detail": "Performance snapshot requires valuation history and cashflow history.",
                "requirements": ["valuation history", "cashflow history"],
            },
            "warnings": ["PERFORMANCE_SNAPSHOT_UNAVAILABLE"],
            "partial_failures": [
                {
                    "source_service": "lotus-performance",
                    "error_code": "PERFORMANCE_SNAPSHOT_UNAVAILABLE",
                    "detail": "valuation history missing",
                }
            ],
        }

    monkeypatch.setattr(
        portfolio_router._performance_workspace_service(),
        "get_portfolio_performance_snapshot",
        _snapshot,
    )
    client = TestClient(app)
    response = client.get("/api/v1/portfolio/portfolios/PF_1001/performance-snapshot")

    assert response.status_code == 200
    body = response.json()
    assert body["report_start_date"] == "2026-01-01"
    assert body["report_end_date"] == "2026-03-27"
    assert body["unavailable"]["title"] == "Performance data unavailable"
    assert body["warnings"] == ["PERFORMANCE_SNAPSHOT_UNAVAILABLE"]
    assert body["partial_failures"][0]["error_code"] == "PERFORMANCE_SNAPSHOT_UNAVAILABLE"
