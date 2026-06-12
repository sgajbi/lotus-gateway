from app.contracts.portfolio import (
    PortfolioInsight,
)
from app.contracts.portfolio_activity_income import PortfolioActivitySummaryResponse
from app.contracts.portfolio_core import PortfolioSummary
from app.contracts.portfolio_holdings import PortfolioPositionView, PortfolioTopPosition


def build_portfolio_insights(
    *,
    portfolio_id: str,
    summary: PortfolioSummary,
    positions: list[PortfolioPositionView],
    top_positions: list[PortfolioTopPosition],
    activity_summary: PortfolioActivitySummaryResponse,
    pricing_status: str,
    reporting_status: str,
) -> list[PortfolioInsight]:
    candidates = [
        holdings_booked_insight(positions),
        cash_funding_insight(summary=summary, activity_summary=activity_summary),
        pricing_readiness_insight(pricing_status),
        reporting_readiness_insight(reporting_status),
        concentration_insight(
            portfolio_id=portfolio_id,
            positions=positions,
            top_positions=top_positions,
        ),
        cash_allocation_insight(summary),
        activity_outflow_insight(activity_summary),
    ]
    return [insight for insight in candidates if insight is not None]


def holdings_booked_insight(
    positions: list[PortfolioPositionView],
) -> PortfolioInsight | None:
    if positions:
        return None
    return PortfolioInsight(
        key="no-holdings-booked",
        title="No holdings booked",
        detail="Book the first position to activate holdings, allocation, and valuation views.",
        severity="critical",
        href="#portfolio-drilldown",
    )


def cash_funding_insight(
    *,
    summary: PortfolioSummary,
    activity_summary: PortfolioActivitySummaryResponse,
) -> PortfolioInsight | None:
    if has_cash_funding_evidence(summary=summary, activity_summary=activity_summary):
        return None
    return PortfolioInsight(
        key="no-cash-funding",
        title="No cash funding recorded",
        detail="Add opening cash or a subscription so the portfolio can be funded and invested.",
        severity="critical",
        href="#portfolio-insights",
    )


def pricing_readiness_insight(pricing_status: str) -> PortfolioInsight | None:
    if pricing_status == "Ready":
        return None
    return PortfolioInsight(
        key="pricing-not-published",
        title="Pricing not yet published",
        detail="Publish prices to complete valuation and unlock reliable reporting.",
        severity="warning",
        href="#portfolio-attention",
    )


def reporting_readiness_insight(reporting_status: str) -> PortfolioInsight | None:
    if reporting_status == "Ready":
        return None
    return PortfolioInsight(
        key="reporting-unavailable",
        title="Reporting cannot be generated yet",
        detail="Reporting remains blocked until book coverage and valuation are complete.",
        severity="warning",
        href="#portfolio-health",
    )


def concentration_insight(
    *,
    portfolio_id: str,
    positions: list[PortfolioPositionView],
    top_positions: list[PortfolioTopPosition],
) -> PortfolioInsight | None:
    if max_position_weight(positions=positions, top_positions=top_positions) < 20:
        return None
    return PortfolioInsight(
        key="equity-concentration-high",
        title="Large position dominates portfolio risk",
        detail=(
            "One holding has become large enough to dominate current portfolio concentration. "
            "Open Risk to review concentration pressure."
        ),
        severity="warning",
        href=f"/risk?portfolioId={portfolio_id}",
    )


def cash_allocation_insight(summary: PortfolioSummary) -> PortfolioInsight | None:
    if (summary.cash_weight_pct or 0) < 15:
        return None
    return PortfolioInsight(
        key="cash-above-target",
        title="Cash exceeds target allocation",
        detail="Available cash is elevated relative to invested assets.",
        severity="info",
        href="#portfolio-insights",
    )


def activity_outflow_insight(
    activity_summary: PortfolioActivitySummaryResponse,
) -> PortfolioInsight | None:
    if requested_window_activity_amount(activity_summary) >= 0:
        return None
    return PortfolioInsight(
        key="net-outflows-window",
        title="Net outflows in last 30 days",
        detail="Recent activity is net negative over the selected reporting window.",
        severity="warning",
        href="#portfolio-changes",
    )


def max_position_weight(
    *,
    positions: list[PortfolioPositionView],
    top_positions: list[PortfolioTopPosition],
) -> float:
    weighted_positions = [
        *(position.weight_pct or 0 for position in top_positions),
        *(position.weight_pct or 0 for position in positions),
    ]
    return max(weighted_positions, default=0)


def has_cash_funding_evidence(
    *,
    summary: PortfolioSummary,
    activity_summary: PortfolioActivitySummaryResponse,
) -> bool:
    if summary.cash_balance_count > 0:
        return True
    if summary.cash_market_value_base > 0:
        return True

    inflow_bucket = next(
        (bucket for bucket in activity_summary.buckets if bucket.bucket.upper() == "INFLOWS"),
        None,
    )
    if inflow_bucket is None:
        return False
    if inflow_bucket.requested_window.transaction_count > 0:
        return True
    return inflow_bucket.requested_window.reporting_currency_amount > 0


def requested_window_activity_amount(
    activity_summary: PortfolioActivitySummaryResponse,
) -> float:
    return sum(
        bucket.requested_window.reporting_currency_amount
        * (
            1
            if bucket.bucket.upper() == "INFLOWS"
            else -1
            if bucket.bucket.upper() in {"OUTFLOWS", "FEES", "TAXES"}
            else 0
        )
        for bucket in activity_summary.buckets
    )
