from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from app.contracts.workbench import WorkbenchPartialFailure
from app.middleware.caller_identity import admitted_tenant_cache_scope
from app.services.async_ttl_cache import AsyncTtlCache
from app.services.performance_workspace_failures import build_performance_failure
from app.services.upstream_envelope import safe_upstream_detail
from app.services.workspace_client_protocols import PerformanceWorkspaceCoreClient


@dataclass(frozen=True)
class BenchmarkAssignmentFailure:
    error_code: str
    detail: str


@dataclass(frozen=True)
class BenchmarkAssignmentResult:
    benchmark_code: str | None
    failure: BenchmarkAssignmentFailure | None = None


def benchmark_assignment_cache_key(
    *,
    portfolio_id: str,
    as_of_date: str,
    reporting_currency: str,
) -> tuple[str, str, str, str, str]:
    return (
        "benchmark_assignment",
        admitted_tenant_cache_scope(),
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
    result = await _fetch_benchmark_assignment_result(
        core_client=core_client,
        portfolio_id=portfolio_id,
        as_of_date=as_of_date,
        reporting_currency=reporting_currency,
        correlation_id=correlation_id,
    )
    _record_assignment_result(result, warnings=warnings, partial_failures=partial_failures)
    return result.benchmark_code


async def _fetch_benchmark_assignment_result(
    *,
    core_client: PerformanceWorkspaceCoreClient,
    portfolio_id: str,
    as_of_date: str,
    reporting_currency: str,
    correlation_id: str,
) -> BenchmarkAssignmentResult:
    status_code, payload = await core_client.get_benchmark_assignment(
        portfolio_id=portfolio_id,
        as_of_date=as_of_date,
        reporting_currency=reporting_currency,
        correlation_id=correlation_id,
    )
    if status_code >= 400:
        return _failed_assignment_result(
            error_code=f"HTTP_{status_code}",
            detail=(
                safe_upstream_detail(payload, default_detail="benchmark assignment unavailable")
                if isinstance(payload, dict)
                else "benchmark assignment returned an invalid payload"
            ),
        )
    if not isinstance(payload, dict):
        return _failed_assignment_result(
            error_code="INVALID_UPSTREAM_PAYLOAD",
            detail="benchmark assignment returned an invalid payload",
        )
    benchmark_id = payload.get("benchmark_id")
    if isinstance(benchmark_id, str) and benchmark_id.strip():
        return BenchmarkAssignmentResult(benchmark_code=benchmark_id.strip())
    if benchmark_id is None and payload.get("assignment_status") == "not_found":
        return BenchmarkAssignmentResult(benchmark_code=None)
    return _failed_assignment_result(
        error_code="INVALID_UPSTREAM_PAYLOAD",
        detail=safe_upstream_detail(payload, default_detail="benchmark assignment unavailable"),
    )


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
    resolved_assignment, cache_hit = await cache.get_or_set_with_status(
        key=cache_key,
        factory=lambda: _fetch_benchmark_assignment_result(
            core_client=core_client,
            portfolio_id=portfolio_id,
            as_of_date=as_of_date,
            reporting_currency=reporting_currency,
            correlation_id=correlation_id,
        ),
    )
    if resolved_assignment.benchmark_code:
        return cast(str, resolved_assignment.benchmark_code)

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
        initial_result=resolved_assignment,
    )


async def _refresh_missing_benchmark_code(
    *,
    cache: AsyncTtlCache[Any],
    cache_key: tuple[str, str, str, str, str],
    cache_hit: bool,
    core_client: PerformanceWorkspaceCoreClient,
    portfolio_id: str,
    correlation_id: str,
    as_of_date: str,
    reporting_currency: str,
    warnings: list[str] | None,
    partial_failures: list[WorkbenchPartialFailure] | None,
    initial_result: BenchmarkAssignmentResult,
) -> str | None:
    cache.discard(cache_key)
    if not cache_hit:
        _record_assignment_result(
            initial_result,
            warnings=warnings,
            partial_failures=partial_failures,
        )
        return None
    refreshed_result = await _fetch_benchmark_assignment_result(
        core_client=core_client,
        portfolio_id=portfolio_id,
        as_of_date=as_of_date,
        reporting_currency=reporting_currency,
        correlation_id=correlation_id,
    )
    _record_assignment_result(
        refreshed_result,
        warnings=warnings,
        partial_failures=partial_failures,
    )
    if refreshed_result.benchmark_code:
        cache.set(cache_key, refreshed_result)
    return refreshed_result.benchmark_code


def _failed_assignment_result(*, error_code: str, detail: str) -> BenchmarkAssignmentResult:
    return BenchmarkAssignmentResult(
        benchmark_code=None,
        failure=BenchmarkAssignmentFailure(error_code=error_code, detail=detail),
    )


def _record_assignment_result(
    result: BenchmarkAssignmentResult,
    *,
    warnings: list[str] | None,
    partial_failures: list[WorkbenchPartialFailure] | None,
) -> None:
    if result.failure is None:
        return
    record_benchmark_assignment_failure(
        warnings=warnings,
        partial_failures=partial_failures,
        error_code=result.failure.error_code,
        detail=result.failure.detail,
    )


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
