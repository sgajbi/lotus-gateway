import pytest

from app.services.foundation_service import FoundationService


class _StubLotusCoreQueryClient:
    def __init__(
        self,
        *,
        list_payload: dict,
        portfolio_payload: dict,
        positions_payload: dict,
        overview_payload: dict,
        transactions_result: tuple[int, dict],
        cashflow_result: tuple[int, dict],
    ):
        self.list_payload = list_payload
        self.portfolio_payload = portfolio_payload
        self.positions_payload = positions_payload
        self.overview_payload = overview_payload
        self.transactions_result = transactions_result
        self.cashflow_result = cashflow_result

    async def list_portfolios(self, correlation_id: str):
        return 200, self.list_payload

    async def get_portfolio(self, portfolio_id: str, correlation_id: str):
        return 200, self.portfolio_payload

    async def get_portfolio_positions(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None = None,
        include_projected: bool = False,
    ):
        return 200, self.positions_payload

    async def get_core_snapshot(
        self,
        portfolio_id: str,
        as_of_date: str,
        sections: list[str],
        consumer_system: str,
        correlation_id: str,
    ):
        return 200, self.overview_payload

    async def get_portfolio_transactions(
        self,
        portfolio_id: str,
        correlation_id: str,
        **kwargs,
    ):
        return self.transactions_result

    async def get_cashflow_projection(
        self,
        portfolio_id: str,
        correlation_id: str,
        **kwargs,
    ):
        return self.cashflow_result


class _StubLotusAnalyticsClient:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self.payload = payload

    async def get_stateful_twr(
        self,
        portfolio_id: str,
        report_end_date: str,
        period: str,
        correlation_id: str,
    ):
        return self.status_code, self.payload


class _StubDpmClient:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self.payload = payload

    async def list_runs(self, params: dict, correlation_id: str):
        return self.status_code, self.payload


class _StubReportingClient:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self.payload = payload

    async def get_portfolio_snapshot(self, portfolio_id: str, as_of_date: str, correlation_id: str):
        return self.status_code, self.payload


@pytest.mark.asyncio
async def test_foundation_portfolio_catalog_success():
    service = FoundationService(
        lotus_core_query_client=_StubLotusCoreQueryClient(
            list_payload={
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
            },
            portfolio_payload={},
            positions_payload={},
            overview_payload={},
            transactions_result=(200, {"transactions": []}),
            cashflow_result=(200, {"points": []}),
        ),
        analytics_client=_StubLotusAnalyticsClient(200, {}),
        dpm_client=_StubDpmClient(200, {}),
        reporting_client=_StubReportingClient(200, {}),
    )

    response = await service.get_portfolio_catalog(correlation_id="corr-1")

    assert [item.portfolio_id for item in response.items] == ["PF_1001", "PF_2002"]
    assert response.items[0].display_name == "PF_1001"


