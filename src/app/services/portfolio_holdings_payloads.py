from typing import Any

from app.contracts.portfolio_holdings import (
    PortfolioAllocationBucket,
    PortfolioAllocationLookThroughCapability,
    PortfolioAllocationResponse,
    PortfolioAllocationView,
    PortfolioCashBalance,
)
from app.precision_policy import quantize_money, quantize_performance
from app.services.portfolio_position_book import parse_position_book_summary


def build_portfolio_allocation_response(
    *,
    correlation_id: str,
    contract_version: str,
    portfolio_id: str,
    as_of_date: str | None,
    default_as_of_date: str,
    reporting_currency: str | None,
    aum_payload: dict[str, Any],
    positions_payload: dict[str, Any],
    allocation_payload: dict[str, Any],
) -> PortfolioAllocationResponse:
    return PortfolioAllocationResponse(
        correlation_id=correlation_id,
        contract_version=contract_version,
        portfolio_id=portfolio_id,
        as_of_date=str(aum_payload.get("resolved_as_of_date") or as_of_date or default_as_of_date),
        reporting_currency=optional_str(allocation_payload.get("reporting_currency"))
        or reporting_currency,
        look_through=parse_look_through_capability(allocation_payload.get("look_through")),
        summary=parse_position_book_summary(aum_payload, positions_payload),
        views=parse_allocation_views(allocation_payload),
    )


def parse_look_through_capability(
    payload: Any,
) -> PortfolioAllocationLookThroughCapability | None:
    if not isinstance(payload, dict):
        return None
    requested_mode = optional_str(payload.get("requested_mode"))
    effective_mode = optional_str(payload.get("effective_mode"))
    if requested_mode is None or effective_mode is None:
        return None
    return PortfolioAllocationLookThroughCapability(
        requested_mode=requested_mode,
        effective_mode=effective_mode,
        applied=bool(payload.get("applied", False)),
    )


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
