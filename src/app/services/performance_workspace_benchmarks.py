from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Sequence
from typing import Any, TypeAlias, cast

from app.contracts.workbench import WorkbenchPartialFailure
from app.services.async_ttl_cache import AsyncTtlCache
from app.services.performance_workspace_benchmark_assignment import (
    fetch_assigned_benchmark_code,
    record_benchmark_assignment_failure,
    resolve_benchmark_code,
)
from app.services.performance_workspace_benchmark_catalog import (
    parse_benchmark_catalog_result,
)
from app.services.workspace_client_protocols import PerformanceWorkspaceCoreClient

__all__ = [
    "fetch_assigned_benchmark_code",
    "fetch_benchmark_context",
    "parse_benchmark_catalog_result",
    "resolve_benchmark_code",
]

UpstreamPayload: TypeAlias = dict[str, Any]
UpstreamResult: TypeAlias = tuple[int, UpstreamPayload]
GatheredResult: TypeAlias = UpstreamResult | BaseException


def benchmark_catalog_cache_key(
    *,
    report_end_date: str,
    reporting_currency: str,
) -> tuple[str, str, str]:
    return ("benchmark_catalog", report_end_date, reporting_currency)


async def fetch_benchmark_context(
    *,
    cache: AsyncTtlCache[Any],
    core_client: PerformanceWorkspaceCoreClient,
    portfolio_id: str,
    correlation_id: str,
    report_end_date: str,
    reporting_currency: str,
    benchmark_code: str | None,
    include_benchmark_catalog: bool,
    warnings: list[str] | None = None,
    partial_failures: list[WorkbenchPartialFailure] | None = None,
) -> tuple[str | None, GatheredResult]:
    assignment_task, benchmark_catalog_task = _benchmark_context_tasks(
        cache=cache,
        core_client=core_client,
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        report_end_date=report_end_date,
        reporting_currency=reporting_currency,
        benchmark_code=benchmark_code,
        include_benchmark_catalog=include_benchmark_catalog,
        warnings=warnings,
        partial_failures=partial_failures,
    )
    benchmark_context_results = await asyncio.gather(
        assignment_task,
        benchmark_catalog_task,
        return_exceptions=True,
    )
    return _resolve_benchmark_context_results(
        benchmark_code=benchmark_code,
        benchmark_context_results=benchmark_context_results,
        warnings=warnings,
        partial_failures=partial_failures,
    )


def _benchmark_context_tasks(
    *,
    cache: AsyncTtlCache[Any],
    core_client: PerformanceWorkspaceCoreClient,
    portfolio_id: str,
    correlation_id: str,
    report_end_date: str,
    reporting_currency: str,
    benchmark_code: str | None,
    include_benchmark_catalog: bool,
    warnings: list[str] | None,
    partial_failures: list[WorkbenchPartialFailure] | None,
) -> tuple[Awaitable[str | None], Awaitable[GatheredResult]]:
    return (
        _benchmark_assignment_task(
            cache=cache,
            core_client=core_client,
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            report_end_date=report_end_date,
            reporting_currency=reporting_currency,
            benchmark_code=benchmark_code,
            warnings=warnings,
            partial_failures=partial_failures,
        ),
        _benchmark_catalog_task(
            cache=cache,
            core_client=core_client,
            report_end_date=report_end_date,
            reporting_currency=reporting_currency,
            correlation_id=correlation_id,
            include_benchmark_catalog=include_benchmark_catalog,
        ),
    )


def _benchmark_assignment_task(
    *,
    cache: AsyncTtlCache[Any],
    core_client: PerformanceWorkspaceCoreClient,
    portfolio_id: str,
    correlation_id: str,
    report_end_date: str,
    reporting_currency: str,
    benchmark_code: str | None,
    warnings: list[str] | None,
    partial_failures: list[WorkbenchPartialFailure] | None,
) -> Awaitable[str | None]:
    if benchmark_code:
        return _empty_async_scalar_result(None)
    return resolve_benchmark_code(
        cache=cache,
        core_client=core_client,
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        as_of_date=report_end_date,
        reporting_currency=reporting_currency,
        benchmark_code=benchmark_code,
        warnings=warnings,
        partial_failures=partial_failures,
    )


def _benchmark_catalog_task(
    *,
    cache: AsyncTtlCache[Any],
    core_client: PerformanceWorkspaceCoreClient,
    report_end_date: str,
    reporting_currency: str,
    correlation_id: str,
    include_benchmark_catalog: bool,
) -> Awaitable[GatheredResult]:
    if not include_benchmark_catalog:
        return _empty_async_result()
    return cache.get_or_set(
        key=benchmark_catalog_cache_key(
            report_end_date=report_end_date,
            reporting_currency=reporting_currency,
        ),
        factory=lambda: core_client.get_benchmark_catalog(
            as_of_date=report_end_date,
            benchmark_currency=reporting_currency,
            benchmark_status="active",
            benchmark_type="composite",
            correlation_id=correlation_id,
        ),
    )


def _resolve_benchmark_context_results(
    *,
    benchmark_code: str | None,
    benchmark_context_results: Sequence[object],
    warnings: list[str] | None,
    partial_failures: list[WorkbenchPartialFailure] | None,
) -> tuple[str | None, GatheredResult]:
    resolved_benchmark_code_result = cast(
        str | None | BaseException,
        benchmark_context_results[0],
    )
    benchmark_catalog_result_value = cast(GatheredResult, benchmark_context_results[1])
    if isinstance(resolved_benchmark_code_result, BaseException):
        record_benchmark_assignment_failure(
            warnings=warnings,
            partial_failures=partial_failures,
            error_code="UPSTREAM_EXCEPTION",
            detail="benchmark assignment unavailable",
        )
        return benchmark_code, benchmark_catalog_result_value
    return benchmark_code or cast(str | None, resolved_benchmark_code_result), (
        benchmark_catalog_result_value
    )


async def _empty_async_result() -> tuple[int, dict[str, Any]]:
    return 200, {}


async def _empty_async_scalar_result(value: str | None) -> str | None:
    return value
