import asyncio

import pytest

from app.contracts.workbench import (
    WorkbenchOverviewResponse,
    WorkbenchOverviewSummary,
    WorkbenchPartialFailure,
    WorkbenchPortfolioSummary,
)
from app.services.performance_workspace_service import PerformanceWorkspaceService


class _StubWorkbenchService:
    async def get_workbench_overview(
        self,
        portfolio_id: str,
        correlation_id: str,
        include_performance_snapshot: bool = True,  # noqa: ARG002
        include_rebalance_snapshot: bool = True,  # noqa: ARG002
    ):
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
        self.attribution_calls: list[dict[str, object]] = []
        self.twr_calls: list[dict[str, object]] = []

    async def get_workspace_summary(self, **kwargs):
        self.workspace_summary_calls.append(kwargs)
        periods = kwargs.get("periods") or []
        if periods:
            results_by_period: dict[str, object] = {}
            source_results = _workspace_summary_payload()["results_by_period"]
            for period_request in periods:
                if not isinstance(period_request, dict):
                    continue
                period_key = str(period_request.get("period"))
                if period_key in source_results:
                    results_by_period[period_key] = source_results[period_key]
            return 200, {"results_by_period": results_by_period}

        requested_period = kwargs.get("period")
        if requested_period == "EXPLICIT":
            report_start_date = str(kwargs.get("report_start_date"))
            explicit_label = "MTD" if report_start_date.endswith("-03-01") else "QTD"
            return 200, {
                "results_by_period": {
                    "EXPLICIT": _workspace_summary_payload()["results_by_period"][explicit_label]
                }
            }
        if requested_period in {"YTD", "1Y"}:
            return 200, {
                "results_by_period": {
                    requested_period: _workspace_summary_payload()["results_by_period"][
                        requested_period
                    ]
                }
            }
        return 200, _workspace_summary_payload()

    async def get_attribution_analytics(self, **kwargs):
        self.attribution_calls.append(kwargs)
        return 200, _attribution_payload(
            report_start_date=str(kwargs["report_start_date"]),
            report_end_date=str(kwargs["report_end_date"]),
        )

    async def get_twr_analytics(self, **kwargs):
        self.twr_calls.append(kwargs)
        analyses = kwargs.get("analyses") or []
        if analyses:
            results_by_period: dict[str, object] = {}
            for analysis in analyses:
                if not isinstance(analysis, dict):
                    continue
                analysis_period = str(analysis.get("period"))
                results_by_period.update(_twr_payload_for_period(analysis_period, analysis_period)["results_by_period"])
            return 200, {
                "benchmark_context": {
                    "benchmark_id": "BMK_GLOBAL_BALANCED_60_40",
                    "return_source": "calculated",
                },
                "results_by_period": results_by_period,
            }

        requested_period = str(kwargs["period"])
        return 200, _twr_payload_for_period(requested_period, requested_period)


class _StubLotusCoreQueryClient:
    def __init__(self):
        self.reference_calls = 0
        self.benchmark_catalog_calls: list[dict[str, object]] = []
        self.benchmark_assignment_calls: list[dict[str, object]] = []

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

    async def get_benchmark_assignment(self, **kwargs):
        self.benchmark_assignment_calls.append(kwargs)
        return (
            200,
            {
                "benchmark_id": "BMK_GLOBAL_BALANCED_60_40",
                "assignment_status": "active",
            },
        )


def _workspace_summary_payload() -> dict:
    return {
        "results_by_period": {
            "MTD": {
                "benchmark": {
                    "benchmark_id": "BMK_GLOBAL_BALANCED_60_40",
                    "return_source": "calculated",
                    "summary": {
                        "period_return": {"base": 1.0},
                        "annualized_return": {"base": 1.0},
                    },
                },
                "active": {
                    "net": {"period_return": {"base": 0.2}},
                    "gross": {"period_return": {"base": 0.22}},
                },
                "portfolio_twr": {
                    "net": {
                        "summary": {
                            "period_return": {"base": 1.2},
                            "annualized_return": {"base": 1.2},
                        }
                    },
                    "gross": {
                        "summary": {
                            "period_return": {"base": 1.22},
                            "annualized_return": {"base": 1.22},
                        }
                    },
                },
            },
            "QTD": {
                "benchmark": {
                    "benchmark_id": "BMK_GLOBAL_BALANCED_60_40",
                    "return_source": "calculated",
                    "summary": {
                        "period_return": {"base": 4.0},
                        "annualized_return": {"base": 4.0},
                    },
                },
                "active": {
                    "net": {"period_return": {"base": 0.3}},
                    "gross": {"period_return": {"base": 0.34}},
                },
                "portfolio_twr": {
                    "net": {
                        "summary": {
                            "period_return": {"base": 4.3},
                            "annualized_return": {"base": 4.3},
                        }
                    },
                    "gross": {
                        "summary": {
                            "period_return": {"base": 4.34},
                            "annualized_return": {"base": 4.34},
                        }
                    },
                },
            },
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
            },
            "1Y": {
                "benchmark": {
                    "benchmark_id": "BMK_GLOBAL_BALANCED_60_40",
                    "return_source": "calculated",
                    "summary": {
                        "period_return": {"base": 12.6},
                        "annualized_return": {"base": 12.6},
                    },
                },
                "active": {
                    "net": {"period_return": {"base": 0.6}},
                    "gross": {"period_return": {"base": 0.64}},
                },
                "portfolio_twr": {
                    "net": {
                        "summary": {
                            "period_return": {"base": 13.2},
                            "annualized_return": {"base": 13.2},
                        }
                    },
                    "gross": {
                        "summary": {
                            "period_return": {"base": 13.24},
                            "annualized_return": {"base": 13.24},
                        }
                    },
                },
            },
        }
    }


