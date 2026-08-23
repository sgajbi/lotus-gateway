from dataclasses import dataclass
from typing import Any, cast

from fastapi import HTTPException, status

from app.config import settings
from app.contracts.workbench import (
    WorkbenchAnalyticsBucket,
    WorkbenchAnalyticsResponse,
    WorkbenchOverviewResponse,
    WorkbenchPartialFailure,
    WorkbenchPerformanceSnapshot,
    WorkbenchPortfolio360Response,
    WorkbenchRebalanceSnapshot,
    WorkbenchTopChange,
)
from app.services.workbench_analytics_projection import (
    build_workbench_allocation_buckets,
    build_workbench_return_metrics,
    build_workbench_top_changes,
    with_controlled_risk_bff_gap,
)
from app.services.workbench_overview_enrichment import (
    load_workbench_overview_enrichment,
    resolve_workbench_performance_snapshot_end_date,
)
from app.services.workbench_sandbox_service import WorkbenchSandboxServiceMixin
from app.services.workbench_snapshot_context import (
    WorkbenchSnapshotContext,
    load_workbench_snapshot_context,
    raise_for_lotus_core_snapshot_error,
)
from app.services.workspace_client_protocols import (
    WorkbenchAdviseClient,
    WorkbenchCoreClient,
    WorkbenchManageClient,
    WorkbenchPerformanceClient,
)


@dataclass(frozen=True)
class WorkbenchAnalyticsParts:
    portfolio_360: WorkbenchPortfolio360Response
    allocation_buckets: list[WorkbenchAnalyticsBucket]
    top_changes: list[WorkbenchTopChange]
    portfolio_return_pct: Any
    benchmark_return_pct: Any
    active_return_pct: Any


def _snapshot_temporal_response_fields(context: WorkbenchSnapshotContext) -> dict[str, Any]:
    return {
        "as_of_date": context.effective_as_of_date,
        "requested_as_of_date": context.requested_as_of_date,
        "effective_as_of_date": context.effective_as_of_date,
        "as_of_state": context.as_of_state,
    }


def _build_workbench_analytics_parts(
    *,
    portfolio_360: WorkbenchPortfolio360Response,
    group_by: str,
) -> WorkbenchAnalyticsParts:
    try:
        allocation_buckets = build_workbench_allocation_buckets(
            group_by=group_by,
            current_positions=portfolio_360.current_positions,
            projected_positions=portfolio_360.projected_positions,
        )
        top_changes = build_workbench_top_changes(portfolio_360.projected_positions)
        controlled_portfolio_360 = with_controlled_risk_bff_gap(portfolio_360)
        (
            portfolio_return_pct,
            benchmark_return_pct,
            active_return_pct,
        ) = build_workbench_return_metrics(
            controlled_portfolio_360.performance_snapshot,
        )
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Invalid workbench analytics source payload: {exc}",
        ) from exc
    return WorkbenchAnalyticsParts(
        portfolio_360=controlled_portfolio_360,
        allocation_buckets=allocation_buckets,
        top_changes=top_changes,
        portfolio_return_pct=portfolio_return_pct,
        benchmark_return_pct=benchmark_return_pct,
        active_return_pct=active_return_pct,
    )


