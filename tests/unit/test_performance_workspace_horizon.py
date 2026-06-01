from typing import Any

import pytest

from app.services.performance_workspace_horizon import (
    build_horizon_comparison_frequencies,
    fetch_workspace_horizon_dependencies,
    merge_standard_horizon_results,
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
        "periods": [
            {"period": "EXPLICIT", "frequencies": ["monthly", "quarterly", "yearly"]}
        ],
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
            (503, {"detail": "qtd unavailable"}),
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
                    "detail": "qtd unavailable",
                },
            ],
        },
    )
