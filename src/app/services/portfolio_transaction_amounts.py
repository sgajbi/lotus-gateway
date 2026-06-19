from typing import Any

from app.contracts.portfolio_activity_income import PortfolioMoneySummary
from app.precision_policy import quantize_money


def new_flow_metric() -> dict[str, float | int]:
    return {
        "transaction_count": 0,
        "amount_portfolio_currency": 0.0,
        "amount_reporting_currency": 0.0,
    }


def accumulate_flow_metric(
    accumulator: dict[str, float | int],
    *,
    portfolio_amount: float,
    reporting_amount: float,
) -> None:
    accumulator["transaction_count"] = int(accumulator["transaction_count"]) + 1
    accumulator["amount_portfolio_currency"] = (
        float(accumulator["amount_portfolio_currency"]) + portfolio_amount
    )
    accumulator["amount_reporting_currency"] = (
        float(accumulator["amount_reporting_currency"]) + reporting_amount
    )


def build_money_summary(
    payload: dict[str, float | int],
    *,
    portfolio_key: str = "amount_portfolio_currency",
    reporting_key: str = "amount_reporting_currency",
) -> PortfolioMoneySummary:
    return PortfolioMoneySummary(
        portfolio_currency_amount=(
            float(quantize_money(payload.get(portfolio_key, 0)))
            if payload.get(portfolio_key) is not None
            else None
        ),
        reporting_currency_amount=float(quantize_money(payload.get(reporting_key, 0))),
        transaction_count=int(payload.get("transaction_count", 0)),
    )


def activity_bucket_name(transaction_type: str) -> str | None:
    if transaction_type in {"DEPOSIT", "TRANSFER_IN"}:
        return "INFLOWS"
    if transaction_type in {"WITHDRAWAL", "TRANSFER_OUT"}:
        return "OUTFLOWS"
    if transaction_type == "FEE":
        return "FEES"
    if transaction_type == "TAX":
        return "TAXES"
    return None


def activity_portfolio_amount(row: dict[str, Any]) -> float:
    if str(row.get("transaction_type") or "").strip().upper() == "FEE":
        return absolute_money(row.get("gross_transaction_amount")) + absolute_money(
            row.get("trade_fee")
        )
    return absolute_money(row.get("gross_transaction_amount"))


def activity_reporting_amount(row: dict[str, Any]) -> float:
    if str(row.get("transaction_type") or "").strip().upper() == "FEE":
        return reporting_money(
            row,
            reporting_key="gross_transaction_amount_reporting_currency",
            portfolio_key="gross_transaction_amount",
        ) + reporting_money(
            row,
            reporting_key="trade_fee_reporting_currency",
            portfolio_key="trade_fee",
        )
    return reporting_money(
        row,
        reporting_key="gross_transaction_amount_reporting_currency",
        portfolio_key="gross_transaction_amount",
    )


def reporting_money(
    row: dict[str, Any],
    *,
    reporting_key: str,
    portfolio_key: str,
) -> float:
    if row.get(reporting_key) is not None:
        return absolute_money(row.get(reporting_key))
    return absolute_money(row.get(portfolio_key))


def absolute_money(value: Any) -> float:
    if value is None:
        return 0.0
    return float(quantize_money(abs(float(value))))