class WorkbenchService(WorkbenchSandboxServiceMixin):
    def __init__(
        self,
        lotus_core_query_client: WorkbenchCoreClient,
        analytics_client: WorkbenchPerformanceClient,
        dpm_client: WorkbenchManageClient,
        advise_client: WorkbenchAdviseClient | None = None,
    ):
        self._lotus_core_query_client = lotus_core_query_client
        self._analytics_client = analytics_client
        self._dpm_client = dpm_client
        self._advise_client = advise_client or cast(WorkbenchAdviseClient, dpm_client)

    async def get_workbench_overview(
        self,
        portfolio_id: str,
        correlation_id: str,
        include_performance_snapshot: bool = True,
        include_rebalance_snapshot: bool = True,
        requested_as_of_date: str | None = None,
    ) -> WorkbenchOverviewResponse:
        context = await self._load_workbench_snapshot_context(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            requested_as_of_date=requested_as_of_date,
        )
        (
            performance_snapshot,
            rebalance_snapshot,
            warnings,
            partial_failures,
        ) = await self._load_overview_enrichment(
            portfolio_id=portfolio_id,
            as_of_date=context.enrichment_as_of_date,
            correlation_id=correlation_id,
            include_performance_snapshot=include_performance_snapshot,
            include_rebalance_snapshot=include_rebalance_snapshot,
        )

        return WorkbenchOverviewResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            **_snapshot_temporal_response_fields(context),
            portfolio=context.portfolio,
            overview=context.overview,
            performance_snapshot=performance_snapshot,
            rebalance_snapshot=rebalance_snapshot,
            warnings=warnings,
            partial_failures=partial_failures,
        )

    async def _resolve_performance_snapshot_end_date(
        self,
        *,
        portfolio_id: str,
        as_of_date: str,
        correlation_id: str,
    ) -> str:
        return await resolve_workbench_performance_snapshot_end_date(
            core_client=self._lotus_core_query_client,
            portfolio_id=portfolio_id,
            as_of_date=as_of_date,
            correlation_id=correlation_id,
        )

    async def get_portfolio_360(
        self,
        portfolio_id: str,
        correlation_id: str,
        session_id: str | None = None,
        benchmark_code: str | None = None,
        requested_as_of_date: str | None = None,
    ) -> WorkbenchPortfolio360Response:
        context = await self._load_workbench_snapshot_context(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            requested_as_of_date=requested_as_of_date,
        )
        (
            performance_snapshot,
            rebalance_snapshot,
            warnings,
            partial_failures,
        ) = await self._load_overview_enrichment(
            portfolio_id=portfolio_id,
            as_of_date=context.enrichment_as_of_date,
            correlation_id=correlation_id,
            include_performance_snapshot=True,
            include_rebalance_snapshot=True,
            benchmark_code=benchmark_code,
        )
        projected_positions, projected_summary = (
            await self._load_projected_state(session_id=session_id, correlation_id=correlation_id)
            if session_id
            else ([], None)
        )

        return WorkbenchPortfolio360Response(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            **_snapshot_temporal_response_fields(context),
            portfolio=context.portfolio,
            overview=context.overview,
            performance_snapshot=performance_snapshot,
            rebalance_snapshot=rebalance_snapshot,
            current_positions=context.current_positions,
            projected_positions=projected_positions,
            projected_summary=projected_summary,
            active_session_id=session_id,
            warnings=warnings,
            partial_failures=partial_failures,
        )

    async def get_workbench_analytics(
        self,
        portfolio_id: str,
        correlation_id: str,
        period: str,
        group_by: str,
        benchmark_code: str,
        session_id: str | None,
    ) -> WorkbenchAnalyticsResponse:
        portfolio_360 = await self.get_portfolio_360(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            session_id=session_id,
            benchmark_code=benchmark_code,
        )
        analytics_parts = _build_workbench_analytics_parts(
            portfolio_360=portfolio_360,
            group_by=group_by,
        )

        return WorkbenchAnalyticsResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            portfolio_id=portfolio_id,
            session_id=session_id,
            period=period,
            group_by=group_by,
            benchmark_code=benchmark_code,
            portfolio_return_pct=analytics_parts.portfolio_return_pct,
            benchmark_return_pct=analytics_parts.benchmark_return_pct,
            active_return_pct=analytics_parts.active_return_pct,
            allocation_buckets=analytics_parts.allocation_buckets,
            top_changes=analytics_parts.top_changes,
            warnings=analytics_parts.portfolio_360.warnings,
            partial_failures=analytics_parts.portfolio_360.partial_failures,
        )

    async def _load_workbench_snapshot_context(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        requested_as_of_date: str | None = None,
    ) -> WorkbenchSnapshotContext:
        return await load_workbench_snapshot_context(
            core_client=self._lotus_core_query_client,
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            requested_as_of_date=requested_as_of_date,
        )

    async def _load_overview_enrichment(
        self,
        *,
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
        return await load_workbench_overview_enrichment(
            core_client=self._lotus_core_query_client,
            analytics_client=self._analytics_client,
            dpm_client=self._dpm_client,
            portfolio_id=portfolio_id,
            as_of_date=as_of_date,
            correlation_id=correlation_id,
            include_performance_snapshot=include_performance_snapshot,
            include_rebalance_snapshot=include_rebalance_snapshot,
            benchmark_code=benchmark_code,
        )

    def _raise_for_lotus_core_error(self, upstream_status: int, payload: dict[str, Any]) -> None:
        raise_for_lotus_core_snapshot_error(upstream_status, payload)
