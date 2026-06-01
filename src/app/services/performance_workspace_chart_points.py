from __future__ import annotations

from typing import Any

from app.contracts.performance_workspace import PerformanceChartPoint
from app.precision_policy import quantize_performance
from app.services.performance_workspace_parsing import extract_return, safe_str


def build_workspace_chart_points(
    *,
    portfolio_block: dict[str, Any],
    benchmark_block: dict[str, Any],
    chart_frequency: str,
) -> list[PerformanceChartPoint]:
    normalized_frequency = chart_frequency.lower()
    portfolio_breakdowns = portfolio_block.get("breakdowns", {})
    benchmark_breakdowns = benchmark_block.get("breakdowns", {})
    if not isinstance(portfolio_breakdowns, dict):
        return []
    portfolio_rows = portfolio_breakdowns.get(normalized_frequency, [])
    benchmark_rows = (
        benchmark_breakdowns.get(normalized_frequency, [])
        if isinstance(benchmark_breakdowns, dict)
        else []
    )
    if not isinstance(portfolio_rows, list):
        return []
    points: list[PerformanceChartPoint] = []
    for index, portfolio_row in enumerate(portfolio_rows):
        if not isinstance(portfolio_row, dict):
            continue
        benchmark_row = (
            benchmark_rows[index]
            if index < len(benchmark_rows) and isinstance(benchmark_rows[index], dict)
            else {}
        )
        portfolio_period = extract_return(portfolio_row, "period_return", "base")
        benchmark_period = extract_return(benchmark_row, "period_return", "base")
        portfolio_cumulative = extract_return(portfolio_row, "cumulative_return", "base")
        benchmark_cumulative = extract_return(benchmark_row, "cumulative_return", "base")
        active_period = None
        active_cumulative = None
        if portfolio_period is not None and benchmark_period is not None:
            active_period = float(quantize_performance(portfolio_period - benchmark_period))
        if portfolio_cumulative is not None and benchmark_cumulative is not None:
            active_cumulative = float(
                quantize_performance(portfolio_cumulative - benchmark_cumulative)
            )
        points.append(
            PerformanceChartPoint(
                label=str(portfolio_row.get("period", f"point-{index + 1}")),
                frequency=normalized_frequency,
                period_start=safe_str(portfolio_row.get("period_start")),
                period_end=safe_str(portfolio_row.get("period_end")),
                portfolio_return_pct=portfolio_period,
                benchmark_return_pct=benchmark_period,
                active_return_pct=active_period,
                cumulative_portfolio_return_pct=portfolio_cumulative,
                cumulative_benchmark_return_pct=benchmark_cumulative,
                cumulative_active_return_pct=active_cumulative,
            )
        )
    return points


def parse_chart_points(
    *,
    portfolio_block: dict[str, Any],
    benchmark_block: dict[str, Any],
    relative_block: dict[str, Any],
    chart_frequency: str,
) -> list[PerformanceChartPoint]:
    normalized_frequency = chart_frequency.lower()
    portfolio_breakdowns = portfolio_block.get("breakdowns", {})
    benchmark_breakdowns = benchmark_block.get("breakdowns", {})
    relative_breakdowns = relative_block.get("breakdowns", {})
    if not isinstance(portfolio_breakdowns, dict):
        return []
    portfolio_rows = portfolio_breakdowns.get(normalized_frequency, [])
    benchmark_rows = (
        benchmark_breakdowns.get(normalized_frequency, [])
        if isinstance(benchmark_breakdowns, dict)
        else []
    )
    relative_rows = (
        relative_breakdowns.get(normalized_frequency, [])
        if isinstance(relative_breakdowns, dict)
        else []
    )
    if not isinstance(portfolio_rows, list):
        return []
    points: list[PerformanceChartPoint] = []
    for index, portfolio_row in enumerate(portfolio_rows):
        if not isinstance(portfolio_row, dict):
            continue
        benchmark_row = benchmark_rows[index] if index < len(benchmark_rows) else {}
        relative_row = relative_rows[index] if index < len(relative_rows) else {}
        if not isinstance(benchmark_row, dict):
            benchmark_row = {}
        if not isinstance(relative_row, dict):
            relative_row = {}
        points.append(
            PerformanceChartPoint(
                label=str(portfolio_row.get("period", f"point-{index + 1}")),
                frequency=normalized_frequency,
                period_start=safe_str(portfolio_row.get("period_start")),
                period_end=safe_str(portfolio_row.get("period_end")),
                portfolio_return_pct=extract_return(portfolio_row, "period_return", "base"),
                benchmark_return_pct=extract_return(benchmark_row, "period_return", "base"),
                active_return_pct=extract_return(relative_row, "period_return", "base"),
                cumulative_portfolio_return_pct=extract_return(
                    portfolio_row, "cumulative_return", "base"
                ),
                cumulative_benchmark_return_pct=extract_return(
                    benchmark_row, "cumulative_return", "base"
                ),
                cumulative_active_return_pct=extract_return(
                    relative_row, "cumulative_return", "base"
                ),
            )
        )
    return points
