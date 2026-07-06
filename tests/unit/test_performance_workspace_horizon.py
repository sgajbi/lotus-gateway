from typing import Any

import pytest

from app.services.performance_workspace_horizon import (
    build_horizon_comparison_frequencies,
    fetch_workspace_horizon_dependencies,
    merge_standard_horizon_results,
    parse_horizon_comparison_result,
)


class FakeAnalyticsClient:
    def __init__(self, results: list[tuple[int, dict[str, Any]]] | None = None) -> None:
        self.results = results or [
            (200, {"results_by_period": {"EXPLICIT": {"value": "MTD"}}}),
            (200, {"results_by_period": {"EXPLICIT": {"value": "QTD"}}}),
            (200, {"results_by_period": {"YTD": {"value": "YTD"}}}),
        ]
        self.workspace_summary_calls: list[dict[str, Any]] = []

    async def get_workspace_summary(self, **kwargs):
        self.workspace_summary_calls.append(kwargs)
        return self.results.pop(0)

    async def get_twr_analytics(self, *args, **kwargs):
        raise AssertionError("not used by horizon helpers")

    async def get_mwr_analytics(self, *args, **kwargs):
        raise AssertionError("not used by horizon helpers")

    async def get_contribution_analytics(self, *args, **kwargs):
        raise AssertionError("not used by horizon helpers")

    async def get_attribution_analytics(self, *args, **kwargs):
        raise AssertionError("not used by horizon helpers")

    async def get_execution(self, *args, **kwargs):
        raise AssertionError("not used by horizon helpers")

    async def get_lineage(self, *args, **kwargs):
        raise AssertionError("not used by horizon helpers")

    async def get_lineage_artifact(self, *args, **kwargs):
        raise AssertionError("not used by horizon helpers")


def test_build_horizon_comparison_frequencies_deduplicates_requested_frequency():
    assert build_horizon_comparison_frequencies("monthly") == [
        "monthly",
        "quarterly",
        "yearly",
    ]
    assert build_horizon_comparison_frequencies("daily") == [
        "daily",
        "monthly",
        "quarterly",
        "yearly",
    ]


@pytest.mark.asyncio
async def test_fetch_workspace_horizon_dependencies_calls_explicit_summary_once():
    client = FakeAnalyticsClient(results=[(200, {"results_by_period": {"EXPLICIT": {}}})])

    result = await fetch_workspace_horizon_dependencies(
        analytics_client=client,
        portfolio_id="DEMO_ADV_USD_001",
        correlation_id="corr-1",
        report_end_date="2026-03-27",
        report_start_date="2026-01-01",
        period="EXPLICIT",
        detail_basis="NET",
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
        portfolio_currency="USD",
        chart_frequency="monthly",
    )

    assert result == (200, {"results_by_period": {"EXPLICIT": {}}})
    assert len(client.workspace_summary_calls) == 1
    assert client.workspace_summary_calls[0] == {
        "portfolio_id": "DEMO_ADV_USD_001",
        "report_end_date": "2026-03-27",
        "report_start_date": "2026-01-01",
        "period": "EXPLICIT",
        "chart_frequency": "monthly",
        "detail_basis": "NET",
        "benchmark_id": "BMK_PB_GLOBAL_BALANCED_60_40",
        "reporting_currency": "USD",
        "segment": "asset_class",
        "correlation_id": "corr-1",
        "periods": [{"period": "EXPLICIT", "frequencies": ["monthly", "quarterly", "yearly"]}],
        "include_detail_blocks": False,
    }


@pytest.mark.asyncio
async def test_fetch_workspace_horizon_dependencies_merges_standard_period_results():
    client = FakeAnalyticsClient()

    result = await fetch_workspace_horizon_dependencies(
        analytics_client=client,
        portfolio_id="DEMO_ADV_USD_001",
        correlation_id="corr-1",
        report_end_date="2026-03-27",
        report_start_date=None,
        period="YTD",
        detail_basis="NET",
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
        portfolio_currency="USD",
        chart_frequency="daily",
    )

    assert result == (
        200,
        {
            "results_by_period": {
                "MTD": {
                    "value": "MTD",
                    "_gateway_requested_period_start": "2026-03-01",
                    "_gateway_requested_period_end": "2026-03-27",
                },
                "QTD": {
                    "value": "QTD",
                    "_gateway_requested_period_start": "2026-01-01",
                    "_gateway_requested_period_end": "2026-03-27",
                },
                "YTD": {"value": "YTD"},
            },
            "_gateway_warnings": [],
            "_gateway_partial_failures": [],
        },
    )
    assert [call["report_start_date"] for call in client.workspace_summary_calls] == [
        "2026-03-01",
        "2026-01-01",
        None,
    ]
    assert [call["period"] for call in client.workspace_summary_calls] == [
        "EXPLICIT",
        "EXPLICIT",
        "YTD",
    ]