def _twr_payload_for_period(result_key: str, source_label: str) -> dict:
    source = _workspace_summary_payload()["results_by_period"][source_label]
    return {
        "benchmark_context": {
            "benchmark_id": "BMK_GLOBAL_BALANCED_60_40",
            "return_source": "calculated",
        },
        "results_by_period": {
            result_key: {
                "portfolio": source["portfolio_twr"]["net"],
                "benchmark": source["benchmark"],
                "relative_performance": {
                    "summary": source["active"]["net"],
                },
            }
        },
    }


def _attribution_payload(*, report_start_date: str, report_end_date: str) -> dict:
    month = report_start_date[:7]
    totals_by_month = {
        "2026-01": {"allocation": 0.12, "selection": 0.08, "interaction": 0.02, "total": 0.22},
        "2026-02": {"allocation": -0.04, "selection": 0.11, "interaction": 0.01, "total": 0.08},
        "2026-03": {"allocation": 0.05, "selection": -0.02, "interaction": 0.01, "total": 0.04},
    }
    totals = totals_by_month[month]
    return {
        "benchmark_context": {
            "benchmark_id": "BMK_GLOBAL_BALANCED_60_40",
            "return_source": "calculated",
        },
        "results_by_period": {
            "EXPLICIT": {
                "reconciliation": {
                    "total_active_return": totals["total"],
                    "sum_of_effects": totals["total"],
                    "residual": 0.0,
                },
                "levels": [
                    {
                        "dimension": "asset_class",
                        "totals": {
                            "allocation": totals["allocation"],
                            "selection": totals["selection"],
                            "interaction": totals["interaction"],
                            "total_effect": totals["total"],
                        },
                        "groups": [],
                    }
                ],
            }
        },
    }


@pytest.mark.asyncio
async def test_performance_workspace_service_deduplicates_benchmark_catalog_options():
    service = PerformanceWorkspaceService(
        workbench_service=_StubWorkbenchService(),
        analytics_client=_StubAnalyticsClient(),
        lotus_core_query_client=_StubLotusCoreQueryClient(),
    )

    warnings: list[str] = []
    partial_failures: list[WorkbenchPartialFailure] = []
    options = service._parse_benchmark_catalog_result(
        result=(
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
        ),
        assigned_benchmark_code="BMK_GLOBAL_BALANCED_60_40",
        warnings=warnings,
        partial_failures=partial_failures,
    )

    assert [option.benchmark_code for option in options] == [
        "BMK_GLOBAL_BALANCED_60_40",
        "BMK_GLOBAL_GROWTH_80_20",
    ]
    assert options[0].is_assigned is True
    assert warnings == []
    assert partial_failures == []


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
async def test_performance_workspace_service_projects_summary_contract():
    service = PerformanceWorkspaceService(
        workbench_service=_StubWorkbenchService(),
        analytics_client=_StubAnalyticsClient(),
        lotus_core_query_client=_StubLotusCoreQueryClient(),
    )

    response = await service.get_performance_workspace_summary(
        portfolio_id="DEMO_ADV_USD_001",
        correlation_id="corr-performance",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="BMK_GLOBAL_BALANCED_60_40",
    )

    assert response.portfolio_id == "DEMO_ADV_USD_001"
    assert response.net_performance.portfolio_return_pct == 15.1
    assert response.gross_performance.portfolio_return_pct == 15.13
    assert response.money_weighted_return is not None
    assert response.money_weighted_return.method == "XIRR"
    assert response.benchmark_options[0].benchmark_name == "Global Balanced 60/40"
    assert not hasattr(response, "net_chart")
    assert not hasattr(response, "contribution")


