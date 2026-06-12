from typing import Any

from app.contracts.portfolio import PortfolioPerformanceSummary
from app.precision_policy import quantize_performance


def parse_workspace_performance_summary(
    payload: dict[str, Any],
    warnings: list[str],
) -> PortfolioPerformanceSummary | None:
    results_by_period = payload.get("results_by_period", payload.get("resultsByPeriod", {}))
    if not isinstance(results_by_period, dict):
        warnings.append("PORTFOLIO_PERFORMANCE_INVALID")
        return None
    period_key = "YTD" if "YTD" in results_by_period else next(iter(results_by_period), None)
    if period_key is None:
        return None
    period_payload = results_by_period.get(period_key, {})
    if not isinstance(period_payload, dict):
        return None
    portfolio_payload = period_payload.get("portfolio", {})
    if not isinstance(portfolio_payload, dict):
        return None
    summary_payload = portfolio_payload.get("summary", {})
    if not isinstance(summary_payload, dict):
        return None
    period_return_payload = summary_payload.get("period_return", {})
    if not isinstance(period_return_payload, dict):
        return None
    return PortfolioPerformanceSummary(
        period=str(period_key),
        return_pct=quantized_performance_return(period_return_payload.get("base")),
    )


def quantized_performance_return(value: Any) -> float | None:
    try:
        return float(quantize_performance(value)) if value is not None else None
    except (TypeError, ValueError):
        return None