def test_merge_standard_horizon_results_records_partial_failures():
    result = merge_standard_horizon_results(
        gathered_results=[
            RuntimeError("mtd timeout"),
            (
                503,
                {
                    "detail": {
                        "code": "QTD_UNAVAILABLE",
                        "message": "qtd unavailable",
                        "debug_payload": {
                            "client_name": "Private Client",
                            "token": "secret-token",
                        },
                    }
                },
            ),
            (200, {"results_by_period": {"YTD": {"value": "YTD"}}}),
        ],
        month_start="2026-03-01",
        quarter_start="2026-01-01",
        report_end_date="2026-03-27",
    )

    assert result == (
        200,
        {
            "results_by_period": {"YTD": {"value": "YTD"}},
            "_gateway_warnings": [
                "PERFORMANCE_HORIZON_MTD_UNAVAILABLE",
                "PERFORMANCE_HORIZON_QTD_UNAVAILABLE",
            ],
            "_gateway_partial_failures": [
                {
                    "source_service": "lotus-performance",
                    "error_code": "UPSTREAM_EXCEPTION",
                    "detail": "mtd timeout",
                },
                {
                    "source_service": "lotus-performance",
                    "error_code": "HTTP_503",
                    "detail": "QTD_UNAVAILABLE",
                },
            ],
        },
    )
    assert "Private Client" not in str(result)
    assert "secret-token" not in str(result)


def test_parse_horizon_comparison_result_returns_row_and_benchmark_code():
    warnings: list[str] = []
    partial_failures = []

    rows, benchmark_code = parse_horizon_comparison_result(
        result=(
            200,
            {
                "results_by_period": {
                    "YTD": {
                        "portfolio_twr": {
                            "net": {
                                "summary": {
                                    "period_return": {"base": 3.1},
                                    "cumulative_return": {"base": 5.2},
                                    "annualized_return": {"base": 6.3},
                                    "economics": {
                                        "begin_market_value": 100.0,
                                        "end_market_value": 110.0,
                                    },
                                },
                            },
                            "gross": {
                                "summary": {
                                    "period_return": {"base": 3.3},
                                    "cumulative_return": {"base": 5.4},
                                    "annualized_return": {"base": 6.5},
                                },
                            },
                        },
                        "benchmark": {
                            "benchmark_id": "BMK_PB_GLOBAL_BALANCED_60_40",
                            "summary": {
                                "period_return": {"base": 2.9},
                                "cumulative_return": {"base": 4.8},
                            },
                        },
                        "active": {"net": {"period_return": {"base": 0.2}}},
                        "money_weighted_return": {
                            "start_date": "2026-01-01",
                            "end_date": "2026-03-27",
                        },
                    },
                },
            },
        ),
        requested_period="EXPLICIT",
        requested_report_start_date=None,
        requested_report_end_date="2026-03-27",
        detail_basis="NET",
        warnings=warnings,
        partial_failures=partial_failures,
    )

    assert len(rows) == 1
    row = rows[0]
    assert row.period == "YTD"
    assert row.period_start == "2026-01-01"
    assert row.period_end == "2026-03-27"
    assert row.portfolio_return_pct == 3.1
    assert row.net_return_pct == 3.1
    assert row.gross_return_pct == 3.3
    assert row.benchmark_return_pct == 2.9
    assert row.active_return_pct == 0.2
    assert row.cumulative_net_return_pct == 5.2
    assert row.cumulative_gross_return_pct == 5.4
    assert row.cumulative_benchmark_return_pct == 4.8
    assert row.annualized_return_pct == 6.3
    assert row.begin_market_value == 100.0
    assert row.end_market_value == 110.0
    assert benchmark_code == "BMK_PB_GLOBAL_BALANCED_60_40"
    assert warnings == []
    assert partial_failures == []


