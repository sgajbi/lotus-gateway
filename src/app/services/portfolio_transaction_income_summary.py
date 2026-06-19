from datetime import date
from typing import Any, Protocol

from app.contracts.portfolio_activity_income import (
    PortfolioIncomePeriodSummary,
    PortfolioIncomeSummaryResponse,
    PortfolioIncomeTypeSummary,
)
from app.precision_policy import quantize_money
from app.services.portfolio_transaction_amounts import (
    absolute_money,
    build_money_summary,
    reporting_money,
)


class PortfolioTransactionIncomeContext(Protocol):
    @property
    def portfolio_id(self) -> str: ...

    @property
    def correlation_id(self) -> str: ...

    @property
    def reporting_currency(self) -> str: ...

    @property
    def requested_window_rows(self) -> list[dict[str, Any]]: ...

    @property
    def year_to_date_rows(self) -> list[dict[str, Any]]: ...

    @property
    def window_start(self) -> date: ...

    @property
    def window_end(self) -> date: ...


def build_income_summary_response(
    *,
    context: PortfolioTransactionIncomeContext,
    contract_version: str,
) -> PortfolioIncomeSummaryResponse:
    requested_totals, income_type_totals = summarize_income_rows(context.requested_window_rows)
    year_to_date_totals, income_type_ytd_totals = summarize_income_rows(context.year_to_date_rows)
    income_types = sorted(set(income_type_totals) | set(income_type_ytd_totals))
    return PortfolioIncomeSummaryResponse(
        correlation_id=context.correlation_id,
        contract_version=contract_version,
        portfolio_id=context.portfolio_id,
        reporting_currency=context.reporting_currency,
        window_start_date=context.window_start.isoformat(),
        window_end_date=context.window_end.isoformat(),
        totals_requested_window=build_income_period_summary(requested_totals),
        totals_year_to_date=build_income_period_summary(year_to_date_totals),
        income_types=[
            PortfolioIncomeTypeSummary(
                income_type=income_type,
                requested_window=build_income_period_summary(
                    income_type_totals.get(income_type, new_income_metric())
                ),
                year_to_date=build_income_period_summary(
                    income_type_ytd_totals.get(income_type, new_income_metric())
                ),
            )
            for income_type in income_types
        ],
    )


def summarize_income_rows(
    rows: list[dict[str, Any]],
) -> tuple[dict[str, float | int], dict[str, dict[str, float | int]]]:
    totals = new_income_metric()
    by_income_type: dict[str, dict[str, float | int]] = {}
    for row in rows:
        income_type = str(row.get("transaction_type") or "").strip().upper()
        if income_type not in {"DIVIDEND", "INTEREST"}:
            continue
        bucket = by_income_type.setdefault(income_type, new_income_metric())
        accumulate_income_metric(totals, row)
        accumulate_income_metric(bucket, row)
    return totals, by_income_type


def new_income_metric() -> dict[str, float | int]:
    return {
        "transaction_count": 0,
        "gross_amount_portfolio_currency": 0.0,
        "gross_amount_reporting_currency": 0.0,
        "withholding_tax_portfolio_currency": 0.0,
        "withholding_tax_reporting_currency": 0.0,
        "other_deductions_portfolio_currency": 0.0,
        "other_deductions_reporting_currency": 0.0,
        "net_amount_portfolio_currency": 0.0,
        "net_amount_reporting_currency": 0.0,
    }


