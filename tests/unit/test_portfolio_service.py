import pytest
from fastapi import HTTPException

from app.contracts.portfolio import PortfolioSummary, PortfolioWorkflowLaunchCue
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

    async def get_portfolio_readiness(self, portfolio_id: str, correlation_id: str, **kwargs):
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

    async def get_portfolio_analytics_reference(
        self,
        portfolio_id: str,
        as_of_date: str,
        consumer_system: str,
        correlation_id: str,
    ):
        _ = portfolio_id, as_of_date, consumer_system, correlation_id
        return 200, {"performance_end_date": "2026-03-27"}

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

    async def get_portfolio_cash_balances(self, **kwargs):
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
                {
                    "security_id": "CASH_USD",
                    "instrument_name": "USD Cash",
                    "asset_class": "Cash",
                    "currency": "USD",
                    "quantity": 100.0,
                    "weight": 0.1,
                    "valuation": {"market_value_base": 100.0, "market_price": 1.0},
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
        transactions = [
            {
                "transaction_id": "TX_1",
                "transaction_date": "2026-03-27T09:30:00Z",
                "transaction_type": "BUY",
                "component_type": "FX_CONTRACT_OPEN",
                "security_id": "EQ_1",
                "instrument_id": "INST_EQ_1",
                "quantity": 10,
                "price": 70.0,
                "gross_transaction_amount": 700.0,
                "gross_transaction_amount_reporting_currency": 700.0,
                "currency": "USD",
                "linked_transaction_group_id": "LTG-FX-2026-0001",
                "fx_contract_id": "FXC-2026-0001",
                "swap_event_id": "FXSWAP-2026-0001",
                "near_leg_group_id": "FXSWAP-2026-0001-NEAR",
                "far_leg_group_id": "FXSWAP-2026-0001-FAR",
            },
            {
                "transaction_id": "TX_DIV_REQ",
                "transaction_date": "2026-03-20T09:30:00Z",
                "transaction_type": "DIVIDEND",
                "security_id": "EQ_1",
                "instrument_id": "EQ_1",
                "quantity": 0,
                "price": None,
                "gross_transaction_amount": 20.0,
                "gross_transaction_amount_reporting_currency": 20.0,
                "withholding_tax_amount": 2.0,
                "withholding_tax_amount_reporting_currency": 2.0,
                "other_interest_deductions_amount": 0.0,
                "other_interest_deductions_amount_reporting_currency": 0.0,
                "currency": "USD",
            },
            {
                "transaction_id": "TX_INT_REQ",
                "transaction_date": "2026-03-10T09:30:00Z",
                "transaction_type": "INTEREST",
                "security_id": "CASH_USD",
                "instrument_id": "CASH_USD",
                "quantity": 0,
                "price": None,
                "gross_transaction_amount": 10.0,
                "gross_transaction_amount_reporting_currency": 10.0,
                "withholding_tax_amount": 1.0,
                "withholding_tax_amount_reporting_currency": 1.0,
                "other_interest_deductions_amount": 1.0,
                "other_interest_deductions_amount_reporting_currency": 1.0,
                "net_interest_amount": 8.0,
                "net_interest_amount_reporting_currency": 8.0,
                "interest_direction": "INCOME",
                "currency": "USD",
            },
            {
                "transaction_id": "TX_DIV_YTD",
                "transaction_date": "2026-02-15T09:30:00Z",
                "transaction_type": "DIVIDEND",
                "security_id": "EQ_1",
                "instrument_id": "EQ_1",
                "quantity": 0,
                "price": None,
                "gross_transaction_amount": 20.0,
                "gross_transaction_amount_reporting_currency": 20.0,
                "withholding_tax_amount": 2.0,
                "withholding_tax_amount_reporting_currency": 2.0,
                "other_interest_deductions_amount": 0.0,
                "other_interest_deductions_amount_reporting_currency": 0.0,
                "currency": "USD",
            },
            {
                "transaction_id": "TX_INT_YTD",
                "transaction_date": "2026-01-15T09:30:00Z",
                "transaction_type": "INTEREST",
                "security_id": "CASH_USD",
                "instrument_id": "CASH_USD",
                "quantity": 0,
                "price": None,
                "gross_transaction_amount": 10.0,
                "gross_transaction_amount_reporting_currency": 10.0,
                "withholding_tax_amount": 1.0,
                "withholding_tax_amount_reporting_currency": 1.0,
                "other_interest_deductions_amount": 1.0,
                "other_interest_deductions_amount_reporting_currency": 1.0,
                "net_interest_amount": 8.0,
                "net_interest_amount_reporting_currency": 8.0,
                "interest_direction": "INCOME",
                "currency": "USD",
            },
            {
                "transaction_id": "TX_DEP_REQ",
                "transaction_date": "2026-03-05T09:30:00Z",
                "transaction_type": "DEPOSIT",
                "security_id": "CASH_USD",
                "instrument_id": "CASH_USD",
                "quantity": 0,
                "price": None,
                "gross_transaction_amount": 100.0,
                "gross_transaction_amount_reporting_currency": 100.0,
                "currency": "USD",
            },
            {
                "transaction_id": "TX_DEP_YTD",
                "transaction_date": "2026-02-05T09:30:00Z",
                "transaction_type": "TRANSFER_IN",
                "security_id": "CASH_USD",
                "instrument_id": "CASH_USD",
                "quantity": 0,
                "price": None,
                "gross_transaction_amount": 80.0,
                "gross_transaction_amount_reporting_currency": 80.0,
                "currency": "USD",
            },
        ]
        start_date = kwargs.get("start_date")
        end_date = kwargs.get("end_date")
        security_id = kwargs.get("security_id")
        instrument_id = kwargs.get("instrument_id")
        transaction_type = kwargs.get("transaction_type")
        sort_order = str(kwargs.get("sort_order", "desc")).lower()
        skip = int(kwargs.get("skip", 0))
        limit = int(kwargs.get("limit", 50))

        filtered = transactions
        if start_date is not None:
            filtered = [item for item in filtered if item["transaction_date"][:10] >= start_date]
        if end_date is not None:
            filtered = [item for item in filtered if item["transaction_date"][:10] <= end_date]
        if security_id is not None:
            filtered = [item for item in filtered if item["security_id"] == security_id]
        if instrument_id is not None:
            filtered = [item for item in filtered if item["instrument_id"] == instrument_id]
        if transaction_type is not None:
            filtered = [item for item in filtered if item["transaction_type"] == transaction_type]
        filtered = sorted(
            filtered,
            key=lambda item: item["transaction_date"],
            reverse=sort_order != "asc",
        )

        return 200, {
            "reporting_currency": kwargs.get("reporting_currency", "USD"),
            "total": len(filtered),
            "skip": skip,
            "limit": limit,
            "transactions": filtered[skip : skip + limit],
        }


class _CountingLotusCoreQueryClient(_StubLotusCoreQueryClient):
    def __init__(self):
        self.calls: dict[str, int] = {}

    def _record(self, name: str) -> None:
        self.calls[name] = self.calls.get(name, 0) + 1

    async def get_portfolio(self, portfolio_id: str, correlation_id: str):
        self._record("get_portfolio")
        return await super().get_portfolio(portfolio_id, correlation_id)

    async def query_assets_under_management(self, **kwargs):
        self._record("query_assets_under_management")
        return await super().query_assets_under_management(**kwargs)

    async def get_support_overview(self, portfolio_id: str, correlation_id: str):
        self._record("get_support_overview")
        return await super().get_support_overview(portfolio_id, correlation_id)

    async def get_portfolio_readiness(self, portfolio_id: str, correlation_id: str, **kwargs):
        self._record("get_portfolio_readiness")
        return await super().get_portfolio_readiness(portfolio_id, correlation_id, **kwargs)

    async def get_cashflow_projection(self, portfolio_id: str, correlation_id: str, **kwargs):
        self._record("get_cashflow_projection")
        return await super().get_cashflow_projection(portfolio_id, correlation_id, **kwargs)

    async def get_portfolio_cash_balances(self, **kwargs):
        self._record("get_portfolio_cash_balances")
        return await super().get_portfolio_cash_balances(**kwargs)

    async def get_portfolio_positions(self, portfolio_id: str, correlation_id: str, **kwargs):
        self._record("get_portfolio_positions")
        return await super().get_portfolio_positions(portfolio_id, correlation_id, **kwargs)

    async def query_asset_allocation(self, **kwargs):
        self._record("query_asset_allocation")
        return await super().query_asset_allocation(**kwargs)

    async def get_portfolio_transactions(self, portfolio_id: str, correlation_id: str, **kwargs):
        self._record("get_portfolio_transactions")
        return await super().get_portfolio_transactions(portfolio_id, correlation_id, **kwargs)


class _StubAnalyticsClient:
    async def get_twr_analytics(self, **kwargs):
        _ = kwargs
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


class _StubDpmClient:
    async def list_runs(self, params: dict[str, object], correlation_id: str):
        _ = params, correlation_id
        return 200, {
            "items": [
                {
                    "status": "PENDING_REVIEW",
                    "created_at": "2026-03-27T12:00:00Z",
                    "rebalance_run_id": "rr_100",
                }
            ]
        }


@pytest.mark.asyncio
async def test_portfolio_catalog_is_sorted_and_mapped():
    service = PortfolioService(_StubLotusCoreQueryClient())
    response = await service.get_portfolio_catalog(correlation_id="corr-1")
    assert [item.portfolio_id for item in response.items] == ["PF_1001", "PF_2002"]
    assert response.items[0].base_currency == "USD"


@pytest.mark.asyncio
async def test_portfolio_workspace_uses_aum_and_cash_balance_reporting():
    service = PortfolioService(
        _StubLotusCoreQueryClient(),
        analytics_client=_StubAnalyticsClient(),
        dpm_client=_StubDpmClient(),
    )
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
    assert response.performance is not None
    assert response.performance.return_pct == 2.5
    assert response.rebalance is not None
    assert response.rebalance.status == "PENDING_REVIEW"


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
        "Pending",
        "Ready",
        "Ready",
    ]
    assert response.pricing is not None
    assert response.pricing.reasons[0].code == "pricing_not_published"
    assert response.blocking_reasons[0].code == "awaiting_pricing"


