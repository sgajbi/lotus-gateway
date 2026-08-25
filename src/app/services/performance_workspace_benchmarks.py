from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Sequence
from typing import Any, TypeAlias, cast

from app.contracts.workbench import WorkbenchPartialFailure
from app.services.async_ttl_cache import AsyncTtlCache
from app.services.performance_workspace_benchmark_catalog import (
    parse_benchmark_catalog_result,
)
from app.services.performance_workspace_failures import build_performance_failure
from app.services.performance_workspace_parsing import safe_str
from app.services.upstream_envelope import safe_upstream_detail
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


def benchmark_assignment_cache_key(
    *,
    portfolio_id: str,
    as_of_date: str,
    reporting_currency: str,
) -> tuple[str, str, str, str]:
    return (
        "benchmark_assignment",
        portfolio_id,
        as_of_date,
        reporting_currency,
    )


def benchmark_catalog_cache_key(
    *,
    report_end_date: str,
    reporting_currency: str,
) -> tuple[str, str, str]:
    return ("benchmark_catalog", report_end_date, reporting_currency)


async def fetch_assigned_benchmark_code(
    *,
    core_client: PerformanceWorkspaceCoreClient,
    portfolio_id: str,
    as_of_date: str,
    reporting_currency: str,
    correlation_id: str,
    warnings: list[str] | None = None,
    partial_failures: list[WorkbenchPartialFailure] | None = None,
) -> str | None:
    status_code, payload = await core_client.get_benchmark_assignment(
        portfolio_id=portfolio_id,
        as_of_date=as_of_date,
        reporting_currency=reporting_currency,
        correlation_id=correlation_id,
    )
    if status_code >= 400 or not isinstance(payload, dict):
        _record_benchmark_assignment_failure(
            warnings=warnings,
            partial_failures=partial_failures,
            error_code=(
                f"HTTP_{status_code}"
                if isinstance(status_code, int)
                else "INVALID_UPSTREAM_PAYLOAD"
            ),
            detail=(
                safe_upstream_detail(payload, default_detail="benchmark assignment unavailable")
                if isinstance(payload, dict)
                else "benchmark assignment returned an invalid payload"
            ),
        )
        return None
    return safe_str(payload.get("benchmark_id"))


async def resolve_benchmark_code(
    *,
    cache: AsyncTtlCache[Any],
    core_client: PerformanceWorkspaceCoreClient,
    portfolio_id: str,
    correlation_id: str,
    as_of_date: str,
    reporting_currency: str,
    benchmark_code: str | None,
    warnings: list[str] | None = None,
    partial_failures: list[WorkbenchPartialFailure] | None = None,
) -> str | None:
    if benchmark_code:
        return benchmark_code

    cache_key = benchmark_assignment_cache_key(
        portfolio_id=portfolio_id,
        as_of_date=as_of_date,
        reporting_currency=reporting_currency,
    )
    resolved_benchmark_code, cache_hit = await cache.get_or_set_with_status(
        key=cache_key,
        factory=lambda: fetch_assigned_benchmark_code(
            core_client=core_client,
            portfolio_id=portfolio_id,
            as_of_date=as_of_date,
            reporting_currency=reporting_currency,
            correlation_id=correlation_id,
            warnings=warnings,
            partial_failures=partial_failures,
        ),
    )
    if resolved_benchmark_code:
        return cast(str, resolved_benchmark_code)

    cache.discard(cache_key)
    if not cache_hit:
        return None

    refreshed_benchmark_code = await fetch_assigned_benchmark_code(
        core_client=core_client,
        portfolio_id=portfolio_id,
        as_of_date=as_of_date,
        reporting_currency=reporting_currency,
        correlation_id=correlation_id,
        warnings=warnings,
        partial_failures=partial_failures,
    )
    if refreshed_benchmark_code:
        cache.set(cache_key, refreshed_benchmark_code)
    return refreshed_benchmark_code


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
        _record_benchmark_assignment_failure(
            warnings=warnings,
            partial_failures=partial_failures,
            error_code="UPSTREAM_EXCEPTION",
            detail=str(resolved_benchmark_code_result),
        )
        return benchmark_code, benchmark_catalog_result_value
    return benchmark_code or cast(str | None, resolved_benchmark_code_result), (
        benchmark_catalog_result_value
    )


async def _empty_async_result() -> tuple[int, dict[str, Any]]:
    return 200, {}


async def _empty_async_scalar_result(value: str | None) -> str | None:
    return value


def _record_benchmark_assignment_failure(
    *,
    warnings: list[str] | None,
    partial_failures: list[WorkbenchPartialFailure] | None,
    error_code: str,
    detail: str,
) -> None:
    if warnings is None or partial_failures is None:
        return
    warnings.append("BENCHMARK_ASSIGNMENT_UNAVAILABLE")
    partial_failures.append(build_performance_failure("lotus-core", error_code, detail))