@pytest.mark.asyncio
async def test_performance_workspace_service_resolves_linked_benchmark_when_code_is_omitted():
    analytics_client = _StubAnalyticsClient()
    query_client = _StubLotusCoreQueryClient()
    service = PerformanceWorkspaceService(
        workbench_service=_StubWorkbenchService(),
        analytics_client=analytics_client,
        lotus_core_query_client=query_client,
    )

    response = await service.get_performance_workspace_summary(
        portfolio_id="DEMO_ADV_USD_001",
        correlation_id="corr-performance",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code=None,
    )

    assert response.benchmark_code == "BMK_GLOBAL_BALANCED_60_40"
    assert (
        analytics_client.workspace_summary_calls[0]["benchmark_id"] == "BMK_GLOBAL_BALANCED_60_40"
    )
    assert query_client.benchmark_assignment_calls[0]["portfolio_id"] == "DEMO_ADV_USD_001"


@pytest.mark.asyncio
async def test_performance_workspace_service_builds_horizon_comparison_contract():
    analytics_client = _StubAnalyticsClient()
    query_client = _StubLotusCoreQueryClient()
    service = PerformanceWorkspaceService(
        workbench_service=_StubWorkbenchService(),
        analytics_client=analytics_client,
        lotus_core_query_client=query_client,
    )

    response = await service.get_performance_horizon_comparison(
        portfolio_id="DEMO_ADV_USD_001",
        correlation_id="corr-performance",
        detail_basis="NET",
        benchmark_code="BMK_GLOBAL_BALANCED_60_40",
        chart_frequency="monthly",
    )

    assert response.portfolio_id == "DEMO_ADV_USD_001"
    assert response.benchmark_code == "BMK_GLOBAL_BALANCED_60_40"
    assert response.reporting_currency == "USD"
    assert [row.period for row in response.rows] == ["MTD", "QTD", "YTD", "1Y"]
    assert response.rows[0].portfolio_return_pct == 1.2
    assert response.rows[0].net_return_pct == 1.2
    assert response.rows[0].gross_return_pct == 1.22
    assert response.rows[2].benchmark_return_pct == 14.72
    assert response.rows[2].begin_market_value == 450000.0
    assert response.rows[3].active_return_pct == 0.6
    assert response.rows[2].period_start == "2026-01-01"
    assert response.rows[2].period_end == "2026-03-27"
    assert len(analytics_client.workspace_summary_calls) == 1
    assert analytics_client.workspace_summary_calls[0]["period"] == "YTD"
    assert analytics_client.workspace_summary_calls[0]["include_detail_blocks"] is False
    assert [analysis["period"] for analysis in analytics_client.workspace_summary_calls[0]["periods"]] == [
        "MTD",
        "QTD",
        "YTD",
        "1Y",
    ]


@pytest.mark.asyncio
async def test_performance_workspace_service_resolves_linked_benchmark_for_horizon_comparison():
    analytics_client = _StubAnalyticsClient()
    query_client = _StubLotusCoreQueryClient()
    service = PerformanceWorkspaceService(
        workbench_service=_StubWorkbenchService(),
        analytics_client=analytics_client,
        lotus_core_query_client=query_client,
    )

    response = await service.get_performance_horizon_comparison(
        portfolio_id="DEMO_ADV_USD_001",
        correlation_id="corr-performance",
        detail_basis="NET",
        benchmark_code=None,
        chart_frequency="monthly",
    )

    assert response.benchmark_code == "BMK_GLOBAL_BALANCED_60_40"
    assert analytics_client.workspace_summary_calls[0]["benchmark_id"] == "BMK_GLOBAL_BALANCED_60_40"
    assert query_client.benchmark_assignment_calls[0]["portfolio_id"] == "DEMO_ADV_USD_001"


@pytest.mark.asyncio
async def test_performance_workspace_service_builds_attribution_trend_contract():
    analytics_client = _StubAnalyticsClient()
    service = PerformanceWorkspaceService(
        workbench_service=_StubWorkbenchService(),
        analytics_client=analytics_client,
        lotus_core_query_client=_StubLotusCoreQueryClient(),
    )

    response = await service.get_performance_attribution_trend(
        portfolio_id="DEMO_ADV_USD_001",
        correlation_id="corr-performance",
        period="YTD",
        chart_frequency="monthly",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="BMK_GLOBAL_BALANCED_60_40",
    )

    assert response.portfolio_id == "DEMO_ADV_USD_001"
    assert response.chart_frequency == "monthly"
    assert [row.period_label for row in response.rows] == ["2026-01", "2026-02", "2026-03"]
    assert response.rows[0].allocation_pct == 0.12
    assert response.rows[1].selection_pct == 0.11
    assert response.rows[2].cumulative_total_effect_pct == 0.34
    assert analytics_client.attribution_calls[0]["period"] == "EXPLICIT"
    assert analytics_client.attribution_calls[0]["dimension"] == "asset_class"
    assert analytics_client.attribution_calls[-1]["report_end_date"] == "2026-03-27"