@pytest.mark.asyncio
async def test_portfolio_insights_returns_source_backed_insight_and_exception_summaries():
    service = PortfolioService(_StubLotusCoreQueryClient())
    response = await service.get_portfolio_insights(
        portfolio_id="PF_1001",
        correlation_id="corr-2bb",
        as_of_date="2026-03-27",
    )

    assert response.portfolio_id == "PF_1001"
    assert [insight.model_dump() for insight in response.insights] == [
        {
            "key": "equity-concentration-high",
            "title": "Large position dominates portfolio risk",
            "detail": (
                "One holding has become large enough to dominate current portfolio "
                "concentration. Open Risk to review concentration pressure."
            ),
            "severity": "warning",
            "href": "/risk?portfolioId=PF_1001",
        }
    ]
    assert response.exception_summaries == []


@pytest.mark.asyncio
async def test_portfolio_insights_treats_recent_inflows_as_cash_funding_evidence():
    class _FundingEvidenceClient(_StubLotusCoreQueryClient):
        async def query_assets_under_management(self, **kwargs):
            return 200, {
                "resolved_as_of_date": "2026-03-27",
                "portfolios": [
                    {
                        "portfolio_id": kwargs["portfolio_id"],
                        "aum_reporting_currency": 0.0,
                        "position_count": 0,
                    }
                ],
            }

        async def get_portfolio_cash_balances(self, **kwargs):
            return 200, {
                "totals": {
                    "cash_account_count": 0,
                    "total_balance_reporting_currency": 0.0,
                },
                "cash_accounts": [],
            }

        async def get_portfolio_positions(self, portfolio_id: str, correlation_id: str, **kwargs):
            return 200, {"positions": []}

        async def query_asset_allocation(self, **kwargs):
            return 200, {"views": []}

        async def get_portfolio_transactions(
            self, portfolio_id: str, correlation_id: str, **kwargs
        ):
            return 200, {
                "reporting_currency": "USD",
                "total": 1,
                "skip": kwargs["skip"],
                "limit": kwargs["limit"],
                "transactions": [
                    {
                        "transaction_id": "TX_DEP_REQ",
                        "transaction_date": "2026-03-05T09:30:00Z",
                        "transaction_type": "DEPOSIT",
                        "security_id": "CASH_USD",
                        "instrument_id": "CASH_USD",
                        "quantity": 0,
                        "price": None,
                        "gross_transaction_amount": 100.0,
                        "gross_transaction_amount_reporting_currency": 100.0,
                        "currency": "USD",
                    }
                ],
            }

    service = PortfolioService(_FundingEvidenceClient())
    response = await service.get_portfolio_insights(
        portfolio_id="PF_1001",
        correlation_id="corr-2bb-funding",
        as_of_date="2026-03-27",
    )

    insight_keys = {insight.key for insight in response.insights}
    assert "no-holdings-booked" in insight_keys
    assert "no-cash-funding" not in insight_keys


