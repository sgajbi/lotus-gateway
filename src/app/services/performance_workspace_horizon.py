from __future__ import annotations

import asyncio
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
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
from app.services.upstream_envelope import safe_upstream_detail
from app.services.workspace_client_protocols import PerformanceWorkspaceAnalyticsClient

STANDARD_HORIZON_COMPARISON_PERIODS = ("MTD", "QTD", "YTD")

UpstreamPayload: TypeAlias = dict[str, Any]
UpstreamResult: TypeAlias = tuple[int, UpstreamPayload]
GatheredResult: TypeAlias = UpstreamResult | BaseException


@dataclass(frozen=True)
class HorizonPeriodBlocks:
    period_payload: dict[str, Any]
    benchmark_block: dict[str, Any]
    active_block: dict[str, Any]
    net_block: dict[str, Any]
    gross_block: dict[str, Any]
    economics: dict[str, Any]
    money_weighted_return: dict[str, Any]


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
    if isinstance(result, BaseException):
        record_horizon_upstream_failure(
            warnings=warnings,
            partial_failures=partial_failures,
            error_code="UPSTREAM_EXCEPTION",
            detail=str(result),
        )
        return [], None

    status_code, payload = result
    if not isinstance(payload, dict):
        warnings.append("PERFORMANCE_HORIZON_COMPARISON_INVALID")
        return [], None

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
        return [], None

    results_by_period = payload.get("results_by_period", {})
    if not isinstance(results_by_period, dict) or not results_by_period:
        warnings.append("PERFORMANCE_HORIZON_COMPARISON_INVALID")
        return [], None

    return build_horizon_comparison_rows(
        results_by_period=results_by_period,
        requested_period=requested_period,
        requested_report_start_date=requested_report_start_date,
        requested_report_end_date=requested_report_end_date,
        detail_basis=detail_basis,
    )


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


def build_horizon_comparison_rows(
    *,
    results_by_period: dict[str, Any],
    requested_period: str,
    requested_report_start_date: str | None,
    requested_report_end_date: str | None,
    detail_basis: str,
) -> tuple[list[PerformanceHorizonComparisonRow], str | None]:
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

        row, benchmark_code = build_horizon_comparison_row(
            period=period,
            period_payload=period_payload,
            detail_basis=detail_basis,
            requested_report_start_date=requested_report_start_date,
            requested_report_end_date=requested_report_end_date,
        )
        if row is None:
            continue
        rows.append(row)
        if resolved_benchmark_code is None:
            resolved_benchmark_code = benchmark_code
    return rows, resolved_benchmark_code


def build_horizon_comparison_row(
    *,
    period: str,
    period_payload: dict[str, Any],
    detail_basis: str,
    requested_report_start_date: str | None,
    requested_report_end_date: str | None,
) -> tuple[PerformanceHorizonComparisonRow | None, str | None]:
    blocks = extract_horizon_period_blocks(period_payload)
    comparative = build_workspace_comparative_summary(
        metric_basis=detail_basis.upper(),
        portfolio_block=blocks.net_block,
        benchmark_block=blocks.benchmark_block,
        active_basis_block=blocks.active_block.get("net", {}),
    )
    if comparative.portfolio_return_pct is None and comparative.benchmark_return_pct is None:
        return None, None

    return (
        PerformanceHorizonComparisonRow(
            period=period,
            **build_horizon_row_period_fields(
                blocks=blocks,
                requested_report_start_date=requested_report_start_date,
                requested_report_end_date=requested_report_end_date,
            ),
            **build_horizon_row_economics_fields(blocks),
            **build_horizon_row_return_fields(blocks),
            portfolio_return_pct=comparative.portfolio_return_pct,
            benchmark_return_pct=comparative.benchmark_return_pct,
            active_return_pct=comparative.active_return_pct,
            annualized_return_pct=comparative.annualized_return_pct,
        ),
        comparative.benchmark_id,
    )


