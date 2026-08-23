from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, TypeAlias, cast

from app.services.async_ttl_cache import AsyncTtlCache
from app.services.workspace_client_protocols import PerformanceWorkspaceAnalyticsClient

UpstreamPayload: TypeAlias = dict[str, Any]
UpstreamResult: TypeAlias = tuple[int, UpstreamPayload]
GatheredResult: TypeAlias = UpstreamResult | BaseException


@dataclass(frozen=True)
class WorkspaceSummaryRequest:
    portfolio_id: str
    report_end_date: str
    report_start_date: str | None
    effective_period: str
    chart_frequency: str
    detail_basis: str
    benchmark_code: str | None
    reporting_currency: str
    segment: str
    include_detail_blocks: bool

    @property
    def effective_report_start_date(self) -> str | None:
        if self.effective_period != "EXPLICIT":
            return None
        return self.report_start_date


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
    reporting_currency: str,
    segment: str,
    include_detail_blocks: bool = True,
) -> GatheredResult:
    request = WorkspaceSummaryRequest(
        portfolio_id=portfolio_id,
        report_end_date=report_end_date,
        report_start_date=report_start_date,
        effective_period=effective_period,
        chart_frequency=chart_frequency,
        detail_basis=detail_basis,
        benchmark_code=benchmark_code,
        reporting_currency=reporting_currency,
        segment=segment,
        include_detail_blocks=include_detail_blocks,
    )
    return await _fetch_workspace_summary_result(
        cache=cache,
        analytics_client=analytics_client,
        correlation_id=correlation_id,
        request=request,
    )


async def _fetch_workspace_summary_result(
    *,
    cache: AsyncTtlCache[Any],
    analytics_client: PerformanceWorkspaceAnalyticsClient,
    correlation_id: str,
    request: WorkspaceSummaryRequest,
) -> GatheredResult:
    return cast(
        GatheredResult,
        await cache.get_or_set(
            key=_workspace_summary_cache_key(request),
            factory=lambda: analytics_client.get_workspace_summary(
                portfolio_id=request.portfolio_id,
                report_end_date=request.report_end_date,
                report_start_date=request.effective_report_start_date,
                period=request.effective_period,
                chart_frequency=request.chart_frequency,
                detail_basis=request.detail_basis,
                benchmark_id=request.benchmark_code,
                reporting_currency=request.reporting_currency,
                segment=request.segment,
                correlation_id=correlation_id,
                include_detail_blocks=request.include_detail_blocks,
            ),
        ),
    )


def _workspace_summary_cache_key(request: WorkspaceSummaryRequest) -> tuple[object, ...]:
    return (
        "workspace_summary",
        request.portfolio_id,
        request.report_end_date,
        request.effective_report_start_date,
        request.effective_period,
        request.chart_frequency,
        request.detail_basis,
        request.benchmark_code,
        request.reporting_currency,
        request.segment,
        request.include_detail_blocks,
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
