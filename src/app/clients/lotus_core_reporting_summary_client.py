"""Client mixin for Lotus Core's bounded bulk portfolio-summary contract."""

from typing import Any


class LotusCoreReportingSummaryClientMixin:
    async def _post_query_resource(
        self,
        *,
        operation: str,
        path: str,
        correlation_id: str,
        payload: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        raise NotImplementedError

    async def query_bulk_portfolio_summary(
        self,
        *,
        correlation_id: str,
        portfolio_ids: list[str],
        as_of_date: str | None = None,
        reporting_currency: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        payload: dict[str, Any] = {"portfolio_ids": portfolio_ids}
        if as_of_date is not None:
            payload["as_of_date"] = as_of_date
        if reporting_currency is not None:
            payload["reporting_currency"] = reporting_currency
        return await self._post_query_resource(
            operation="core.reporting.portfolio-summary.bulk-query",
            path="/reporting/portfolio-summary/bulk-query",
            correlation_id=correlation_id,
            payload=payload,
        )