@pytest.mark.asyncio
async def test_foundation_workspace_success():
    service = FoundationService(
        lotus_core_query_client=_StubLotusCoreQueryClient(
            list_payload={"portfolios": []},
            portfolio_payload={
                "portfolio_id": "PF_1001",
                "base_currency": "USD",
                "booking_center_code": "SG",
                "client_id": "CIF_1001",
                "status": "ACTIVE",
                "portfolio_type": "ADVISORY",
                "risk_exposure": "MODERATE",
                "investment_time_horizon": "LONG_TERM",
                "objective": "GROWTH",
                "is_leverage_allowed": False,
            },
            positions_payload={
                "positions": [
                    {
                        "security_id": "EQ_1",
                        "instrument_name": "Equity 1",
                        "asset_class": "Equity",
                        "quantity": 10,
                        "cost_basis": 500.0,
                        "valuation": {"market_value_base": 700.0},
                        "weight": 0.70,
                    },
                    {
                        "security_id": "FI_1",
                        "instrument_name": "Bond 1",
                        "asset_class": "Fixed Income",
                        "quantity": 4,
                        "cost_basis": 250.0,
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
            },
            overview_payload={
                "as_of_date": "2026-03-25",
                "sections": {
                    "portfolio_totals": {"baseline_total_market_value_base": 1000.0},
                    "positions_baseline": [],
                    "instrument_enrichment": [],
                },
            },
            transactions_result=(
                200,
                {
                    "transactions": [
                        {
                            "transaction_id": "TX_1",
                            "transaction_date": "2026-03-24T08:00:00Z",
                            "transaction_type": "BUY",
                            "security_id": "EQ_1",
                            "instrument_id": "EQ_1",
                            "quantity": 10,
                            "price": 70.0,
                            "gross_transaction_amount": 700.0,
                            "currency": "USD",
                            "net_cost": 700.0,
                        }
                    ]
                },
            ),
            cashflow_result=(
                200,
                {
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
                },
            ),
        ),
        analytics_client=_StubLotusAnalyticsClient(
            200,
            {
                "results_by_period": {
                    "YTD": {"portfolio": {"summary": {"period_return": {"base": 4.3}}}}
                }
            },
        ),
        dpm_client=_StubDpmClient(
            200,
            {
                "items": [
                    {
                        "rebalance_run_id": "rr_1",
                        "status": "READY",
                        "created_at": "2026-03-25T08:00:00Z",
                    }
                ]
            },
        ),
        reporting_client=_StubReportingClient(
            200,
            {
                "generatedAt": "2026-03-25T09:00:00Z",
                "rows": [{"metric": "market_value_base"}],
            },
        ),
    )

    response = await service.get_portfolio_workspace(
        portfolio_id="PF_1001",
        correlation_id="corr-2",
    )

    assert response.portfolio.display_name == "PF_1001"
    assert response.profile.status == "ACTIVE"
    assert response.summary.cash_weight_pct == 10.0
    assert {bucket.asset_class for bucket in response.allocations} == {
        "Cash",
        "Equity",
        "Fixed Income",
    }
    assert response.top_positions[0].security_id == "EQ_1"
    assert response.positions[0].instrument_name == "Equity 1"
    assert response.recent_transactions[0].transaction_id == "TX_1"
    assert response.cashflow_outlook is not None
    assert response.cashflow_outlook.total_net_cashflow_base == -25.0
    assert response.performance is not None
    assert response.performance.return_pct == 4.3
    assert response.rebalance is not None
    assert response.rebalance.status == "READY"
    assert response.readiness.reporting.status == "READY"
    assert response.partial_failures == []


@pytest.mark.asyncio
async def test_foundation_workspace_degrades_when_optional_upstreams_fail():
    service = FoundationService(
        lotus_core_query_client=_StubLotusCoreQueryClient(
            list_payload={"portfolios": []},
            portfolio_payload={
                "portfolio_id": "PF_1001",
                "base_currency": "USD",
                "booking_center_code": "SG",
                "client_id": "CIF_1001",
            },
            positions_payload={
                "positions": [
                    {
                        "security_id": "EQ_1",
                        "instrument_name": "Equity 1",
                        "asset_class": "Equity",
                        "quantity": 5,
                    }
                ]
            },
            overview_payload={
                "as_of_date": "2026-03-25",
                "sections": {
                    "portfolio_totals": {"baseline_total_market_value_base": 500.0},
                    "positions_baseline": [],
                    "instrument_enrichment": [],
                },
            },
            transactions_result=(503, {"detail": "transactions unavailable"}),
            cashflow_result=(503, {"detail": "cashflow unavailable"}),
        ),
        analytics_client=_StubLotusAnalyticsClient(
            503, {"detail": "lotus-performance unavailable"}
        ),
        dpm_client=_StubDpmClient(500, {"detail": "dpm unavailable"}),
        reporting_client=_StubReportingClient(503, {"detail": "reporting unavailable"}),
    )

    response = await service.get_portfolio_workspace(
        portfolio_id="PF_1001",
        correlation_id="corr-3",
    )

    assert response.performance is None
    assert response.rebalance is None
    assert response.recent_transactions == []
    assert response.cashflow_outlook is None
    assert response.readiness.reporting.status == "UNAVAILABLE"
    assert response.top_positions[0].security_id == "EQ_1"
    assert response.warnings == [
        "FOUNDATION_TRANSACTIONS_UNAVAILABLE",
        "FOUNDATION_CASHFLOW_UNAVAILABLE",
        "FOUNDATION_PERFORMANCE_UNAVAILABLE",
        "FOUNDATION_REBALANCE_UNAVAILABLE",
        "FOUNDATION_REPORTING_UNAVAILABLE",
    ]
    assert len(response.partial_failures) == 5
