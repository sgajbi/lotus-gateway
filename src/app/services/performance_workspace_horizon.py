from __future__ import annotations

import asyncio
from collections.abc import Sequence
from datetime import date
from typing import Any, TypeAlias, cast

from app.services.workspace_client_protocols import PerformanceWorkspaceAnalyticsClient

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