@pytest.mark.asyncio
async def test_portfolio_insights_flags_net_outflows_from_activity_buckets():
    class _OutflowClient(_StubLotusCoreQueryClient):
        async def get_portfolio_transactions(
            self, portfolio_id: str, correlation_id: str, **kwargs
        ):
            return 200, {
                "reporting_currency": "USD",
                "total": 1,
                "skip": kwargs["skip"],
                "limit": kwargs["limit"],
                "transactions": [
                    {
                        "transaction_id": "TX_OUT_1",
                        "transaction_date": "2026-03-05T09:30:00Z",
                        "transaction_type": "WITHDRAWAL",
                        "security_id": "CASH_USD",
                        "instrument_id": "CASH_USD",
                        "quantity": 0,
                        "gross_transaction_amount": 100.0,
                        "gross_transaction_amount_reporting_currency": 100.0,
                        "currency": "USD",
                    }
                ],
            }

    service = PortfolioService(_OutflowClient())
    response = await service.get_portfolio_insights(
        portfolio_id="PF_1001",
        correlation_id="corr-2bb-outflows",
        as_of_date="2026-03-27",
    )

    assert "net-outflows-window" in {insight.key for insight in response.insights}


@pytest.mark.asyncio
async def test_portfolio_insights_uses_minimal_transaction_probe_for_exception_totals():
    class _ProbeClient(_StubLotusCoreQueryClient):
        def __init__(self):
            self.transaction_limits: list[int | None] = []
            self.include_projected_flags: list[bool | None] = []

        async def get_portfolio_transactions(
            self, portfolio_id: str, correlation_id: str, **kwargs
        ):
            self.transaction_limits.append(kwargs.get("limit"))
            self.include_projected_flags.append(kwargs.get("include_projected"))
            return await super().get_portfolio_transactions(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                **kwargs,
            )

    client = _ProbeClient()
    service = PortfolioService(client)

    await service.get_portfolio_insights(
        portfolio_id="PF_1001",
        correlation_id="corr-2bb-probe",
        as_of_date="2026-03-27",
    )

    assert client.transaction_limits[0] == 1
    assert client.include_projected_flags[0] is False


