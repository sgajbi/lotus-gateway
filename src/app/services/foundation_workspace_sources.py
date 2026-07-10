import asyncio
from dataclasses import dataclass
from typing import Any, cast

from fastapi import status

from app.services.foundation_client_protocols import (
    FoundationCoreClient,
    FoundationManageClient,
    FoundationPerformanceClient,
    FoundationReportingClient,
)
from app.services.foundation_workspace_optional import (
    FoundationWorkspaceOptionalResults,
    GatheredResult,
    optional_str,
)

UpstreamResult = tuple[int, dict[str, Any]]


@dataclass(frozen=True)
class FoundationWorkspaceSourceResults:
    identity_result: UpstreamResult
    snapshot_result: UpstreamResult


class FoundationWorkspaceSourceLoadingMixin:
    _lotus_core_query_client: FoundationCoreClient
    _analytics_client: FoundationPerformanceClient
    _dpm_client: FoundationManageClient
    _reporting_client: FoundationReportingClient

    async def _load_foundation_workspace_sources(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str,
    ) -> FoundationWorkspaceSourceResults:
        identity_result, snapshot_result = await asyncio.gather(
            self._lotus_core_query_client.get_portfolio(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
            ),
            self._lotus_core_query_client.get_core_snapshot(
                portfolio_id=portfolio_id,
                as_of_date=as_of_date,
                sections=["positions_baseline", "portfolio_totals", "instrument_enrichment"],
                consumer_system="lotus-gateway",
                correlation_id=correlation_id,
            ),
        )
        return FoundationWorkspaceSourceResults(
            identity_result=identity_result,
            snapshot_result=snapshot_result,
        )

    async def _load_foundation_workspace_optional_results(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str,
        performance_report_end_date: str,
    ) -> FoundationWorkspaceOptionalResults:
        performance_task = self._analytics_client.get_stateful_twr(
            portfolio_id=portfolio_id,
            report_end_date=performance_report_end_date,
            period="YTD",
            correlation_id=correlation_id,
        )
        rebalance_task = self._dpm_client.list_runs(
            params={"portfolio_id": portfolio_id, "limit": 1},
            correlation_id=correlation_id,
        )
        reporting_task = self._reporting_client.get_portfolio_snapshot(
            portfolio_id=portfolio_id,
            as_of_date=as_of_date,
            correlation_id=correlation_id,
        )
        gathered = await asyncio.gather(
            performance_task,
            rebalance_task,
            reporting_task,
            return_exceptions=True,
        )
        return FoundationWorkspaceOptionalResults(
            performance_result=cast(GatheredResult, gathered[0]),
            rebalance_result=cast(GatheredResult, gathered[1]),
            reporting_result=cast(GatheredResult, gathered[2]),
        )

    async def _resolve_performance_report_end_date(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str,
    ) -> str:
        try:
            (
                reference_status,
                reference_payload,
            ) = await self._lotus_core_query_client.get_portfolio_analytics_reference(
                portfolio_id=portfolio_id,
                as_of_date=as_of_date,
                consumer_system="lotus-gateway",
                correlation_id=correlation_id,
            )
        except Exception:
            return as_of_date

        if reference_status >= status.HTTP_400_BAD_REQUEST:
            return as_of_date
        if not isinstance(reference_payload, dict):
            return as_of_date
        return optional_str(reference_payload.get("performance_end_date")) or as_of_date
