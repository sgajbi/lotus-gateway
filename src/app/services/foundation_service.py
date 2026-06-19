import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast

from fastapi import HTTPException, status

from app.config import settings
from app.contracts.foundation import (
    FoundationAllocationBucket,
    FoundationPortfolioCatalogResponse,
    FoundationPortfolioIdentity,
    FoundationPortfolioSummary,
    FoundationTopPosition,
    FoundationWorkspaceReadiness,
    FoundationWorkspaceResponse,
)
from app.services.foundation_catalog_payloads import parse_foundation_catalog_items
from app.services.foundation_core_snapshot import FoundationCoreSnapshotMapper
from app.services.foundation_workspace_optional import (
    FoundationWorkspaceOptionalResults,
    FoundationWorkspaceOptionalViews,
    GatheredResult,
    build_foundation_evidence_summary,
    build_foundation_workflow_cues,
    build_foundation_workspace_optional_views,
    optional_str,
)
from app.services.upstream_envelope import safe_upstream_detail
from app.services.workspace_client_protocols import (
    FoundationCoreClient,
    FoundationManageClient,
    FoundationPerformanceClient,
    FoundationReportingClient,
)

UpstreamResult = tuple[int, dict[str, Any]]


@dataclass(frozen=True)
class FoundationWorkspaceCoreView:
    portfolio: FoundationPortfolioIdentity
    summary: FoundationPortfolioSummary
    allocations: list[FoundationAllocationBucket]
    top_positions: list[FoundationTopPosition]
    as_of_date: str


@dataclass(frozen=True)
class FoundationWorkspaceSourceResults:
    identity_result: UpstreamResult
    snapshot_result: UpstreamResult


class FoundationService:
    def __init__(
        self,
        lotus_core_query_client: FoundationCoreClient,
        analytics_client: FoundationPerformanceClient,
        dpm_client: FoundationManageClient,
        reporting_client: FoundationReportingClient,
    ):
        self._lotus_core_query_client = lotus_core_query_client
        self._analytics_client = analytics_client
        self._dpm_client = dpm_client
        self._reporting_client = reporting_client
        self._core_snapshot_mapper = FoundationCoreSnapshotMapper()

    async def get_portfolio_catalog(
        self,
        correlation_id: str,
    ) -> FoundationPortfolioCatalogResponse:
        status_code, payload = await self._lotus_core_query_client.get_portfolio_lookups(
            correlation_id=correlation_id
        )
        if status_code >= status.HTTP_400_BAD_REQUEST:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=self._build_safe_upstream_error_detail(
                    "lotus-core portfolio catalog unavailable",
                    payload,
                ),
            )

        items_payload = payload.get("items", [])
        if not isinstance(items_payload, list):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invalid lotus-core portfolio catalog payload structure.",
            )

        return FoundationPortfolioCatalogResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            items=parse_foundation_catalog_items(items_payload),
        )

    async def get_portfolio_workspace(
        self,
        portfolio_id: str,
        correlation_id: str,
    ) -> FoundationWorkspaceResponse:
        as_of_date = datetime.now(UTC).date().isoformat()
        source_results = await self._load_foundation_workspace_sources(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            as_of_date=as_of_date,
        )
        return await self._build_foundation_workspace_response(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            fallback_as_of_date=as_of_date,
            source_results=source_results,
        )

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

    async def _build_foundation_workspace_response(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        fallback_as_of_date: str,
        source_results: FoundationWorkspaceSourceResults,
    ) -> FoundationWorkspaceResponse:
        core_view = self._build_foundation_workspace_core_view(
            portfolio_id=portfolio_id,
            fallback_as_of_date=fallback_as_of_date,
            source_results=source_results,
        )
        performance_report_end_date = await self._resolve_performance_report_end_date(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            as_of_date=core_view.as_of_date,
        )
        optional_results = await self._load_foundation_workspace_optional_results(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            as_of_date=core_view.as_of_date,
            performance_report_end_date=performance_report_end_date,
        )
        optional_views = build_foundation_workspace_optional_views(optional_results)
        return self._compose_foundation_workspace_response(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            core_view=core_view,
            optional_views=optional_views,
        )

    def _build_foundation_workspace_core_view(
        self,
        *,
        portfolio_id: str,
        fallback_as_of_date: str,
        source_results: FoundationWorkspaceSourceResults,
    ) -> FoundationWorkspaceCoreView:
        identity_status, identity_payload = source_results.identity_result
        if identity_status >= status.HTTP_400_BAD_REQUEST:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=self._build_safe_upstream_error_detail(
                    "lotus-core portfolio identity unavailable",
                    identity_payload,
                ),
            )

        pas_status, pas_payload = source_results.snapshot_result
        if pas_status >= status.HTTP_400_BAD_REQUEST:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=self._build_safe_upstream_error_detail(
                    "lotus-core foundation snapshot unavailable",
                    pas_payload,
                ),
            )

        portfolio, summary, allocations, top_positions, as_of_date = (
            self._core_snapshot_mapper.parse_core_snapshot(
                fallback_portfolio_id=portfolio_id,
                portfolio_payload=identity_payload,
                payload=pas_payload,
                fallback_as_of_date=fallback_as_of_date,
            )
        )
        return FoundationWorkspaceCoreView(
            portfolio=portfolio,
            summary=summary,
            allocations=allocations,
            top_positions=top_positions,
            as_of_date=as_of_date,
        )

    def _build_safe_upstream_error_detail(
        self,
        detail_prefix: str,
        payload: dict[str, Any],
    ) -> str:
        detail = safe_upstream_detail(payload, default_detail="upstream request failed")
        return f"{detail_prefix}: {detail}"

    def _compose_foundation_workspace_response(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        core_view: FoundationWorkspaceCoreView,
        optional_views: FoundationWorkspaceOptionalViews,
    ) -> FoundationWorkspaceResponse:
        readiness = FoundationWorkspaceReadiness(
            has_positions=core_view.summary.position_count > 0,
            reporting=optional_views.reporting,
        )
        evidence = build_foundation_evidence_summary(
            warnings=optional_views.warnings,
            partial_failures=optional_views.partial_failures,
        )

        return FoundationWorkspaceResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            as_of_date=core_view.as_of_date,
            portfolio=core_view.portfolio,
            summary=core_view.summary,
            allocations=core_view.allocations,
            top_positions=core_view.top_positions,
            performance=optional_views.performance,
            rebalance=optional_views.rebalance,
            readiness=readiness,
            workflow_cues=build_foundation_workflow_cues(portfolio_id=portfolio_id),
            evidence=evidence,
            warnings=optional_views.warnings,
            partial_failures=optional_views.partial_failures,
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
