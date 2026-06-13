from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any, Awaitable, Callable

from app.contracts.portfolio_activity_income import (
    PortfolioActivityBucketSummary,
    PortfolioActivitySummaryResponse,
    PortfolioIncomePeriodSummary,
    PortfolioIncomeSummaryResponse,
    PortfolioIncomeTypeSummary,
    PortfolioMoneySummary,
)
from app.precision_policy import quantize_money


@dataclass(frozen=True)
class PortfolioTransactionSummaryContext:
    portfolio_id: str
    correlation_id: str
    reporting_currency: str
    window_start: date
    window_end: date
    requested_window_rows: list[dict[str, Any]]
    year_to_date_rows: list[dict[str, Any]]


@dataclass(frozen=True)
class PortfolioTransactionSummaryRequest:
    portfolio_id: str
    correlation_id: str
    as_of_date: str | None
    start_date: str | None
    end_date: str | None
    reporting_currency: str | None


@dataclass(frozen=True)
class TransactionRowsPageRequest:
    portfolio_id: str
    correlation_id: str
    as_of_date: str | None
    skip: int
    limit: int
    start_date: str
    end_date: str
    reporting_currency: str | None


TransactionRowsPageLoader = Callable[[TransactionRowsPageRequest], Awaitable[dict[str, Any]]]


class InvalidPortfolioReportingWindow(ValueError):
    pass


async def build_transaction_summary_context(
    *,
    request: PortfolioTransactionSummaryRequest,
    page_loader: TransactionRowsPageLoader,
    page_size: int = 500,
) -> PortfolioTransactionSummaryContext:
    window_start, window_end = resolve_reporting_window(
        start_date=request.start_date,
        end_date=request.end_date,
        default_end_date=request.as_of_date,
    )
    ytd_start = date(window_end.year, 1, 1)
    resolved_reporting_currency, year_to_date_rows = await list_transaction_rows(
        request=request,
        page_loader=page_loader,
        start_date=ytd_start,
        end_date=window_end,
        page_size=page_size,
    )
    requested_window_rows = [
        item
        for item in year_to_date_rows
        if transaction_date_in_range(
            transaction_date=transaction_date_value(item),
            start_date=window_start,
            end_date=window_end,
        )
    ]
    return PortfolioTransactionSummaryContext(
        portfolio_id=request.portfolio_id,
        correlation_id=request.correlation_id,
        reporting_currency=resolved_reporting_currency or request.reporting_currency or "USD",
        window_start=window_start,
        window_end=window_end,
        requested_window_rows=requested_window_rows,
        year_to_date_rows=year_to_date_rows,
    )


async def list_transaction_rows(
    *,
    request: PortfolioTransactionSummaryRequest,
    page_loader: TransactionRowsPageLoader,
    start_date: date,
    end_date: date,
    page_size: int = 500,
) -> tuple[str | None, list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    resolved_reporting_currency: str | None = None
    skip = 0

    while True:
        result_payload = await page_loader(
            TransactionRowsPageRequest(
                portfolio_id=request.portfolio_id,
                correlation_id=request.correlation_id,
                as_of_date=request.as_of_date,
                skip=skip,
                limit=page_size,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                reporting_currency=request.reporting_currency,
            )
        )
        if resolved_reporting_currency is None:
            resolved_reporting_currency = optional_text(result_payload.get("reporting_currency"))
        page_rows = transaction_page_rows(result_payload)
        rows.extend(page_rows)
        total = int(result_payload.get("total", len(page_rows)))
        skip += len(page_rows)
        if not page_rows or skip >= total:
            break

    return resolved_reporting_currency, rows


def transaction_page_rows(result_payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in result_payload.get("transactions", []) if isinstance(item, dict)]


def resolve_reporting_window(
    *,
    start_date: str | None,
    end_date: str | None,
    default_end_date: str | None = None,
) -> tuple[date, date]:
    window_end = (
        date.fromisoformat(end_date)
        if end_date
        else date.fromisoformat(default_end_date)
        if default_end_date
        else datetime.now(UTC).date()
    )
    window_start = date.fromisoformat(start_date) if start_date else window_end - timedelta(days=29)
    if window_start > window_end:
        raise InvalidPortfolioReportingWindow(
            "portfolio reporting window start_date cannot be after end_date"
        )
    return window_start, window_end


def build_income_summary_response(
    *,
    context: PortfolioTransactionSummaryContext,
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


def build_activity_summary_response(
    *,
    context: PortfolioTransactionSummaryContext,
    contract_version: str,
) -> PortfolioActivitySummaryResponse:
    requested_buckets = summarize_activity_rows(context.requested_window_rows)
    year_to_date_buckets = summarize_activity_rows(context.year_to_date_rows)
    bucket_names = list(dict.fromkeys([*requested_buckets.keys(), *year_to_date_buckets.keys()]))
    return PortfolioActivitySummaryResponse(
        correlation_id=context.correlation_id,
        contract_version=contract_version,
        portfolio_id=context.portfolio_id,
        reporting_currency=context.reporting_currency,
        window_start_date=context.window_start.isoformat(),
        window_end_date=context.window_end.isoformat(),
        buckets=[
            PortfolioActivityBucketSummary(
                bucket=bucket,
                requested_window=build_money_summary(
                    requested_buckets.get(bucket, new_flow_metric())
                ),
                year_to_date=build_money_summary(
                    year_to_date_buckets.get(bucket, new_flow_metric())
                ),
            )
            for bucket in bucket_names
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


def summarize_activity_rows(rows: list[dict[str, Any]]) -> dict[str, dict[str, float | int]]:
    buckets: dict[str, dict[str, float | int]] = {}
    for row in rows:
        transaction_type = str(row.get("transaction_type") or "").strip().upper()
        bucket_name = activity_bucket_name(transaction_type)
        if bucket_name is not None:
            bucket = buckets.setdefault(bucket_name, new_flow_metric())
            accumulate_flow_metric(
                bucket,
                portfolio_amount=activity_portfolio_amount(row),
                reporting_amount=activity_reporting_amount(row),
            )
        withholding_portfolio = absolute_money(row.get("withholding_tax_amount"))
        withholding_reporting = absolute_money(row.get("withholding_tax_amount_reporting_currency"))
        if withholding_portfolio > 0 or withholding_reporting > 0:
            tax_bucket = buckets.setdefault("TAXES", new_flow_metric())
            accumulate_flow_metric(
                tax_bucket,
                portfolio_amount=withholding_portfolio,
                reporting_amount=withholding_reporting,
            )
    return buckets


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


def new_flow_metric() -> dict[str, float | int]:
    return {
        "transaction_count": 0,
        "amount_portfolio_currency": 0.0,
        "amount_reporting_currency": 0.0,
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


def transaction_date_value(item: dict[str, Any]) -> date | None:
    raw_value = optional_text(item.get("transaction_date"))
    if raw_value is None:
        return None
    try:
        return date.fromisoformat(raw_value[:10])
    except ValueError:
        return None


def transaction_date_in_range(
    *,
    transaction_date: date | None,
    start_date: date,
    end_date: date,
) -> bool:
    if transaction_date is None:
        return False
    return start_date <= transaction_date <= end_date


def optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
