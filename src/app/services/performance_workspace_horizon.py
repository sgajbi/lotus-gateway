from __future__ import annotations

import asyncio
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from typing import Any, TypeAlias, cast

from app.contracts.performance_workspace import PerformanceHorizonComparisonRow
from app.contracts.workbench import WorkbenchPartialFailure
from app.services.performance_workspace_failures import build_performance_failure
from app.services.performance_workspace_horizon_rows import build_horizon_comparison_rows
from app.services.upstream_envelope import safe_upstream_detail
from app.services.workspace_client_protocols import PerformanceWorkspaceAnalyticsClient

UpstreamPayload: TypeAlias = dict[str, Any]
UpstreamResult: TypeAlias = tuple[int, UpstreamPayload]
GatheredResult: TypeAlias = UpstreamResult | BaseException


@dataclass(frozen=True)
class StandardHorizonWindow:
    label: str
    report_start_date: str | None
    period: str


@dataclass
class StandardHorizonMergeState:
    results_by_period: dict[str, Any]
    warnings: list[str]
    partial_failures: list[dict[str, str]]

    def record_failure(self, *, label: str, error_code: str, detail: str) -> None:
        self.warnings.append(f"PERFORMANCE_HORIZON_{label}_UNAVAILABLE")
        self.partial_failures.append(
            {
                "source_service": "lotus-performance",
                "error_code": error_code,
                "detail": detail,
            }
        )


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
    portfolio_currency: str,
    chart_frequency: str,
) -> GatheredResult:
    if period != "EXPLICIT":
        return await fetch_standard_horizon_workspace_summary(
            analytics_client=analytics_client,
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            report_end_date=report_end_date,
            detail_basis=detail_basis,
            benchmark_code=benchmark_code,
            portfolio_currency=portfolio_currency,
            chart_frequency=chart_frequency,
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
        portfolio_currency=portfolio_currency,
        chart_frequency=chart_frequency,
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
    portfolio_currency: str,
    chart_frequency: str,
) -> GatheredResult:
    horizon_periods = [
        {
            "period": period,
            "frequencies": build_horizon_comparison_frequencies(chart_frequency),
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
            reporting_currency=portfolio_currency,
            segment="asset_class",
            correlation_id=correlation_id,
            periods=horizon_periods,
            include_detail_blocks=False,
        ),
    )


async def fetch_standard_horizon_workspace_summary(
    *,
    analytics_client: PerformanceWorkspaceAnalyticsClient,
    portfolio_id: str,
    correlation_id: str,
    report_end_date: str,
    detail_basis: str,
    benchmark_code: str | None,
    portfolio_currency: str,
    chart_frequency: str,
) -> GatheredResult:
    frequencies = build_horizon_comparison_frequencies(chart_frequency)
    report_end = date.fromisoformat(report_end_date)
    windows = build_standard_horizon_windows(report_end)

    gathered_results = await asyncio.gather(
        *[
            fetch_standard_horizon_window_summary(
                analytics_client=analytics_client,
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                report_end_date=report_end_date,
                detail_basis=detail_basis,
                benchmark_code=benchmark_code,
                portfolio_currency=portfolio_currency,
                chart_frequency=chart_frequency,
                frequencies=frequencies,
                window=window,
            )
            for window in windows
        ],
        return_exceptions=True,
    )

    return merge_standard_horizon_results(
        gathered_results=gathered_results,
        month_start=windows[0].report_start_date or report_end_date,
        quarter_start=windows[1].report_start_date or report_end_date,
        report_end_date=report_end_date,
    )


