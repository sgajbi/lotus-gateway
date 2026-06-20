from datetime import date
from typing import Any, Protocol

from app.contracts.portfolio_activity_income import (
    PortfolioActivityBucketSummary,
    PortfolioActivitySummaryResponse,
)
from app.services.portfolio_transaction_amounts import (
    absolute_money,
    accumulate_flow_metric,
    activity_bucket_name,
    activity_portfolio_amount,
    activity_reporting_amount,
    build_money_summary,
    new_flow_metric,
)


class PortfolioTransactionActivityContext(Protocol):
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


def build_activity_summary_response(
    *,
    context: PortfolioTransactionActivityContext,
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
