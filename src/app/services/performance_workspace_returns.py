from __future__ import annotations

from typing import Any

from app.contracts.performance_workspace import PerformanceComparativeSummary
from app.services.performance_workspace_parsing import extract_return, quantize_optional, safe_str


def extract_twr_workspace_block(period_payload: dict[str, Any], basis: str) -> dict[str, Any]:
    portfolio_twr = period_payload.get("portfolio_twr", {})
    if not isinstance(portfolio_twr, dict):
        return {}
    block = portfolio_twr.get(basis.lower(), {})
    return block if isinstance(block, dict) else {}


def build_workspace_comparative_summary(
    *,
    metric_basis: str,
    portfolio_block: dict[str, Any],
    benchmark_block: dict[str, Any],
    active_basis_block: Any,
) -> PerformanceComparativeSummary:
    active_payload = active_basis_block if isinstance(active_basis_block, dict) else {}
    economics = (
        portfolio_block.get("summary", {}).get("economics", {})
        if isinstance(portfolio_block.get("summary"), dict)
        else {}
    )
    return PerformanceComparativeSummary(
        metric_basis=metric_basis,
        portfolio_return_pct=extract_return(portfolio_block, "summary", "period_return", "base"),
        benchmark_return_pct=extract_return(benchmark_block, "summary", "period_return", "base"),
        active_return_pct=extract_return(active_payload, "period_return", "base"),
        annualized_return_pct=extract_return(
            portfolio_block, "summary", "annualized_return", "base"
        ),
        benchmark_id=safe_str(benchmark_block.get("benchmark_id")),
        benchmark_return_source=safe_str(benchmark_block.get("return_source")),
        benchmark_input_mode=safe_str(benchmark_block.get("input_mode")),
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
        fees=quantize_optional(economics.get("fees")) if isinstance(economics, dict) else None,
    )
