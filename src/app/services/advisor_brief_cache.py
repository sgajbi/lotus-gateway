"""Cache key ownership for the advisor-brief response cache."""

from app.middleware.caller_identity import admitted_tenant_cache_scope


def advisor_brief_cache_key(
    *,
    portfolio_id: str,
    period: str,
    chart_frequency: str,
    contribution_dimension: str,
    attribution_dimension: str,
    detail_basis: str,
    benchmark_code: str | None,
    explicit_start_date: str | None,
    explicit_end_date: str | None,
    requested_as_of_date: str | None,
    requested_reporting_currency: str | None,
) -> tuple[str, ...]:
    # The brief wraps the Core-backed performance workspace; the response cache
    # is partitioned by the admitted tenant fence.
    return (
        "advisor_brief",
        admitted_tenant_cache_scope(),
        portfolio_id,
        period,
        chart_frequency,
        contribution_dimension,
        attribution_dimension,
        detail_basis,
        benchmark_code or "",
        explicit_start_date or "",
        explicit_end_date or "",
        requested_as_of_date or "",
        requested_reporting_currency or "",
    )
