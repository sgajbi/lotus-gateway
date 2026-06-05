from __future__ import annotations

import asyncio
from typing import Any, TypeAlias, cast

from app.services.async_ttl_cache import AsyncTtlCache
from app.services.workspace_client_protocols import PerformanceWorkspaceAnalyticsClient

UpstreamPayload: TypeAlias = dict[str, Any]
UpstreamResult: TypeAlias = tuple[int, UpstreamPayload]
GatheredResult: TypeAlias = UpstreamResult | BaseException


async def fetch_workspace_summary_result(
    *,
    cache: AsyncTtlCache[Any],
    analytics_client: PerformanceWorkspaceAnalyticsClient,
    portfolio_id: str,
    correlation_id: str,
    report_end_date: str,
    report_start_date: str | None,
    effective_period: str,
    chart_frequency: str,
    detail_basis: str,
    benchmark_code: str | None,
    portfolio_currency: str,
    segment: str,
    include_detail_blocks: bool = True,
) -> GatheredResult:
    effective_report_start_date = report_start_date if effective_period == "EXPLICIT" else None
    return cast(
        GatheredResult,
        await cache.get_or_set(
            key=_workspace_summary_cache_key(
                portfolio_id=portfolio_id,
                report_end_date=report_end_date,
                effective_report_start_date=effective_report_start_date,
                effective_period=effective_period,
                chart_frequency=chart_frequency,
                detail_basis=detail_basis,
                benchmark_code=benchmark_code,
                portfolio_currency=portfolio_currency,
                segment=segment,
                include_detail_blocks=include_detail_blocks,
            ),
            factory=lambda: analytics_client.get_workspace_summary(
                portfolio_id=portfolio_id,
                report_end_date=report_end_date,
                report_start_date=effective_report_start_date,
                period=effective_period,
                chart_frequency=chart_frequency,
                detail_basis=detail_basis,
                benchmark_id=benchmark_code,
                reporting_currency=portfolio_currency,
                segment=segment,
                correlation_id=correlation_id,
                include_detail_blocks=include_detail_blocks,
            ),
        ),
    )


def _workspace_summary_cache_key(
    *,
    portfolio_id: str,
    report_end_date: str,
    effective_report_start_date: str | None,
    effective_period: str,
    chart_frequency: str,
    detail_basis: str,
    benchmark_code: str | None,
    portfolio_currency: str,
    segment: str,
    include_detail_blocks: bool,
) -> tuple[object, ...]:
    return (
        "workspace_summary",
        portfolio_id,
        report_end_date,
        effective_report_start_date,
        effective_period,
        chart_frequency,
        detail_basis,
        benchmark_code,
        portfolio_currency,
        segment,
        include_detail_blocks,
    )


async def fetch_workspace_detail_results(
    *,
    cache: AsyncTtlCache[Any],
    analytics_client: PerformanceWorkspaceAnalyticsClient,
    portfolio_id: str,
    correlation_id: str,
    report_start_date: str,
    report_end_date: str,
    requested_period: str,
    detail_basis: str,
    benchmark_code: str | None,
    contribution_dimension: str,
    attribution_dimension: str,
) -> tuple[GatheredResult, GatheredResult]:
    return cast(
        tuple[GatheredResult, GatheredResult],
        await asyncio.gather(
            _fetch_contribution_detail_result(
                cache=cache,
                analytics_client=analytics_client,
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                report_start_date=report_start_date,
                report_end_date=report_end_date,
                requested_period=requested_period,
                detail_basis=detail_basis,
                contribution_dimension=contribution_dimension,
            ),
            _fetch_attribution_detail_result(
                cache=cache,
                analytics_client=analytics_client,
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                report_start_date=report_start_date,
                report_end_date=report_end_date,
                requested_period=requested_period,
                detail_basis=detail_basis,
                benchmark_code=benchmark_code,
                attribution_dimension=attribution_dimension,
            ),
            return_exceptions=True,
        ),
    )


async def _fetch_contribution_detail_result(
    *,
    cache: AsyncTtlCache[Any],
    analytics_client: PerformanceWorkspaceAnalyticsClient,
    portfolio_id: str,
    correlation_id: str,
    report_start_date: str,
    report_end_date: str,
    requested_period: str,
    detail_basis: str,
    contribution_dimension: str,
) -> GatheredResult:
    return cast(
        GatheredResult,
        await cache.get_or_set(
            key=(
                "workspace_contribution_detail",
                portfolio_id,
                report_start_date,
                report_end_date,
                requested_period,
                detail_basis,
                contribution_dimension,
            ),
            factory=lambda: analytics_client.get_contribution_analytics(
                portfolio_id=portfolio_id,
                report_start_date=report_start_date,
                report_end_date=report_end_date,
                period=requested_period,
                metric_basis=detail_basis,
                dimension=contribution_dimension,
                correlation_id=correlation_id,
            ),
        ),
    )


async def _fetch_attribution_detail_result(
    *,
    cache: AsyncTtlCache[Any],
    analytics_client: PerformanceWorkspaceAnalyticsClient,
    portfolio_id: str,
    correlation_id: str,
    report_start_date: str,
    report_end_date: str,
    requested_period: str,
    detail_basis: str,
    benchmark_code: str | None,
    attribution_dimension: str,
) -> GatheredResult:
    return cast(
        GatheredResult,
        await cache.get_or_set(
            key=(
                "workspace_attribution_detail",
                portfolio_id,
                report_start_date,
                report_end_date,
                requested_period,
                detail_basis,
                benchmark_code,
                attribution_dimension,
            ),
            factory=lambda: _fetch_attribution_detail(
                analytics_client=analytics_client,
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                report_start_date=report_start_date,
                report_end_date=report_end_date,
                requested_period=requested_period,
                detail_basis=detail_basis,
                benchmark_code=benchmark_code,
                attribution_dimension=attribution_dimension,
            ),
        ),
    )


async def _fetch_attribution_detail(
    *,
    analytics_client: PerformanceWorkspaceAnalyticsClient,
    portfolio_id: str,
    correlation_id: str,
    report_start_date: str,
    report_end_date: str,
    requested_period: str,
    detail_basis: str,
    benchmark_code: str | None,
    attribution_dimension: str,
) -> GatheredResult:
    if not benchmark_code:
        return 204, {}
    return await analytics_client.get_attribution_analytics(
        portfolio_id=portfolio_id,
        report_start_date=report_start_date,
        report_end_date=report_end_date,
        period=requested_period,
        metric_basis=detail_basis,
        benchmark_id=benchmark_code,
        dimension=attribution_dimension,
        correlation_id=correlation_id,
    )
