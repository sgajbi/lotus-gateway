import pytest

from app.services.portfolio_service import PortfolioService


class _StubLotusCoreQueryClient:
    async def list_portfolios(self, correlation_id: str):
        return 200, {
            "portfolios": [
                {"portfolio_id": "PF_2002", "base_currency": "EUR", "client_id": "CIF_2"},
                {"portfolio_id": "PF_1001", "base_currency": "USD", "client_id": "CIF_1"},
            ]
        }

    async def get_portfolio(self, portfolio_id: str, correlation_id: str):
        return 200, {
            "portfolio_id": portfolio_id,
            "base_currency": "USD",
            "booking_center_code": "SGPB",
            "client_id": "CIF_1",
            "status": "ACTIVE",
            "portfolio_type": "ADVISORY",
        }

    async def query_assets_under_management(self, **kwargs):
        return 200, {
            "resolved_as_of_date": "2026-03-27",
            "portfolios": [
                {
                    "portfolio_id": kwargs["portfolio_id"],
                    "aum_reporting_currency": 1000.0,
                    "position_count": 3,
                }
            ],
        }

    async def get_support_overview(self, portfolio_id: str, correlation_id: str):
        return 200, {
            "business_date": "2026-03-27",
            "latest_booked_transaction_date": "2026-03-27",
            "latest_booked_position_snapshot_date": "2026-03-27",
            "publish_allowed": True,
            "controls_blocking": False,
        }

    async def get_cashflow_projection(self, portfolio_id: str, correlation_id: str, **kwargs):
        return 200, {
            "as_of_date": "2026-03-27",
            "range_end_date": "2026-04-06",
            "total_net_cashflow": -25.0,
            "projection_days": 10,
            "include_projected": True,
            "points": [
                {
                    "projection_date": "2026-03-28",
                    "net_cashflow": -25.0,
                    "projected_cumulative_cashflow": -25.0,
                }
            ],
        }

    async def query_cash_balances(self, **kwargs):
        return 200, {
            "totals": {
                "cash_account_count": 1,
                "total_balance_reporting_currency": 100.0,
            },
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

    async def get_portfolio_positions(self, portfolio_id: str, correlation_id: str, **kwargs):
        return 200, {
            "positions": [
                {
                    "security_id": "EQ_1",
                    "instrument_name": "Equity 1",
                    "asset_class": "Equity",
                    "quantity": 10,
                    "cost_basis": 500.0,
                    "weight": 0.7,
                    "valuation": {"market_value_base": 700.0, "market_price": 70.0},
                },
                {
                    "security_id": "FI_1",
                    "instrument_name": "Bond 1",
                    "asset_class": "Fixed Income",
                    "quantity": 4,
                    "cost_basis": 200.0,
                    "weight": 0.2,
                    "valuation": {"market_value_base": 200.0, "market_price": 50.0},
                },
            ]
        }

    async def query_asset_allocation(self, **kwargs):
        return 200, {
            "views": [
                {
                    "dimension": "asset_class",
                    "buckets": [
                        {
                            "dimension_value": "Equity",
                            "market_value_reporting_currency": 700.0,
                            "weight": 0.7,
                            "position_count": 1,
                        }
                    ],
                }
            ]
        }

    async def get_portfolio_transactions(self, portfolio_id: str, correlation_id: str, **kwargs):
        return 200, {
            "total": 1,
            "skip": kwargs["skip"],
            "limit": kwargs["limit"],
            "transactions": [
                {
                    "transaction_id": "TX_1",
                    "transaction_date": "2026-03-27T09:30:00Z",
                    "transaction_type": "BUY",
                    "security_id": "EQ_1",
                    "instrument_id": "EQ_1",
                    "quantity": 10,
                    "price": 70.0,
                    "gross_transaction_amount": 700.0,
                    "currency": "USD",
                }
            ],
        }

    async def query_income_summary(self, **kwargs):
        return 200, {
            "reporting_currency": "USD",
            "totals": {
                "requested_window": {
                    "transaction_count": 2,
                    "gross_amount_portfolio_currency": 30.0,
                    "gross_amount_reporting_currency": 30.0,
                    "withholding_tax_portfolio_currency": 3.0,
                    "withholding_tax_reporting_currency": 3.0,
                    "other_deductions_portfolio_currency": 1.0,
                    "other_deductions_reporting_currency": 1.0,
                    "net_amount_portfolio_currency": 26.0,
                    "net_amount_reporting_currency": 26.0,
                },
                "year_to_date": {
                    "transaction_count": 4,
                    "gross_amount_portfolio_currency": 60.0,
                    "gross_amount_reporting_currency": 60.0,
                    "withholding_tax_portfolio_currency": 6.0,
                    "withholding_tax_reporting_currency": 6.0,
                    "other_deductions_portfolio_currency": 2.0,
                    "other_deductions_reporting_currency": 2.0,
                    "net_amount_portfolio_currency": 52.0,
                    "net_amount_reporting_currency": 52.0,
                },
            },
            "portfolios": [
                {
                    "portfolio_id": kwargs["portfolio_id"],
                    "income_types": [
                        {
                            "income_type": "DIVIDEND",
                            "requested_window": {
                                "transaction_count": 1,
                                "gross_amount_portfolio_currency": 20.0,
                                "gross_amount_reporting_currency": 20.0,
                                "withholding_tax_portfolio_currency": 2.0,
                                "withholding_tax_reporting_currency": 2.0,
                                "other_deductions_portfolio_currency": 0.0,
                                "other_deductions_reporting_currency": 0.0,
                                "net_amount_portfolio_currency": 18.0,
                                "net_amount_reporting_currency": 18.0,
                            },
                            "year_to_date": {
                                "transaction_count": 2,
                                "gross_amount_portfolio_currency": 40.0,
                                "gross_amount_reporting_currency": 40.0,
                                "withholding_tax_portfolio_currency": 4.0,
                                "withholding_tax_reporting_currency": 4.0,
                                "other_deductions_portfolio_currency": 0.0,
                                "other_deductions_reporting_currency": 0.0,
                                "net_amount_portfolio_currency": 36.0,
                                "net_amount_reporting_currency": 36.0,
                            },
                        }
                    ],
                }
            ],
        }

    async def query_activity_summary(self, **kwargs):
        return 200, {
            "reporting_currency": "USD",
            "totals": {
                "buckets": [
                    {
                        "bucket": "INFLOWS",
                        "requested_window": {
                            "transaction_count": 1,
                            "amount_portfolio_currency": 100.0,
                            "amount_reporting_currency": 100.0,
                        },
                        "year_to_date": {
                            "transaction_count": 2,
                            "amount_portfolio_currency": 180.0,
                            "amount_reporting_currency": 180.0,
                        },
                    }
                ]
            },
        }


@pytest.mark.asyncio
async def test_portfolio_catalog_is_sorted_and_mapped():
    service = PortfolioService(_StubLotusCoreQueryClient())
    response = await service.get_portfolio_catalog(correlation_id="corr-1")
    assert [item.portfolio_id for item in response.items] == ["PF_1001", "PF_2002"]
    assert response.items[0].base_currency == "USD"


@pytest.mark.asyncio
async def test_portfolio_workspace_uses_aum_and_cash_balance_reporting():
    service = PortfolioService(_StubLotusCoreQueryClient())
    response = await service.get_portfolio_workspace(
        portfolio_id="PF_1001",
        correlation_id="corr-2",
    )
    assert response.summary.assets_under_management_base == 1000.0
    assert response.summary.cash_market_value_base == 100.0
    assert response.summary.invested_market_value_base == 900.0
    assert response.summary.cash_balance_count == 1
    assert response.reporting.status == "READY"
    assert response.operations is not None
    assert response.cashflow_outlook is not None


@pytest.mark.asyncio
async def test_portfolio_readiness_returns_compact_indicators():
    service = PortfolioService(_StubLotusCoreQueryClient())
    response = await service.get_portfolio_readiness(
        portfolio_id="PF_1001",
        correlation_id="corr-2b",
        as_of_date="2026-03-27",
    )
    assert [indicator.key for indicator in response.indicators] == [
        "holdings",
        "pricing",
        "transactions",
        "reporting",
    ]
    assert [indicator.status for indicator in response.indicators] == [
        "Ready",
        "Ready",
        "Ready",
        "Ready",
    ]


@pytest.mark.asyncio
async def test_portfolio_workflow_returns_prioritized_actions():
    service = PortfolioService(_StubLotusCoreQueryClient())
    response = await service.get_portfolio_workflow(
        portfolio_id="PF_1001",
        correlation_id="corr-2c",
        as_of_date="2026-03-27",
    )
    assert response.actions[0].title == "Review performance"
    assert response.actions[0].recommended is True
    assert [action.cta_label for action in response.actions] == [
        "Performance",
        "Holdings",
        "Transactions",
    ]


@pytest.mark.asyncio
async def test_portfolio_book_returns_allocations_cash_and_positions():
    service = PortfolioService(_StubLotusCoreQueryClient())
    response = await service.get_portfolio_book(
        portfolio_id="PF_1001",
        correlation_id="corr-3",
        as_of_date="2026-03-27",
        include_projected=False,
    )
    assert response.summary.assets_under_management_base == 1000.0
    assert response.cash_balances[0].security_id == "CASH_USD"
    assert response.allocation_views[0].dimension == "asset_class"
    assert response.positions[0].security_id == "EQ_1"
    assert response.top_positions[0].security_id == "EQ_1"


@pytest.mark.asyncio
async def test_portfolio_liquidity_returns_cash_and_cashflow():
    service = PortfolioService(_StubLotusCoreQueryClient())
    response = await service.get_portfolio_liquidity(
        portfolio_id="PF_1001",
        correlation_id="corr-3b",
        as_of_date="2026-03-27",
    )
    assert response.summary.cash_market_value_base == 100.0
    assert response.cash_balances[0].security_id == "CASH_USD"
    assert response.cashflow_outlook is not None
    assert response.cashflow_outlook.upcoming_points[0].projection_date == "2026-03-28"


@pytest.mark.asyncio
async def test_portfolio_allocations_return_dimension_views():
    service = PortfolioService(_StubLotusCoreQueryClient())
    response = await service.get_portfolio_allocations(
        portfolio_id="PF_1001",
        correlation_id="corr-3c",
        as_of_date="2026-03-27",
    )
    assert response.summary.assets_under_management_base == 1000.0
    assert response.views[0].dimension == "asset_class"
    assert response.views[0].buckets[0].bucket == "Equity"


@pytest.mark.asyncio
async def test_portfolio_positions_return_top_positions_and_full_book():
    service = PortfolioService(_StubLotusCoreQueryClient())
    response = await service.get_portfolio_positions(
        portfolio_id="PF_1001",
        correlation_id="corr-3d",
        as_of_date="2026-03-27",
        include_projected=False,
    )
    assert response.summary.position_count == 3
    assert response.positions[0].security_id == "EQ_1"
    assert response.top_positions[0].security_id == "EQ_1"
    assert response.positions[0].market_value_base == 700.0
    assert response.positions[0].market_value_local is None


@pytest.mark.asyncio
async def test_portfolio_positions_fall_back_to_legacy_core_valuation_keys():
    class _LegacyValuationClient(_StubLotusCoreQueryClient):
        async def get_portfolio_positions(self, portfolio_id: str, correlation_id: str, **kwargs):
            return 200, {
                "positions": [
                    {
                        "security_id": "EQ_1",
                        "instrument_name": "Equity 1",
                        "asset_class": "Equity",
                        "quantity": 10,
                        "cost_basis": 500.0,
                        "weight": 0.7,
                        "valuation": {
                            "market_value": 700.0,
                            "market_price": 70.0,
                            "unrealized_gain_loss": 200.0,
                        },
                    }
                ]
            }

    service = PortfolioService(_LegacyValuationClient())
    response = await service.get_portfolio_positions(
        portfolio_id="PF_1001",
        correlation_id="corr-3e",
        as_of_date="2026-03-27",
        include_projected=False,
    )

    assert response.positions[0].market_value_base == 700.0
    assert response.positions[0].market_value_local == 700.0
    assert response.positions[0].unrealized_gain_loss_base == 200.0
    assert response.positions[0].unrealized_gain_loss_local == 200.0


@pytest.mark.asyncio
async def test_transaction_ledger_preserves_paging_metadata():
    service = PortfolioService(_StubLotusCoreQueryClient())
    response = await service.get_transaction_ledger(
        portfolio_id="PF_1001",
        correlation_id="corr-4",
        as_of_date="2026-03-27",
        include_projected=False,
        skip=20,
        limit=25,
    )
    assert response.total == 1
    assert response.skip == 20
    assert response.limit == 25
    assert response.transactions[0].transaction_id == "TX_1"


@pytest.mark.asyncio
async def test_income_summary_returns_requested_window_and_income_types():
    service = PortfolioService(_StubLotusCoreQueryClient())
    response = await service.get_income_summary(
        portfolio_id="PF_1001",
        correlation_id="corr-5",
        start_date="2026-03-01",
        end_date="2026-03-27",
    )
    assert response.reporting_currency == "USD"
    assert response.totals_requested_window.net.reporting_currency_amount == 26.0
    assert response.income_types[0].income_type == "DIVIDEND"


@pytest.mark.asyncio
async def test_activity_summary_returns_bucket_totals():
    service = PortfolioService(_StubLotusCoreQueryClient())
    response = await service.get_activity_summary(
        portfolio_id="PF_1001",
        correlation_id="corr-6",
        start_date="2026-03-01",
        end_date="2026-03-27",
    )
    assert response.buckets[0].bucket == "INFLOWS"
    assert response.buckets[0].requested_window.reporting_currency_amount == 100.0