@pytest.mark.asyncio
async def test_portfolio_insights_returns_blocked_exception_summaries():
    class _BlockedPortfolioClient(_StubLotusCoreQueryClient):
        async def query_assets_under_management(self, **kwargs):
            return 200, {
                "resolved_as_of_date": "2026-03-27",
                "portfolios": [
                    {
                        "portfolio_id": kwargs["portfolio_id"],
                        "aum_reporting_currency": 0.0,
                        "position_count": 0,
                    }
                ],
            }

        async def get_support_overview(self, portfolio_id: str, correlation_id: str):
            return 200, {
                "business_date": "2026-03-27",
                "latest_booked_transaction_date": None,
                "latest_booked_position_snapshot_date": None,
                "publish_allowed": False,
                "controls_blocking": True,
            }

        async def get_portfolio_readiness(self, portfolio_id: str, correlation_id: str, **kwargs):
            return 200, {
                "holdings": {"status": "MISSING", "reasons": []},
                "pricing": {"status": "PENDING", "reasons": []},
                "transactions": {"status": "MISSING", "reasons": []},
                "reporting": {"status": "MISSING", "reasons": []},
                "blocking_reasons": [],
            }

        async def get_cashflow_projection(self, portfolio_id: str, correlation_id: str, **kwargs):
            return 503, {"detail": "cashflow temporarily unavailable"}

        async def get_portfolio_cash_balances(self, **kwargs):
            return 200, {
                "totals": {
                    "cash_account_count": 0,
                    "total_balance_reporting_currency": 0.0,
                },
                "cash_accounts": [],
            }

        async def get_portfolio_positions(self, portfolio_id: str, correlation_id: str, **kwargs):
            return 200, {"positions": []}

        async def query_asset_allocation(self, **kwargs):
            return 200, {"views": []}

        async def get_portfolio_transactions(
            self, portfolio_id: str, correlation_id: str, **kwargs
        ):
            return 200, {
                "reporting_currency": "USD",
                "total": 0,
                "skip": kwargs["skip"],
                "limit": kwargs["limit"],
                "transactions": [],
            }

    service = PortfolioService(_BlockedPortfolioClient())
    response = await service.get_portfolio_insights(
        portfolio_id="PF_1001",
        correlation_id="corr-2bb-blocked",
        as_of_date="2026-03-27",
    )

    assert [insight.model_dump() for insight in response.insights] == [
        {
            "key": "no-holdings-booked",
            "title": "No holdings booked",
            "detail": (
                "Book the first position to activate holdings, allocation, and valuation views."
            ),
            "severity": "critical",
            "href": "#portfolio-drilldown",
        },
        {
            "key": "no-cash-funding",
            "title": "No cash funding recorded",
            "detail": (
                "Add opening cash or a subscription so the portfolio can be funded and invested."
            ),
            "severity": "critical",
            "href": "#portfolio-insights",
        },
        {
            "key": "pricing-not-published",
            "title": "Pricing not yet published",
            "detail": "Publish prices to complete valuation and unlock reliable reporting.",
            "severity": "warning",
            "href": "#portfolio-attention",
        },
        {
            "key": "reporting-unavailable",
            "title": "Reporting cannot be generated yet",
            "detail": "Reporting remains blocked until book coverage and valuation are complete.",
            "severity": "warning",
            "href": "#portfolio-health",
        },
    ]
    assert [summary.model_dump() for summary in response.exception_summaries] == [
        {
            "key": "holdings",
            "title": "Missing holdings",
            "detail": "No positions are currently booked for this portfolio.",
            "tone": "danger",
            "href": "#portfolio-drilldown",
        },
        {
            "key": "pricing",
            "title": "No priced positions",
            "detail": "Valuation cannot run until priced positions are available.",
            "tone": "danger",
            "href": "#portfolio-attention",
        },
        {
            "key": "transactions",
            "title": "Empty transaction history",
            "detail": "No funding, trading, or cash activity has been recorded yet.",
            "tone": "danger",
            "href": "#portfolio-drilldown",
        },
        {
            "key": "reporting",
            "title": "Reporting output missing",
            "detail": "Reporting coverage is not yet available for this portfolio.",
            "tone": "danger",
            "href": "#portfolio-health",
        },
        {
            "key": "controls_blocking",
            "title": "Blocking controls active",
            "detail": (
                "Operational controls are currently preventing publication or downstream "
                "processing."
            ),
            "tone": "danger",
            "href": "#portfolio-attention",
        },
        {
            "key": "partial_failure_PORTFOLIO_CASHFLOW_UNAVAILABLE",
            "title": "PORTFOLIO CASHFLOW UNAVAILABLE",
            "detail": "cashflow temporarily unavailable",
            "tone": "warn",
            "href": "#portfolio-attention",
        },
    ]


@pytest.mark.asyncio
async def test_portfolio_workflow_returns_prioritized_actions():
    service = PortfolioService(_StubLotusCoreQueryClient())
    response = await service.get_portfolio_workflow(
        portfolio_id="PF_1001",
        correlation_id="corr-2c",
        as_of_date="2026-03-27",
    )
    assert [action.sequence for action in response.actions] == [1, 2, 3]
    assert [action.title for action in response.actions] == [
        "Review performance",
        "Review holdings",
        "Review transactions",
    ]
    assert [action.impact for action in response.actions] == [
        "Review portfolio return, benchmark context, and contribution once the book is valued.",
        "Confirm funded positions, valuations, and portfolio weights before client review.",
        "Inspect recent funding, trading, and cash activity affecting the book.",
    ]
    assert [action.target for action in response.actions] == [
        "Target: Performance workflow for this portfolio",
        "Target: Holdings workflow for this portfolio",
        "Target: Transactions workflow for this portfolio",
    ]
    assert [action.href for action in response.actions] == [
        "/performance?portfolioId=PF_1001",
        "/portfolio?portfolioId=PF_1001#portfolio-drilldown",
        "/portfolio?portfolioId=PF_1001#portfolio-drilldown",
    ]
    assert [action.cta_label for action in response.actions] == [
        "Performance",
        "Holdings",
        "Transactions",
    ]
    assert [action.recommended for action in response.actions] == [True, False, False]


def test_build_workflow_actions_dedupes_and_ignores_unsupported_cues():
    service = PortfolioService(_StubLotusCoreQueryClient())

    actions = service._build_workflow_actions(
        portfolio_id="PF_1001",
        summary=PortfolioSummary(
            assets_under_management_base=1000.0,
            invested_market_value_base=900.0,
            cash_market_value_base=100.0,
            cash_weight_pct=10.0,
            position_count=2,
            cash_balance_count=1,
        ),
        operations=None,
        workflow_cues=[
            PortfolioWorkflowLaunchCue(
                key="holdings",
                label="Holdings",
                href="/portfolio?portfolioId=PF_1001#portfolio-drilldown",
            ),
            PortfolioWorkflowLaunchCue(
                key="custom",
                label="Custom",
                href="/custom",
            ),
            PortfolioWorkflowLaunchCue(
                key="performance",
                label="Performance",
                href="/performance?portfolioId=PF_1001",
            ),
            PortfolioWorkflowLaunchCue(
                key="holdings",
                label="Holdings",
                href="/portfolio?portfolioId=PF_1001#portfolio-drilldown",
            ),
        ],
        transaction_total=3,
    )

    assert [action.title for action in actions] == [
        "Review performance",
        "Review holdings",
    ]
    assert [action.cta_label for action in actions] == [
        "Performance",
        "Holdings",
    ]
    assert actions[0].recommended is True


