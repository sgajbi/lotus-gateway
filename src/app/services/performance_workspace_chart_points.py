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
    portfolio_rows = _frequency_rows(
        block=portfolio_block,
        normalized_frequency=normalized_frequency,
    )
    if portfolio_rows is None:
        return []
    benchmark_rows = _frequency_rows(
        block=benchmark_block,
        normalized_frequency=normalized_frequency,
    )
    points: list[PerformanceChartPoint] = []
    for index, portfolio_row in enumerate(portfolio_rows):
        if not isinstance(portfolio_row, dict):
            continue
        points.append(
            _build_active_chart_point(
                index=index,
                normalized_frequency=normalized_frequency,
                portfolio_row=portfolio_row,
                benchmark_row=_peer_row_at(benchmark_rows, index),
            )
        )
    return points


def _frequency_rows(
    *,
    block: dict[str, Any],
    normalized_frequency: str,
) -> list[Any] | None:
    breakdowns = block.get("breakdowns", {})
    if not isinstance(breakdowns, dict):
        return None
    rows = breakdowns.get(normalized_frequency, [])
    if isinstance(rows, list):
        return rows
    return None


def _peer_row_at(rows: list[Any] | None, index: int) -> dict[str, Any]:
    if rows is None or index >= len(rows):
        return {}
    row = rows[index]
    if isinstance(row, dict):
        return row
    return {}


def _build_active_chart_point(
    *,
    index: int,
    normalized_frequency: str,
    portfolio_row: dict[str, Any],
    benchmark_row: dict[str, Any],
) -> PerformanceChartPoint:
    portfolio_period = extract_return(portfolio_row, "period_return", "base")
    benchmark_period = extract_return(benchmark_row, "period_return", "base")
    portfolio_cumulative = extract_return(portfolio_row, "cumulative_return", "base")
    benchmark_cumulative = extract_return(benchmark_row, "cumulative_return", "base")
    return PerformanceChartPoint(
        label=str(portfolio_row.get("period", f"point-{index + 1}")),
        frequency=normalized_frequency,
        period_start=safe_str(portfolio_row.get("period_start")),
        period_end=safe_str(portfolio_row.get("period_end")),
        portfolio_return_pct=portfolio_period,
        benchmark_return_pct=benchmark_period,
        active_return_pct=_active_return(portfolio_period, benchmark_period),
        cumulative_portfolio_return_pct=portfolio_cumulative,
        cumulative_benchmark_return_pct=benchmark_cumulative,
        cumulative_active_return_pct=_active_return(
            portfolio_cumulative,
            benchmark_cumulative,
        ),
    )


def _active_return(
    portfolio_return: float | None,
    benchmark_return: float | None,
) -> float | None:
    if portfolio_return is None or benchmark_return is None:
        return None
    return float(quantize_performance(portfolio_return - benchmark_return))


def _build_parsed_chart_point(
    *,
    index: int,
    normalized_frequency: str,
    portfolio_row: dict[str, Any],
    benchmark_row: dict[str, Any],
    relative_row: dict[str, Any],
) -> PerformanceChartPoint:
    return PerformanceChartPoint(
        label=str(portfolio_row.get("period", f"point-{index + 1}")),
        frequency=normalized_frequency,
        period_start=safe_str(portfolio_row.get("period_start")),
        period_end=safe_str(portfolio_row.get("period_end")),
        portfolio_return_pct=extract_return(portfolio_row, "period_return", "base"),
        benchmark_return_pct=extract_return(benchmark_row, "period_return", "base"),
        active_return_pct=extract_return(relative_row, "period_return", "base"),
        cumulative_portfolio_return_pct=extract_return(portfolio_row, "cumulative_return", "base"),
        cumulative_benchmark_return_pct=extract_return(benchmark_row, "cumulative_return", "base"),
        cumulative_active_return_pct=extract_return(relative_row, "cumulative_return", "base"),
    )


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
            _build_parsed_chart_point(
                index=index,
                normalized_frequency=normalized_frequency,
                portfolio_row=portfolio_row,
                benchmark_row=benchmark_row,
                relative_row=relative_row,
            )
        )
    return points
