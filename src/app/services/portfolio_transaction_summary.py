from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any, Awaitable, Callable

from app.services.portfolio_transaction_amounts import (
    absolute_money as absolute_money,
)
from app.services.portfolio_transaction_amounts import (
    accumulate_flow_metric as accumulate_flow_metric,
)
from app.services.portfolio_transaction_amounts import (
    activity_bucket_name as activity_bucket_name,
)
from app.services.portfolio_transaction_amounts import (
    activity_portfolio_amount as activity_portfolio_amount,
)
from app.services.portfolio_transaction_amounts import (
    activity_reporting_amount as activity_reporting_amount,
)
from app.services.portfolio_transaction_amounts import (
    build_money_summary as build_money_summary,
)
from app.services.portfolio_transaction_amounts import (
    new_flow_metric as new_flow_metric,
)
from app.services.portfolio_transaction_amounts import (
    reporting_money as reporting_money,
)
from app.services.portfolio_transaction_income_summary import (
    build_income_summary_response as build_income_summary_response,
)
from app.services.portfolio_transaction_income_summary import (
    summarize_income_rows as summarize_income_rows,
)

__all__ = [
    "InvalidPortfolioReportingWindow",
    "PortfolioTransactionSummaryContext",
    "PortfolioTransactionSummaryRequest",
    "TransactionRowsPageRequest",
    "build_income_summary_response",
    "build_transaction_summary_context",
    "resolve_reporting_window",
    "summarize_income_rows",
    "transaction_date_in_range",
    "transaction_date_value",
    "transaction_page_rows",
]


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
