from __future__ import annotations

import asyncio
from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any, TypeAlias, cast

from app.contracts.performance_workspace import PerformanceHorizonComparisonRow
from app.contracts.workbench import WorkbenchPartialFailure
from app.services.performance_workspace_failures import build_performance_failure
from app.services.performance_workspace_parsing import (
    extract_return,
    quantize_optional,
    safe_str,
)
from app.services.performance_workspace_returns import (
    build_workspace_comparative_summary,
    extract_twr_workspace_block,
    resolve_results_period_key,
)
from app.services.workspace_client_protocols import PerformanceWorkspaceAnalyticsClient

STANDARD_HORIZON_COMPARISON_PERIODS = ("MTD", "QTD", "YTD")

UpstreamPayload: TypeAlias = dict[str, Any]
UpstreamResult: TypeAlias = tuple[int, UpstreamPayload]
GatheredResult: TypeAlias = UpstreamResult | BaseException


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
    month_start = report_end.replace(day=1).isoformat()
    quarter_start_month = ((report_end.month - 1) // 3) * 3 + 1
    quarter_start = report_end.replace(month=quarter_start_month, day=1).isoformat()

    gathered_results = await asyncio.gather(
        analytics_client.get_workspace_summary(
            portfolio_id=portfolio_id,
            report_end_date=report_end_date,
            report_start_date=month_start,
            period="EXPLICIT",
            chart_frequency=chart_frequency,
            detail_basis=detail_basis,
            benchmark_id=benchmark_code,
            reporting_currency=portfolio_currency,
            segment="asset_class",
            correlation_id=correlation_id,
            periods=[{"period": "EXPLICIT", "frequencies": frequencies}],
            include_detail_blocks=False,
        ),
        analytics_client.get_workspace_summary(
            portfolio_id=portfolio_id,
            report_end_date=report_end_date,
            report_start_date=quarter_start,
            period="EXPLICIT",
            chart_frequency=chart_frequency,
            detail_basis=detail_basis,
            benchmark_id=benchmark_code,
            reporting_currency=portfolio_currency,
            segment="asset_class",
            correlation_id=correlation_id,
            periods=[{"period": "EXPLICIT", "frequencies": frequencies}],
            include_detail_blocks=False,
        ),
        analytics_client.get_workspace_summary(
            portfolio_id=portfolio_id,
            report_end_date=report_end_date,
            report_start_date=None,
            period="YTD",
            chart_frequency=chart_frequency,
            detail_basis=detail_basis,
            benchmark_id=benchmark_code,
            reporting_currency=portfolio_currency,
            segment="asset_class",
            correlation_id=correlation_id,
            periods=[{"period": "YTD", "frequencies": frequencies}],
            include_detail_blocks=False,
        ),
        return_exceptions=True,
    )

    return merge_standard_horizon_results(
        gathered_results=gathered_results,
        month_start=month_start,
        quarter_start=quarter_start,
        report_end_date=report_end_date,
    )


def merge_standard_horizon_results(
    *,
    gathered_results: Sequence[UpstreamResult | BaseException],
    month_start: str,
    quarter_start: str,
    report_end_date: str,
) -> UpstreamResult:
    result_labels = ("MTD", "QTD", "STANDARD")
    merged_results: dict[str, Any] = {}
    merged_warnings: list[str] = []
    merged_failures: list[dict[str, str]] = []

    for label, result in zip(result_labels, gathered_results, strict=True):
        if isinstance(result, BaseException):
            merged_warnings.append(f"PERFORMANCE_HORIZON_{label}_UNAVAILABLE")
            merged_failures.append(
                {
                    "source_service": "lotus-performance",
                    "error_code": "UPSTREAM_EXCEPTION",
                    "detail": str(result),
                }
            )
            continue

        status_code, payload = result
        if status_code >= 400 or not isinstance(payload, dict):
            merged_warnings.append(f"PERFORMANCE_HORIZON_{label}_UNAVAILABLE")
            merged_failures.append(
                {
                    "source_service": "lotus-performance",
                    "error_code": (
                        f"HTTP_{status_code}"
                        if isinstance(status_code, int)
                        else "INVALID_UPSTREAM_PAYLOAD"
                    ),
                    "detail": str(payload.get("detail", payload))
                    if isinstance(payload, dict)
                    else str(payload),
                }
            )
            continue

        results_by_period = payload.get("results_by_period", {})
        if not isinstance(results_by_period, dict):
            continue

        if label in {"MTD", "QTD"}:
            explicit_result = results_by_period.get("EXPLICIT")
            if isinstance(explicit_result, dict):
                merged_results[label] = {
                    **explicit_result,
                    "_gateway_requested_period_start": month_start
                    if label == "MTD"
                    else quarter_start,
                    "_gateway_requested_period_end": report_end_date,
                }
            continue

        period_payload = results_by_period.get("YTD")
        if isinstance(period_payload, dict):
            merged_results["YTD"] = period_payload

    return 200, {
        "results_by_period": merged_results,
        "_gateway_warnings": merged_warnings,
        "_gateway_partial_failures": merged_failures,
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
    if isinstance(result, BaseException):
        warnings.append("PERFORMANCE_HORIZON_COMPARISON_UNAVAILABLE")
        partial_failures.append(
            build_performance_failure("lotus-performance", "UPSTREAM_EXCEPTION", str(result))
        )
        return [], None

    status_code, payload = result
    if not isinstance(payload, dict):
        warnings.append("PERFORMANCE_HORIZON_COMPARISON_INVALID")
        return [], None
    gateway_warnings = payload.get("_gateway_warnings", [])
    if isinstance(gateway_warnings, list):
        warnings.extend(str(warning) for warning in gateway_warnings)
    gateway_partial_failures = payload.get("_gateway_partial_failures", [])
    if isinstance(gateway_partial_failures, list):
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
    if status_code >= 400:
        warnings.append("PERFORMANCE_HORIZON_COMPARISON_UNAVAILABLE")
        partial_failures.append(
            build_performance_failure(
                "lotus-performance",
                f"HTTP_{status_code}",
                str(payload.get("detail", payload)),
            )
        )
        return [], None

    results_by_period = payload.get("results_by_period", {})
    if not isinstance(results_by_period, dict) or not results_by_period:
        warnings.append("PERFORMANCE_HORIZON_COMPARISON_INVALID")
        return [], None

    rows: list[PerformanceHorizonComparisonRow] = []
    resolved_benchmark_code: str | None = None
    periods_to_render = (
        tuple(results_by_period.keys())
        if requested_period.upper() == "EXPLICIT"
        else STANDARD_HORIZON_COMPARISON_PERIODS
    )
    for period in periods_to_render:
        period_key = resolve_results_period_key(
            requested_period=period,
            results_by_period=results_by_period,
        )
        period_payload = results_by_period.get(period_key, {})
        if not isinstance(period_payload, dict):
            continue
        benchmark_block = period_payload.get("benchmark", {})
        active_block = period_payload.get("active", {})
        net_block = extract_twr_workspace_block(period_payload, "net")
        gross_block = extract_twr_workspace_block(period_payload, "gross")
        net_summary_payload = net_block.get("summary", {}) if isinstance(net_block, dict) else {}
        money_weighted_return = period_payload.get("money_weighted_return", {})
        economics = (
            net_summary_payload.get("economics", {})
            if isinstance(net_summary_payload, dict)
            else {}
        )
        comparative = build_workspace_comparative_summary(
            metric_basis=detail_basis.upper(),
            portfolio_block=net_block,
            benchmark_block=benchmark_block if isinstance(benchmark_block, dict) else {},
            active_basis_block=active_block.get("net") if isinstance(active_block, dict) else {},
        )
        if comparative.portfolio_return_pct is None and comparative.benchmark_return_pct is None:
            continue
        rows.append(
            PerformanceHorizonComparisonRow(
                period=period,
                period_start=(
                    safe_str(money_weighted_return.get("start_date"))
                    if isinstance(money_weighted_return, dict)
                    else None
                )
                or safe_str(period_payload.get("_gateway_requested_period_start"))
                or requested_report_start_date,
                period_end=(
                    safe_str(money_weighted_return.get("end_date"))
                    if isinstance(money_weighted_return, dict)
                    else None
                )
                or safe_str(period_payload.get("_gateway_requested_period_end"))
                or requested_report_end_date,
                begin_market_value=quantize_optional(economics.get("begin_market_value"))
                if isinstance(economics, dict)
                else None,
                end_market_value=quantize_optional(economics.get("end_market_value"))
                if isinstance(economics, dict)
                else None,
                beginning_cash_flow=quantize_optional(economics.get("beginning_cash_flow"))
                if isinstance(economics, dict)
                else None,
                ending_cash_flow=quantize_optional(economics.get("ending_cash_flow"))
                if isinstance(economics, dict)
                else None,
                flow_adjusted_end_market_value=quantize_optional(
                    economics.get("flow_adjusted_end_market_value")
                )
                if isinstance(economics, dict)
                else None,
                net_cash_flow=quantize_optional(economics.get("net_cash_flow"))
                if isinstance(economics, dict)
                else None,
                fees=quantize_optional(economics.get("fees"))
                if isinstance(economics, dict)
                else None,
                net_return_pct=extract_return(net_block, "summary", "period_return", "base"),
                gross_return_pct=extract_return(gross_block, "summary", "period_return", "base"),
                portfolio_return_pct=comparative.portfolio_return_pct,
                benchmark_return_pct=comparative.benchmark_return_pct,
                active_return_pct=comparative.active_return_pct,
                cumulative_net_return_pct=extract_return(
                    net_block,
                    "summary",
                    "cumulative_return",
                    "base",
                ),
                cumulative_gross_return_pct=extract_return(
                    gross_block,
                    "summary",
                    "cumulative_return",
                    "base",
                ),
                cumulative_benchmark_return_pct=extract_return(
                    benchmark_block if isinstance(benchmark_block, dict) else {},
                    "summary",
                    "cumulative_return",
                    "base",
                ),
                cumulative_active_return_pct=extract_return(
                    active_block.get("net") if isinstance(active_block, dict) else {},
                    "cumulative_return",
                    "base",
                ),
                annualized_net_return_pct=extract_return(
                    net_block,
                    "summary",
                    "annualized_return",
                    "base",
                ),
                annualized_gross_return_pct=extract_return(
                    gross_block,
                    "summary",
                    "annualized_return",
                    "base",
                ),
                annualized_return_pct=comparative.annualized_return_pct,
            )
        )
        if resolved_benchmark_code is None:
            resolved_benchmark_code = comparative.benchmark_id
    return rows, resolved_benchmark_code
