import pytest

from app.contracts.workbench import (
    WorkbenchOverviewResponse,
    WorkbenchOverviewSummary,
    WorkbenchPartialFailure,
    WorkbenchPortfolioSummary,
)
from app.services.performance_workspace_service import PerformanceWorkspaceService


class _StubWorkbenchService:
    async def get_workbench_overview(self, portfolio_id: str, correlation_id: str):  # noqa: ARG002
        return WorkbenchOverviewResponse(
            correlation_id=correlation_id,
            contract_version="v1",
            as_of_date="2026-03-27",
            portfolio=WorkbenchPortfolioSummary(
                portfolio_id=portfolio_id,
                client_id="CIF_1001",
                base_currency="USD",
                booking_center_code="SG",
            ),
            overview=WorkbenchOverviewSummary(
                market_value_base=508_870.0,
                cash_weight_pct=46.25,
                position_count=3,
            ),
            warnings=["FOUNDATION_WARNING"],
            partial_failures=[
                WorkbenchPartialFailure(
                    source_service="lotus-core",
                    error_code="STALE_REPORTING",
                    detail="reporting snapshot is older than expected",
                )
            ],
        )


class _StubAnalyticsClient:
    def __init__(self):
        self.workspace_summary_calls: list[dict[str, object]] = []

    async def get_workspace_summary(self, **kwargs):
        self.workspace_summary_calls.append(kwargs)
        return 200, _workspace_summary_payload()


class _StubLotusCoreQueryClient:
    def __init__(self):
        self.reference_calls = 0
        self.benchmark_catalog_calls: list[dict[str, object]] = []

    async def get_portfolio_analytics_reference(
        self,
        portfolio_id: str,
        as_of_date: str,
        consumer_system: str,
        correlation_id: str,
    ):  # noqa: ARG002
        self.reference_calls += 1
        return 200, {"performance_end_date": "2026-03-27"}

    async def get_benchmark_catalog(self, **kwargs):
        self.benchmark_catalog_calls.append(kwargs)
        return (
            200,
            {
                "records": [
                    {
                        "benchmark_id": "BMK_GLOBAL_BALANCED_60_40",
                        "benchmark_name": "Global Balanced 60/40",
                        "benchmark_currency": "USD",
                        "benchmark_type": "composite",
                        "benchmark_family": "Balanced",
                        "benchmark_provider": "Lotus",
                    },
                    {
                        "benchmark_id": "BMK_GLOBAL_GROWTH_80_20",
                        "benchmark_name": "Global Growth 80/20",
                        "benchmark_currency": "USD",
                        "benchmark_type": "composite",
                        "benchmark_family": "Growth",
                        "benchmark_provider": "Lotus",
                    },
                ]
            },
        )