def accumulate_income_metric(
    accumulator: dict[str, float | int],
    row: dict[str, Any],
) -> None:
    accumulator["transaction_count"] = int(accumulator["transaction_count"]) + 1
    accumulator["gross_amount_portfolio_currency"] = float(
        accumulator["gross_amount_portfolio_currency"]
    ) + absolute_money(row.get("gross_transaction_amount"))
    accumulator["gross_amount_reporting_currency"] = float(
        accumulator["gross_amount_reporting_currency"]
    ) + reporting_money(
        row,
        reporting_key="gross_transaction_amount_reporting_currency",
        portfolio_key="gross_transaction_amount",
    )
    accumulator["withholding_tax_portfolio_currency"] = float(
        accumulator["withholding_tax_portfolio_currency"]
    ) + absolute_money(row.get("withholding_tax_amount"))
    accumulator["withholding_tax_reporting_currency"] = float(
        accumulator["withholding_tax_reporting_currency"]
    ) + reporting_money(
        row,
        reporting_key="withholding_tax_amount_reporting_currency",
        portfolio_key="withholding_tax_amount",
    )
    accumulator["other_deductions_portfolio_currency"] = float(
        accumulator["other_deductions_portfolio_currency"]
    ) + absolute_money(row.get("other_interest_deductions_amount"))
    accumulator["other_deductions_reporting_currency"] = float(
        accumulator["other_deductions_reporting_currency"]
    ) + reporting_money(
        row,
        reporting_key="other_interest_deductions_amount_reporting_currency",
        portfolio_key="other_interest_deductions_amount",
    )
    accumulator["net_amount_portfolio_currency"] = float(
        accumulator["net_amount_portfolio_currency"]
    ) + income_net_portfolio_amount(row)
    accumulator["net_amount_reporting_currency"] = float(
        accumulator["net_amount_reporting_currency"]
    ) + income_net_reporting_amount(row)


def build_income_period_summary(
    payload: dict[str, float | int],
) -> PortfolioIncomePeriodSummary:
    return PortfolioIncomePeriodSummary(
        gross=build_money_summary(
            payload,
            portfolio_key="gross_amount_portfolio_currency",
            reporting_key="gross_amount_reporting_currency",
        ),
        withholding_tax=build_money_summary(
            payload,
            portfolio_key="withholding_tax_portfolio_currency",
            reporting_key="withholding_tax_reporting_currency",
        ),
        other_deductions=build_money_summary(
            payload,
            portfolio_key="other_deductions_portfolio_currency",
            reporting_key="other_deductions_reporting_currency",
        ),
        net=build_money_summary(
            payload,
            portfolio_key="net_amount_portfolio_currency",
            reporting_key="net_amount_reporting_currency",
        ),
    )


def income_net_portfolio_amount(row: dict[str, Any]) -> float:
    if (
        str(row.get("transaction_type") or "").strip().upper() == "INTEREST"
        and row.get("net_interest_amount") is not None
    ):
        return absolute_money(row.get("net_interest_amount"))
    gross = absolute_money(row.get("gross_transaction_amount"))
    withholding = absolute_money(row.get("withholding_tax_amount"))
    other_deductions = absolute_money(row.get("other_interest_deductions_amount"))
    trade_fee = absolute_money(row.get("trade_fee"))
    return float(quantize_money(gross - withholding - other_deductions - trade_fee))


def income_net_reporting_amount(row: dict[str, Any]) -> float:
    if (
        str(row.get("transaction_type") or "").strip().upper() == "INTEREST"
        and row.get("net_interest_amount_reporting_currency") is not None
    ):
        return absolute_money(row.get("net_interest_amount_reporting_currency"))
    gross = reporting_money(
        row,
        reporting_key="gross_transaction_amount_reporting_currency",
        portfolio_key="gross_transaction_amount",
    )
    withholding = reporting_money(
        row,
        reporting_key="withholding_tax_amount_reporting_currency",
        portfolio_key="withholding_tax_amount",
    )
    other_deductions = reporting_money(
        row,
        reporting_key="other_interest_deductions_amount_reporting_currency",
        portfolio_key="other_interest_deductions_amount",
    )
    trade_fee = reporting_money(
        row,
        reporting_key="trade_fee_reporting_currency",
        portfolio_key="trade_fee",
    )
    return float(quantize_money(gross - withholding - other_deductions - trade_fee))
