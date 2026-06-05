from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Sequence
from typing import Any, TypeAlias, cast

from app.contracts.performance_workspace import PerformanceBenchmarkOptionView
from app.contracts.workbench import WorkbenchPartialFailure
from app.services.async_ttl_cache import AsyncTtlCache
from app.services.performance_workspace_failures import build_performance_failure
from app.services.performance_workspace_parsing import safe_str
from app.services.upstream_envelope import safe_upstream_detail
from app.services.workspace_client_protocols import PerformanceWorkspaceCoreClient

UpstreamPayload: TypeAlias = dict[str, Any]
UpstreamResult: TypeAlias = tuple[int, UpstreamPayload]
GatheredResult: TypeAlias = UpstreamResult | BaseException


def benchmark_assignment_cache_key(
    *,
    portfolio_id: str,
    as_of_date: str,
    portfolio_currency: str,
) -> tuple[str, str, str, str]:
    return (
        "benchmark_assignment",
        portfolio_id,
        as_of_date,
        portfolio_currency,
    )


def benchmark_catalog_cache_key(
    *,
    report_end_date: str,
    portfolio_currency: str,
) -> tuple[str, str, str]:
    return ("benchmark_catalog", report_end_date, portfolio_currency)


async def fetch_assigned_benchmark_code(
    *,
    core_client: PerformanceWorkspaceCoreClient,
    portfolio_id: str,
    as_of_date: str,
    portfolio_currency: str,
    correlation_id: str,
) -> str | None:
    status_code, payload = await core_client.get_benchmark_assignment(
        portfolio_id=portfolio_id,
        as_of_date=as_of_date,
        reporting_currency=portfolio_currency,
        correlation_id=correlation_id,
    )
    if status_code >= 400 or not isinstance(payload, dict):
        return None
    return safe_str(payload.get("benchmark_id"))


