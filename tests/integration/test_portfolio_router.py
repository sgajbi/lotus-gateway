from fastapi.testclient import TestClient

from app.main import app

LOTUS_CORE_QUERY_CLIENT = "app.clients.lotus_core_query_client.LotusCoreQueryClient"


def test_portfolio_catalog_router(monkeypatch):
    async def _list_portfolios(*args, **kwargs):
        return 200, {"portfolios": [{"portfolio_id": "PF_1001", "base_currency": "USD"}]}

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.list_portfolios", _list_portfolios)
    client = TestClient(app)
    response = client.get("/api/v1/portfolio/portfolios")
    assert response.status_code == 200
    assert response.json()["items"][0]["portfolio_id"] == "PF_1001"


def test_portfolio_workspace_router(monkeypatch):
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

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio", _get_portfolio)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_assets_under_management", _query_aum)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_support_overview", _support)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_cashflow_projection", _cashflow)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_cash_balances", _cash_balances)

    client = TestClient(app)
    response = client.get("/api/v1/portfolio/portfolios/PF_1001/workspace")
    assert response.status_code == 200
    body = response.json()
    assert body["portfolio"]["portfolio_id"] == "PF_1001"
    assert body["summary"]["assets_under_management_base"] == 1000.0


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

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio", _get_portfolio)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_assets_under_management", _query_aum)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_support_overview", _support)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_cashflow_projection", _cashflow)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_cash_balances", _cash_balances)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_positions", _positions)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_asset_allocation", _allocation)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_transactions", _transactions)

    client = TestClient(app)
    response = client.get("/api/v1/portfolio/portfolios/PF_1001/readiness")
    assert response.status_code == 200
    assert response.json()["indicators"][0]["key"] == "holdings"
    assert response.json()["indicators"][0]["status"] == "Ready"


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

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio", _get_portfolio)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_assets_under_management", _query_aum)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_support_overview", _support)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_cashflow_projection", _cashflow)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_cash_balances", _cash_balances)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_transactions", _transactions)

    client = TestClient(app)
    response = client.get("/api/v1/portfolio/portfolios/PF_1001/workflow")
    assert response.status_code == 200
    assert response.json()["actions"][0]["title"] == "Review performance"


def test_portfolio_book_router(monkeypatch):
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
    response = client.get("/api/v1/portfolio/portfolios/PF_1001/book")
    assert response.status_code == 200
    assert response.json()["positions"][0]["security_id"] == "EQ_1"


def test_portfolio_transactions_router(monkeypatch):
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

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_transactions", _transactions)
    client = TestClient(app)
    response = client.get("/api/v1/portfolio/portfolios/PF_1001/transactions")
    assert response.status_code == 200
    assert response.json()["transactions"][0]["transaction_id"] == "TX_1"


def test_portfolio_liquidity_router(monkeypatch):
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
    response = client.get("/api/v1/portfolio/portfolios/PF_1001/liquidity")
    assert response.status_code == 200
    assert response.json()["cash_balances"][0]["security_id"] == "CASH_USD"


def test_portfolio_allocations_router(monkeypatch):
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
        return 200, {
            "views": [
                {
                    "dimension": "asset_class",
                    "buckets": [{"dimension_value": "Equity", "position_count": 1, "weight": 0.7}],
                }
            ]
        }

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_assets_under_management", _query_aum)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_cash_balances", _cash_balances)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.query_asset_allocation", _allocation)

    client = TestClient(app)
    response = client.get("/api/v1/portfolio/portfolios/PF_1001/allocations")
    assert response.status_code == 200
    assert response.json()["views"][0]["dimension"] == "asset_class"


def test_portfolio_positions_router(monkeypatch):
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
    response = client.get("/api/v1/portfolio/portfolios/PF_1001/positions")
    assert response.status_code == 200
    assert response.json()["positions"][0]["security_id"] == "EQ_1"


def test_portfolio_income_summary_router(monkeypatch):
    async def _income_summary(*args, **kwargs):
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
    response = client.get("/api/v1/portfolio/portfolios/PF_1001/income-summary")
    assert response.status_code == 200
    assert response.json()["income_types"][0]["income_type"] == "DIVIDEND"


def test_portfolio_activity_summary_router(monkeypatch):
    async def _activity_summary(*args, **kwargs):
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
    response = client.get("/api/v1/portfolio/portfolios/PF_1001/activity-summary")
    assert response.status_code == 200
    assert response.json()["buckets"][0]["bucket"] == "INFLOWS"