def test_build_workflow_actions_returns_empty_portfolio_setup_sequence():
    service = PortfolioService(_StubLotusCoreQueryClient())

    actions = service._build_workflow_actions(
        portfolio_id="PF_EMPTY",
        summary=PortfolioSummary(
            assets_under_management_base=0.0,
            invested_market_value_base=0.0,
            cash_market_value_base=0.0,
            cash_weight_pct=0.0,
            position_count=0,
            cash_balance_count=0,
        ),
        operations=None,
        workflow_cues=[],
        transaction_total=0,
    )

    assert [action.title for action in actions] == [
        "Fund portfolio",
        "Book first trade",
        "Publish pricing",
        "Review holdings",
        "Open performance",
    ]
    assert [action.sequence for action in actions] == [1, 2, 3, 4, 5]
    assert [action.target for action in actions] == [
        "Target: cash funding and opening balance setup",
        "Target: transaction entry and execution workflow",
        "Target: pricing publication and valuation refresh",
        "Target: holdings and allocation review",
        "Target: performance workspace after valuation is available",
    ]
    assert actions[0].recommended is True
    assert actions[0].href == "/workbench?portfolioId=PF_EMPTY"
    assert actions[-1].href == "/performance?portfolioId=PF_EMPTY"


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
async def test_portfolio_book_passes_include_projected_to_positions():
    class _ProjectedAwareClient(_StubLotusCoreQueryClient):
        def __init__(self):
            self.last_include_projected: bool | None = None

        async def get_portfolio_positions(self, portfolio_id: str, correlation_id: str, **kwargs):
            self.last_include_projected = kwargs.get("include_projected")
            return await super().get_portfolio_positions(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                **kwargs,
            )

    client = _ProjectedAwareClient()
    service = PortfolioService(client)

    await service.get_portfolio_book(
        portfolio_id="PF_1001",
        correlation_id="corr-3-projected",
        as_of_date="2026-03-27",
        include_projected=True,
    )

    assert client.last_include_projected is True


@pytest.mark.asyncio
async def test_portfolio_book_does_not_require_cashflow_projection():
    class _BookClient(_StubLotusCoreQueryClient):
        async def get_cashflow_projection(self, portfolio_id: str, correlation_id: str, **kwargs):
            raise AssertionError("book endpoint should not request projected cashflow")

    service = PortfolioService(_BookClient())
    response = await service.get_portfolio_book(
        portfolio_id="PF_1001",
        correlation_id="corr-3-book",
        as_of_date="2026-03-27",
        include_projected=False,
    )

    assert response.cash_balances[0].security_id == "CASH_USD"
    assert response.summary.assets_under_management_base == 1000.0


@pytest.mark.asyncio
async def test_portfolio_liquidity_returns_cash_and_cashflow():
    class _LiquidityCaptureClient(_StubLotusCoreQueryClient):
        def __init__(self):
            self.cashflow_kwargs: dict[str, object] | None = None

        async def get_cashflow_projection(self, portfolio_id: str, correlation_id: str, **kwargs):
            self.cashflow_kwargs = kwargs
            return await super().get_cashflow_projection(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                **kwargs,
            )

    client = _LiquidityCaptureClient()
    service = PortfolioService(client)
    response = await service.get_portfolio_liquidity(
        portfolio_id="PF_1001",
        correlation_id="corr-3b",
        as_of_date="2026-03-27",
    )
    assert response.summary.cash_market_value_base == 100.0
    assert response.cash_balances[0].security_id == "CASH_USD"
    assert response.cashflow_outlook is not None
    assert response.cashflow_outlook.upcoming_points[0].projection_date == "2026-03-28"
    assert client.cashflow_kwargs == {
        "as_of_date": "2026-03-27",
        "include_projected": True,
        "horizon_days": 10,
    }


@pytest.mark.asyncio
async def test_portfolio_liquidity_preserves_cashflow_partial_failure():
    class _LiquidityAwareClient(_StubLotusCoreQueryClient):
        def __init__(self):
            self.aum_reporting_currency: str | None = None
            self.cash_reporting_currency: str | None = None

        async def query_assets_under_management(self, **kwargs):
            self.aum_reporting_currency = kwargs.get("reporting_currency")
            return await super().query_assets_under_management(**kwargs)

        async def get_portfolio_cash_balances(self, **kwargs):
            self.cash_reporting_currency = kwargs.get("reporting_currency")
            return await super().get_portfolio_cash_balances(**kwargs)

        async def get_cashflow_projection(self, portfolio_id: str, correlation_id: str, **kwargs):
            return 503, {"detail": "cashflow temporarily unavailable"}

    client = _LiquidityAwareClient()
    service = PortfolioService(client)
    response = await service.get_portfolio_liquidity(
        portfolio_id="PF_1001",
        correlation_id="corr-3b-ccy",
        as_of_date="2026-03-27",
        reporting_currency="SGD",
    )

    assert client.aum_reporting_currency == "SGD"
    assert client.cash_reporting_currency == "SGD"
    assert response.cashflow_outlook is None
    assert "PORTFOLIO_CASHFLOW_UNAVAILABLE" in response.warnings
    assert response.partial_failures[0].error_code == "PORTFOLIO_CASHFLOW_UNAVAILABLE"
    assert response.partial_failures[0].detail == "cashflow temporarily unavailable"


