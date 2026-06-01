import asyncio

import pytest
from fastapi import HTTPException

from app.contracts.workbench import (
    WorkbenchOverviewResponse,
    WorkbenchOverviewSummary,
    WorkbenchPartialFailure,
    WorkbenchPortfolioSummary,
)
from app.services.performance_workspace_capabilities import build_workspace_capabilities
from app.services.performance_workspace_service import PerformanceWorkspaceService


class _StubWorkbenchService:
    def __init__(self):
        self.overview_calls = 0

    async def get_workbench_overview(
        self,
        portfolio_id: str,
        correlation_id: str,
        include_performance_snapshot: bool = True,  # noqa: ARG002
        include_rebalance_snapshot: bool = True,  # noqa: ARG002
    ):
        self.overview_calls += 1
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
        self.contribution_calls: list[dict[str, object]] = []
        self.attribution_calls: list[dict[str, object]] = []
        self.twr_calls: list[dict[str, object]] = []
        self.execution_calls: list[str] = []
        self.lineage_calls: list[str] = []

    async def get_workspace_summary(self, **kwargs):
        self.workspace_summary_calls.append(kwargs)
        source_payload = _workspace_summary_payload(
            include_detail_blocks=bool(kwargs.get("include_detail_blocks", True))
        )
        periods = kwargs.get("periods") or []
        if periods:
            results_by_period: dict[str, object] = {}
            source_results = source_payload["results_by_period"]
            for period_request in periods:
                if not isinstance(period_request, dict):
                    continue
                period_key = str(period_request.get("period"))
                if period_key == "EXPLICIT":
                    report_start_date = str(kwargs.get("report_start_date"))
                    explicit_label = "MTD" if report_start_date.endswith("-03-01") else "QTD"
                    results_by_period["EXPLICIT"] = source_results[explicit_label]
                    continue
                if period_key in source_results:
                    results_by_period[period_key] = source_results[period_key]
            return 200, {
                "calculation_id": "calc-workspace-summary",
                "results_by_period": results_by_period,
            }

        requested_period = kwargs.get("period")
        if requested_period == "EXPLICIT":
            report_start_date = str(kwargs.get("report_start_date"))
            explicit_label = "MTD" if report_start_date.endswith("-03-01") else "QTD"
            return 200, {
                "calculation_id": "calc-workspace-summary",
                "results_by_period": {
                    "EXPLICIT": source_payload["results_by_period"][explicit_label]
                },
            }
        if requested_period in {"YTD", "1Y"}:
            return 200, {
                "calculation_id": "calc-workspace-summary",
                "results_by_period": {
                    requested_period: source_payload["results_by_period"][requested_period]
                },
            }
        source_payload["calculation_id"] = "calc-workspace-summary"
        return 200, source_payload

    async def get_contribution_analytics(self, **kwargs):
        self.contribution_calls.append(kwargs)
        payload = _contribution_payload(dimension=str(kwargs["dimension"]))
        payload["calculation_id"] = "calc-contribution"
        return 200, payload

    async def get_attribution_analytics(self, **kwargs):
        self.attribution_calls.append(kwargs)
        payload = _attribution_payload(
            dimension=str(kwargs.get("dimension", "asset_class")),
            report_start_date=str(kwargs["report_start_date"]),
            report_end_date=str(kwargs["report_end_date"]),
        )
        payload["calculation_id"] = "calc-attribution"
        return 200, payload

    async def get_twr_analytics(self, **kwargs):
        self.twr_calls.append(kwargs)
        analyses = kwargs.get("analyses") or []
        if analyses:
            results_by_period: dict[str, object] = {}
            for analysis in analyses:
                if not isinstance(analysis, dict):
                    continue
                analysis_period = str(analysis.get("period"))
                results_by_period.update(
                    _twr_payload_for_period(analysis_period, analysis_period)["results_by_period"]
                )
            return 200, {
                "benchmark_context": {
                    "benchmark_id": "BMK_PB_GLOBAL_BALANCED_60_40",
                    "return_source": "calculated",
                },
                "calculation_id": "calc-twr",
                "results_by_period": results_by_period,
            }

        requested_period = str(kwargs["period"])
        return 200, _twr_payload_for_period(requested_period, requested_period)

    async def get_execution(self, *, calculation_id: str, correlation_id: str):
        _ = correlation_id
        self.execution_calls.append(calculation_id)
        return 200, {
            "calculation_id": calculation_id,
            "analytics_type": calculation_id.replace("calc-", "").replace("-", "_").upper(),
            "execution_mode": "sync",
            "status": "complete",
            "stages": [
                {
                    "stage_name": "execution",
                    "status": "complete",
                    "completed_at_utc": "2026-03-27T12:00:00Z",
                },
                {
                    "stage_name": "lineage_materialization",
                    "status": "complete",
                    "completed_at_utc": "2026-03-27T12:00:01Z",
                },
            ],
            "upstream_snapshots": [
                {
                    "upstream_endpoint": "portfolio_timeseries",
                    "source_identifier": "DEMO_ADV_USD_001",
                    "as_of_date": "2026-03-27",
                    "retrieval_status": "200",
                }
            ],
        }

    async def get_lineage(self, *, calculation_id: str, correlation_id: str):
        _ = correlation_id
        self.lineage_calls.append(calculation_id)
        return 200, {
            "calculation_id": calculation_id,
            "status": "complete",
            "artifacts": {
                "request.json": {
                    "url": f"http://performance.dev.lotus/performance/lineage/{calculation_id}/artifacts/request.json"
                },
                "response.json": {
                    "url": f"http://performance.dev.lotus/performance/lineage/{calculation_id}/artifacts/response.json"
                },
            },
        }

    async def get_lineage_artifact(
        self, *, calculation_id: str, artifact_name: str, correlation_id: str
    ):
        _ = calculation_id, artifact_name, correlation_id
        return 200, b"{}", "application/json"


