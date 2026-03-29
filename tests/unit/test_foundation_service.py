import pytest

from app.services.foundation_service import FoundationService


class _StubPasClient:
    def __init__(self, list_payload: dict, snapshot_payload: dict):
        self.list_payload = list_payload
        self.snapshot_payload = snapshot_payload

    async def list_portfolios(self, correlation_id: str):
        return 200, self.list_payload

    async def get_core_snapshot(
        self,
        portfolio_id: str,
        as_of_date: str,
        include_sections: list[str],
        consumer_system: str,
        correlation_id: str,
    ):
        return 200, self.snapshot_payload


class _StubPaClient:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self.payload = payload

    async def get_pas_input_twr(
        self,
        portfolio_id: str,
        as_of_date: str,
        periods: list[str],
        consumer_system: str,
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
        pas_client=_StubPasClient(
            list_payload={
                "items": [
                    {
                        "portfolio_id": "PF_2002",
                        "portfolio_name": "Income",
                        "base_currency": "EUR",
                    },
                    {
                        "portfolio_id": "PF_1001",
                        "portfolio_name": "Alpha Growth",
                        "base_currency": "USD",
                    },
                ]
            },
            snapshot_payload={},
        ),
        pa_client=_StubPaClient(200, {}),
        dpm_client=_StubDpmClient(200, {}),
        reporting_client=_StubReportingClient(200, {}),
    )

    response = await service.get_portfolio_catalog(correlation_id="corr-1")

    assert [item.portfolio_id for item in response.items] == ["PF_1001", "PF_2002"]
    assert response.items[0].display_name == "Alpha Growth"


@pytest.mark.asyncio
async def test_foundation_workspace_success():
    service = FoundationService(
        pas_client=_StubPasClient(
            list_payload={"items": []},
            snapshot_payload={
                "portfolio": {
                    "portfolio_id": "PF_1001",
                    "portfolio_name": "Alpha Growth",
                    "base_currency": "USD",
                    "booking_center": "SG",
                    "cif_id": "CIF_1001",
                },
                "snapshot": {
                    "as_of_date": "2026-03-25",
                    "overview": {"total_market_value": 1000.0, "total_cash": 100.0},
                    "holdings": {
                        "holdingsByAssetClass": {
                            "Equity": [
                                {"instrument_id": "EQ_1", "valuation": {"market_value_base": 700.0}}
                            ],
                            "Cash": [
                                {
                                    "instrument_id": "CASH_1",
                                    "valuation": {"market_value_base": 100.0},
                                }
                            ],
                        }
                    },
                },
            },
        ),
        pa_client=_StubPaClient(200, {"resultsByPeriod": {"YTD": {"net_cumulative_return": 4.3}}}),
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

    assert response.portfolio.display_name == "Alpha Growth"
    assert response.summary.cash_weight_pct == 10.0
    assert response.allocations[0].asset_class == "Cash"
    assert response.performance is not None
    assert response.performance.return_pct == 4.3
    assert response.rebalance is not None
    assert response.rebalance.status == "READY"
    assert response.readiness.reporting.status == "READY"
    assert response.partial_failures == []


@pytest.mark.asyncio
async def test_foundation_workspace_degrades_when_optional_upstreams_fail():
    service = FoundationService(
        pas_client=_StubPasClient(
            list_payload={"items": []},
            snapshot_payload={
                "portfolio": {"portfolio_id": "PF_1001", "base_currency": "USD"},
                "snapshot": {
                    "as_of_date": "2026-03-25",
                    "overview": {"total_market_value": 500.0, "total_cash": 50.0},
                    "holdings": {"holdingsByAssetClass": {"Equity": [{"instrument_id": "EQ_1"}]}},
                },
            },
        ),
        pa_client=_StubPaClient(503, {"detail": "pa unavailable"}),
        dpm_client=_StubDpmClient(500, {"detail": "dpm unavailable"}),
        reporting_client=_StubReportingClient(503, {"detail": "reporting unavailable"}),
    )

    response = await service.get_portfolio_workspace(
        portfolio_id="PF_1001",
        correlation_id="corr-3",
    )

    assert response.performance is None
    assert response.rebalance is None
    assert response.readiness.reporting.status == "UNAVAILABLE"
    assert response.warnings == [
        "FOUNDATION_PERFORMANCE_UNAVAILABLE",
        "FOUNDATION_REBALANCE_UNAVAILABLE",
        "FOUNDATION_REPORTING_UNAVAILABLE",
    ]
    assert len(response.partial_failures) == 3
