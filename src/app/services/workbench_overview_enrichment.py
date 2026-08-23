from __future__ import annotations

import asyncio
from collections.abc import Awaitable
from dataclasses import dataclass
from typing import Any, cast

from fastapi import status

from app.config import settings
from app.contracts.workbench import (
    WorkbenchPartialFailure,
    WorkbenchPerformanceSnapshot,
    WorkbenchRebalanceSnapshot,
)
from app.services.workbench_performance_snapshot import parse_performance_snapshot
from app.services.workbench_rebalance_snapshot import parse_rebalance_snapshot
from app.services.workspace_client_protocols import (
    WorkbenchCoreClient,
    WorkbenchManageClient,
    WorkbenchPerformanceClient,
)


@dataclass(frozen=True)
class WorkbenchOverviewEnrichmentResults:
    performance_result: object
    rebalance_result: object
    rebalance_supportability_result: object


def _unavailable_date_enrichment() -> tuple[
    None,
    None,
    list[str],
    list[WorkbenchPartialFailure],
]:
    return (
        None,
        None,
        ["WORKBENCH_AS_OF_DATE_UNAVAILABLE"],
        [
            WorkbenchPartialFailure(
                source_service="lotus-core",
                error_code="WORKBENCH_AS_OF_DATE_UNAVAILABLE",
                detail=(
                    "Core did not confirm a usable business date for the Workbench snapshot; "
                    "date-dependent enrichment was withheld."
                ),
            )
        ],
    )


async def load_workbench_overview_enrichment(
    *,
    core_client: WorkbenchCoreClient,
    analytics_client: WorkbenchPerformanceClient,
    dpm_client: WorkbenchManageClient,
    portfolio_id: str,
    as_of_date: str | None,
    correlation_id: str,
    include_performance_snapshot: bool,
    include_rebalance_snapshot: bool,
    benchmark_code: str | None = None,
) -> tuple[
    WorkbenchPerformanceSnapshot | None,
    WorkbenchRebalanceSnapshot | None,
    list[str],
    list[WorkbenchPartialFailure],
]:
    if as_of_date is None:
        return (
            _unavailable_date_enrichment()
            if include_performance_snapshot or include_rebalance_snapshot
            else (None, None, [], [])
        )

    if not (include_performance_snapshot or include_rebalance_snapshot):
        return None, None, [], []
    gathered = await _gather_overview_enrichment_results(
        core_client=core_client,
        analytics_client=analytics_client,
        dpm_client=dpm_client,
        portfolio_id=portfolio_id,
        as_of_date=as_of_date,
        correlation_id=correlation_id,
        include_performance_snapshot=include_performance_snapshot,
        include_rebalance_snapshot=include_rebalance_snapshot,
        benchmark_code=benchmark_code,
    )
    return _parse_overview_enrichment_results(
        gathered=gathered,
        include_performance_snapshot=include_performance_snapshot,
        include_rebalance_snapshot=include_rebalance_snapshot,
    )


def _parse_overview_enrichment_results(
    *,
    gathered: WorkbenchOverviewEnrichmentResults,
    include_performance_snapshot: bool,
    include_rebalance_snapshot: bool,
) -> tuple[
    WorkbenchPerformanceSnapshot | None,
    WorkbenchRebalanceSnapshot | None,
    list[str],
    list[WorkbenchPartialFailure],
]:
    partial_failures: list[WorkbenchPartialFailure] = []
    warnings: list[str] = []
    performance_snapshot = (
        parse_performance_snapshot(
            result=gathered.performance_result,
            partial_failures=partial_failures,
            warnings=warnings,
        )
        if include_performance_snapshot
        else None
    )
    rebalance_snapshot = (
        parse_rebalance_snapshot(
            result=gathered.rebalance_result,
            supportability_result=gathered.rebalance_supportability_result,
            partial_failures=partial_failures,
            warnings=warnings,
        )
        if include_rebalance_snapshot
        else None
    )
    return performance_snapshot, rebalance_snapshot, warnings, partial_failures


