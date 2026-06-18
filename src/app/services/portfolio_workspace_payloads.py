from typing import Any

from app.contracts.portfolio_core import PortfolioIdentity, PortfolioSummary
from app.contracts.portfolio_liquidity import PortfolioCashflowOutlook, PortfolioCashflowPoint
from app.contracts.portfolio_workspace import PortfolioOperationalReadiness, PortfolioProfile
from app.precision_policy import quantize_money, quantize_performance


def parse_portfolio_identity(payload: dict[str, Any]) -> PortfolioIdentity:
    portfolio_id = str(payload.get("portfolio_id", ""))
    return PortfolioIdentity(
        portfolio_id=portfolio_id,
        display_name=resolve_portfolio_display_name(payload, fallback_portfolio_id=portfolio_id),
        client_id=optional_text(payload.get("client_id", payload.get("cif_id"))),
        base_currency=str(payload.get("base_currency", "USD")),
        booking_center_code=optional_text(
            payload.get("booking_center_code", payload.get("booking_center"))
        ),
    )


def parse_portfolio_profile(payload: dict[str, Any]) -> PortfolioProfile:
    return PortfolioProfile(
        status=optional_text(payload.get("status")),
        portfolio_type=optional_text(payload.get("portfolio_type")),
        risk_exposure=optional_text(payload.get("risk_exposure")),
        investment_time_horizon=optional_text(payload.get("investment_time_horizon")),
        objective=optional_text(payload.get("objective")),
        is_leverage_allowed=payload.get("is_leverage_allowed"),
        advisor_id=optional_text(payload.get("advisor_id")),
        open_date=optional_text(payload.get("open_date")),
        close_date=optional_text(payload.get("close_date")),
    )


def parse_portfolio_summary(
    *,
    aum_payload: dict[str, Any],
    cash_payload: dict[str, Any],
) -> PortfolioSummary:
    first_portfolio = first_mapping(aum_payload.get("portfolios"))
    invested = float(quantize_money(first_portfolio.get("aum_reporting_currency", 0)))
    cash_totals = cash_payload.get("totals", {})
    if not isinstance(cash_totals, dict):
        cash_totals = {}
    cash_total = float(quantize_money(cash_totals.get("total_balance_reporting_currency", 0)))
    cash_weight = (
        float(quantize_performance((cash_total / invested) * 100)) if invested > 0 else 0.0
    )
    return PortfolioSummary(
        assets_under_management_base=invested,
        invested_market_value_base=float(quantize_money(invested - cash_total)),
        cash_market_value_base=cash_total,
        cash_weight_pct=cash_weight,
        position_count=int(first_portfolio.get("position_count", 0)),
        cash_balance_count=int(cash_totals.get("cash_account_count", 0)),
    )


def parse_cashflow_outlook(payload: dict[str, Any]) -> PortfolioCashflowOutlook:
    return PortfolioCashflowOutlook(
        as_of_date=str(payload.get("as_of_date")),
        range_end_date=str(payload.get("range_end_date")),
        total_net_cashflow_base=float(quantize_money(payload.get("total_net_cashflow", 0))),
        projection_days=int(payload.get("projection_days", 0)),
        include_projected=bool(payload.get("include_projected", False)),
        upcoming_points=[
            PortfolioCashflowPoint(
                projection_date=str(point.get("projection_date")),
                net_cashflow_base=float(quantize_money(point.get("net_cashflow", 0))),
                projected_cumulative_cashflow_base=float(
                    quantize_money(point.get("projected_cumulative_cashflow", 0))
                ),
            )
            for point in payload.get("points", [])
            if isinstance(point, dict)
        ],
    )


def parse_operational_readiness(payload: dict[str, Any]) -> PortfolioOperationalReadiness:
    return PortfolioOperationalReadiness(
        **{key: payload.get(key) for key in PortfolioOperationalReadiness.model_fields}
    )


def resolve_portfolio_display_name(
    payload: dict[str, Any],
    *,
    fallback_portfolio_id: str,
) -> str:
    return str(
        payload.get("portfolio_name")
        or payload.get("name")
        or payload.get("label")
        or payload.get("display_name")
        or fallback_portfolio_id
    )


def optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def first_mapping(value: Any) -> dict[str, Any]:
    if not isinstance(value, list):
        return {}
    return next((item for item in value if isinstance(item, dict)), {})