def _workspace_summary_payload() -> dict:
    return {
        "results_by_period": {
            "YTD": {
                "benchmark": {
                    "benchmark_id": "BMK_GLOBAL_BALANCED_60_40",
                    "return_source": "calculated",
                    "summary": {
                        "period_return": {"base": 14.72},
                    },
                    "breakdowns": {
                        "monthly": [
                            {
                                "period": "2026-01",
                                "period_start": "2026-01-01",
                                "period_end": "2026-01-31",
                                "period_return": {"base": 1.8},
                                "cumulative_return": {"base": 1.8},
                            },
                            {
                                "period": "2026-02",
                                "period_start": "2026-02-01",
                                "period_end": "2026-02-28",
                                "period_return": {"base": 5.4},
                                "cumulative_return": {"base": 7.3},
                            },
                            {
                                "period": "2026-03",
                                "period_start": "2026-03-01",
                                "period_end": "2026-03-27",
                                "period_return": {"base": 6.91},
                                "cumulative_return": {"base": 14.72},
                            },
                        ]
                    },
                },
                "active": {
                    "net": {"period_return": {"base": 0.38}},
                    "gross": {"period_return": {"base": 0.41}},
                },
                "portfolio_twr": {
                    "net": {
                        "summary": {
                            "period_return": {"base": 15.1},
                            "annualized_return": {"base": 15.1},
                            "economics": {
                                "begin_market_value": 450_000.0,
                                "end_market_value": 508_870.0,
                                "net_cash_flow": 22_500.0,
                            },
                        },
                        "breakdowns": {
                            "monthly": [
                                {
                                    "period": "2026-01",
                                    "period_start": "2026-01-01",
                                    "period_end": "2026-01-31",
                                    "period_return": {"base": 2.0},
                                    "cumulative_return": {"base": 2.0},
                                },
                                {
                                    "period": "2026-02",
                                    "period_start": "2026-02-01",
                                    "period_end": "2026-02-28",
                                    "period_return": {"base": 5.5},
                                    "cumulative_return": {"base": 7.61},
                                },
                                {
                                    "period": "2026-03",
                                    "period_start": "2026-03-01",
                                    "period_end": "2026-03-27",
                                    "period_return": {"base": 6.96},
                                    "cumulative_return": {"base": 15.1},
                                },
                            ]
                        },
                    },
                    "gross": {
                        "summary": {
                            "period_return": {"base": 15.13},
                            "annualized_return": {"base": 15.13},
                            "economics": {
                                "begin_market_value": 450_000.0,
                                "end_market_value": 508_870.0,
                                "net_cash_flow": 22_500.0,
                            },
                        },
                        "breakdowns": {
                            "monthly": [
                                {
                                    "period": "2026-01",
                                    "period_start": "2026-01-01",
                                    "period_end": "2026-01-31",
                                    "period_return": {"base": 2.01},
                                    "cumulative_return": {"base": 2.01},
                                },
                                {
                                    "period": "2026-02",
                                    "period_start": "2026-02-01",
                                    "period_end": "2026-02-28",
                                    "period_return": {"base": 5.51},
                                    "cumulative_return": {"base": 7.63},
                                },
                                {
                                    "period": "2026-03",
                                    "period_start": "2026-03-01",
                                    "period_end": "2026-03-27",
                                    "period_return": {"base": 6.97},
                                    "cumulative_return": {"base": 15.13},
                                },
                            ]
                        },
                    },
                },
                "money_weighted_return": {
                    "period_return": 14.05,
                    "annualized_return": 14.05,
                    "method": "XIRR",
                    "start_date": "2026-01-01",
                    "end_date": "2026-03-27",
                    "notes": ["cash-flow aware"],
                },
                "contribution": {
                    "metric_basis": "NET",
                    "summary": {
                        "total_contribution": 15.1,
                        "portfolio_return": 15.1,
                        "portfolio_local_return": 13.9,
                        "portfolio_fx_return": 1.2,
                    },
                    "levels": [
                        {
                            "level": 1,
                            "name": "asset_class",
                            "rows": [
                                {
                                    "key": {"asset_class": "Equity"},
                                    "contribution": 10.2,
                                    "weight_avg": 30.365565,
                                    "return": 24.8,
                                    "local_contribution": 9.5,
                                    "fx_contribution": 0.7,
                                },
                                {
                                    "key": {"asset_class": "Fixed Income"},
                                    "contribution": 2.7,
                                    "weight_avg": 23.271435,
                                    "return": 7.2,
                                    "local_contribution": 2.4,
                                    "fx_contribution": 0.3,
                                },
                                {
                                    "key": {"asset_class": "Cash"},
                                    "contribution": 2.2,
                                    "weight_avg": 46.362999,
                                    "return": 4.75,
                                    "local_contribution": 2.0,
                                    "fx_contribution": 0.2,
                                },
                            ],
                        }
                    ],
                    "position_contributions": [
                        {
                            "position_id": "SEC_AAPL_US",
                            "contribution": 5.43,
                            "average_weight": 8.78,
                            "total_return": 76.05,
                            "local_contribution": 5.12,
                            "fx_contribution": 0.31,
                        },
                        {
                            "position_id": "SEC_ETF_WORLD_USD",
                            "contribution": 1.31,
                            "average_weight": 1.81,
                            "total_return": 99.88,
                            "local_contribution": 1.28,
                            "fx_contribution": 0.03,
                        },
                    ],
                },
                "attribution": {
                    "metric_basis": "NET",
                    "model": "BF",
                    "linking": "carino",
                    "benchmark_context": {
                        "benchmark_id": "BMK_GLOBAL_BALANCED_60_40",
                        "return_source": "calculated",
                    },
                    "result": {
                        "reconciliation": {
                            "total_active_return": 0.38,
                            "sum_of_effects": 0.37,
                            "residual": 0.01,
                        },
                        "levels": [
                            {
                                "dimension": "asset_class",
                                "totals": {
                                    "allocation": -0.08,
                                    "selection": 0.35,
                                    "interaction": 0.10,
                                    "total_effect": 0.37,
                                },
                                "rows": [
                                    {
                                        "key": {"asset_class": "Equity"},
                                        "portfolio_weight_avg": 30.365565,
                                        "benchmark_weight_avg": 60.0,
                                        "portfolio_return": 24.8,
                                        "benchmark_return": 18.4,
                                        "allocation": -0.52,
                                        "selection": 1.01,
                                        "interaction": 0.09,
                                        "total_effect": 0.58,
                                    },
                                    {
                                        "key": {"asset_class": "Fixed Income"},
                                        "portfolio_weight_avg": 23.271435,
                                        "benchmark_weight_avg": 40.0,
                                        "portfolio_return": 7.2,
                                        "benchmark_return": 8.0,
                                        "allocation": 0.44,
                                        "selection": -0.52,
                                        "interaction": 0.01,
                                        "total_effect": -0.07,
                                    },
                                    {
                                        "key": {"asset_class": "Cash"},
                                        "portfolio_weight_avg": 46.362999,
                                        "benchmark_weight_avg": 0.0,
                                        "portfolio_return": 4.75,
                                        "benchmark_return": 0.0,
                                        "allocation": 0.0,
                                        "selection": -0.14,
                                        "interaction": 0.0,
                                        "total_effect": -0.14,
                                    },
                                ],
                            }
                        ],
                    },
                },
            }
        }
    }


