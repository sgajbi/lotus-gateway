from typing import Any, Protocol, Self


class CallerBoundClient(Protocol):
    """Client capability for binding an admitted caller context."""

    def with_caller_headers(self, caller_headers: dict[str, str]) -> Self: ...


class PerformanceTwrClient(Protocol):
    """Client capability for portfolio time-weighted-return analytics."""

    async def get_twr_analytics(
        self,
        *,
        portfolio_id: str,
        report_end_date: str,
        report_start_date: str | None,
        period: str,
        metric_basis: str,
        benchmark_id: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...