@pytest.mark.asyncio
async def test_performance_workspace_service_resolves_linked_benchmark_for_attribution_trend():
    analytics_client = _StubAnalyticsClient()
    query_client = _StubLotusCoreQueryClient()
    service = PerformanceWorkspaceService(
        workbench_service=_StubWorkbenchService(),
        analytics_client=analytics_client,
        lotus_core_query_client=query_client,
    )

    response = await service.get_performance_attribution_trend(
        portfolio_id="DEMO_ADV_USD_001",
        correlation_id="corr-performance",
        period="YTD",
        chart_frequency="monthly",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code=None,
    )

    assert response.benchmark_code == "BMK_GLOBAL_BALANCED_60_40"
    assert analytics_client.attribution_calls[0]["benchmark_id"] == "BMK_GLOBAL_BALANCED_60_40"
    assert query_client.benchmark_assignment_calls[0]["portfolio_id"] == "DEMO_ADV_USD_001"


@pytest.mark.asyncio
async def test_performance_workspace_service_projects_detail_contract():
    query_client = _StubLotusCoreQueryClient()
    service = PerformanceWorkspaceService(
        workbench_service=_StubWorkbenchService(),
        analytics_client=_StubAnalyticsClient(),
        lotus_core_query_client=query_client,
    )

    response = await service.get_performance_workspace_details(
        portfolio_id="DEMO_ADV_USD_001",
        correlation_id="corr-performance",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="BMK_GLOBAL_BALANCED_60_40",
    )

    assert response.portfolio_id == "DEMO_ADV_USD_001"
    assert len(response.net_chart) == 3
    assert response.contribution is not None
    assert response.contribution.position_rows[0].position_id == "SEC_AAPL_US"
    assert response.attribution is not None
    assert response.attribution.benchmark_id == "BMK_GLOBAL_BALANCED_60_40"
    assert response.segment == "asset_class"
    assert not hasattr(response, "overview")
    assert not hasattr(response, "net_performance")
    assert query_client.benchmark_catalog_calls == []


@pytest.mark.asyncio
async def test_performance_workspace_service_projects_portfolio_performance_snapshot():
    query_client = _StubLotusCoreQueryClient()
    service = PerformanceWorkspaceService(
        workbench_service=_StubWorkbenchService(),
        analytics_client=_StubAnalyticsClient(),
        lotus_core_query_client=query_client,
    )

    response = await service.get_portfolio_performance_snapshot(
        portfolio_id="DEMO_ADV_USD_001",
        correlation_id="corr-performance",
        period="YTD",
        chart_frequency="monthly",
        detail_basis="NET",
        benchmark_code="BMK_GLOBAL_BALANCED_60_40",
    )

    assert response.portfolio_return_pct == 15.1
    assert response.benchmark_return_pct == 14.72
    assert response.excess_return_pct == 0.38
    assert response.sparkline[0].as_of_date == "2026-01-31"
    assert response.sparkline[0].portfolio_return_pct == 2.0
    assert query_client.benchmark_catalog_calls == []


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


@pytest.mark.asyncio
async def test_performance_workspace_service_fetches_assignment_and_catalog_concurrently():
    class _ConcurrentQueryClient(_StubLotusCoreQueryClient):
        def __init__(self):
            super().__init__()
            self.assignment_started = asyncio.Event()
            self.catalog_started = asyncio.Event()

        async def get_benchmark_catalog(self, **kwargs):
            self.catalog_started.set()
            await asyncio.wait_for(self.assignment_started.wait(), timeout=0.1)
            return await super().get_benchmark_catalog(**kwargs)

        async def get_benchmark_assignment(self, **kwargs):
            self.assignment_started.set()
            await asyncio.wait_for(self.catalog_started.wait(), timeout=0.1)
            return await super().get_benchmark_assignment(**kwargs)

    query_client = _ConcurrentQueryClient()
    service = PerformanceWorkspaceService(
        workbench_service=_StubWorkbenchService(),
        analytics_client=_StubAnalyticsClient(),
        lotus_core_query_client=query_client,
    )

    response = await asyncio.wait_for(
        service.get_performance_workspace_summary(
            portfolio_id="DEMO_ADV_USD_001",
            correlation_id="corr-performance",
            period="YTD",
            chart_frequency="monthly",
            contribution_dimension="asset_class",
            attribution_dimension="asset_class",
            detail_basis="NET",
            benchmark_code=None,
        ),
        timeout=0.2,
    )

    assert response.benchmark_code == "BMK_GLOBAL_BALANCED_60_40"
    assert len(query_client.benchmark_assignment_calls) == 1
    assert len(query_client.benchmark_catalog_calls) == 1