@pytest.mark.asyncio
async def test_performance_workspace_service_returns_workspace_summary_contract():
    analytics_client = _StubAnalyticsClient()
    query_client = _StubLotusCoreQueryClient()
    service = PerformanceWorkspaceService(
        workbench_service=_StubWorkbenchService(),
        analytics_client=analytics_client,
        lotus_core_query_client=query_client,
    )

    response = await service.get_performance_workspace(
        portfolio_id="DEMO_ADV_USD_001",
        correlation_id="corr-performance",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="BMK_GLOBAL_BALANCED_60_40",
    )

    assert response.portfolio.portfolio_id == "DEMO_ADV_USD_001"
    assert response.segment == "asset_class"
    assert response.report_start_date == "2026-01-01"
    assert response.report_end_date == "2026-03-27"
    assert response.net_performance.portfolio_return_pct == 15.1
    assert response.net_performance.benchmark_return_pct == 14.72
    assert response.net_performance.active_return_pct == 0.38
    assert response.net_performance.begin_market_value == 450000.0
    assert response.gross_performance.portfolio_return_pct == 15.13
    assert response.money_weighted_return is not None
    assert response.money_weighted_return.money_weighted_return_pct == 14.05
    assert len(response.net_chart) == 3
    assert response.net_chart[-1].cumulative_active_return_pct == 0.38
    assert response.contribution is not None
    assert response.contribution.total_portfolio_return_pct == 15.1
    assert response.contribution.levels[0].rows[0].weight_avg_pct == 30.365565
    assert response.contribution.levels[0].total_weight_avg_pct == 99.999999
    assert response.contribution.position_rows[0].position_id == "SEC_AAPL_US"
    assert response.attribution is not None
    assert response.attribution.benchmark_id == "BMK_GLOBAL_BALANCED_60_40"
    assert response.attribution.levels[0].rows[0].portfolio_weight_avg_pct == 30.365565
    assert response.attribution.levels[0].rows[0].benchmark_return_pct == 18.4
    assert response.benchmark_options[0].is_assigned is True
    assert response.benchmark_options[0].benchmark_code == "BMK_GLOBAL_BALANCED_60_40"
    assert response.warnings == ["FOUNDATION_WARNING"]
    assert response.partial_failures[0].error_code == "STALE_REPORTING"

    assert analytics_client.workspace_summary_calls[0]["chart_frequency"] == "monthly"
    assert analytics_client.workspace_summary_calls[0]["segment"] == "asset_class"
    assert query_client.reference_calls == 1
    assert query_client.benchmark_catalog_calls[0]["benchmark_currency"] == "USD"


