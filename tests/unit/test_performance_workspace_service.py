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
            as_of_date="2026-02-24",
            portfolio=WorkbenchPortfolioSummary(
                portfolio_id=portfolio_id,
                client_id="CIF_1001",
                base_currency="USD",
                booking_center_code="SG",
            ),
            overview=WorkbenchOverviewSummary(
                market_value_base=1_250_000.0,
                cash_weight_pct=6.8,
                position_count=18,
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
    async def get_twr_analytics(self, **kwargs):  # noqa: ARG002
        return (
            200,
            {
                "benchmark_context": {
                    "benchmark_id": "MODEL_60_40",
                    "return_source": "calculated",
                },
                "results_by_period": {
                    "YTD": {
                        "portfolio": {
                            "summary": {
                                "period_return": {"base": 5.42},
                                "annualized_return": {"base": 5.42},
                            },
                            "breakdowns": {
                                "monthly": [
                                    {
                                        "period": "2026-01",
                                        "period_start": "2026-01-01",
                                        "period_end": "2026-01-31",
                                        "period_return": {"base": 2.2},
                                        "cumulative_return": {"base": 2.2},
                                    },
                                    {
                                        "period": "2026-02",
                                        "period_start": "2026-02-01",
                                        "period_end": "2026-02-24",
                                        "period_return": {"base": 3.22},
                                        "cumulative_return": {"base": 5.42},
                                    },
                                ]
                            },
                        },
                        "benchmark": {
                            "summary": {"period_return": {"base": 4.9}},
                            "breakdowns": {
                                "monthly": [
                                    {
                                        "period": "2026-01",
                                        "period_start": "2026-01-01",
                                        "period_end": "2026-01-31",
                                        "period_return": {"base": 1.9},
                                        "cumulative_return": {"base": 1.9},
                                    },
                                    {
                                        "period": "2026-02",
                                        "period_start": "2026-02-01",
                                        "period_end": "2026-02-24",
                                        "period_return": {"base": 3.0},
                                        "cumulative_return": {"base": 4.9},
                                    },
                                ]
                            },
                        },
                        "relative_performance": {
                            "summary": {"period_return": {"base": 0.52}},
                            "breakdowns": {
                                "monthly": [
                                    {
                                        "period": "2026-01",
                                        "period_start": "2026-01-01",
                                        "period_end": "2026-01-31",
                                        "period_return": {"base": 0.3},
                                        "cumulative_return": {"base": 0.3},
                                    },
                                    {
                                        "period": "2026-02",
                                        "period_start": "2026-02-01",
                                        "period_end": "2026-02-24",
                                        "period_return": {"base": 0.22},
                                        "cumulative_return": {"base": 0.52},
                                    },
                                ]
                            },
                        },
                    }
                },
            },
        )

    async def get_mwr_analytics(self, **kwargs):  # noqa: ARG002
        return (
            200,
            {
                "money_weighted_return": 5.12,
                "mwr_annualized": 5.12,
                "method": "XIRR",
                "start_date": "2026-01-01",
                "end_date": "2026-02-24",
                "notes": ["cash-flow aware"],
            },
        )

    async def get_contribution_analytics(self, **kwargs):  # noqa: ARG002
        return (
            200,
            {
                "results_by_period": {
                    "YTD": {
                        "total_portfolio_return": 5.42,
                        "summary": {
                            "portfolio_contribution": 5.42,
                            "coverage_mv_pct": 98.7,
                            "weighting_scheme": "average_weight",
                        },
                        "levels": [
                            {
                                "level": 1,
                                "name": "asset_class",
                                "rows": [
                                    {
                                        "key": {"asset_class": "Equity"},
                                        "contribution": 3.8,
                                        "weight_avg": 0.61,
                                        "local_contribution": 3.4,
                                        "fx_contribution": 0.4,
                                    },
                                    {
                                        "key": {"asset_class": "Fixed Income"},
                                        "contribution": 1.2,
                                        "weight_avg": 0.26,
                                        "local_contribution": 1.1,
                                        "fx_contribution": 0.1,
                                    },
                                ],
                            }
                        ],
                    }
                }
            },
        )

    async def get_attribution_analytics(self, **kwargs):  # noqa: ARG002
        return (
            200,
            {
                "model": "BF",
                "linking": "carino",
                "benchmark_context": {"benchmark_id": "MODEL_60_40"},
                "results_by_period": {
                    "YTD": {
                        "reconciliation": {
                            "total_active_return": 0.52,
                            "sum_of_effects": 0.5,
                            "residual": 0.02,
                        },
                        "levels": [
                            {
                                "dimension": "asset_class",
                                "totals": {"total_effect": 0.5},
                                "groups": [
                                    {
                                        "key": {"asset_class": "Equity"},
                                        "allocation": 0.18,
                                        "selection": 0.24,
                                        "interaction": 0.03,
                                        "total_effect": 0.45,
                                    }
                                ],
                            }
                        ],
                    }
                },
            },
        )


class _StubLotusCoreQueryClient:
    async def get_portfolio_analytics_reference(
        self,
        portfolio_id: str,
        as_of_date: str,
        consumer_system: str,
        correlation_id: str,
    ):  # noqa: ARG002
        return 200, {"performance_end_date": "2026-02-24"}


@pytest.mark.asyncio
async def test_performance_workspace_service_returns_rich_workspace():
    service = PerformanceWorkspaceService(
        workbench_service=_StubWorkbenchService(),
        analytics_client=_StubAnalyticsClient(),
        lotus_core_query_client=_StubLotusCoreQueryClient(),
    )

    response = await service.get_performance_workspace(
        portfolio_id="PF_1001",
        correlation_id="corr-performance",
        period="YTD",
        chart_frequency="monthly",
        detail_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="MODEL_60_40",
    )

    assert response.portfolio.portfolio_id == "PF_1001"
    assert response.net_performance.portfolio_return_pct == 5.42
    assert response.net_performance.benchmark_return_pct == 4.9
    assert response.gross_performance.portfolio_return_pct == 5.42
    assert response.money_weighted_return is not None
    assert response.money_weighted_return.method == "XIRR"
    assert len(response.net_chart) == 2
    assert response.net_chart[1].cumulative_portfolio_return_pct == 5.42
    assert response.contribution is not None
    assert response.contribution.levels[0].rows[0].key_label == "Equity"
    assert response.contribution.levels[0].rows[0].weight_avg_pct == 61.0
    assert response.attribution is not None
    assert response.attribution.levels[0].rows[0].total_effect_pct == 0.45
    assert response.warnings == ["FOUNDATION_WARNING"]
    assert response.partial_failures[0].error_code == "STALE_REPORTING"


@pytest.mark.asyncio
async def test_performance_workspace_service_keeps_workspace_when_analytics_partially_fail():
    class _PartialAnalyticsClient(_StubAnalyticsClient):
        async def get_contribution_analytics(self, **kwargs):  # noqa: ARG002
            return 503, {"detail": "contribution unavailable"}

        async def get_attribution_analytics(self, **kwargs):  # noqa: ARG002
            raise RuntimeError("attribution timeout")

    service = PerformanceWorkspaceService(
        workbench_service=_StubWorkbenchService(),
        analytics_client=_PartialAnalyticsClient(),
        lotus_core_query_client=_StubLotusCoreQueryClient(),
    )

    response = await service.get_performance_workspace(
        portfolio_id="PF_1001",
        correlation_id="corr-performance",
        period="YTD",
        chart_frequency="monthly",
        detail_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="MODEL_60_40",
    )

    assert response.net_performance.portfolio_return_pct == 5.42
    assert response.contribution is None
    assert response.attribution is None
    assert "CONTRIBUTION_UNAVAILABLE" in response.warnings
    assert "ATTRIBUTION_UNAVAILABLE" in response.warnings
    assert any(failure.error_code == "HTTP_503" for failure in response.partial_failures)
    assert any(failure.error_code == "UPSTREAM_EXCEPTION" for failure in response.partial_failures)


@pytest.mark.asyncio
async def test_performance_workspace_service_skips_attribution_without_benchmark():
    class _NoBenchmarkAnalyticsClient(_StubAnalyticsClient):
        async def get_twr_analytics(self, **kwargs):  # noqa: ARG002
            return (
                200,
                {
                    "results_by_period": {
                        "YTD": {
                            "portfolio": {
                                "summary": {
                                    "period_return": {"base": 5.42},
                                    "annualized_return": {"base": 5.42},
                                },
                                "breakdowns": {"monthly": []},
                            }
                        }
                    }
                },
            )

    service = PerformanceWorkspaceService(
        workbench_service=_StubWorkbenchService(),
        analytics_client=_NoBenchmarkAnalyticsClient(),
        lotus_core_query_client=_StubLotusCoreQueryClient(),
    )

    response = await service.get_performance_workspace(
        portfolio_id="PF_1001",
        correlation_id="corr-performance",
        period="YTD",
        chart_frequency="monthly",
        detail_dimension="asset_class",
        detail_basis="NET",
        benchmark_code=None,
    )

    assert response.net_performance.benchmark_return_pct is None
    assert response.attribution is None