def build_horizon_row_period_fields(
    *,
    blocks: HorizonPeriodBlocks,
    requested_report_start_date: str | None,
    requested_report_end_date: str | None,
) -> dict[str, Any]:
    return {
        "period_start": resolve_horizon_period_start(
            blocks=blocks,
            requested_report_start_date=requested_report_start_date,
        ),
        "period_end": resolve_horizon_period_end(
            blocks=blocks,
            requested_report_end_date=requested_report_end_date,
        ),
    }


def build_horizon_row_economics_fields(blocks: HorizonPeriodBlocks) -> dict[str, Any]:
    return {
        "begin_market_value": quantize_optional(blocks.economics.get("begin_market_value")),
        "end_market_value": quantize_optional(blocks.economics.get("end_market_value")),
        "beginning_cash_flow": quantize_optional(blocks.economics.get("beginning_cash_flow")),
        "ending_cash_flow": quantize_optional(blocks.economics.get("ending_cash_flow")),
        "flow_adjusted_end_market_value": quantize_optional(
            blocks.economics.get("flow_adjusted_end_market_value")
        ),
        "net_cash_flow": quantize_optional(blocks.economics.get("net_cash_flow")),
        "fees": quantize_optional(blocks.economics.get("fees")),
    }


def build_horizon_row_return_fields(blocks: HorizonPeriodBlocks) -> dict[str, Any]:
    active_net_block = blocks.active_block.get("net", {})
    return {
        "net_return_pct": extract_return(blocks.net_block, "summary", "period_return", "base"),
        "gross_return_pct": extract_return(
            blocks.gross_block,
            "summary",
            "period_return",
            "base",
        ),
        "cumulative_net_return_pct": extract_return(
            blocks.net_block,
            "summary",
            "cumulative_return",
            "base",
        ),
        "cumulative_gross_return_pct": extract_return(
            blocks.gross_block,
            "summary",
            "cumulative_return",
            "base",
        ),
        "cumulative_benchmark_return_pct": extract_return(
            blocks.benchmark_block,
            "summary",
            "cumulative_return",
            "base",
        ),
        "cumulative_active_return_pct": extract_return(
            active_net_block if isinstance(active_net_block, dict) else {},
            "cumulative_return",
            "base",
        ),
        "annualized_net_return_pct": extract_return(
            blocks.net_block,
            "summary",
            "annualized_return",
            "base",
        ),
        "annualized_gross_return_pct": extract_return(
            blocks.gross_block,
            "summary",
            "annualized_return",
            "base",
        ),
    }


def extract_horizon_period_blocks(
    period_payload: dict[str, Any],
) -> HorizonPeriodBlocks:
    benchmark_payload = period_payload.get("benchmark", {})
    active_payload = period_payload.get("active", {})
    net_block = extract_twr_workspace_block(period_payload, "net")
    gross_block = extract_twr_workspace_block(period_payload, "gross")
    net_summary_payload = net_block.get("summary", {})
    money_weighted_payload = period_payload.get("money_weighted_return", {})
    economics_payload = net_summary_payload.get("economics", {})

    return HorizonPeriodBlocks(
        period_payload=period_payload,
        benchmark_block=benchmark_payload if isinstance(benchmark_payload, dict) else {},
        active_block=active_payload if isinstance(active_payload, dict) else {},
        net_block=net_block,
        gross_block=gross_block,
        economics=economics_payload if isinstance(economics_payload, dict) else {},
        money_weighted_return=money_weighted_payload
        if isinstance(money_weighted_payload, dict)
        else {},
    )


def resolve_horizon_period_start(
    *,
    blocks: HorizonPeriodBlocks,
    requested_report_start_date: str | None,
) -> str | None:
    return (
        safe_str(blocks.money_weighted_return.get("start_date"))
        or safe_str(blocks.period_payload.get("_gateway_requested_period_start"))
        or requested_report_start_date
    )


def resolve_horizon_period_end(
    *,
    blocks: HorizonPeriodBlocks,
    requested_report_end_date: str | None,
) -> str | None:
    return (
        safe_str(blocks.money_weighted_return.get("end_date"))
        or safe_str(blocks.period_payload.get("_gateway_requested_period_end"))
        or requested_report_end_date
    )
