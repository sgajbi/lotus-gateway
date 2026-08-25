from __future__ import annotations

from typing import Any, cast

from app.contracts.workbench import WorkbenchPartialFailure
from app.services.async_ttl_cache import AsyncTtlCache
from app.services.performance_workspace_failures import build_performance_failure
from app.services.performance_workspace_parsing import safe_str
from app.services.upstream_envelope import safe_upstream_detail
from app.services.workspace_client_protocols import PerformanceWorkspaceCoreClient


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
        record_benchmark_assignment_failure(
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

    return await _refresh_missing_benchmark_code(
        cache=cache,
        cache_key=cache_key,
        cache_hit=cache_hit,
        core_client=core_client,
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        as_of_date=as_of_date,
        reporting_currency=reporting_currency,
        warnings=warnings,
        partial_failures=partial_failures,
    )


async def _refresh_missing_benchmark_code(
    *,
    cache: AsyncTtlCache[Any],
    cache_key: tuple[str, str, str, str],
    cache_hit: bool,
    core_client: PerformanceWorkspaceCoreClient,
    portfolio_id: str,
    correlation_id: str,
    as_of_date: str,
    reporting_currency: str,
    warnings: list[str] | None,
    partial_failures: list[WorkbenchPartialFailure] | None,
) -> str | None:
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


def record_benchmark_assignment_failure(
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
