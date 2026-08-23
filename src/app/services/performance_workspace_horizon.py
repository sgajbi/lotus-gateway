from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, TypeAlias, cast

from app.contracts.performance_workspace import PerformanceHorizonComparisonRow
from app.contracts.workbench import WorkbenchPartialFailure
from app.services.performance_workspace_failures import build_performance_failure
from app.services.performance_workspace_horizon_rows import build_horizon_comparison_rows
from app.services.performance_workspace_standard_horizon import (
    fetch_standard_horizon_workspace_summary,
    merge_standard_horizon_results,
)
from app.services.upstream_envelope import safe_upstream_detail
from app.services.workspace_client_protocols import PerformanceWorkspaceAnalyticsClient

UpstreamPayload: TypeAlias = dict[str, Any]
UpstreamResult: TypeAlias = tuple[int, UpstreamPayload]
GatheredResult: TypeAlias = UpstreamResult | BaseException

__all__ = [
    "build_horizon_comparison_frequencies",
    "fetch_workspace_horizon_dependencies",
    "merge_standard_horizon_results",
    "parse_horizon_comparison_result",
]


def build_horizon_comparison_frequencies(chart_frequency: str) -> list[str]:
    frequencies: list[str] = []
    for frequency in [chart_frequency, "monthly", "quarterly", "yearly"]:
        if frequency not in frequencies:
            frequencies.append(frequency)
    return frequencies


async def fetch_workspace_horizon_dependencies(
    *,
    analytics_client: PerformanceWorkspaceAnalyticsClient,
    portfolio_id: str,
    correlation_id: str,
    report_end_date: str,
    report_start_date: str | None,
    period: str,
    detail_basis: str,
    benchmark_code: str | None,
    reporting_currency: str,
    chart_frequency: str,
) -> GatheredResult:
    frequencies = build_horizon_comparison_frequencies(chart_frequency)
    if period != "EXPLICIT":
        return await fetch_standard_horizon_workspace_summary(
            analytics_client=analytics_client,
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            report_end_date=report_end_date,
            detail_basis=detail_basis,
            benchmark_code=benchmark_code,
            reporting_currency=reporting_currency,
            chart_frequency=chart_frequency,
            frequencies=frequencies,
        )

    return await fetch_explicit_horizon_workspace_summary(
        analytics_client=analytics_client,
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        report_end_date=report_end_date,
        report_start_date=report_start_date,
        period=period,
        detail_basis=detail_basis,
        benchmark_code=benchmark_code,
        reporting_currency=reporting_currency,
        chart_frequency=chart_frequency,
        frequencies=frequencies,
    )


async def fetch_explicit_horizon_workspace_summary(
    *,
    analytics_client: PerformanceWorkspaceAnalyticsClient,
    portfolio_id: str,
    correlation_id: str,
    report_end_date: str,
    report_start_date: str | None,
    period: str,
    detail_basis: str,
    benchmark_code: str | None,
    reporting_currency: str,
    chart_frequency: str,
    frequencies: Sequence[str],
) -> GatheredResult:
    horizon_periods = [
        {
            "period": period,
            "frequencies": list(frequencies),
        }
    ]
    return cast(
        GatheredResult,
        await analytics_client.get_workspace_summary(
            portfolio_id=portfolio_id,
            report_end_date=report_end_date,
            report_start_date=report_start_date,
            period=period,
            chart_frequency=chart_frequency,
            detail_basis=detail_basis,
            benchmark_id=benchmark_code,
            reporting_currency=reporting_currency,
            segment="asset_class",
            correlation_id=correlation_id,
            periods=horizon_periods,
            include_detail_blocks=False,
        ),
    )


def parse_horizon_comparison_result(
    *,
    result: GatheredResult,
    requested_period: str,
    requested_report_start_date: str | None,
    requested_report_end_date: str | None,
    detail_basis: str,
    warnings: list[str],
    partial_failures: list[WorkbenchPartialFailure],
) -> tuple[list[PerformanceHorizonComparisonRow], str | None]:
    results_by_period = _extract_horizon_results_by_period(
        result=result,
        warnings=warnings,
        partial_failures=partial_failures,
    )
    if results_by_period is None:
        return [], None

    return build_horizon_comparison_rows(
        results_by_period=results_by_period,
        requested_period=requested_period,
        requested_report_start_date=requested_report_start_date,
        requested_report_end_date=requested_report_end_date,
        detail_basis=detail_basis,
    )


def _extract_horizon_results_by_period(
    *,
    result: GatheredResult,
    warnings: list[str],
    partial_failures: list[WorkbenchPartialFailure],
) -> dict[str, Any] | None:
    if isinstance(result, BaseException):
        record_horizon_upstream_failure(
            warnings=warnings,
            partial_failures=partial_failures,
            error_code="UPSTREAM_EXCEPTION",
            detail=str(result),
        )
        return None

    status_code, payload = result
    if not isinstance(payload, dict):
        warnings.append("PERFORMANCE_HORIZON_COMPARISON_INVALID")
        return None

    propagate_gateway_horizon_diagnostics(
        payload=payload,
        warnings=warnings,
        partial_failures=partial_failures,
    )
    if status_code >= 400:
        record_horizon_upstream_failure(
            warnings=warnings,
            partial_failures=partial_failures,
            error_code=f"HTTP_{status_code}",
            detail=safe_upstream_detail(payload, default_detail="horizon comparison failed"),
        )
        return None

    results_by_period = payload.get("results_by_period", {})
    if not isinstance(results_by_period, dict) or not results_by_period:
        warnings.append("PERFORMANCE_HORIZON_COMPARISON_INVALID")
        return None
    return cast(dict[str, Any], results_by_period)


def record_horizon_upstream_failure(
    *,
    warnings: list[str],
    partial_failures: list[WorkbenchPartialFailure],
    error_code: str,
    detail: str,
) -> None:
    warnings.append("PERFORMANCE_HORIZON_COMPARISON_UNAVAILABLE")
    partial_failures.append(build_performance_failure("lotus-performance", error_code, detail))


def propagate_gateway_horizon_diagnostics(
    *,
    payload: Mapping[str, Any],
    warnings: list[str],
    partial_failures: list[WorkbenchPartialFailure],
) -> None:
    gateway_warnings = payload.get("_gateway_warnings", [])
    if isinstance(gateway_warnings, list):
        warnings.extend(str(warning) for warning in gateway_warnings)

    gateway_partial_failures = payload.get("_gateway_partial_failures", [])
    if not isinstance(gateway_partial_failures, list):
        return

    for failure in gateway_partial_failures:
        if not isinstance(failure, Mapping):
            continue
        partial_failures.append(
            build_performance_failure(
                str(failure.get("source_service", "lotus-performance")),
                str(failure.get("error_code", "UNKNOWN_ERROR")),
                str(failure.get("detail", "")),
            )
        )
