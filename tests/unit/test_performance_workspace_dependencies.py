from typing import Any

import pytest

from app.services.async_ttl_cache import AsyncTtlCache
from app.services.performance_workspace_dependencies import (
    fetch_workspace_detail_results,
    fetch_workspace_summary_result,
)


class FakeAnalyticsClient:
    def __init__(self) -> None:
        self.workspace_summary_calls: list[dict[str, Any]] = []
        self.contribution_calls: list[dict[str, Any]] = []
        self.attribution_calls: list[dict[str, Any]] = []

    async def get_workspace_summary(self, **kwargs):
        self.workspace_summary_calls.append(kwargs)
        return 200, {"summary_call": len(self.workspace_summary_calls)}

    async def get_contribution_analytics(self, **kwargs):
        self.contribution_calls.append(kwargs)
        return 200, {"contribution_call": len(self.contribution_calls)}

    async def get_attribution_analytics(self, **kwargs):
        self.attribution_calls.append(kwargs)
        return 200, {"attribution_call": len(self.attribution_calls)}

    async def get_twr_analytics(self, *args, **kwargs):
        raise AssertionError("not used by dependency helpers")

    async def get_mwr_analytics(self, *args, **kwargs):
        raise AssertionError("not used by dependency helpers")

    async def get_execution(self, *args, **kwargs):
        raise AssertionError("not used by dependency helpers")

    async def get_lineage(self, *args, **kwargs):
        raise AssertionError("not used by dependency helpers")

    async def get_lineage_artifact(self, *args, **kwargs):
        raise AssertionError("not used by dependency helpers")


@pytest.mark.asyncio
async def test_fetch_workspace_summary_result_caches_request_shape():
    cache = AsyncTtlCache[Any](ttl_seconds=30)
    client = FakeAnalyticsClient()

    first_result = await fetch_workspace_summary_result(
        cache=cache,
        analytics_client=client,
        portfolio_id="DEMO_ADV_USD_001",
        correlation_id="corr-1",
        report_end_date="2026-03-27",
        report_start_date="2026-01-01",
        effective_period="EXPLICIT",
        chart_frequency="monthly",
        detail_basis="NET",
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
        reporting_currency="USD",
        segment="asset_class",
        include_detail_blocks=False,
    )
    second_result = await fetch_workspace_summary_result(
        cache=cache,
        analytics_client=client,
        portfolio_id="DEMO_ADV_USD_001",
        correlation_id="corr-2",
        report_end_date="2026-03-27",
        report_start_date="2026-01-01",
        effective_period="EXPLICIT",
        chart_frequency="monthly",
        detail_basis="NET",
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
        reporting_currency="USD",
        segment="asset_class",
        include_detail_blocks=False,
    )

    assert first_result == second_result == (200, {"summary_call": 1})
    assert client.workspace_summary_calls == [
        {
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
            "include_detail_blocks": False,
        }
    ]


@pytest.mark.asyncio
async def test_fetch_workspace_summary_result_omits_non_explicit_start_date():
    cache = AsyncTtlCache[Any](ttl_seconds=30)
    client = FakeAnalyticsClient()

    result = await fetch_workspace_summary_result(
        cache=cache,
        analytics_client=client,
        portfolio_id="DEMO_ADV_USD_001",
        correlation_id="corr-1",
        report_end_date="2026-03-27",
        report_start_date="2026-01-01",
        effective_period="YTD",
        chart_frequency="monthly",
        detail_basis="NET",
        benchmark_code=None,
        reporting_currency="USD",
        segment="asset_class",
    )

    assert result == (200, {"summary_call": 1})
    assert client.workspace_summary_calls[0]["report_start_date"] is None
    assert client.workspace_summary_calls[0]["period"] == "YTD"


@pytest.mark.asyncio
async def test_fetch_workspace_detail_results_fetches_contribution_and_attribution():
    cache = AsyncTtlCache[Any](ttl_seconds=30)
    client = FakeAnalyticsClient()

    contribution_result, attribution_result = await fetch_workspace_detail_results(
        cache=cache,
        analytics_client=client,
        portfolio_id="DEMO_ADV_USD_001",
        correlation_id="corr-1",
        report_start_date="2026-01-01",
        report_end_date="2026-03-27",
        requested_period="EXPLICIT",
        detail_basis="NET",
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
        reporting_currency="SGD",
        contribution_dimension="sector",
        attribution_dimension="currency",
    )

    assert contribution_result == (200, {"contribution_call": 1})
    assert attribution_result == (200, {"attribution_call": 1})
    assert client.contribution_calls[0]["dimension"] == "sector"
    assert client.contribution_calls[0]["reporting_currency"] == "SGD"
    assert client.attribution_calls[0]["dimension"] == "currency"
    assert client.attribution_calls[0]["benchmark_id"] == "BMK_PB_GLOBAL_BALANCED_60_40"
    assert client.attribution_calls[0]["reporting_currency"] == "SGD"


@pytest.mark.asyncio
async def test_fetch_workspace_detail_results_skips_attribution_without_benchmark():
    cache = AsyncTtlCache[Any](ttl_seconds=30)
    client = FakeAnalyticsClient()

    contribution_result, attribution_result = await fetch_workspace_detail_results(
        cache=cache,
        analytics_client=client,
        portfolio_id="DEMO_ADV_USD_001",
        correlation_id="corr-1",
        report_start_date="2026-01-01",
        report_end_date="2026-03-27",
        requested_period="EXPLICIT",
        detail_basis="NET",
        benchmark_code=None,
        reporting_currency="USD",
        contribution_dimension="sector",
        attribution_dimension="currency",
    )

    assert contribution_result == (200, {"contribution_call": 1})
    assert attribution_result == (204, {})
    assert client.attribution_calls == []


@pytest.mark.asyncio
async def test_fetch_workspace_detail_results_cache_isolated_by_reporting_currency():
    cache = AsyncTtlCache[Any](ttl_seconds=30)
    client = FakeAnalyticsClient()
    request = {
        "cache": cache,
        "analytics_client": client,
        "portfolio_id": "DEMO_ADV_USD_001",
        "correlation_id": "corr-1",
        "report_start_date": "2026-01-01",
        "report_end_date": "2026-03-27",
        "requested_period": "EXPLICIT",
        "detail_basis": "NET",
        "benchmark_code": "BMK_PB_GLOBAL_BALANCED_60_40",
        "contribution_dimension": "sector",
        "attribution_dimension": "currency",
    }

    await fetch_workspace_detail_results(**request, reporting_currency="USD")
    await fetch_workspace_detail_results(**request, reporting_currency="SGD")

    assert len(client.contribution_calls) == 2
    assert len(client.attribution_calls) == 2
    assert {call["reporting_currency"] for call in client.contribution_calls} == {"USD", "SGD"}
    assert {call["reporting_currency"] for call in client.attribution_calls} == {"USD", "SGD"}