@pytest.mark.asyncio
async def test_portfolio_projected_cashflow_returns_requested_horizon():
    class _CashflowAwareClient(_StubLotusCoreQueryClient):
        def __init__(self):
            self.last_kwargs = None

        async def get_cashflow_projection(self, portfolio_id: str, correlation_id: str, **kwargs):
            self.last_kwargs = kwargs
            horizon_days = int(kwargs["horizon_days"])
            return 200, {
                "as_of_date": "2026-03-27",
                "range_end_date": "2026-04-26",
                "total_net_cashflow": -25.0,
                "projection_days": horizon_days,
                "include_projected": bool(kwargs["include_projected"]),
                "points": [
                    {
                        "projection_date": "2026-03-28",
                        "net_cashflow": -25.0,
                        "projected_cumulative_cashflow": -25.0,
                    }
                ],
            }

    client = _CashflowAwareClient()
    service = PortfolioService(client)
    response = await service.get_portfolio_projected_cashflow(
        portfolio_id="PF_1001",
        correlation_id="corr-3b2",
        as_of_date="2026-03-27",
        horizon_days=30,
        include_projected=True,
    )

    assert client.last_kwargs is not None
    assert client.last_kwargs["horizon_days"] == 30
    assert response.cashflow_outlook is not None
    assert response.cashflow_outlook.projection_days == 30
    assert response.cashflow_outlook.include_projected is True
    assert response.cashflow_outlook.upcoming_points[0].projection_date == "2026-03-28"


@pytest.mark.asyncio
async def test_portfolio_projected_cashflow_preserves_partial_failure() -> None:
    class _UnavailableCashflowClient(_StubLotusCoreQueryClient):
        async def get_cashflow_projection(self, portfolio_id: str, correlation_id: str, **kwargs):
            return 503, {"detail": "cashflow temporarily unavailable"}

    service = PortfolioService(_UnavailableCashflowClient())
    response = await service.get_portfolio_projected_cashflow(
        portfolio_id="PF_1001",
        correlation_id="corr-3b3",
        as_of_date="2026-03-27",
        horizon_days=30,
        include_projected=True,
    )

    assert response.cashflow_outlook is None
    assert "PORTFOLIO_CASHFLOW_UNAVAILABLE" in response.warnings
    assert response.partial_failures[0].error_code == "PORTFOLIO_CASHFLOW_UNAVAILABLE"
    assert response.partial_failures[0].detail == "cashflow temporarily unavailable"


@pytest.mark.asyncio
async def test_portfolio_allocations_return_dimension_views():
    service = PortfolioService(_StubLotusCoreQueryClient())
    response = await service.get_portfolio_allocations(
        portfolio_id="PF_1001",
        correlation_id="corr-3c",
        as_of_date="2026-03-27",
    )
    assert response.summary.assets_under_management_base == 1000.0
    assert response.summary.cash_market_value_base == 100.0
    assert response.summary.cash_balance_count == 1
    assert response.views[0].dimension == "asset_class"
    assert response.views[0].buckets[0].bucket == "Equity"


@pytest.mark.asyncio
async def test_portfolio_allocations_pass_reporting_currency_and_look_through_mode():
    class _AllocationAwareClient(_StubLotusCoreQueryClient):
        def __init__(self):
            self.last_reporting_currency: str | None = None
            self.last_look_through_mode: str | None = None

        async def query_asset_allocation(self, **kwargs):
            self.last_reporting_currency = kwargs.get("reporting_currency")
            self.last_look_through_mode = kwargs.get("look_through_mode")
            return 200, {
                "reporting_currency": "SGD",
                "look_through": {
                    "requested_mode": "full",
                    "effective_mode": "direct_only",
                    "applied": False,
                },
                "views": [
                    {
                        "dimension": "region",
                        "buckets": [
                            {
                                "dimension_value": "Asia",
                                "market_value_reporting_currency": 700.0,
                                "weight": 0.7,
                                "position_count": 1,
                            }
                        ],
                    }
                ],
            }

    client = _AllocationAwareClient()
    service = PortfolioService(client)
    response = await service.get_portfolio_allocations(
        portfolio_id="PF_1001",
        correlation_id="corr-3c-lookthrough",
        as_of_date="2026-03-27",
        reporting_currency="SGD",
        look_through_mode="full",
    )

    assert client.last_reporting_currency == "SGD"
    assert client.last_look_through_mode == "full"
    assert response.reporting_currency == "SGD"
    assert response.look_through is not None
    assert response.look_through.requested_mode == "full"
    assert response.look_through.effective_mode == "direct_only"
    assert response.views[0].dimension == "region"


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
    assert response.summary.cash_market_value_base == 100.0
    assert response.summary.cash_balance_count == 1
    assert response.positions[0].security_id == "EQ_1"
    assert response.top_positions[0].security_id == "EQ_1"
    assert response.positions[0].market_value_base == 700.0
    assert response.positions[0].market_value_local is None


@pytest.mark.asyncio
async def test_portfolio_positions_pass_reporting_currency_and_include_projected():
    class _PositionsAwareClient(_StubLotusCoreQueryClient):
        def __init__(self):
            self.last_reporting_currency: str | None = None
            self.last_include_projected: bool | None = None
            self.get_portfolio_cash_balances_called = False

        async def get_portfolio_positions(self, portfolio_id: str, correlation_id: str, **kwargs):
            self.last_reporting_currency = kwargs.get("reporting_currency")
            self.last_include_projected = kwargs.get("include_projected")
            return await super().get_portfolio_positions(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                **kwargs,
            )

        async def get_portfolio_cash_balances(self, **kwargs):
            self.get_portfolio_cash_balances_called = True
            return await super().get_portfolio_cash_balances(**kwargs)

    client = _PositionsAwareClient()
    service = PortfolioService(client)
    await service.get_portfolio_positions(
        portfolio_id="PF_1001",
        correlation_id="corr-3d-ccy",
        as_of_date="2026-03-27",
        include_projected=True,
        reporting_currency="SGD",
    )

    assert client.last_include_projected is True
    assert client.last_reporting_currency == "SGD"
    assert client.get_portfolio_cash_balances_called is False


