from app.contracts.portfolio import (
    PortfolioActivityBucketSummary,
    PortfolioActivitySummaryResponse,
    PortfolioMoneySummary,
    PortfolioPositionView,
    PortfolioSummary,
    PortfolioTopPosition,
)
from app.services.portfolio_insights import (
    build_portfolio_insights,
    has_cash_funding_evidence,
    max_position_weight,
    requested_window_activity_amount,
)


def _summary(
    *,
    cash_market_value_base: float = 0.0,
    cash_weight_pct: float = 0.0,
    position_count: int = 0,
    cash_balance_count: int = 0,
) -> PortfolioSummary:
    return PortfolioSummary(
        assets_under_management_base=1000.0,
        invested_market_value_base=1000.0 - cash_market_value_base,
        cash_market_value_base=cash_market_value_base,
        cash_weight_pct=cash_weight_pct,
        position_count=position_count,
        cash_balance_count=cash_balance_count,
    )


def _money(amount: float, count: int = 0) -> PortfolioMoneySummary:
    return PortfolioMoneySummary(
        portfolio_currency_amount=amount,
        reporting_currency_amount=amount,
        transaction_count=count,
    )


def _activity(*buckets: tuple[str, float, int]) -> PortfolioActivitySummaryResponse:
    return PortfolioActivitySummaryResponse(
        correlation_id="corr-insights",
        portfolio_id="PF_1001",
        reporting_currency="USD",
        window_start_date="2026-03-01",
        window_end_date="2026-03-31",
        buckets=[
            PortfolioActivityBucketSummary(
                bucket=name,
                requested_window=_money(amount, count),
                year_to_date=_money(amount, count),
            )
            for name, amount, count in buckets
        ],
    )


def _position(weight_pct: float | None = None) -> PortfolioPositionView:
    return PortfolioPositionView(
        security_id="EQ_1",
        instrument_name="Equity 1",
        quantity=10.0,
        market_value_base=700.0,
        weight_pct=weight_pct,
    )


def _top_position(weight_pct: float | None = None) -> PortfolioTopPosition:
    return PortfolioTopPosition(
        security_id="EQ_1",
        instrument_name="Equity 1",
        quantity=10.0,
        market_value_base=700.0,
        weight_pct=weight_pct,
    )


def test_portfolio_insights_report_empty_unfunded_unready_book() -> None:
    insights = build_portfolio_insights(
        portfolio_id="PF_1001",
        summary=_summary(),
        positions=[],
        top_positions=[],
        activity_summary=_activity(),
        pricing_status="Missing",
        reporting_status="Missing",
    )

    assert [insight.key for insight in insights] == [
        "no-holdings-booked",
        "no-cash-funding",
        "pricing-not-published",
        "reporting-unavailable",
    ]


def test_portfolio_insights_use_cash_activity_and_concentration_evidence() -> None:
    insights = build_portfolio_insights(
        portfolio_id="PF_1001",
        summary=_summary(position_count=1, cash_weight_pct=16.0),
        positions=[_position(weight_pct=5.0)],
        top_positions=[_top_position(weight_pct=22.0)],
        activity_summary=_activity(("INFLOWS", 100.0, 1), ("OUTFLOWS", 130.0, 1)),
        pricing_status="Ready",
        reporting_status="Ready",
    )

    assert [insight.key for insight in insights] == [
        "equity-concentration-high",
        "cash-above-target",
        "net-outflows-window",
    ]
    assert insights[0].href == "/risk?portfolioId=PF_1001"


def test_portfolio_insight_helpers_calculate_source_backed_signals() -> None:
    activity_summary = _activity(("INFLOWS", 20.0, 0), ("FEES", 5.0, 1), ("TAXES", 3.0, 1))

    assert has_cash_funding_evidence(
        summary=_summary(cash_market_value_base=0.0),
        activity_summary=activity_summary,
    )
    assert requested_window_activity_amount(activity_summary) == 12.0
    assert (
        max_position_weight(
            positions=[_position(weight_pct=7.0)],
            top_positions=[_top_position(weight_pct=18.0)],
        )
        == 18.0
    )