def build_standard_horizon_windows(report_end: date) -> tuple[StandardHorizonWindow, ...]:
    quarter_start_month = ((report_end.month - 1) // 3) * 3 + 1
    return (
        StandardHorizonWindow(
            label="MTD",
            report_start_date=report_end.replace(day=1).isoformat(),
            period="EXPLICIT",
        ),
        StandardHorizonWindow(
            label="QTD",
            report_start_date=report_end.replace(month=quarter_start_month, day=1).isoformat(),
            period="EXPLICIT",
        ),
        StandardHorizonWindow(label="STANDARD", report_start_date=None, period="YTD"),
    )


async def fetch_standard_horizon_window_summary(
    *,
    analytics_client: PerformanceWorkspaceAnalyticsClient,
    portfolio_id: str,
    correlation_id: str,
    report_end_date: str,
    detail_basis: str,
    benchmark_code: str | None,
    portfolio_currency: str,
    chart_frequency: str,
    frequencies: Sequence[str],
    window: StandardHorizonWindow,
) -> UpstreamResult:
    return await analytics_client.get_workspace_summary(
        portfolio_id=portfolio_id,
        report_end_date=report_end_date,
        report_start_date=window.report_start_date,
        period=window.period,
        chart_frequency=chart_frequency,
        detail_basis=detail_basis,
        benchmark_id=benchmark_code,
        reporting_currency=portfolio_currency,
        segment="asset_class",
        correlation_id=correlation_id,
        periods=[{"period": window.period, "frequencies": list(frequencies)}],
        include_detail_blocks=False,
    )


def merge_standard_horizon_results(
    *,
    gathered_results: Sequence[UpstreamResult | BaseException],
    month_start: str,
    quarter_start: str,
    report_end_date: str,
) -> UpstreamResult:
    merge_state = StandardHorizonMergeState(
        results_by_period={},
        warnings=[],
        partial_failures=[],
    )

    for label, result in zip(("MTD", "QTD", "STANDARD"), gathered_results, strict=True):
        merge_standard_horizon_result(
            merge_state=merge_state,
            label=label,
            result=result,
            month_start=month_start,
            quarter_start=quarter_start,
            report_end_date=report_end_date,
        )

    return 200, {
        "results_by_period": merge_state.results_by_period,
        "_gateway_warnings": merge_state.warnings,
        "_gateway_partial_failures": merge_state.partial_failures,
    }


def merge_standard_horizon_result(
    *,
    merge_state: StandardHorizonMergeState,
    label: str,
    result: UpstreamResult | BaseException,
    month_start: str,
    quarter_start: str,
    report_end_date: str,
) -> None:
    if isinstance(result, BaseException):
        merge_state.record_failure(
            label=label,
            error_code="UPSTREAM_EXCEPTION",
            detail=str(result),
        )
        return

    status_code, payload = result
    if status_code >= 400 or not isinstance(payload, dict):
        merge_state.record_failure(
            label=label,
            error_code=standard_horizon_error_code(status_code),
            detail=standard_horizon_error_detail(payload),
        )
        return

    results_by_period = payload.get("results_by_period", {})
    if isinstance(results_by_period, dict):
        merge_standard_horizon_period_payload(
            merge_state=merge_state,
            label=label,
            results_by_period=results_by_period,
            month_start=month_start,
            quarter_start=quarter_start,
            report_end_date=report_end_date,
        )


def standard_horizon_error_code(status_code: int) -> str:
    return f"HTTP_{status_code}" if isinstance(status_code, int) else "INVALID_UPSTREAM_PAYLOAD"


def standard_horizon_error_detail(payload: UpstreamPayload) -> str:
    if isinstance(payload, dict):
        return safe_upstream_detail(payload, default_detail="horizon request failed")
    return str(payload)


def merge_standard_horizon_period_payload(
    *,
    merge_state: StandardHorizonMergeState,
    label: str,
    results_by_period: Mapping[str, Any],
    month_start: str,
    quarter_start: str,
    report_end_date: str,
) -> None:
    if label in {"MTD", "QTD"}:
        merge_explicit_standard_horizon_period(
            merge_state=merge_state,
            label=label,
            results_by_period=results_by_period,
            month_start=month_start,
            quarter_start=quarter_start,
            report_end_date=report_end_date,
        )
        return

    period_payload = results_by_period.get("YTD")
    if isinstance(period_payload, dict):
        merge_state.results_by_period["YTD"] = period_payload


def merge_explicit_standard_horizon_period(
    *,
    merge_state: StandardHorizonMergeState,
    label: str,
    results_by_period: Mapping[str, Any],
    month_start: str,
    quarter_start: str,
    report_end_date: str,
) -> None:
    explicit_result = results_by_period.get("EXPLICIT")
    if isinstance(explicit_result, dict):
        merge_state.results_by_period[label] = {
            **explicit_result,
            "_gateway_requested_period_start": month_start if label == "MTD" else quarter_start,
            "_gateway_requested_period_end": report_end_date,
        }


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