@pytest.mark.asyncio
async def test_portfolio_allocations_use_positions_not_deprecated_cash_balances():
    class _HoldingsAwareClient(_StubLotusCoreQueryClient):
        def __init__(self):
            self.get_portfolio_cash_balances_called = False
            self.positions_calls = 0

        async def get_portfolio_cash_balances(self, **kwargs):
            self.get_portfolio_cash_balances_called = True
            return await super().get_portfolio_cash_balances(**kwargs)

        async def get_portfolio_positions(self, portfolio_id: str, correlation_id: str, **kwargs):
            self.positions_calls += 1
            return await super().get_portfolio_positions(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                **kwargs,
            )

    client = _HoldingsAwareClient()
    service = PortfolioService(client)

    response = await service.get_portfolio_allocations(
        portfolio_id="PF_1001",
        correlation_id="corr-3c-positions-only",
        as_of_date="2026-03-27",
    )

    assert response.summary.cash_market_value_base == 100.0
    assert client.positions_calls == 1
    assert client.get_portfolio_cash_balances_called is False


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
    assert response.total == 7
    assert response.skip == 20
    assert response.limit == 25
    assert response.transactions == []


@pytest.mark.asyncio
async def test_transaction_ledger_preserves_group_and_fx_identifiers():
    service = PortfolioService(_StubLotusCoreQueryClient())
    response = await service.get_transaction_ledger(
        portfolio_id="PF_1001",
        correlation_id="corr-4-fx",
        as_of_date="2026-03-27",
        include_projected=False,
        skip=0,
        limit=10,
    )

    row = response.transactions[0]
    assert row.component_type == "FX_CONTRACT_OPEN"
    assert row.instrument_id == "INST_EQ_1"
    assert row.linked_transaction_group_id == "LTG-FX-2026-0001"
    assert row.fx_contract_id == "FXC-2026-0001"
    assert row.swap_event_id == "FXSWAP-2026-0001"
    assert row.near_leg_group_id == "FXSWAP-2026-0001-NEAR"
    assert row.far_leg_group_id == "FXSWAP-2026-0001-FAR"


@pytest.mark.asyncio
async def test_transaction_ledger_passes_transaction_filters_upstream():
    class _FilterAwareClient(_StubLotusCoreQueryClient):
        def __init__(self):
            self.last_kwargs = None

        async def get_portfolio_transactions(
            self, portfolio_id: str, correlation_id: str, **kwargs
        ):
            self.last_kwargs = kwargs
            return await super().get_portfolio_transactions(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                **kwargs,
            )

    client = _FilterAwareClient()
    service = PortfolioService(client)

    await service.get_transaction_ledger(
        portfolio_id="PF_1001",
        correlation_id="corr-4b",
        as_of_date="2026-03-27",
        include_projected=False,
        skip=0,
        limit=100,
        transaction_type="FX_FORWARD",
        instrument_id="INST_EQ_1",
        component_type="FX_CONTRACT_OPEN",
        linked_transaction_group_id="LTG-FX-2026-0001",
        fx_contract_id="FXC-2026-0001",
        swap_event_id="FXSWAP-2026-0001",
        near_leg_group_id="FXSWAP-2026-0001-NEAR",
        far_leg_group_id="FXSWAP-2026-0001-FAR",
        sort_by="settlement_date",
        sort_order="asc",
        start_date="2026-03-01",
        end_date="2026-03-27",
    )

    assert client.last_kwargs is not None
    assert client.last_kwargs["transaction_type"] == "FX_FORWARD"
    assert client.last_kwargs["instrument_id"] == "INST_EQ_1"
    assert client.last_kwargs["component_type"] == "FX_CONTRACT_OPEN"
    assert client.last_kwargs["linked_transaction_group_id"] == "LTG-FX-2026-0001"
    assert client.last_kwargs["fx_contract_id"] == "FXC-2026-0001"
    assert client.last_kwargs["swap_event_id"] == "FXSWAP-2026-0001"
    assert client.last_kwargs["near_leg_group_id"] == "FXSWAP-2026-0001-NEAR"
    assert client.last_kwargs["far_leg_group_id"] == "FXSWAP-2026-0001-FAR"
    assert client.last_kwargs["sort_by"] == "settlement_date"
    assert client.last_kwargs["sort_order"] == "asc"
    assert client.last_kwargs["start_date"] == "2026-03-01"
    assert client.last_kwargs["end_date"] == "2026-03-27"


@pytest.mark.asyncio
async def test_transaction_ledger_passes_security_and_projection_filters_upstream():
    class _FilterAwareClient(_StubLotusCoreQueryClient):
        def __init__(self):
            self.last_kwargs = None

        async def get_portfolio_transactions(
            self, portfolio_id: str, correlation_id: str, **kwargs
        ):
            self.last_kwargs = kwargs
            return await super().get_portfolio_transactions(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                **kwargs,
            )

    client = _FilterAwareClient()
    service = PortfolioService(client)

    response = await service.get_transaction_ledger(
        portfolio_id="PF_1001",
        correlation_id="corr-4c",
        as_of_date="2026-03-27",
        include_projected=True,
        skip=0,
        limit=10,
        security_id="EQ_1",
    )

    assert client.last_kwargs is not None
    assert client.last_kwargs["include_projected"] is True
    assert client.last_kwargs["security_id"] == "EQ_1"
    assert response.include_projected is True


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
async def test_income_summary_passes_reporting_currency_and_uses_as_of_date_as_default_end():
    class _IncomeAwareClient(_StubLotusCoreQueryClient):
        def __init__(self):
            self.last_kwargs = None

        async def get_portfolio_transactions(
            self, portfolio_id: str, correlation_id: str, **kwargs
        ):
            self.last_kwargs = kwargs
            return await super().get_portfolio_transactions(
                portfolio_id,
                correlation_id,
                **kwargs,
            )

    client = _IncomeAwareClient()
    service = PortfolioService(client)
    response = await service.get_income_summary(
        portfolio_id="PF_1001",
        correlation_id="corr-5b",
        as_of_date="2026-03-27",
        reporting_currency="SGD",
    )

    assert client.last_kwargs is not None
    assert client.last_kwargs["reporting_currency"] == "SGD"
    assert client.last_kwargs["end_date"] == "2026-03-27"
    assert response.window_end_date == "2026-03-27"


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