async def resolve_benchmark_code(
    *,
    cache: AsyncTtlCache[Any],
    core_client: PerformanceWorkspaceCoreClient,
    portfolio_id: str,
    correlation_id: str,
    as_of_date: str,
    portfolio_currency: str,
    benchmark_code: str | None,
) -> str | None:
    if benchmark_code:
        return benchmark_code

    cache_key = benchmark_assignment_cache_key(
        portfolio_id=portfolio_id,
        as_of_date=as_of_date,
        portfolio_currency=portfolio_currency,
    )
    resolved_benchmark_code, cache_hit = await cache.get_or_set_with_status(
        key=cache_key,
        factory=lambda: fetch_assigned_benchmark_code(
            core_client=core_client,
            portfolio_id=portfolio_id,
            as_of_date=as_of_date,
            portfolio_currency=portfolio_currency,
            correlation_id=correlation_id,
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
        portfolio_currency=portfolio_currency,
        correlation_id=correlation_id,
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
    portfolio_currency: str,
    benchmark_code: str | None,
    include_benchmark_catalog: bool,
) -> tuple[str | None, GatheredResult]:
    assignment_task, benchmark_catalog_task = _benchmark_context_tasks(
        cache=cache,
        core_client=core_client,
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        report_end_date=report_end_date,
        portfolio_currency=portfolio_currency,
        benchmark_code=benchmark_code,
        include_benchmark_catalog=include_benchmark_catalog,
    )
    benchmark_context_results = await asyncio.gather(
        assignment_task,
        benchmark_catalog_task,
        return_exceptions=True,
    )
    return _resolve_benchmark_context_results(
        benchmark_code=benchmark_code,
        benchmark_context_results=benchmark_context_results,
    )


def _benchmark_context_tasks(
    *,
    cache: AsyncTtlCache[Any],
    core_client: PerformanceWorkspaceCoreClient,
    portfolio_id: str,
    correlation_id: str,
    report_end_date: str,
    portfolio_currency: str,
    benchmark_code: str | None,
    include_benchmark_catalog: bool,
) -> tuple[Awaitable[str | None], Awaitable[GatheredResult]]:
    return (
        _benchmark_assignment_task(
            cache=cache,
            core_client=core_client,
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            report_end_date=report_end_date,
            portfolio_currency=portfolio_currency,
            benchmark_code=benchmark_code,
        ),
        _benchmark_catalog_task(
            cache=cache,
            core_client=core_client,
            report_end_date=report_end_date,
            portfolio_currency=portfolio_currency,
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
    portfolio_currency: str,
    benchmark_code: str | None,
) -> Awaitable[str | None]:
    if benchmark_code:
        return _empty_async_scalar_result(None)
    return resolve_benchmark_code(
        cache=cache,
        core_client=core_client,
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        as_of_date=report_end_date,
        portfolio_currency=portfolio_currency,
        benchmark_code=benchmark_code,
    )


def _benchmark_catalog_task(
    *,
    cache: AsyncTtlCache[Any],
    core_client: PerformanceWorkspaceCoreClient,
    report_end_date: str,
    portfolio_currency: str,
    correlation_id: str,
    include_benchmark_catalog: bool,
) -> Awaitable[GatheredResult]:
    if not include_benchmark_catalog:
        return _empty_async_result()
    return cache.get_or_set(
        key=benchmark_catalog_cache_key(
            report_end_date=report_end_date,
            portfolio_currency=portfolio_currency,
        ),
        factory=lambda: core_client.get_benchmark_catalog(
            as_of_date=report_end_date,
            benchmark_currency=portfolio_currency,
            benchmark_status="active",
            benchmark_type="composite",
            correlation_id=correlation_id,
        ),
    )


def _resolve_benchmark_context_results(
    *,
    benchmark_code: str | None,
    benchmark_context_results: Sequence[object],
) -> tuple[str | None, GatheredResult]:
    resolved_benchmark_code_result = cast(
        str | None | BaseException,
        benchmark_context_results[0],
    )
    benchmark_catalog_result_value = cast(GatheredResult, benchmark_context_results[1])
    if isinstance(resolved_benchmark_code_result, BaseException):
        return benchmark_code, benchmark_catalog_result_value
    return benchmark_code or cast(str | None, resolved_benchmark_code_result), (
        benchmark_catalog_result_value
    )


def parse_benchmark_catalog_result(
    *,
    result: GatheredResult,
    assigned_benchmark_code: str | None,
    warnings: list[str],
    partial_failures: list[WorkbenchPartialFailure],
) -> list[PerformanceBenchmarkOptionView]:
    if isinstance(result, BaseException):
        _record_benchmark_catalog_failure(
            warnings=warnings,
            partial_failures=partial_failures,
            error_code="UPSTREAM_EXCEPTION",
            detail=str(result),
        )
        return []
    status_code, payload = result
    if status_code >= 400 or not isinstance(payload, dict):
        _record_benchmark_catalog_failure(
            warnings=warnings,
            partial_failures=partial_failures,
            error_code=(
                f"HTTP_{status_code}"
                if isinstance(status_code, int)
                else "INVALID_UPSTREAM_PAYLOAD"
            ),
            detail=(
                safe_upstream_detail(payload, default_detail="benchmark catalog unavailable")
                if isinstance(payload, dict)
                else str(payload)
            ),
        )
        return []
    records = payload.get("records", [])
    if not isinstance(records, list):
        return []
    options_by_code: dict[str, PerformanceBenchmarkOptionView] = {}
    for record in records:
        option = _benchmark_option_from_record(
            record=record,
            assigned_benchmark_code=assigned_benchmark_code,
        )
        if option is not None:
            _upsert_benchmark_option(options_by_code, option)
    return sorted(
        options_by_code.values(),
        key=lambda option: (not option.is_assigned, option.benchmark_name),
    )


def _record_benchmark_catalog_failure(
    *,
    warnings: list[str],
    partial_failures: list[WorkbenchPartialFailure],
    error_code: str,
    detail: str,
) -> None:
    warnings.append("BENCHMARK_CATALOG_UNAVAILABLE")
    partial_failures.append(build_performance_failure("lotus-core", error_code, detail))


def _benchmark_option_from_record(
    *,
    record: object,
    assigned_benchmark_code: str | None,
) -> PerformanceBenchmarkOptionView | None:
    if not isinstance(record, dict):
        return None
    benchmark_code = safe_str(record.get("benchmark_id"))
    benchmark_name = safe_str(record.get("benchmark_name"))
    if not benchmark_code or not benchmark_name:
        return None
    return PerformanceBenchmarkOptionView(
        benchmark_code=benchmark_code,
        benchmark_name=benchmark_name,
        benchmark_currency=safe_str(record.get("benchmark_currency")),
        benchmark_type=safe_str(record.get("benchmark_type")),
        benchmark_family=safe_str(record.get("benchmark_family")),
        benchmark_provider=safe_str(record.get("benchmark_provider")),
        is_assigned=benchmark_code == assigned_benchmark_code,
    )


def _upsert_benchmark_option(
    options_by_code: dict[str, PerformanceBenchmarkOptionView],
    option: PerformanceBenchmarkOptionView,
) -> None:
    existing = options_by_code.get(option.benchmark_code)
    if existing is None or (option.is_assigned and not existing.is_assigned):
        options_by_code[option.benchmark_code] = option


async def _empty_async_result() -> tuple[int, dict[str, Any]]:
    return 200, {}


async def _empty_async_scalar_result(value: str | None) -> str | None:
    return value
