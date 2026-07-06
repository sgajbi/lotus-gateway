import asyncio
from typing import Any

import pytest

from app.services.async_ttl_cache import AsyncTtlCache
from app.services.performance_workspace_benchmarks import (
    fetch_assigned_benchmark_code,
    fetch_benchmark_context,
    parse_benchmark_catalog_result,
    resolve_benchmark_code,
)


class FakeCoreClient:
    def __init__(self) -> None:
        self.assignment_payloads: list[tuple[int, dict[str, Any]]] = [
            (200, {"benchmark_id": "BMK_PB_GLOBAL_BALANCED_60_40"})
        ]
        self.catalog_payload: tuple[int, dict[str, Any]] = (
            200,
            {"benchmarks": [{"benchmark_id": "BMK_PB_GLOBAL_BALANCED_60_40"}]},
        )
        self.assignment_calls: list[dict[str, Any]] = []
        self.catalog_calls: list[dict[str, Any]] = []

    async def get_benchmark_assignment(self, **kwargs):
        self.assignment_calls.append(kwargs)
        if self.assignment_payloads:
            return self.assignment_payloads.pop(0)
        return 200, {"benchmark_id": None}

    async def get_benchmark_catalog(self, **kwargs):
        self.catalog_calls.append(kwargs)
        return self.catalog_payload

    async def get_portfolio_analytics_reference(self, *args, **kwargs):
        raise AssertionError("not used by benchmark helpers")


@pytest.mark.asyncio
async def test_fetch_assigned_benchmark_code_returns_assignment_id():
    client = FakeCoreClient()

    benchmark_code = await fetch_assigned_benchmark_code(
        core_client=client,
        portfolio_id="DEMO_ADV_USD_001",
        as_of_date="2026-03-27",
        portfolio_currency="USD",
        correlation_id="corr-1",
    )

    assert benchmark_code == "BMK_PB_GLOBAL_BALANCED_60_40"
    assert client.assignment_calls == [
        {
            "portfolio_id": "DEMO_ADV_USD_001",
            "as_of_date": "2026-03-27",
            "reporting_currency": "USD",
            "correlation_id": "corr-1",
        }
    ]


@pytest.mark.asyncio
async def test_fetch_assigned_benchmark_code_fails_closed_for_upstream_failure():
    client = FakeCoreClient()
    client.assignment_payloads = [(503, {"detail": "core unavailable"})]

    benchmark_code = await fetch_assigned_benchmark_code(
        core_client=client,
        portfolio_id="DEMO_ADV_USD_001",
        as_of_date="2026-03-27",
        portfolio_currency="USD",
        correlation_id="corr-1",
    )

    assert benchmark_code is None


@pytest.mark.asyncio
async def test_resolve_benchmark_code_keeps_explicit_code_local():
    client = FakeCoreClient()
    cache = AsyncTtlCache[Any](ttl_seconds=30)

    benchmark_code = await resolve_benchmark_code(
        cache=cache,
        core_client=client,
        portfolio_id="DEMO_ADV_USD_001",
        correlation_id="corr-1",
        as_of_date="2026-03-27",
        portfolio_currency="USD",
        benchmark_code="BMK_EXPLICIT",
    )

    assert benchmark_code == "BMK_EXPLICIT"
    assert client.assignment_calls == []


@pytest.mark.asyncio
async def test_resolve_benchmark_code_refreshes_cached_missing_assignment():
    client = FakeCoreClient()
    client.assignment_payloads = [
        (200, {"benchmark_id": None, "assignment_status": "not_found"}),
        (200, {"benchmark_id": "BMK_PB_GLOBAL_BALANCED_60_40"}),
    ]
    cache = AsyncTtlCache[Any](ttl_seconds=30)

    first_benchmark_code = await resolve_benchmark_code(
        cache=cache,
        core_client=client,
        portfolio_id="DEMO_ADV_USD_001",
        correlation_id="corr-1",
        as_of_date="2026-03-27",
        portfolio_currency="USD",
        benchmark_code=None,
    )
    second_benchmark_code = await resolve_benchmark_code(
        cache=cache,
        core_client=client,
        portfolio_id="DEMO_ADV_USD_001",
        correlation_id="corr-1",
        as_of_date="2026-03-27",
        portfolio_currency="USD",
        benchmark_code=None,
    )

    assert first_benchmark_code is None
    assert second_benchmark_code == "BMK_PB_GLOBAL_BALANCED_60_40"
    assert len(client.assignment_calls) == 2