@pytest.mark.asyncio
async def test_performance_workspace_service_aligns_mismatched_dimensions_to_shared_segment():
    analytics_client = _StubAnalyticsClient()
    service = PerformanceWorkspaceService(
        workbench_service=_StubWorkbenchService(),
        analytics_client=analytics_client,
        lotus_core_query_client=_StubLotusCoreQueryClient(),
    )

    response = await service.get_performance_workspace(
        portfolio_id="DEMO_ADV_USD_001",
        correlation_id="corr-performance",
        period="YTD",
        chart_frequency="quarterly",
        contribution_dimension="sector",
        attribution_dimension="country",
        detail_basis="NET",
        benchmark_code="BMK_GLOBAL_BALANCED_60_40",
    )

    assert response.segment == "sector"
    assert response.contribution_dimension == "sector"
    assert response.attribution_dimension == "country"
    assert "PERFORMANCE_SEGMENTATION_ALIGNED_TO_SHARED_SOURCE_CONTRACT" in response.warnings
    assert analytics_client.workspace_summary_calls[0]["segment"] == "sector"
    assert analytics_client.workspace_summary_calls[0]["chart_frequency"] == "quarterly"


@pytest.mark.asyncio
async def test_performance_workspace_service_skips_reference_lookup_for_explicit_window():
    analytics_client = _StubAnalyticsClient()
    query_client = _StubLotusCoreQueryClient()
    service = PerformanceWorkspaceService(
        workbench_service=_StubWorkbenchService(),
        analytics_client=analytics_client,
        lotus_core_query_client=query_client,
    )

    response = await service.get_performance_workspace(
        portfolio_id="DEMO_ADV_USD_001",
        correlation_id="corr-performance",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="BMK_GLOBAL_BALANCED_60_40",
        explicit_start_date="2026-01-15",
        explicit_end_date="2026-03-20",
    )

    assert response.period == "EXPLICIT"
    assert response.report_start_date == "2026-01-15"
    assert response.report_end_date == "2026-03-20"
    assert query_client.reference_calls == 0
    assert analytics_client.workspace_summary_calls[0]["period"] == "EXPLICIT"
    assert analytics_client.workspace_summary_calls[0]["report_start_date"] == "2026-01-15"


@pytest.mark.asyncio
async def test_performance_workspace_service_handles_workspace_summary_failure():
    class _FailingAnalyticsClient(_StubAnalyticsClient):
        async def get_workspace_summary(self, **kwargs):  # noqa: ARG002
            return 503, {"detail": "workspace summary unavailable"}

    service = PerformanceWorkspaceService(
        workbench_service=_StubWorkbenchService(),
        analytics_client=_FailingAnalyticsClient(),
        lotus_core_query_client=_StubLotusCoreQueryClient(),
    )

    response = await service.get_performance_workspace(
        portfolio_id="DEMO_ADV_USD_001",
        correlation_id="corr-performance",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="BMK_GLOBAL_BALANCED_60_40",
    )

    assert response.net_performance.portfolio_return_pct is None
    assert response.gross_performance.portfolio_return_pct is None
    assert response.contribution is None
    assert response.attribution is None
    assert "PERFORMANCE_WORKSPACE_SUMMARY_UNAVAILABLE" in response.warnings
    assert any(failure.error_code == "HTTP_503" for failure in response.partial_failures)


@pytest.mark.asyncio
async def test_performance_workspace_service_handles_benchmark_catalog_failure():
    class _FailingQueryClient(_StubLotusCoreQueryClient):
        async def get_benchmark_catalog(self, **kwargs):  # noqa: ARG002
            return 503, {"detail": "benchmark catalog unavailable"}

    service = PerformanceWorkspaceService(
        workbench_service=_StubWorkbenchService(),
        analytics_client=_StubAnalyticsClient(),
        lotus_core_query_client=_FailingQueryClient(),
    )

    response = await service.get_performance_workspace(
        portfolio_id="DEMO_ADV_USD_001",
        correlation_id="corr-performance",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="BMK_GLOBAL_BALANCED_60_40",
    )

    assert response.benchmark_options == []
    assert "BENCHMARK_CATALOG_UNAVAILABLE" in response.warnings
    assert any(failure.error_code == "HTTP_503" for failure in response.partial_failures)