def test_parse_horizon_comparison_result_renders_standard_period_date_fallbacks():
    warnings: list[str] = []
    partial_failures = []

    rows, benchmark_code = parse_horizon_comparison_result(
        result=(
            200,
            {
                "results_by_period": {
                    "MTD": {
                        "_gateway_requested_period_start": "2026-03-01",
                        "_gateway_requested_period_end": "2026-03-27",
                        "portfolio_twr": {
                            "net": {"summary": {"period_return": {"base": 1.1}}},
                        },
                    },
                    "QTD": {
                        "_gateway_requested_period_start": "2026-01-01",
                        "_gateway_requested_period_end": "2026-03-27",
                        "portfolio_twr": {
                            "net": {"summary": {"period_return": {"base": 2.2}}},
                        },
                    },
                    "YTD": {
                        "portfolio_twr": {
                            "net": {"summary": {"period_return": {"base": 3.3}}},
                        },
                        "benchmark": {
                            "benchmark_id": "BMK_PB_GLOBAL_BALANCED_60_40",
                            "summary": {"period_return": {"base": 2.8}},
                        },
                    },
                },
            },
        ),
        requested_period="YTD",
        requested_report_start_date=None,
        requested_report_end_date="2026-03-27",
        detail_basis="NET",
        warnings=warnings,
        partial_failures=partial_failures,
    )

    assert [row.period for row in rows] == ["MTD", "QTD", "YTD"]
    assert [(row.period_start, row.period_end) for row in rows] == [
        ("2026-03-01", "2026-03-27"),
        ("2026-01-01", "2026-03-27"),
        (None, "2026-03-27"),
    ]
    assert [row.portfolio_return_pct for row in rows] == [1.1, 2.2, 3.3]
    assert rows[2].benchmark_return_pct == 2.8
    assert benchmark_code == "BMK_PB_GLOBAL_BALANCED_60_40"
    assert warnings == []
    assert partial_failures == []


def test_parse_horizon_comparison_result_propagates_gateway_failures():
    warnings: list[str] = []
    partial_failures = []

    rows, benchmark_code = parse_horizon_comparison_result(
        result=(
            200,
            {
                "results_by_period": {},
                "_gateway_warnings": ["PERFORMANCE_HORIZON_MTD_UNAVAILABLE"],
                "_gateway_partial_failures": [
                    {
                        "source_service": "lotus-performance",
                        "error_code": "HTTP_503",
                        "detail": "mtd unavailable",
                    },
                ],
            },
        ),
        requested_period="YTD",
        requested_report_start_date=None,
        requested_report_end_date="2026-03-27",
        detail_basis="NET",
        warnings=warnings,
        partial_failures=partial_failures,
    )

    assert rows == []
    assert benchmark_code is None
    assert warnings == [
        "PERFORMANCE_HORIZON_MTD_UNAVAILABLE",
        "PERFORMANCE_HORIZON_COMPARISON_INVALID",
    ]
    assert len(partial_failures) == 1
    assert partial_failures[0].source_service == "lotus-performance"
    assert partial_failures[0].error_code == "HTTP_503"
    assert partial_failures[0].detail == "mtd unavailable"


def test_parse_horizon_comparison_result_bounds_upstream_failure_detail():
    warnings: list[str] = []
    partial_failures = []

    rows, benchmark_code = parse_horizon_comparison_result(
        result=(
            503,
            {
                "detail": {
                    "code": "HORIZON_UNAVAILABLE",
                    "message": "horizon comparison unavailable",
                    "debug_payload": {
                        "client_name": "Private Client",
                        "token": "secret-token",
                    },
                }
            },
        ),
        requested_period="YTD",
        requested_report_start_date=None,
        requested_report_end_date="2026-03-27",
        detail_basis="NET",
        warnings=warnings,
        partial_failures=partial_failures,
    )

    assert rows == []
    assert benchmark_code is None
    assert warnings == ["PERFORMANCE_HORIZON_COMPARISON_UNAVAILABLE"]
    assert len(partial_failures) == 1
    assert partial_failures[0].detail == "HORIZON_UNAVAILABLE"
    assert "Private Client" not in str(partial_failures[0])
    assert "secret-token" not in str(partial_failures[0])