@pytest.mark.asyncio
async def test_fetch_benchmark_context_fetches_assignment_and_catalog_concurrently():
    assignment_started = asyncio.Event()
    catalog_started = asyncio.Event()
    release = asyncio.Event()

    class CoordinatedCoreClient(FakeCoreClient):
        async def get_benchmark_assignment(self, **kwargs):
            self.assignment_calls.append(kwargs)
            assignment_started.set()
            await catalog_started.wait()
            release.set()
            return 200, {"benchmark_id": "BMK_PB_GLOBAL_BALANCED_60_40"}

        async def get_benchmark_catalog(self, **kwargs):
            self.catalog_calls.append(kwargs)
            catalog_started.set()
            await assignment_started.wait()
            await release.wait()
            return self.catalog_payload

    client = CoordinatedCoreClient()
    cache = AsyncTtlCache[Any](ttl_seconds=30)

    benchmark_code, catalog_result = await asyncio.wait_for(
        fetch_benchmark_context(
            cache=cache,
            core_client=client,
            portfolio_id="DEMO_ADV_USD_001",
            correlation_id="corr-1",
            report_end_date="2026-03-27",
            portfolio_currency="USD",
            benchmark_code=None,
            include_benchmark_catalog=True,
        ),
        timeout=1,
    )

    assert benchmark_code == "BMK_PB_GLOBAL_BALANCED_60_40"
    assert catalog_result == client.catalog_payload
    assert len(client.assignment_calls) == 1
    assert len(client.catalog_calls) == 1


@pytest.mark.asyncio
async def test_fetch_benchmark_context_skips_catalog_when_not_requested():
    client = FakeCoreClient()
    cache = AsyncTtlCache[Any](ttl_seconds=30)

    benchmark_code, catalog_result = await fetch_benchmark_context(
        cache=cache,
        core_client=client,
        portfolio_id="DEMO_ADV_USD_001",
        correlation_id="corr-1",
        report_end_date="2026-03-27",
        portfolio_currency="USD",
        benchmark_code=None,
        include_benchmark_catalog=False,
    )

    assert benchmark_code == "BMK_PB_GLOBAL_BALANCED_60_40"
    assert catalog_result == (200, {})
    assert client.catalog_calls == []


def test_parse_benchmark_catalog_result_deduplicates_and_marks_assigned_option():
    warnings: list[str] = []
    partial_failures = []

    options = parse_benchmark_catalog_result(
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


def test_parse_benchmark_catalog_result_records_upstream_failure():
    warnings: list[str] = []
    partial_failures = []

    options = parse_benchmark_catalog_result(
        result=(
            503,
            {
                "detail": {
                    "code": "CATALOG_UNAVAILABLE",
                    "message": "catalog unavailable",
                    "debug_payload": {
                        "client_name": "Private Client",
                        "token": "secret-token",
                    },
                }
            },
        ),
        assigned_benchmark_code=None,
        warnings=warnings,
        partial_failures=partial_failures,
    )

    assert options == []
    assert warnings == ["BENCHMARK_CATALOG_UNAVAILABLE"]
    assert len(partial_failures) == 1
    assert partial_failures[0].source_service == "lotus-core"
    assert partial_failures[0].error_code == "HTTP_503"
    assert partial_failures[0].detail == "CATALOG_UNAVAILABLE"
    assert "Private Client" not in str(partial_failures[0])
    assert "secret-token" not in str(partial_failures[0])


def test_parse_benchmark_catalog_result_records_exception_failure():
    warnings: list[str] = []
    partial_failures = []

    options = parse_benchmark_catalog_result(
        result=TimeoutError("benchmark catalog timed out"),
        assigned_benchmark_code=None,
        warnings=warnings,
        partial_failures=partial_failures,
    )

    assert options == []
    assert warnings == ["BENCHMARK_CATALOG_UNAVAILABLE"]
    assert len(partial_failures) == 1
    assert partial_failures[0].source_service == "lotus-core"
    assert partial_failures[0].error_code == "UPSTREAM_EXCEPTION"
    assert partial_failures[0].detail == "benchmark catalog timed out"