class _StubLotusCoreQueryClient:
    def __init__(self):
        self.reference_calls = 0
        self.reference_kwargs: list[dict[str, object]] = []
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
        self.reference_kwargs.append(
            {
                "portfolio_id": portfolio_id,
                "as_of_date": as_of_date,
                "consumer_system": consumer_system,
                "correlation_id": correlation_id,
            }
        )
        return 200, {"performance_end_date": "2026-03-27"}

    async def get_benchmark_catalog(self, **kwargs):
        self.benchmark_catalog_calls.append(kwargs)
        return (
            200,
            {
                "records": [
                    {
                        "benchmark_id": "BMK_PB_GLOBAL_BALANCED_60_40",
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
                "benchmark_id": "BMK_PB_GLOBAL_BALANCED_60_40",
                "assignment_status": "active",
            },
        )


def _workspace_summary_payload(*, include_detail_blocks: bool = True) -> dict:
    payload = {
        "results_by_period": {
            "MTD": {
                "benchmark": {
                    "benchmark_id": "BMK_PB_GLOBAL_BALANCED_60_40",
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
                    "benchmark_id": "BMK_PB_GLOBAL_BALANCED_60_40",
                    "return_source": "calculated",
                    "input_mode": "stateful",
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
                            "economics": {
                                "begin_market_value": 470_000.0,
                                "end_market_value": 508_870.0,
                                "beginning_cash_flow": 15_000.0,
                                "ending_cash_flow": -2_500.0,
                                "flow_adjusted_end_market_value": 496_370.0,
                                "fees": 0.0,
                                "net_cash_flow": 12_500.0,
                            },
                        }
                    },
                    "gross": {
                        "summary": {
                            "period_return": {"base": 4.34},
                            "annualized_return": {"base": 4.34},
                            "economics": {
                                "begin_market_value": 470_000.0,
                                "end_market_value": 508_870.0,
                                "beginning_cash_flow": 15_000.0,
                                "ending_cash_flow": -2_500.0,
                                "flow_adjusted_end_market_value": 496_370.0,
                                "fees": 0.0,
                                "net_cash_flow": 12_500.0,
                            },
                        }
                    },
                },
                "money_weighted_return": {
                    "period_return": 4.11,
                    "annualized_return": 4.11,
                    "holding_period_return": 4.11,
                    "input_mode": "stateful",
                    "method": "XIRR",
                    "status": "CALCULATED",
                    "reason_codes": [],
                    "warnings": [],
                    "is_annualized_primary": True,
                    "is_approximation": False,
                    "start_date": "2026-01-01",
                    "end_date": "2026-03-27",
                    "economics": {
                        "begin_market_value": 470_000.0,
                        "end_market_value": 508_870.0,
                        "beginning_cash_flow": 15_000.0,
                        "ending_cash_flow": -2_500.0,
                        "flow_adjusted_end_market_value": 496_370.0,
                        "fees": 0.0,
                        "net_cash_flow": 12_500.0,
                    },
                    "notes": ["cash-flow aware"],
                },
                "contribution": {
                    "metric_basis": "NET",
                    "summary": {
                        "portfolio_contribution": 4.3,
                        "coverage_mv_pct": 98.7,
                        "weighting_scheme": "average_weight",
                        "local_contribution": 4.0,
                        "fx_contribution": 0.3,
                    },
                    "levels": [
                        {
                            "level": 1,
                            "name": "asset_class",
                            "rows": [
                                {
                                    "key": {"asset_class": "Equity"},
                                    "contribution": 3.2,
                                    "weight_avg": 32.0,
                                    "return": 9.2,
                                    "local_contribution": 3.0,
                                    "fx_contribution": 0.2,
                                },
                                {
                                    "key": {"asset_class": "Fixed Income"},
                                    "contribution": 0.7,
                                    "weight_avg": 21.0,
                                    "return": 2.6,
                                    "local_contribution": 0.6,
                                    "fx_contribution": 0.1,
                                },
                            ],
                        }
                    ],
                    "position_contributions": [
                        {
                            "position_id": "SEC_AAPL_US",
                            "total_contribution": 1.93,
                            "average_weight": 8.78,
                            "total_return": 28.05,
                            "local_contribution": 1.76,
                            "fx_contribution": 0.17,
                        },
                        {
                            "position_id": "SEC_ETF_WORLD_USD",
                            "total_contribution": 0.71,
                            "average_weight": 1.81,
                            "total_return": 18.88,
                            "local_contribution": 0.68,
                            "fx_contribution": 0.03,
                        },
                    ],
                },
                "attribution": {
                    "metric_basis": "NET",
                    "model": "BF",
                    "linking": "carino",
                    "benchmark_context": {
                        "benchmark_id": "BMK_PB_GLOBAL_BALANCED_60_40",
                        "return_source": "calculated",
                    },
                    "result": {
                        "status": "partial",
                        "reason_codes": ["off_benchmark_exposure"],
                        "reasons": [
                            {
                                "code": "off_benchmark_exposure",
                                "severity": "warning",
                                "message": (
                                    "Portfolio-only exposure was found in the attribution set."
                                ),
                                "affected_group_count": 1,
                            }
                        ],
                        "supportability_evidence": {
                            "portfolio_only_group_count": 1,
                            "benchmark_only_group_count": 0,
                            "unclassified_group_count": 0,
                            "missing_benchmark_return_count": 0,
                            "negative_weight_count": 0,
                            "zero_portfolio_exposure_count": 0,
                            "currency_attribution_status": "not_requested",
                            "linking_status": "linked",
                        },
                        "reconciliation": {
                            "total_active_return": 0.3,
                            "sum_of_effects": 0.28,
                            "residual": 0.02,
                            "residual_materiality": {
                                "classification": "watch",
                                "treatment": "review",
                                "absolute_residual": 0.02,
                                "warning_threshold": 0.001,
                                "material_threshold": 0.01,
                            },
                        },
                        "levels": [
                            {
                                "dimension": "asset_class",
                                "totals": {
                                    "allocation": -0.04,
                                    "selection": 0.25,
                                    "interaction": 0.07,
                                    "total_effect": 0.28,
                                },
                                "rows": [
                                    {
                                        "key": {"asset_class": "Equity"},
                                        "portfolio_weight_avg": 32.0,
                                        "benchmark_weight_avg": 60.0,
                                        "portfolio_return": 9.2,
                                        "benchmark_return": 7.6,
                                        "allocation": -0.14,
                                        "selection": 0.32,
                                        "interaction": 0.04,
                                        "total_effect": 0.22,
                                    }
                                ],
                            }
                        ],
                    },
                },
            },
            "YTD": {
                "benchmark": {
                    "benchmark_id": "BMK_PB_GLOBAL_BALANCED_60_40",
                    "return_source": "calculated",
                    "input_mode": "stateful",
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
                                "beginning_cash_flow": 30_000.0,
                                "ending_cash_flow": -7_500.0,
                                "flow_adjusted_end_market_value": 486_370.0,
                                "fees": 0.0,
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
                                "beginning_cash_flow": 30_000.0,
                                "ending_cash_flow": -7_500.0,
                                "flow_adjusted_end_market_value": 486_370.0,
                                "fees": 0.0,
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
                    "holding_period_return": 3.05,
                    "input_mode": "stateful",
                    "method": "XIRR",
                    "status": "CALCULATED",
                    "reason_codes": [],
                    "warnings": [],
                    "is_annualized_primary": True,
                    "is_approximation": False,
                    "start_date": "2026-01-01",
                    "end_date": "2026-03-27",
                    "economics": {
                        "begin_market_value": 450_000.0,
                        "end_market_value": 508_870.0,
                        "beginning_cash_flow": 30_000.0,
                        "ending_cash_flow": -7_500.0,
                        "flow_adjusted_end_market_value": 486_370.0,
                        "fees": 0.0,
                        "net_cash_flow": 22_500.0,
                    },
                    "notes": ["cash-flow aware"],
                },
                "contribution": {
                    "metric_basis": "NET",
                    "summary": {
                        "portfolio_contribution": 15.1,
                        "coverage_mv_pct": 96.4,
                        "weighting_scheme": "average_weight",
                        "local_contribution": 13.9,
                        "fx_contribution": 1.2,
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
                            "total_contribution": 5.43,
                            "average_weight": 8.78,
                            "total_return": 76.05,
                            "local_contribution": 5.12,
                            "fx_contribution": 0.31,
                        },
                        {
                            "position_id": "SEC_ETF_WORLD_USD",
                            "total_contribution": 1.31,
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
                        "benchmark_id": "BMK_PB_GLOBAL_BALANCED_60_40",
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
                    "benchmark_id": "BMK_PB_GLOBAL_BALANCED_60_40",
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
    if include_detail_blocks:
        return payload

    for period_payload in payload["results_by_period"].values():
        if isinstance(period_payload, dict):
            period_payload.pop("contribution", None)
            period_payload.pop("attribution", None)
    return payload


def _twr_payload_for_period(result_key: str, source_label: str) -> dict:
    source = _workspace_summary_payload()["results_by_period"][source_label]
    return {
        "benchmark_context": {
            "benchmark_id": "BMK_PB_GLOBAL_BALANCED_60_40",
            "return_source": "calculated",
            "supportability_evidence": {
                "currency_state": "fx_decomposed",
                "calendar_alignment_state": "partial_overlap",
                "missing_benchmark_date_count": 1,
                "warning_codes": ["BENCHMARK_CALENDAR_GAP"],
            },
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


def _contribution_payload(*, dimension: str) -> dict:
    return {
        "source_economics_evidence": {
            "status": "SOURCE_LIMITED",
            "reason_codes": [
                "LOTUS_CORE_ANALYTICS_INPUTS_USED",
                "COMPONENT_PNL_NOT_SOURCE_AUTHORED",
            ],
            "source_contracts": ["PortfolioTimeseriesInput:v1", "PositionTimeseriesInput:v1"],
            "available_economics": ["portfolio_market_values", "position_market_values"],
            "unsupported_economics": ["income_pnl", "tax_pnl"],
            "degraded_economics": ["unsupported_cash_flow_types"],
            "source_snapshot_count": 2,
        },
        "results_by_period": {
            "YTD": {
                "summary": {
                    "portfolio_contribution": 5.2,
                    "coverage_mv_pct": 97.4,
                    "weighting_scheme": "average_weight",
                    "local_contribution": 4.7,
                    "fx_contribution": 0.5,
                },
                "total_portfolio_return": 6.4,
                "smoothing_evidence": {
                    "status": "APPLIED",
                    "reason_codes": ["CARINO_FACTOR_APPLIED"],
                    "linked_return": 6.4,
                    "raw_contribution": 5.9,
                    "final_contribution": 5.2,
                    "smoothing_residual": 0.0,
                },
                "levels": [
                    {
                        "level": 1,
                        "name": dimension,
                        "rows": [
                            {
                                "key": {
                                    dimension: ("Technology" if dimension != "currency" else "USD")
                                },
                                "contribution": 3.1,
                                "weight_avg": 42.0,
                                "local_contribution": 2.8,
                                "fx_contribution": 0.3,
                            }
                        ],
                    }
                ],
                "position_contributions": [
                    {
                        "position_id": "AAPL_US",
                        "total_contribution": 1.55,
                        "average_weight": 8.6,
                        "total_return": 28.4,
                        "local_contribution": 1.33,
                        "fx_contribution": 0.22,
                    }
                ],
            }
        },
    }


def _attribution_payload(*, dimension: str, report_start_date: str, report_end_date: str) -> dict:
    month = report_start_date[:7]
    totals_by_month = {
        "2026-01": {"allocation": 0.12, "selection": 0.08, "interaction": 0.02, "total": 0.22},
        "2026-02": {"allocation": -0.04, "selection": 0.11, "interaction": 0.01, "total": 0.08},
        "2026-03": {"allocation": 0.05, "selection": -0.02, "interaction": 0.01, "total": 0.04},
    }
    totals = totals_by_month[month]
    return {
        "benchmark_context": {
            "benchmark_id": "BMK_PB_GLOBAL_BALANCED_60_40",
            "return_source": "calculated",
        },
        "results_by_period": {
            "EXPLICIT": {
                "status": "partial",
                "reason_codes": ["off_benchmark_exposure"],
                "reasons": [
                    {
                        "code": "off_benchmark_exposure",
                        "severity": "warning",
                        "message": "Portfolio-only exposure was found in the attribution set.",
                        "affected_group_count": 1,
                    }
                ],
                "supportability_evidence": {
                    "portfolio_only_group_count": 1,
                    "benchmark_only_group_count": 0,
                    "unclassified_group_count": 0,
                    "missing_benchmark_return_count": 0,
                    "negative_weight_count": 0,
                    "zero_portfolio_exposure_count": 0,
                    "currency_attribution_status": "not_requested",
                    "linking_status": "linked",
                },
                "reconciliation": {
                    "total_active_return": totals["total"],
                    "sum_of_effects": totals["total"],
                    "residual": 0.0,
                    "residual_materiality": {
                        "classification": "immaterial",
                        "treatment": "no_action",
                        "absolute_residual": 0.0,
                        "warning_threshold": 0.001,
                        "material_threshold": 0.01,
                    },
                },
                "levels": [
                    {
                        "dimension": dimension,
                        "totals": {
                            "allocation": totals["allocation"],
                            "selection": totals["selection"],
                            "interaction": totals["interaction"],
                            "total_effect": totals["total"],
                        },
                        "groups": [
                            {
                                "key": {dimension: "Equity" if dimension != "currency" else "USD"},
                                "portfolio_weight_avg": 61.0,
                                "benchmark_weight_avg": 58.0,
                                "portfolio_return": 7.4,
                                "benchmark_return": 6.8,
                                "allocation": totals["allocation"],
                                "selection": totals["selection"],
                                "interaction": totals["interaction"],
                                "total_effect": totals["total"],
                            }
                        ],
                    }
                ],
            }
        },
    }


def _attribution_detail_payload(*, dimension: str) -> dict:
    return {
        "benchmark_context": {
            "benchmark_id": "BMK_PB_GLOBAL_BALANCED_60_40",
            "return_source": "calculated",
        },
        "results_by_period": {
            "YTD": {
                "status": "partial",
                "reason_codes": ["off_benchmark_exposure"],
                "reasons": [
                    {
                        "code": "off_benchmark_exposure",
                        "severity": "warning",
                        "message": "Portfolio-only exposure was found in the attribution set.",
                        "affected_group_count": 1,
                    }
                ],
                "supportability_evidence": {
                    "portfolio_only_group_count": 1,
                    "benchmark_only_group_count": 0,
                    "unclassified_group_count": 0,
                    "missing_benchmark_return_count": 0,
                    "negative_weight_count": 0,
                    "zero_portfolio_exposure_count": 0,
                    "currency_attribution_status": "not_requested",
                    "linking_status": "linked",
                },
                "reconciliation": {
                    "total_active_return": 0.52,
                    "sum_of_effects": 0.5,
                    "residual": 0.02,
                    "residual_materiality": {
                        "classification": "watch",
                        "treatment": "review",
                        "absolute_residual": 0.02,
                        "warning_threshold": 0.001,
                        "material_threshold": 0.01,
                    },
                },
                "levels": [
                    {
                        "dimension": dimension,
                        "totals": {
                            "allocation": 0.18,
                            "selection": 0.24,
                            "interaction": 0.03,
                            "total_effect": 0.45,
                        },
                        "groups": [
                            {
                                "key": {
                                    dimension: (
                                        "Singapore" if dimension == "country" else "Technology"
                                    )
                                },
                                "portfolio_weight_avg": 61.0,
                                "benchmark_weight_avg": 58.0,
                                "portfolio_return": 7.4,
                                "benchmark_return": 6.8,
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
    }


def _many_contribution_rows_payload(*, dimension: str) -> dict:
    payload = _contribution_payload(dimension=dimension)
    payload["results_by_period"]["YTD"]["levels"][0]["rows"] = [
        {
            "key": {dimension: f"group-{index:02d}"},
            "contribution": 0.1,
            "weight_avg": 5.0,
            "local_contribution": 0.08,
            "fx_contribution": 0.02,
        }
        for index in range(12)
    ]
    payload["results_by_period"]["YTD"]["levels"][0]["total_contribution"] = 1.2
    payload["results_by_period"]["YTD"]["position_contributions"] = [
        {
            "position_id": f"POSITION_{index:02d}",
            "total_contribution": 0.1,
            "average_weight": 5.0,
            "total_return": 1.0,
            "local_contribution": 0.08,
            "fx_contribution": 0.02,
        }
        for index in range(12)
    ]
    payload["results_by_period"]["YTD"]["summary"]["portfolio_contribution"] = 1.2
    payload["results_by_period"]["YTD"]["total_portfolio_return"] = 1.2
    return payload


def _many_attribution_groups_payload(*, dimension: str) -> dict:
    payload = _attribution_detail_payload(dimension=dimension)
    payload["results_by_period"]["YTD"]["levels"][0]["groups"] = [
        {
            "key": {dimension: f"group-{index:02d}"},
            "portfolio_weight_avg": 5.0,
            "benchmark_weight_avg": 4.0,
            "portfolio_return": 1.0,
            "benchmark_return": 0.8,
            "allocation": 0.01,
            "selection": 0.02,
            "interaction": 0.0,
            "total_effect": 0.03,
        }
        for index in range(12)
    ]
    payload["results_by_period"]["YTD"]["levels"][0]["totals"] = {
        "allocation": 0.12,
        "selection": 0.24,
        "interaction": 0.0,
        "total_effect": 0.36,
    }
    payload["results_by_period"]["YTD"]["reconciliation"] = {
        "total_active_return": 0.36,
        "sum_of_effects": 0.36,
        "residual": 0.0,
    }
    return payload


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
                        "benchmark_id": "BMK_PB_GLOBAL_BALANCED_60_40",
                        "benchmark_name": "Global Balanced 60/40",
                        "benchmark_currency": "USD",
                        "benchmark_type": "composite",
                        "benchmark_family": "Balanced",
                        "benchmark_provider": "Lotus",
                    },
                    {
                        "benchmark_id": "BMK_PB_GLOBAL_BALANCED_60_40",
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
        assigned_benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
        warnings=warnings,
        partial_failures=partial_failures,
    )

    assert [option.benchmark_code for option in options] == [
        "BMK_PB_GLOBAL_BALANCED_60_40",
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
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )

    assert response.portfolio.portfolio_id == "DEMO_ADV_USD_001"
    assert response.segment == "asset_class"
    assert response.report_start_date == "2026-01-01"
    assert response.report_end_date == "2026-03-27"
    assert response.net_performance.portfolio_return_pct == 15.1
    assert response.net_performance.benchmark_return_pct == 14.72
    assert response.net_performance.active_return_pct == 0.38
    assert response.net_performance.benchmark_input_mode == "stateful"
    assert response.net_performance.begin_market_value == 450000.0
    assert response.net_performance.end_market_value == 508870.0
    assert response.net_performance.beginning_cash_flow == 30000.0
    assert response.net_performance.ending_cash_flow == -7500.0
    assert response.net_performance.flow_adjusted_end_market_value == 486370.0
    assert response.net_performance.net_cash_flow == 22500.0
    assert response.net_performance.fees == 0.0
    assert response.gross_performance.portfolio_return_pct == 15.13
    assert response.money_weighted_return is not None
    assert response.money_weighted_return.money_weighted_return_pct == 14.05
    assert response.money_weighted_return.holding_period_return_pct == 3.05
    assert response.money_weighted_return.input_mode == "stateful"
    assert response.money_weighted_return.begin_market_value == 450000.0
    assert response.money_weighted_return.end_market_value == 508870.0
    assert response.money_weighted_return.beginning_cash_flow == 30000.0
    assert response.money_weighted_return.ending_cash_flow == -7500.0
    assert response.money_weighted_return.flow_adjusted_end_market_value == 486370.0
    assert response.money_weighted_return.net_cash_flow == 22500.0
    assert response.money_weighted_return.fees == 0.0
    assert len(response.net_chart) == 3
    assert response.net_chart[-1].cumulative_active_return_pct == 0.38
    assert response.contribution is not None
    assert response.contribution.total_portfolio_return_pct == 6.4
    assert response.contribution.smoothing_evidence is not None
    assert response.contribution.smoothing_evidence.status == "APPLIED"
    assert response.contribution.source_economics_evidence is not None
    assert response.contribution.source_economics_evidence.status == "SOURCE_LIMITED"
    assert response.contribution.levels[0].rows[0].weight_avg_pct == 42.0
    assert response.contribution.levels[0].total_weight_avg_pct is None
    assert response.contribution.position_rows[0].position_id == "AAPL_US"
    assert response.attribution is not None
    assert response.attribution.benchmark_id == "BMK_PB_GLOBAL_BALANCED_60_40"
    assert response.attribution.status == "partial"
    assert response.attribution.reason_codes == ["off_benchmark_exposure"]
    assert response.attribution.reasons[0].affected_group_count == 1
    assert response.attribution.residual_materiality is not None
    assert response.attribution.residual_materiality.classification == "immaterial"
    assert response.attribution.residual_materiality.treatment == "no_action"
    assert response.attribution.supportability_evidence is not None
    assert response.attribution.supportability_evidence.portfolio_only_group_count == 1
    assert response.attribution.supportability_evidence.linking_status == "linked"
    assert response.attribution.levels[0].rows[0].portfolio_weight_avg_pct == 61.0
    assert response.attribution.levels[0].rows[0].benchmark_return_pct == 6.8
    assert response.benchmark_options[0].is_assigned is True
    assert response.benchmark_options[0].benchmark_code == "BMK_PB_GLOBAL_BALANCED_60_40"
    assert response.capabilities.return_path.state == "supported"
    assert response.capabilities.return_path.earliest_available_date == "2026-01-01"
    assert response.capabilities.return_path.latest_available_date == "2026-03-27"
    assert response.capabilities.return_path.supported_frequencies == ["monthly", "quarterly"]
    assert response.capabilities.benchmark_comparison.state == "supported"
    assert response.capabilities.contribution_ranking.state == "supported"
    assert response.capabilities.contribution_ranking.coverage_level == "position"
    assert response.capabilities.contribution_ranking.supported_dimensions == [
        "asset_class",
        "sector",
        "country",
    ]
    assert response.capabilities.attribution_detail.state == "supported"
    assert response.capabilities.attribution_detail.supported_dimensions == [
        "asset_class",
        "sector",
        "country",
        "currency",
    ]
    assert response.capabilities.attribution_detail.supported_frequencies == [
        "monthly",
        "quarterly",
    ]
    assert response.capabilities.evidence.state == "supported"
    assert response.evidence_view is not None
    assert response.evidence_view.state == "supported"
    assert response.evidence_view.calculations[0].calculation_role == "workspace_summary"
    assert response.evidence_view.calculations[0].execution_status == "complete"
    assert response.evidence_view.calculations[0].lineage_status == "complete"
    assert response.evidence_view.as_of_date == "2026-03-27"
    assert response.evidence_view.period == "YTD"
    assert response.evidence_view.basis == "NET"
    assert response.evidence_view.benchmark_code == "BMK_PB_GLOBAL_BALANCED_60_40"
    assert response.evidence_view.calculation_scope == "performance_workspace"
    assert response.evidence_view.source_services == ["lotus-performance"]
    assert response.evidence_view.input_freshness == {
        "performance": "fresh",
        "benchmark": "fresh",
    }
    assert response.evidence_view.methodology_references == ["lotus-performance/docs/methodologies"]
    assert response.evidence_view.calculation_versions == {
        "analytics_types": "ATTRIBUTION,CONTRIBUTION,WORKSPACE_SUMMARY",
        "gateway_contract": "v1",
    }
    assert response.evidence_view.coverage == {
        "supported_dimensions": ["asset_class", "country", "currency", "sector"],
        "unsupported_dimensions": ["issuer"],
    }
    assert response.evidence_view.fallbacks == []
    assert response.evidence_view.limitations == []
    assert response.evidence_view.source_supportability == []
    assert (
        response.evidence_view.calculations[0]
        .artifacts[0]
        .url.startswith("/api/v1/workbench/DEMO_ADV_USD_001/performance/evidence/artifacts/")
    )
    assert response.warnings == ["FOUNDATION_WARNING"]
    assert response.partial_failures[0].error_code == "STALE_REPORTING"

    assert analytics_client.workspace_summary_calls[0]["chart_frequency"] == "monthly"
    assert analytics_client.workspace_summary_calls[0]["segment"] == "asset_class"
    assert analytics_client.workspace_summary_calls[0]["include_detail_blocks"] is False
    assert analytics_client.execution_calls == [
        "calc-workspace-summary",
        "calc-contribution",
        "calc-attribution",
    ]
    assert analytics_client.lineage_calls == [
        "calc-workspace-summary",
        "calc-contribution",
        "calc-attribution",
    ]
    assert query_client.reference_calls == 1
    assert query_client.reference_kwargs[0]["consumer_system"] == "lotus-gateway"
    assert query_client.reference_kwargs[0]["as_of_date"] == "2026-03-27"
    assert query_client.benchmark_assignment_calls == []
    assert query_client.benchmark_catalog_calls[0]["as_of_date"] == "2026-03-27"
    assert query_client.benchmark_catalog_calls[0]["benchmark_currency"] == "USD"
    assert query_client.benchmark_catalog_calls[0]["benchmark_status"] == "active"
    assert query_client.benchmark_catalog_calls[0]["benchmark_type"] == "composite"


def test_performance_workspace_service_preserves_twr_benchmark_supportability_evidence():
    service = PerformanceWorkspaceService(
        workbench_service=_StubWorkbenchService(),
        analytics_client=_StubAnalyticsClient(),
        lotus_core_query_client=_StubLotusCoreQueryClient(),
    )

    summary, _ = service._parse_twr_result(
        result=(200, _twr_payload_for_period("YTD", "YTD")),
        metric_basis="NET",
        chart_frequency="monthly",
        requested_period="YTD",
        warnings=[],
        partial_failures=[],
    )

    assert summary.benchmark_id == "BMK_PB_GLOBAL_BALANCED_60_40"
    assert summary.benchmark_return_source == "calculated"
    assert summary.benchmark_currency_state == "fx_decomposed"
    assert summary.benchmark_calendar_alignment_state == "partial_overlap"
    assert summary.benchmark_missing_date_count == 1
    assert summary.benchmark_warning_codes == ["BENCHMARK_CALENDAR_GAP"]


@pytest.mark.asyncio
async def test_performance_workspace_service_projects_summary_contract():
    analytics_client = _StubAnalyticsClient()
    service = PerformanceWorkspaceService(
        workbench_service=_StubWorkbenchService(),
        analytics_client=analytics_client,
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
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )

    assert response.portfolio_id == "DEMO_ADV_USD_001"
    assert response.net_performance.portfolio_return_pct == 15.1
    assert response.gross_performance.portfolio_return_pct == 15.13
    assert response.money_weighted_return is not None
    assert response.money_weighted_return.input_mode == "stateful"
    assert response.money_weighted_return.method == "XIRR"
    assert response.money_weighted_return.status == "CALCULATED"
    assert response.money_weighted_return.reason_codes == []
    assert response.money_weighted_return.warnings == []
    assert response.money_weighted_return.is_annualized_primary is True
    assert response.money_weighted_return.is_approximation is False
    assert response.money_weighted_return.flow_adjusted_end_market_value == 486370.0
    assert response.benchmark_options[0].benchmark_name == "Global Balanced 60/40"
    assert response.capabilities.return_path.state == "supported"
    assert response.capabilities.contribution_ranking.state == "supported"
    assert response.capabilities.contribution_detail.state == "supported"
    assert response.capabilities.attribution_detail.state == "supported"
    assert response.capabilities.evidence.state == "supported"
    assert response.evidence_view is not None
    assert [item.calculation_role for item in response.evidence_view.calculations] == [
        "workspace_summary"
    ]
    assert analytics_client.workspace_summary_calls[0]["include_detail_blocks"] is False
    assert not hasattr(response, "net_chart")
    assert not hasattr(response, "contribution")


@pytest.mark.asyncio
async def test_performance_workspace_summary_preserves_source_calculation_supportability():
    class _StaleSupportabilityAnalyticsClient(_StubAnalyticsClient):
        async def get_workspace_summary(self, **kwargs):
            status_code, payload = await super().get_workspace_summary(**kwargs)
            payload["metadata"] = {
                "calculation_supportability": {
                    "state": "stale",
                    "reason": "Source data window stale",
                    "freshness_bucket": "stale",
                    "source_service": "lotus-performance",
                }
            }
            return status_code, payload

    service = PerformanceWorkspaceService(
        workbench_service=_StubWorkbenchService(),
        analytics_client=_StaleSupportabilityAnalyticsClient(),
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
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )

    assert response.evidence_view is not None
    assert response.evidence_view.state == "partial"
    assert response.evidence_view.reason == "Source data window stale"
    assert response.evidence_view.limitations == ["Source data window stale"]
    assert response.capabilities.evidence.state == "partial"
    assert response.capabilities.evidence.reason == "Source data window stale"
    assert response.evidence_view.source_supportability[0].model_dump() == {
        "key": "source_calculation",
        "state": "partial",
        "reason": "Source data window stale",
        "freshness_bucket": "stale",
        "source_service": "lotus-performance",
    }


@pytest.mark.asyncio
async def test_performance_workspace_service_reuses_cached_workspace_summary_result():
    analytics_client = _StubAnalyticsClient()
    workbench_service = _StubWorkbenchService()
    query_client = _StubLotusCoreQueryClient()
    service = PerformanceWorkspaceService(
        workbench_service=workbench_service,
        analytics_client=analytics_client,
        lotus_core_query_client=query_client,
        upstream_cache_ttl_seconds=60,
    )

    first_response = await service.get_performance_workspace_summary(
        portfolio_id="DEMO_ADV_USD_001",
        correlation_id="corr-performance-first",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )
    second_response = await service.get_performance_workspace_summary(
        portfolio_id="DEMO_ADV_USD_001",
        correlation_id="corr-performance-second",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )

    assert first_response.net_performance.portfolio_return_pct == 15.1
    assert second_response.net_performance.portfolio_return_pct == 15.1
    assert workbench_service.overview_calls == 1
    assert query_client.reference_calls == 1
    assert len(query_client.benchmark_catalog_calls) == 1
    assert len(analytics_client.workspace_summary_calls) == 1
    assert analytics_client.workspace_summary_calls[0]["correlation_id"] == "corr-performance-first"


@pytest.mark.asyncio
async def test_performance_workspace_service_clear_upstream_cache_forces_summary_refresh():
    analytics_client = _StubAnalyticsClient()
    service = PerformanceWorkspaceService(
        workbench_service=_StubWorkbenchService(),
        analytics_client=analytics_client,
        lotus_core_query_client=_StubLotusCoreQueryClient(),
        upstream_cache_ttl_seconds=60,
    )

    await service.get_performance_workspace_summary(
        portfolio_id="DEMO_ADV_USD_001",
        correlation_id="corr-performance-first",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )
    service.clear_upstream_cache()
    await service.get_performance_workspace_summary(
        portfolio_id="DEMO_ADV_USD_001",
        correlation_id="corr-performance-second",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )

    assert len(analytics_client.workspace_summary_calls) == 2
    assert (
        analytics_client.workspace_summary_calls[1]["correlation_id"] == "corr-performance-second"
    )


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

    assert response.benchmark_code == "BMK_PB_GLOBAL_BALANCED_60_40"
    assert analytics_client.workspace_summary_calls[0]["benchmark_id"] == (
        "BMK_PB_GLOBAL_BALANCED_60_40"
    )
    assert query_client.benchmark_assignment_calls[0]["portfolio_id"] == "DEMO_ADV_USD_001"
    assert query_client.benchmark_assignment_calls[0]["as_of_date"] == "2026-03-27"
    assert query_client.benchmark_assignment_calls[0]["reporting_currency"] == "USD"


@pytest.mark.asyncio
async def test_performance_workspace_service_does_not_negative_cache_missing_benchmark_assignment():
    class _LaggedBenchmarkAssignmentClient(_StubLotusCoreQueryClient):
        async def get_benchmark_assignment(self, **kwargs):
            self.benchmark_assignment_calls.append(kwargs)
            if len(self.benchmark_assignment_calls) == 1:
                return 200, {"benchmark_id": None, "assignment_status": "not_found"}
            return 200, {
                "benchmark_id": "BMK_PB_GLOBAL_BALANCED_60_40",
                "assignment_status": "active",
            }

    analytics_client = _StubAnalyticsClient()
    query_client = _LaggedBenchmarkAssignmentClient()
    service = PerformanceWorkspaceService(
        workbench_service=_StubWorkbenchService(),
        analytics_client=analytics_client,
        lotus_core_query_client=query_client,
    )

    await service.get_performance_workspace_summary(
        portfolio_id="DEMO_ADV_USD_001",
        correlation_id="corr-performance-first",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code=None,
    )
    second_response = await service.get_performance_workspace_summary(
        portfolio_id="DEMO_ADV_USD_001",
        correlation_id="corr-performance-second",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code=None,
    )

    assert analytics_client.workspace_summary_calls[0]["benchmark_id"] is None
    assert second_response.benchmark_code == "BMK_PB_GLOBAL_BALANCED_60_40"
    assert analytics_client.workspace_summary_calls[1]["benchmark_id"] == (
        "BMK_PB_GLOBAL_BALANCED_60_40"
    )
    assert len(query_client.benchmark_assignment_calls) == 2


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
        period="YTD",
        detail_basis="NET",
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
        chart_frequency="monthly",
    )

    assert response.portfolio_id == "DEMO_ADV_USD_001"
    assert response.benchmark_code == "BMK_PB_GLOBAL_BALANCED_60_40"
    assert response.reporting_currency == "USD"
    assert response.period == "YTD"
    assert response.report_start_date == "2026-01-01"
    assert response.report_end_date == "2026-03-27"
    assert [row.period for row in response.rows] == ["MTD", "QTD", "YTD"]
    assert response.rows[0].portfolio_return_pct == 1.2
    assert response.rows[0].net_return_pct == 1.2
    assert response.rows[0].gross_return_pct == 1.22
    assert response.rows[2].benchmark_return_pct == 14.72
    assert response.rows[2].begin_market_value == 450000.0
    assert response.rows[2].beginning_cash_flow == 30000.0
    assert response.rows[2].ending_cash_flow == -7500.0
    assert response.rows[2].flow_adjusted_end_market_value == 486370.0
    assert response.rows[2].active_return_pct == 0.38
    assert response.rows[0].period_start == "2026-03-01"
    assert response.rows[1].period_start == "2026-01-01"
    assert response.rows[2].period_start == "2026-01-01"
    assert response.rows[2].period_end == "2026-03-27"
    assert len(analytics_client.workspace_summary_calls) == 3
    assert analytics_client.workspace_summary_calls[0]["period"] == "EXPLICIT"
    assert analytics_client.workspace_summary_calls[0]["report_start_date"] == "2026-03-01"
    assert analytics_client.workspace_summary_calls[1]["period"] == "EXPLICIT"
    assert analytics_client.workspace_summary_calls[1]["report_start_date"] == "2026-01-01"
    assert analytics_client.workspace_summary_calls[2]["period"] == "YTD"
    assert analytics_client.workspace_summary_calls[0]["include_detail_blocks"] is False
    assert [
        analysis["period"] for analysis in analytics_client.workspace_summary_calls[0]["periods"]
    ] == ["EXPLICIT"]
    assert [
        analysis["period"] for analysis in analytics_client.workspace_summary_calls[1]["periods"]
    ] == ["EXPLICIT"]
    assert [
        analysis["period"] for analysis in analytics_client.workspace_summary_calls[2]["periods"]
    ] == ["YTD"]


@pytest.mark.asyncio
async def test_workspace_service_maps_position_contributions_from_upstream_contract():
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
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )

    assert response.contribution is not None
    assert [row.position_id for row in response.contribution.position_rows] == ["AAPL_US"]
    assert response.contribution.position_rows[0].contribution_pct == 1.55
    assert response.contribution.weighting_scheme == "average_weight"
    assert response.contribution.portfolio_contribution_pct == 5.2
    assert response.contribution.total_portfolio_return_pct == 6.4
    assert response.contribution.coverage_mv_pct == 97.4
    assert response.contribution.portfolio_local_contribution_pct == 4.7
    assert response.contribution.portfolio_fx_contribution_pct == 0.5
    assert response.contribution.levels[0].total_contribution_pct == 3.1
    assert response.contribution.levels[0].total_portfolio_return_pct == 6.4
    assert response.contribution.smoothing_evidence is not None
    assert response.contribution.smoothing_evidence.raw_contribution_pct == 5.9
    assert response.contribution.smoothing_evidence.linked_return_pct == 6.4
    assert response.contribution.source_economics_evidence is not None
    assert response.contribution.source_economics_evidence.source_contracts == [
        "PortfolioTimeseriesInput:v1",
        "PositionTimeseriesInput:v1",
    ]
    assert response.contribution.source_economics_evidence.unsupported_economics == [
        "income_pnl",
        "tax_pnl",
    ]
    assert analytics_client.workspace_summary_calls[0]["reporting_currency"] == "USD"
    assert analytics_client.workspace_summary_calls[0]["include_detail_blocks"] is False
    assert response.capabilities.contribution_ranking.state == "supported"


@pytest.mark.asyncio
async def test_workspace_service_preserves_full_contribution_row_coverage():
    class _ManyContributionRowsAnalyticsClient(_StubAnalyticsClient):
        async def get_contribution_analytics(self, **kwargs):
            self.contribution_calls.append(kwargs)
            payload = _many_contribution_rows_payload(dimension=str(kwargs["dimension"]))
            payload["calculation_id"] = "calc-contribution"
            return 200, payload

        async def get_attribution_analytics(self, **kwargs):
            self.attribution_calls.append(kwargs)
            payload = _attribution_detail_payload(dimension=str(kwargs["dimension"]))
            payload["calculation_id"] = "calc-attribution"
            return 200, payload

    service = PerformanceWorkspaceService(
        workbench_service=_StubWorkbenchService(),
        analytics_client=_ManyContributionRowsAnalyticsClient(),
        lotus_core_query_client=_StubLotusCoreQueryClient(),
    )

    response = await service.get_performance_workspace_details(
        portfolio_id="DEMO_ADV_USD_001",
        correlation_id="corr-performance",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="sector",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )

    assert response.contribution is not None
    assert len(response.contribution.levels[0].rows) == 12
    assert len(response.contribution.position_rows) == 12
    assert response.contribution.levels[0].total_contribution_pct == 1.2


@pytest.mark.asyncio
async def test_workspace_service_preserves_full_attribution_row_coverage():
    class _ManyAttributionRowsAnalyticsClient(_StubAnalyticsClient):
        async def get_contribution_analytics(self, **kwargs):
            self.contribution_calls.append(kwargs)
            payload = _contribution_payload(dimension=str(kwargs["dimension"]))
            payload["calculation_id"] = "calc-contribution"
            return 200, payload

        async def get_attribution_analytics(self, **kwargs):
            self.attribution_calls.append(kwargs)
            payload = _many_attribution_groups_payload(dimension=str(kwargs["dimension"]))
            payload["calculation_id"] = "calc-attribution"
            return 200, payload

    service = PerformanceWorkspaceService(
        workbench_service=_StubWorkbenchService(),
        analytics_client=_ManyAttributionRowsAnalyticsClient(),
        lotus_core_query_client=_StubLotusCoreQueryClient(),
    )

    response = await service.get_performance_workspace_details(
        portfolio_id="DEMO_ADV_USD_001",
        correlation_id="corr-performance",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="country",
        detail_basis="NET",
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )

    assert response.attribution is not None
    assert len(response.attribution.levels[0].rows) == 12
    assert response.attribution.levels[0].allocation_total_pct == 0.12
    assert response.attribution.levels[0].selection_total_pct == 0.24
    assert response.attribution.levels[0].total_effect_pct == 0.36


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
        period="YTD",
        detail_basis="NET",
        benchmark_code=None,
        chart_frequency="monthly",
    )

    assert response.benchmark_code == "BMK_PB_GLOBAL_BALANCED_60_40"
    assert analytics_client.workspace_summary_calls[0]["benchmark_id"] == (
        "BMK_PB_GLOBAL_BALANCED_60_40"
    )
    assert query_client.benchmark_assignment_calls[0]["portfolio_id"] == "DEMO_ADV_USD_001"
    assert query_client.benchmark_assignment_calls[0]["as_of_date"] == "2026-03-27"
    assert query_client.benchmark_assignment_calls[0]["reporting_currency"] == "USD"


@pytest.mark.asyncio
async def test_performance_workspace_service_normalizes_unsupported_horizon_frequency():
    analytics_client = _StubAnalyticsClient()
    service = PerformanceWorkspaceService(
        workbench_service=_StubWorkbenchService(),
        analytics_client=analytics_client,
        lotus_core_query_client=_StubLotusCoreQueryClient(),
    )

    response = await service.get_performance_horizon_comparison(
        portfolio_id="DEMO_ADV_USD_001",
        correlation_id="corr-performance",
        period="YTD",
        detail_basis="NET",
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
        chart_frequency="weekly",
    )

    assert response.chart_frequency == "monthly"
    assert response.requested_chart_frequency_supported is False
    assert "PERFORMANCE_HORIZON_CHART_FREQUENCY_NORMALIZED" in response.warnings
    assert analytics_client.workspace_summary_calls[0]["chart_frequency"] == "monthly"


@pytest.mark.asyncio
async def test_performance_workspace_service_builds_explicit_horizon_comparison_contract():
    analytics_client = _StubAnalyticsClient()
    service = PerformanceWorkspaceService(
        workbench_service=_StubWorkbenchService(),
        analytics_client=analytics_client,
        lotus_core_query_client=_StubLotusCoreQueryClient(),
    )

    response = await service.get_performance_horizon_comparison(
        portfolio_id="DEMO_ADV_USD_001",
        correlation_id="corr-performance",
        period="YTD",
        detail_basis="NET",
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
        chart_frequency="monthly",
        explicit_start_date="2026-01-01",
        explicit_end_date="2026-03-27",
    )

    assert [row.period for row in response.rows] == ["EXPLICIT"]
    assert response.rows[0].period_start == "2026-01-01"
    assert response.rows[0].period_end == "2026-03-27"
    assert analytics_client.workspace_summary_calls[0]["period"] == "EXPLICIT"
    assert analytics_client.workspace_summary_calls[0]["report_start_date"] == "2026-01-01"
    assert [
        analysis["period"] for analysis in analytics_client.workspace_summary_calls[0]["periods"]
    ] == ["EXPLICIT"]


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
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )

    assert response.portfolio_id == "DEMO_ADV_USD_001"
    assert response.chart_frequency == "monthly"
    assert [row.period_label for row in response.rows] == ["2026-01", "2026-02", "2026-03"]
    assert response.rows[0].allocation_pct == 0.12
    assert response.rows[0].status == "partial"
    assert response.rows[0].reason_codes == ["off_benchmark_exposure"]
    assert response.rows[0].residual_materiality is not None
    assert response.rows[0].residual_materiality.classification == "immaterial"
    assert response.rows[0].supportability_evidence is not None
    assert response.rows[0].supportability_evidence.portfolio_only_group_count == 1
    assert response.rows[1].selection_pct == 0.11
    assert response.rows[2].cumulative_total_effect_pct == 0.34
    assert analytics_client.attribution_calls[0]["period"] == "EXPLICIT"
    assert analytics_client.attribution_calls[0]["dimension"] == "asset_class"
    assert analytics_client.attribution_calls[-1]["report_end_date"] == "2026-03-27"


@pytest.mark.asyncio
async def test_performance_workspace_service_normalizes_unsupported_attribution_trend_controls():
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
        chart_frequency="weekly",
        attribution_dimension="issuer",
        detail_basis="NET",
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )

    assert response.chart_frequency == "monthly"
    assert response.attribution_dimension == "asset_class"
    assert response.requested_chart_frequency_supported is False
    assert response.requested_attribution_dimension_supported is False
    assert "PERFORMANCE_ATTRIBUTION_TREND_CHART_FREQUENCY_NORMALIZED" in response.warnings
    assert "PERFORMANCE_ATTRIBUTION_TREND_DIMENSION_NORMALIZED" in response.warnings
    assert analytics_client.attribution_calls[0]["dimension"] == "asset_class"


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

    assert response.benchmark_code == "BMK_PB_GLOBAL_BALANCED_60_40"
    assert analytics_client.attribution_calls[0]["benchmark_id"] == "BMK_PB_GLOBAL_BALANCED_60_40"
    assert query_client.benchmark_assignment_calls[0]["portfolio_id"] == "DEMO_ADV_USD_001"
    assert query_client.benchmark_assignment_calls[0]["as_of_date"] == "2026-03-27"
    assert query_client.benchmark_assignment_calls[0]["reporting_currency"] == "USD"


@pytest.mark.asyncio
async def test_performance_workspace_service_projects_detail_contract():
    analytics_client = _StubAnalyticsClient()
    query_client = _StubLotusCoreQueryClient()
    service = PerformanceWorkspaceService(
        workbench_service=_StubWorkbenchService(),
        analytics_client=analytics_client,
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
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )

    assert response.portfolio_id == "DEMO_ADV_USD_001"
    assert len(response.net_chart) == 3
    assert response.contribution is not None
    assert response.contribution.position_rows[0].position_id == "AAPL_US"
    assert response.attribution is not None
    assert response.attribution.benchmark_id == "BMK_PB_GLOBAL_BALANCED_60_40"
    assert response.capabilities.contribution_ranking.state == "supported"
    assert response.capabilities.attribution_detail.state == "supported"
    assert analytics_client.workspace_summary_calls[0]["include_detail_blocks"] is False
    assert response.segment == "asset_class"
    assert not hasattr(response, "overview")
    assert not hasattr(response, "net_performance")
    assert query_client.benchmark_catalog_calls == []


@pytest.mark.asyncio
async def test_performance_workspace_service_normalizes_qtd_workspace_summary_to_explicit():
    analytics_client = _StubAnalyticsClient()
    service = PerformanceWorkspaceService(
        workbench_service=_StubWorkbenchService(),
        analytics_client=analytics_client,
        lotus_core_query_client=_StubLotusCoreQueryClient(),
    )

    response = await service.get_performance_workspace_details(
        portfolio_id="DEMO_ADV_USD_001",
        correlation_id="corr-performance",
        period="QTD",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )

    assert response.period == "QTD"
    assert response.report_start_date == "2026-01-01"
    assert response.contribution is not None
    assert response.contribution.position_rows[0].position_id == "AAPL_US"
    assert analytics_client.workspace_summary_calls[0]["period"] == "EXPLICIT"
    assert analytics_client.workspace_summary_calls[0]["report_start_date"] == "2026-01-01"


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
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )

    assert response.portfolio_return_pct == 15.1
    assert response.benchmark_return_pct == 14.72
    assert response.excess_return_pct == 0.38
    assert response.report_start_date == "2026-01-01"
    assert response.report_end_date == "2026-03-27"
    assert response.sparkline[0].as_of_date == "2026-01-31"
    assert response.sparkline[0].portfolio_return_pct == 2.0
    assert query_client.benchmark_catalog_calls == []


@pytest.mark.asyncio
async def test_performance_workspace_service_marks_portfolio_performance_snapshot_unavailable():
    class _UnavailableSnapshotAnalyticsClient(_StubAnalyticsClient):
        async def get_workspace_summary(self, **kwargs):
            self.workspace_summary_calls.append(kwargs)
            return 503, {"detail": "workspace summary unavailable"}

    service = PerformanceWorkspaceService(
        workbench_service=_StubWorkbenchService(),
        analytics_client=_UnavailableSnapshotAnalyticsClient(),
        lotus_core_query_client=_StubLotusCoreQueryClient(),
    )

    response = await service.get_portfolio_performance_snapshot(
        portfolio_id="DEMO_ADV_USD_001",
        correlation_id="corr-performance",
        period="YTD",
        chart_frequency="monthly",
        detail_basis="NET",
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )

    assert response.portfolio_return_pct is None
    assert response.benchmark_return_pct is None
    assert response.excess_return_pct is None
    assert response.report_start_date == "2026-01-01"
    assert response.report_end_date == "2026-03-27"
    assert response.sparkline == []
    assert response.unavailable is not None
    assert response.unavailable.title == "Performance data unavailable"
    assert response.unavailable.requirements == [
        "valuation history",
        "cashflow history",
        "selected reporting period",
    ]
    assert "PERFORMANCE_WORKSPACE_SUMMARY_UNAVAILABLE" in response.warnings
    assert any(failure.error_code == "HTTP_503" for failure in response.partial_failures)


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
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )

    assert response.segment == "sector"
    assert response.contribution_dimension == "sector"
    assert response.attribution_dimension == "country"
    assert "PERFORMANCE_SEGMENTATION_ALIGNED_TO_SHARED_SOURCE_CONTRACT" in response.warnings
    assert analytics_client.workspace_summary_calls[0]["segment"] == "sector"
    assert analytics_client.workspace_summary_calls[0]["chart_frequency"] == "quarterly"


@pytest.mark.asyncio
async def test_performance_workspace_service_normalizes_unsupported_controls():
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
        chart_frequency="weekly",
        contribution_dimension="currency",
        attribution_dimension="issuer",
        detail_basis="NET",
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )

    assert response.chart_frequency == "monthly"
    assert response.contribution_dimension == "asset_class"
    assert response.attribution_dimension == "asset_class"
    assert response.requested_chart_frequency_supported is False
    assert response.requested_contribution_dimension_supported is False
    assert response.requested_attribution_dimension_supported is False
    assert "PERFORMANCE_CHART_FREQUENCY_NORMALIZED" in response.warnings
    assert "PERFORMANCE_CONTRIBUTION_DIMENSION_NORMALIZED" in response.warnings
    assert "PERFORMANCE_ATTRIBUTION_DIMENSION_NORMALIZED" in response.warnings
    assert analytics_client.workspace_summary_calls[0]["chart_frequency"] == "monthly"
    assert analytics_client.workspace_summary_calls[0]["segment"] == "asset_class"


@pytest.mark.asyncio
async def test_workspace_details_use_independent_dimensions_and_keep_segment_context():
    class _DetailAwareAnalyticsClient(_StubAnalyticsClient):
        async def get_contribution_analytics(self, **kwargs):
            self.contribution_calls.append(kwargs)
            payload = _contribution_payload(dimension=str(kwargs["dimension"]))
            payload["calculation_id"] = "calc-contribution"
            return 200, payload

        async def get_attribution_analytics(self, **kwargs):
            self.attribution_calls.append(kwargs)
            payload = _attribution_detail_payload(dimension=str(kwargs["dimension"]))
            payload["calculation_id"] = "calc-attribution"
            return 200, payload

    analytics_client = _DetailAwareAnalyticsClient()
    service = PerformanceWorkspaceService(
        workbench_service=_StubWorkbenchService(),
        analytics_client=analytics_client,
        lotus_core_query_client=_StubLotusCoreQueryClient(),
    )

    response = await service.get_performance_workspace_details(
        portfolio_id="DEMO_ADV_USD_001",
        correlation_id="corr-performance",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="sector",
        attribution_dimension="currency",
        detail_basis="NET",
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )

    assert response.contribution_dimension == "sector"
    assert response.attribution_dimension == "currency"
    assert response.segment == "sector"
    assert response.contribution is not None
    assert response.contribution.levels[0].name == "sector"
    assert response.attribution is not None
    assert response.attribution.levels[0].dimension == "currency"
    assert response.attribution.levels[0].rows[0].portfolio_weight_avg_pct == 61.0
    assert response.attribution.levels[0].rows[0].benchmark_weight_avg_pct == 58.0
    assert response.attribution.levels[0].rows[0].portfolio_return_pct == 7.4
    assert response.attribution.levels[0].rows[0].benchmark_return_pct == 6.8
    assert response.attribution.levels[0].allocation_total_pct == 0.18
    assert response.attribution.levels[0].selection_total_pct == 0.24
    assert response.attribution.levels[0].interaction_total_pct == 0.03
    assert analytics_client.contribution_calls[0]["dimension"] == "sector"
    assert analytics_client.attribution_calls[0]["dimension"] == "currency"
    assert analytics_client.workspace_summary_calls[0]["include_detail_blocks"] is False


@pytest.mark.asyncio
async def test_workspace_details_do_not_fallback_when_detail_is_segment_only():
    class _SegmentOnlyContributionAnalyticsClient(_StubAnalyticsClient):
        async def get_contribution_analytics(self, **kwargs):
            self.contribution_calls.append(kwargs)
            payload = _contribution_payload(dimension=str(kwargs["dimension"]))
            period_payload = payload["results_by_period"]["YTD"]
            period_payload.pop("position_contributions", None)
            payload["calculation_id"] = "calc-contribution"
            return 200, payload

        async def get_attribution_analytics(self, **kwargs):
            self.attribution_calls.append(kwargs)
            payload = _attribution_detail_payload(dimension=str(kwargs["dimension"]))
            payload["calculation_id"] = "calc-attribution"
            return 200, payload

    analytics_client = _SegmentOnlyContributionAnalyticsClient()
    service = PerformanceWorkspaceService(
        workbench_service=_StubWorkbenchService(),
        analytics_client=analytics_client,
        lotus_core_query_client=_StubLotusCoreQueryClient(),
    )

    response = await service.get_performance_workspace_details(
        portfolio_id="DEMO_ADV_USD_001",
        correlation_id="corr-performance",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="sector",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )

    assert response.contribution is not None
    assert response.contribution.levels[0].name == "sector"
    assert response.contribution.position_rows == []
    assert response.capabilities.contribution_ranking.state == "partial"
    assert response.capabilities.contribution_ranking.coverage_level == "aggregate"


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
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
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
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )

    assert response.net_performance.portfolio_return_pct is None
    assert response.gross_performance.portfolio_return_pct is None
    assert response.contribution is None
    assert response.attribution is None
    assert response.capabilities.return_path.state == "unavailable"
    assert response.capabilities.contribution_detail.state == "unavailable"
    assert response.capabilities.attribution_detail.state == "unavailable"
    assert response.capabilities.evidence.state == "unavailable"
    assert response.evidence_view is not None
    assert response.evidence_view.state == "unavailable"
    assert "PERFORMANCE_WORKSPACE_SUMMARY_UNAVAILABLE" in response.warnings
    assert any(failure.error_code == "HTTP_503" for failure in response.partial_failures)


@pytest.mark.asyncio
async def test_performance_workspace_service_marks_pending_lineage_as_partial_evidence():
    class _PendingLineageAnalyticsClient(_StubAnalyticsClient):
        async def get_lineage(self, *, calculation_id: str, correlation_id: str):
            _ = correlation_id
            self.lineage_calls.append(calculation_id)
            return 200, {
                "calculation_id": calculation_id,
                "status": "pending",
                "artifacts": {},
            }

    analytics_client = _PendingLineageAnalyticsClient()
    service = PerformanceWorkspaceService(
        workbench_service=_StubWorkbenchService(),
        analytics_client=analytics_client,
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
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )

    assert response.capabilities.evidence.state == "partial"
    assert response.evidence_view is not None
    assert response.evidence_view.state == "partial"
    assert response.evidence_view.calculations[0].lineage_status == "pending"
    assert "PERFORMANCE_EVIDENCE_PARTIAL" in response.warnings
    assert any(
        failure.error_code == "PERFORMANCE_EVIDENCE_PARTIAL"
        for failure in response.partial_failures
    )


@pytest.mark.asyncio
async def test_performance_workspace_service_promotes_recently_materialized_lineage(monkeypatch):
    monkeypatch.setattr(
        "app.services.performance_workspace_service.LINEAGE_COMPLETION_POLL_INTERVAL_SECONDS",
        0,
    )

    class _EventuallyCompleteLineageAnalyticsClient(_StubAnalyticsClient):
        def __init__(self):
            super().__init__()
            self._execution_attempts = 0
            self._lineage_attempts = 0

        async def get_execution(self, *, calculation_id: str, correlation_id: str):
            _ = correlation_id
            self._execution_attempts += 1
            self.execution_calls.append(calculation_id)
            lineage_stage_status = "in_progress" if self._execution_attempts == 1 else "complete"
            return 200, {
                "calculation_id": calculation_id,
                "analytics_type": "WORKSPACE_SUMMARY",
                "execution_mode": "sync",
                "status": "complete",
                "stages": [
                    {
                        "stage_name": "execution",
                        "status": "complete",
                        "completed_at_utc": "2026-03-27T12:00:00Z",
                    },
                    {
                        "stage_name": "lineage_materialization",
                        "status": lineage_stage_status,
                        "completed_at_utc": (
                            "2026-03-27T12:00:01Z" if lineage_stage_status == "complete" else None
                        ),
                    },
                ],
                "upstream_snapshots": [
                    {
                        "upstream_endpoint": "portfolio_timeseries",
                        "source_identifier": "DEMO_ADV_USD_001",
                        "as_of_date": "2026-03-27",
                        "retrieval_status": "200",
                    }
                ],
            }

        async def get_lineage(self, *, calculation_id: str, correlation_id: str):
            _ = correlation_id
            self._lineage_attempts += 1
            self.lineage_calls.append(calculation_id)
            if self._lineage_attempts == 1:
                return 200, {
                    "calculation_id": calculation_id,
                    "status": "pending",
                    "artifacts": {},
                }
            return 200, {
                "calculation_id": calculation_id,
                "status": "complete",
                "artifacts": {
                    "request.json": {
                        "url": (
                            "http://performance.dev.lotus/performance/lineage/"
                            f"{calculation_id}/artifacts/request.json"
                        )
                    },
                    "response.json": {
                        "url": (
                            "http://performance.dev.lotus/performance/lineage/"
                            f"{calculation_id}/artifacts/response.json"
                        )
                    },
                },
            }

    analytics_client = _EventuallyCompleteLineageAnalyticsClient()
    service = PerformanceWorkspaceService(
        workbench_service=_StubWorkbenchService(),
        analytics_client=analytics_client,
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
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )

    assert response.capabilities.evidence.state == "supported"
    assert response.evidence_view is not None
    assert response.evidence_view.state == "supported"
    assert response.evidence_view.calculations[0].lineage_status == "complete"
    assert response.evidence_view.calculations[0].stage_statuses[1].status == "complete"
    assert len(analytics_client.execution_calls) == 2
    assert len(analytics_client.lineage_calls) == 2
    assert "PERFORMANCE_EVIDENCE_PARTIAL" not in response.warnings


@pytest.mark.asyncio
async def test_performance_workspace_service_marks_missing_execution_and_lineage_as_unavailable():
    class _UnavailableEvidenceAnalyticsClient(_StubAnalyticsClient):
        async def get_execution(self, *, calculation_id: str, correlation_id: str):
            _ = correlation_id
            self.execution_calls.append(calculation_id)
            return 404, {"detail": "Execution data not found for the given calculation_id."}

        async def get_lineage(self, *, calculation_id: str, correlation_id: str):
            _ = correlation_id
            self.lineage_calls.append(calculation_id)
            return 404, {"detail": "Lineage data not found for the given calculation_id."}

    analytics_client = _UnavailableEvidenceAnalyticsClient()
    service = PerformanceWorkspaceService(
        workbench_service=_StubWorkbenchService(),
        analytics_client=analytics_client,
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
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )

    assert response.capabilities.evidence.state == "unavailable"
    assert response.evidence_view is not None
    assert response.evidence_view.state == "unavailable"
    assert "PERFORMANCE_EVIDENCE_UNAVAILABLE" in response.warnings


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
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )

    assert response.benchmark_options == []
    assert "BENCHMARK_CATALOG_UNAVAILABLE" in response.warnings
    assert any(failure.error_code == "HTTP_503" for failure in response.partial_failures)


@pytest.mark.asyncio
async def test_performance_workspace_service_marks_aggregate_contribution_as_partial_fallback():
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
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )

    response.contribution.position_rows = []
    response.capabilities = build_workspace_capabilities(
        benchmark_code=response.benchmark_code,
        net_performance=response.net_performance,
        net_chart=response.net_chart,
        contribution=response.contribution,
        attribution=response.attribution,
        evidence_view=response.evidence_view,
    )

    assert response.capabilities.contribution_ranking.state == "partial"
    assert response.capabilities.contribution_ranking.coverage_level == "aggregate"
    assert response.capabilities.contribution_ranking.fallback_available is True
    assert response.capabilities.contribution_ranking.supported_dimensions == [
        "asset_class",
        "sector",
        "country",
    ]
    assert response.capabilities.contribution_detail.state == "partial"


@pytest.mark.asyncio
async def test_performance_workspace_service_marks_summary_only_attribution_as_partial_fallback():
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
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )

    assert response.attribution is not None
    response.attribution.levels[0].rows = []
    response.capabilities = build_workspace_capabilities(
        benchmark_code=response.benchmark_code,
        net_performance=response.net_performance,
        net_chart=response.net_chart,
        contribution=response.contribution,
        attribution=response.attribution,
        evidence_view=response.evidence_view,
    )

    assert response.capabilities.attribution_detail.state == "partial"
    assert response.capabilities.attribution_detail.coverage_level == "summary"
    assert response.capabilities.attribution_detail.fallback_available is True
    assert response.capabilities.attribution_detail.supported_dimensions == [
        "asset_class",
        "sector",
        "country",
        "currency",
    ]


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

    assert response.benchmark_code == "BMK_PB_GLOBAL_BALANCED_60_40"
    assert len(query_client.benchmark_assignment_calls) == 1
    assert len(query_client.benchmark_catalog_calls) == 1


