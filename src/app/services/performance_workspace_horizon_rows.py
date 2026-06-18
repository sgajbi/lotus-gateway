from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.contracts.performance_workspace import PerformanceHorizonComparisonRow
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

STANDARD_HORIZON_COMPARISON_PERIODS = ("MTD", "QTD", "YTD")


@dataclass(frozen=True)
class HorizonPeriodBlocks:
    period_payload: dict[str, Any]
    benchmark_block: dict[str, Any]
    active_block: dict[str, Any]
    net_block: dict[str, Any]
    gross_block: dict[str, Any]
    economics: dict[str, Any]
    money_weighted_return: dict[str, Any]


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
