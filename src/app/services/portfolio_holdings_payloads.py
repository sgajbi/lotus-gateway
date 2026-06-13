from typing import Any

from app.contracts.portfolio_holdings import (
    PortfolioAllocationBucket,
    PortfolioAllocationView,
    PortfolioCashBalance,
)
from app.precision_policy import quantize_money, quantize_performance


def parse_allocation_views(payload: dict[str, Any]) -> list[PortfolioAllocationView]:
    return [
        PortfolioAllocationView(
            dimension=str(view.get("dimension")),
            buckets=[
                PortfolioAllocationBucket(
                    bucket=str(bucket.get("dimension_value")),
                    position_count=int(bucket.get("position_count", 0)),
                    market_value_base=float(
                        quantize_money(bucket.get("market_value_reporting_currency", 0))
                    ),
                    weight_pct=float(quantize_performance(float(bucket.get("weight", 0)) * 100)),
                )
                for bucket in view.get("buckets", [])
                if isinstance(bucket, dict)
            ],
        )
        for view in payload.get("views", [])
        if isinstance(view, dict)
    ]


def parse_cash_balances(payload: dict[str, Any], total_aum: float) -> list[PortfolioCashBalance]:
    balances: list[PortfolioCashBalance] = []
    for item in payload.get("cash_accounts", []):
        balance = float(quantize_money(item.get("balance_reporting_currency", 0)))
        weight = float(quantize_performance((balance / total_aum) * 100)) if total_aum > 0 else 0.0
        balances.append(
            PortfolioCashBalance(
                security_id=str(item.get("security_id", "")),
                instrument_name=str(item.get("instrument_name", "")),
                currency=optional_str(item.get("account_currency")),
                quantity=float(quantize_money(item.get("balance_account_currency", 0))),
                market_value_base=balance,
                weight_pct=weight,
            )
        )
    return balances


def optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