async def resolve_workbench_performance_snapshot_end_date(
    *,
    core_client: WorkbenchCoreClient,
    portfolio_id: str,
    as_of_date: str,
    correlation_id: str,
) -> str:
    (
        status_code,
        payload,
    ) = await core_client.get_portfolio_analytics_reference(
        portfolio_id=portfolio_id,
        as_of_date=as_of_date,
        consumer_system="lotus-gateway",
        correlation_id=correlation_id,
    )
    if status_code >= status.HTTP_400_BAD_REQUEST or not isinstance(payload, dict):
        return as_of_date

    performance_end_date = payload.get("performance_end_date")
    if not isinstance(performance_end_date, str) or not performance_end_date.strip():
        return as_of_date
    if portfolio_id == settings.workbench_canonical_portfolio_id:
        return min(performance_end_date, settings.workbench_canonical_performance_end_date)
    return performance_end_date


async def _empty_async_result() -> tuple[int, dict[str, Any]]:
    return 204, {}


async def _gather_overview_enrichment_results(
    *,
    core_client: WorkbenchCoreClient,
    analytics_client: WorkbenchPerformanceClient,
    dpm_client: WorkbenchManageClient,
    portfolio_id: str,
    as_of_date: str,
    correlation_id: str,
    include_performance_snapshot: bool,
    include_rebalance_snapshot: bool,
    benchmark_code: str | None,
) -> WorkbenchOverviewEnrichmentResults:
    performance_task = await _build_performance_snapshot_task(
        core_client=core_client,
        analytics_client=analytics_client,
        portfolio_id=portfolio_id,
        as_of_date=as_of_date,
        correlation_id=correlation_id,
        include_performance_snapshot=include_performance_snapshot,
        benchmark_code=benchmark_code,
    )
    dpm_runs_task, dpm_supportability_task = _build_rebalance_snapshot_tasks(
        dpm_client=dpm_client,
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        include_rebalance_snapshot=include_rebalance_snapshot,
    )
    performance_result, rebalance_result, supportability_result = cast(
        tuple[object, object, object],
        await asyncio.gather(
            performance_task,
            dpm_runs_task,
            dpm_supportability_task,
            return_exceptions=True,
        ),
    )
    return WorkbenchOverviewEnrichmentResults(
        performance_result=performance_result,
        rebalance_result=rebalance_result,
        rebalance_supportability_result=supportability_result,
    )


async def _build_performance_snapshot_task(
    *,
    core_client: WorkbenchCoreClient,
    analytics_client: WorkbenchPerformanceClient,
    portfolio_id: str,
    as_of_date: str,
    correlation_id: str,
    include_performance_snapshot: bool,
    benchmark_code: str | None,
) -> Awaitable[tuple[int, dict[str, Any]]]:
    if not include_performance_snapshot:
        return _empty_async_result()
    performance_end_date = await resolve_workbench_performance_snapshot_end_date(
        core_client=core_client,
        portfolio_id=portfolio_id,
        as_of_date=as_of_date,
        correlation_id=correlation_id,
    )
    return analytics_client.get_workspace_summary(
        portfolio_id=portfolio_id,
        report_end_date=performance_end_date,
        report_start_date=None,
        period="YTD",
        chart_frequency="monthly",
        detail_basis="NET",
        benchmark_id=benchmark_code or settings.workbench_default_benchmark_code,
        reporting_currency=None,
        segment="asset_class",
        correlation_id=correlation_id,
        include_detail_blocks=False,
    )


def _build_rebalance_snapshot_tasks(
    *,
    dpm_client: WorkbenchManageClient,
    portfolio_id: str,
    correlation_id: str,
    include_rebalance_snapshot: bool,
) -> tuple[Awaitable[tuple[int, dict[str, Any]]], Awaitable[tuple[int, dict[str, Any]]]]:
    if not include_rebalance_snapshot:
        return _empty_async_result(), _empty_async_result()
    return (
        dpm_client.list_runs(
            params={"portfolio_id": portfolio_id, "limit": 5},
            correlation_id=correlation_id,
        ),
        dpm_client.get_supportability_summary(correlation_id=correlation_id),
    )