@pytest.mark.asyncio
async def test_performance_workspace_service_downloads_evidence_artifact_bytes():
    analytics_client = _StubAnalyticsClient()
    service = PerformanceWorkspaceService(
        workbench_service=_StubWorkbenchService(),
        analytics_client=analytics_client,
        lotus_core_query_client=_StubLotusCoreQueryClient(),
    )

    content, content_type = await service.get_performance_evidence_artifact(
        calculation_id="calc-workspace-summary",
        artifact_name="request.json",
        correlation_id="corr-performance",
    )

    assert content == b"{}"
    assert content_type == "application/json"


@pytest.mark.asyncio
async def test_performance_workspace_service_surfaces_evidence_artifact_failure_detail():
    class _ArtifactFailingAnalyticsClient(_StubAnalyticsClient):
        async def get_lineage_artifact(
            self, *, calculation_id: str, artifact_name: str, correlation_id: str
        ):
            _ = calculation_id, artifact_name, correlation_id
            return 404, b"artifact not found", "text/plain"

    service = PerformanceWorkspaceService(
        workbench_service=_StubWorkbenchService(),
        analytics_client=_ArtifactFailingAnalyticsClient(),
        lotus_core_query_client=_StubLotusCoreQueryClient(),
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.get_performance_evidence_artifact(
            calculation_id="calc-workspace-summary",
            artifact_name="request.json",
            correlation_id="corr-performance",
        )

    assert exc_info.value.status_code == 404
    assert "artifact not found" in str(exc_info.value)
