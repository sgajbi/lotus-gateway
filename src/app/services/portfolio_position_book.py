from typing import Any

from app.contracts.portfolio import (
    PortfolioPositionView,
    PortfolioSummary,
    PortfolioTopPosition,
)
from app.precision_policy import (
    quantize_money,
    quantize_performance,
    quantize_price,
    quantize_quantity,
)

UpstreamResult = tuple[int, dict[str, Any]]


def parse_position_book_summary(
    aum_payload: dict[str, Any],
    positions_payload: dict[str, Any],
) -> PortfolioSummary:
    first_portfolio: dict[str, Any] = next(iter(aum_payload.get("portfolios", [])), {})
    total_aum = float(quantize_money(first_portfolio.get("aum_reporting_currency", 0)))
    cash_total, cash_balance_count = summarize_cash_positions(positions_payload)
    cash_weight = (
        float(quantize_performance((cash_total / total_aum) * 100)) if total_aum > 0 else 0.0
    )
    return PortfolioSummary(
        assets_under_management_base=total_aum,
        invested_market_value_base=float(quantize_money(total_aum - cash_total)),
        cash_market_value_base=cash_total,
        cash_weight_pct=cash_weight,
        position_count=int(first_portfolio.get("position_count", 0)),
        cash_balance_count=cash_balance_count,
    )


def parse_positions(payload: dict[str, Any]) -> list[PortfolioPositionView]:
    return [parse_position(item) for item in payload.get("positions", []) if isinstance(item, dict)]


def parse_position(item: dict[str, Any]) -> PortfolioPositionView:
    return PortfolioPositionView(
        security_id=str(item.get("security_id", "")),
        instrument_name=str(item.get("instrument_name", "")),
        asset_class=optional_str(item.get("asset_class")),
        isin=optional_str(item.get("isin")),
        currency=optional_str(item.get("currency")),
        sector=optional_str(item.get("sector")),
        country_of_risk=optional_str(item.get("country_of_risk")),
        held_since_date=str(item.get("held_since_date")) if item.get("held_since_date") else None,
        quantity=float(quantize_quantity(item.get("quantity", 0))),
        market_price=position_quote(item),
        cost_basis_base=position_decimal_number(item.get("cost_basis")),
        cost_basis_local=position_decimal_number(item.get("cost_basis_local")),
        market_value_base=position_valuation_money(
            item,
            "market_value_base",
            fallback_key="market_value",
        ),
        market_value_local=position_valuation_money(
            item,
            "market_value_local",
            fallback_key="market_value",
        ),
        unrealized_gain_loss_base=position_valuation_money(
            item,
            "unrealized_gain_loss_base",
            fallback_key="unrealized_gain_loss",
        ),
        unrealized_gain_loss_local=position_valuation_money(
            item,
            "unrealized_gain_loss_local",
            fallback_key="unrealized_gain_loss",
        ),
        weight_pct=position_pct(item),
        reprocessing_status=optional_str(item.get("reprocessing_status")),
    )


def position_quote(item: dict[str, Any]):
    valuation = item.get("valuation", {})
    if not isinstance(valuation, dict):
        return None
    raw_quote = valuation.get("market_price")
    if raw_quote is None:
        return None
    return float(quantize_price(raw_quote))


def position_decimal_number(raw: Any):
    if raw is None:
        return None
    return float(quantize_money(raw))


def position_valuation_money(
    item: dict[str, Any],
    primary_key: str,
    fallback_key: str | None = None,
):
    value = position_valuation_value(item, primary_key, fallback_key=fallback_key)
    return position_decimal_number(value)


def position_pct(item: dict[str, Any]):
    raw = item.get("weight")
    if raw is None:
        return None
    return float(quantize_performance(float(raw or 0) * 100))


def position_valuation_value(
    item: dict[str, Any], primary_key: str, fallback_key: str | None = None
) -> Any:
    valuation = item.get("valuation", {})
    if not isinstance(valuation, dict):
        return None
    primary_value = valuation.get(primary_key)
    if primary_value is not None:
        return primary_value
    if fallback_key is not None:
        return valuation.get(fallback_key)
    return None


def summarize_cash_positions(payload: dict[str, Any]) -> tuple[float, int]:
    cash_total = 0.0
    cash_count = 0
    for item in payload.get("positions", []):
        if not isinstance(item, dict):
            continue
        asset_class = str(item.get("asset_class") or "").strip().upper()
        if asset_class != "CASH":
            continue
        market_value = position_valuation_value(
            item, "market_value_base", fallback_key="market_value"
        )
        cash_total += float(quantize_money(market_value or 0))
        cash_count += 1
    return float(quantize_money(cash_total)), cash_count


def build_top_positions(
    positions: list[PortfolioPositionView],
) -> list[PortfolioTopPosition]:
    ranked = sorted(positions, key=lambda row: row.market_value_base or 0.0, reverse=True)[:10]
    return [PortfolioTopPosition(**row.model_dump()) for row in ranked]


def optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