@pytest.mark.asyncio
async def test_activity_summary_passes_reporting_currency_and_uses_as_of_date_as_default_end():
    class _ActivityAwareClient(_StubLotusCoreQueryClient):
        def __init__(self):
            self.last_kwargs = None

        async def get_portfolio_transactions(
            self, portfolio_id: str, correlation_id: str, **kwargs
        ):
            self.last_kwargs = kwargs
            return await super().get_portfolio_transactions(
                portfolio_id,
                correlation_id,
                **kwargs,
            )

    client = _ActivityAwareClient()
    service = PortfolioService(client)
    response = await service.get_activity_summary(
        portfolio_id="PF_1001",
        correlation_id="corr-6b",
        as_of_date="2026-03-27",
        reporting_currency="SGD",
    )

    assert client.last_kwargs is not None
    assert client.last_kwargs["reporting_currency"] == "SGD"
    assert client.last_kwargs["end_date"] == "2026-03-27"
    assert response.window_end_date == "2026-03-27"


@pytest.mark.asyncio
async def test_portfolio_service_reuses_cached_upstream_results_across_modules():
    client = _CountingLotusCoreQueryClient()
    service = PortfolioService(client, upstream_cache_ttl_seconds=60.0)

    await service.get_portfolio_workspace(
        portfolio_id="PF_1001",
        correlation_id="corr-cache-1",
        as_of_date="2026-03-27",
    )
    await service.get_portfolio_readiness(
        portfolio_id="PF_1001",
        correlation_id="corr-cache-2",
        as_of_date="2026-03-27",
    )
    await service.get_portfolio_insights(
        portfolio_id="PF_1001",
        correlation_id="corr-cache-3",
        as_of_date="2026-03-27",
    )
    await service.get_portfolio_workflow(
        portfolio_id="PF_1001",
        correlation_id="corr-cache-4",
        as_of_date="2026-03-27",
    )

    assert client.calls["get_portfolio"] == 1
    assert client.calls["query_assets_under_management"] == 1
    assert client.calls["get_support_overview"] == 1
    assert client.calls["get_cashflow_projection"] == 1
    assert client.calls["get_portfolio_cash_balances"] == 1
    assert client.calls["get_portfolio_positions"] == 1
    assert client.calls["query_asset_allocation"] == 1
    assert client.calls["get_portfolio_transactions"] == 2


@pytest.mark.asyncio
async def test_portfolio_service_reuses_support_overview_cache_across_workspace_as_of_dates():
    class _SupportAwareClient(_CountingLotusCoreQueryClient):
        def __init__(self):
            super().__init__()
            self.support_requests: list[tuple[str, str]] = []

        async def get_support_overview(self, portfolio_id: str, correlation_id: str):
            self.support_requests.append((portfolio_id, correlation_id))
            return await super().get_support_overview(portfolio_id, correlation_id)

    client = _SupportAwareClient()
    service = PortfolioService(client, upstream_cache_ttl_seconds=60.0)

    await service.get_portfolio_workspace(
        portfolio_id="PF_1001",
        correlation_id="corr-support-1",
        as_of_date="2026-03-27",
    )
    await service.get_portfolio_workspace(
        portfolio_id="PF_1001",
        correlation_id="corr-support-2",
        as_of_date="2026-03-27",
    )
    await service.get_portfolio_workspace(
        portfolio_id="PF_1001",
        correlation_id="corr-support-3",
        as_of_date="2026-03-28",
    )

    assert client.calls["get_support_overview"] == 1
    assert client.support_requests == [("PF_1001", "corr-support-1")]


@pytest.mark.asyncio
async def test_portfolio_readiness_surfaces_upstream_client_errors() -> None:
    class _InvalidReadinessClient(_StubLotusCoreQueryClient):
        async def get_portfolio_readiness(self, portfolio_id: str, correlation_id: str, **kwargs):
            return 400, {"detail": "as_of_date must be YYYY-MM-DD"}

    service = PortfolioService(_InvalidReadinessClient())

    with pytest.raises(HTTPException) as exc_info:
        await service.get_portfolio_readiness(
            portfolio_id="PF_1001",
            correlation_id="corr-400",
            as_of_date="bad-date",
        )

    assert exc_info.value.status_code == 400
    assert "readiness rejected the request" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_portfolio_workspace_preserves_support_overview_partial_failure() -> None:
    class _InvalidSupportOverviewClient(_StubLotusCoreQueryClient):
        async def get_support_overview(self, portfolio_id: str, correlation_id: str):
            _ = portfolio_id, correlation_id
            return 503, {"detail": "support overview unavailable"}

    service = PortfolioService(_InvalidSupportOverviewClient())
    response = await service.get_portfolio_workspace(
        portfolio_id="PF_1001",
        correlation_id="corr-400",
        as_of_date="bad-date",
    )

    assert response.operations is None
    assert "PORTFOLIO_SUPPORT_OVERVIEW_UNAVAILABLE" in response.warnings
    assert response.partial_failures[0].error_code == "PORTFOLIO_SUPPORT_OVERVIEW_UNAVAILABLE"
    assert response.partial_failures[0].detail == "support overview unavailable"
