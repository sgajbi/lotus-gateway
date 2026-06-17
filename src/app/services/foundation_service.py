import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast

from fastapi import HTTPException, status

from app.config import settings
from app.contracts.foundation import (
    FoundationAllocationBucket,
    FoundationEvidenceSummary,
    FoundationPartialFailure,
    FoundationPerformanceSummary,
    FoundationPortfolioCatalogItem,
    FoundationPortfolioCatalogResponse,
    FoundationPortfolioIdentity,
    FoundationPortfolioSummary,
    FoundationRebalanceSummary,
    FoundationReportingReadiness,
    FoundationTopPosition,
    FoundationWorkflowLaunchCue,
    FoundationWorkspaceReadiness,
    FoundationWorkspaceResponse,
)
from app.services.foundation_core_snapshot import FoundationCoreSnapshotMapper
from app.services.upstream_envelope import safe_upstream_detail
from app.services.workspace_client_protocols import (
    FoundationCoreClient,
    FoundationManageClient,
    FoundationPerformanceClient,
    FoundationReportingClient,
)

UpstreamResult = tuple[int, dict[str, Any]]
GatheredResult = UpstreamResult | BaseException
OptionalUpstreamFailureContext = tuple[
    str,
    str,
    list[str],
    list[FoundationPartialFailure],
]


@dataclass(frozen=True)
class FoundationWorkspaceCoreView:
    portfolio: FoundationPortfolioIdentity
    summary: FoundationPortfolioSummary
    allocations: list[FoundationAllocationBucket]
    top_positions: list[FoundationTopPosition]
    as_of_date: str


@dataclass(frozen=True)
class FoundationWorkspaceOptionalViews:
    performance: FoundationPerformanceSummary | None
    rebalance: FoundationRebalanceSummary | None
    reporting: FoundationReportingReadiness
    warnings: list[str]
    partial_failures: list[FoundationPartialFailure]


@dataclass(frozen=True)
class FoundationWorkspaceSourceResults:
    identity_result: UpstreamResult
    snapshot_result: UpstreamResult


@dataclass(frozen=True)
class FoundationWorkspaceOptionalResults:
    performance_result: GatheredResult
    rebalance_result: GatheredResult
    reporting_result: GatheredResult


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

        items = [self._parse_catalog_item(item) for item in items_payload if isinstance(item, dict)]
        items.sort(key=lambda item: item.portfolio_id)

        return FoundationPortfolioCatalogResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            items=items,
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
        optional_views = self._build_foundation_workspace_optional_views(optional_results)
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

    def _build_foundation_workspace_optional_views(
        self,
        optional_results: FoundationWorkspaceOptionalResults,
    ) -> FoundationWorkspaceOptionalViews:
        warnings: list[str] = []
        partial_failures: list[FoundationPartialFailure] = []
        performance = self._parse_performance_result(
            result=optional_results.performance_result,
            warnings=warnings,
            partial_failures=partial_failures,
        )
        rebalance = self._parse_rebalance_result(
            result=optional_results.rebalance_result,
            warnings=warnings,
            partial_failures=partial_failures,
        )
        reporting = self._parse_reporting_result(
            result=optional_results.reporting_result,
            warnings=warnings,
            partial_failures=partial_failures,
        )
        return FoundationWorkspaceOptionalViews(
            performance=performance,
            rebalance=rebalance,
            reporting=reporting,
            warnings=warnings,
            partial_failures=partial_failures,
        )

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
        evidence = self._build_evidence_summary(
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
            workflow_cues=self._build_workflow_cues(portfolio_id=portfolio_id),
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
        return self._optional_str(reference_payload.get("performance_end_date")) or as_of_date

    def _parse_catalog_item(self, item: dict[str, Any]) -> FoundationPortfolioCatalogItem:
        portfolio_id = str(item.get("portfolio_id", item.get("id", ""))).strip()
        if not portfolio_id:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invalid lotus-core portfolio catalog item without portfolio_id.",
            )
        display_name = str(
            item.get("portfolio_name")
            or item.get("name")
            or item.get("label")
            or item.get("display_name")
            or portfolio_id
        )
        return FoundationPortfolioCatalogItem(
            portfolio_id=portfolio_id,
            display_name=display_name,
            base_currency=str(item.get("base_currency", "USD")),
            client_id=self._optional_str(item.get("cif_id", item.get("client_id"))),
            booking_center_code=self._optional_str(
                item.get("booking_center", item.get("booking_center_code"))
            ),
        )

    def _parse_performance_result(
        self,
        result: object,
        warnings: list[str],
        partial_failures: list[FoundationPartialFailure],
    ) -> FoundationPerformanceSummary | None:
        _, payload = self._unpack_optional_upstream(
            result=result,
            source_service="lotus-performance",
            unavailable_warning="FOUNDATION_PERFORMANCE_UNAVAILABLE",
            warnings=warnings,
            partial_failures=partial_failures,
        )
        if payload is None:
            return None

        results_by_period = payload.get("results_by_period", payload.get("resultsByPeriod", {}))
        if not isinstance(results_by_period, dict):
            warnings.append("FOUNDATION_PERFORMANCE_INVALID")
            return None

        period_key = "YTD" if "YTD" in results_by_period else next(iter(results_by_period), None)
        if period_key is None:
            return None

        period_payload = results_by_period.get(period_key, {})
        if not isinstance(period_payload, dict):
            return None
        return FoundationPerformanceSummary(
            period=period_key,
            return_pct=self._extract_performance_return_pct(period_payload),
        )

    def _extract_performance_return_pct(self, period_payload: dict[str, Any]) -> float | None:
        legacy_return = period_payload.get("net_cumulative_return")
        if isinstance(legacy_return, int | float):
            return float(legacy_return)

        portfolio_payload = period_payload.get("portfolio")
        if not isinstance(portfolio_payload, dict):
            return None
        summary = portfolio_payload.get("summary")
        if not isinstance(summary, dict):
            return None
        period_return = summary.get("period_return")
        if isinstance(period_return, dict):
            base_return = period_return.get("base")
            if isinstance(base_return, int | float):
                return float(base_return)
        cumulative_return = summary.get("cumulative_return")
        if isinstance(cumulative_return, dict):
            base_return = cumulative_return.get("base")
            if isinstance(base_return, int | float):
                return float(base_return)
        return None

    def _parse_rebalance_result(
        self,
        result: object,
        warnings: list[str],
        partial_failures: list[FoundationPartialFailure],
    ) -> FoundationRebalanceSummary | None:
        _, payload = self._unpack_optional_upstream(
            result=result,
            source_service="lotus-manage",
            unavailable_warning="FOUNDATION_REBALANCE_UNAVAILABLE",
            warnings=warnings,
            partial_failures=partial_failures,
        )
        if payload is None:
            return None

        items = payload.get("items", [])
        if not isinstance(items, list) or not items:
            return FoundationRebalanceSummary(status="NOT_AVAILABLE")

        latest = items[0]
        if not isinstance(latest, dict):
            return FoundationRebalanceSummary(status="NOT_AVAILABLE")

        return FoundationRebalanceSummary(
            status=str(latest.get("status", "UNKNOWN")),
            last_run_at_utc=self._optional_str(latest.get("created_at")),
            last_rebalance_run_id=self._optional_str(latest.get("rebalance_run_id")),
        )

    def _parse_reporting_result(
        self,
        result: object,
        warnings: list[str],
        partial_failures: list[FoundationPartialFailure],
    ) -> FoundationReportingReadiness:
        _, payload = self._unpack_optional_upstream(
            result=result,
            source_service="lotus-report",
            unavailable_warning="FOUNDATION_REPORTING_UNAVAILABLE",
            warnings=warnings,
            partial_failures=partial_failures,
        )
        if payload is None:
            return FoundationReportingReadiness(status="UNAVAILABLE")

        rows = payload.get("rows", [])
        if not isinstance(rows, list):
            rows = []
        generated_at = self._optional_str(payload.get("generatedAt"))
        status_value = "READY" if rows else "EMPTY"
        return FoundationReportingReadiness(
            status=status_value,
            generated_at_utc=generated_at,
            row_count=len(rows),
        )

    def _unpack_optional_upstream(
        self,
        result: object,
        source_service: str,
        unavailable_warning: str,
        warnings: list[str],
        partial_failures: list[FoundationPartialFailure],
    ) -> tuple[int | None, dict[str, Any] | None]:
        failure_context = (source_service, unavailable_warning, warnings, partial_failures)
        if isinstance(result, Exception):
            return self._unavailable_optional_upstream(
                None,
                "UPSTREAM_EXCEPTION",
                str(result),
                failure_context,
            )

        if not isinstance(result, tuple) or len(result) != 2:
            return self._unavailable_optional_upstream(
                None,
                "INVALID_UPSTREAM_RESPONSE",
                f"unexpected result type: {type(result)}",
                failure_context,
            )

        status_code, payload = result
        if not isinstance(payload, dict):
            return self._unavailable_optional_upstream(
                status_code,
                "INVALID_UPSTREAM_PAYLOAD",
                f"unexpected payload type: {type(payload)}",
                failure_context,
            )

        if status_code >= status.HTTP_400_BAD_REQUEST:
            return self._unavailable_optional_upstream(
                status_code,
                f"HTTP_{status_code}",
                safe_upstream_detail(payload, default_detail="optional upstream unavailable"),
                failure_context,
            )

        return status_code, payload

    def _unavailable_optional_upstream(
        self,
        status_code: int | None,
        error_code: str,
        detail: str,
        failure_context: OptionalUpstreamFailureContext,
    ) -> tuple[int | None, None]:
        source_service, unavailable_warning, warnings, partial_failures = failure_context
        partial_failures.append(
            FoundationPartialFailure(
                source_service=source_service,
                error_code=error_code,
                detail=detail,
            )
        )
        warnings.append(unavailable_warning)
        return status_code, None

    def _build_workflow_cues(self, portfolio_id: str) -> list[FoundationWorkflowLaunchCue]:
        return [
            FoundationWorkflowLaunchCue(
                key="performance",
                label="Open Performance",
                href=f"/app/performance?portfolioId={portfolio_id}",
            ),
            FoundationWorkflowLaunchCue(
                key="risk",
                label="Open Risk",
                href=f"/app/risk?portfolioId={portfolio_id}",
            ),
            FoundationWorkflowLaunchCue(
                key="proposal",
                label="Open Proposal",
                href=f"/app/proposal?portfolioId={portfolio_id}",
            ),
        ]

    def _build_evidence_summary(
        self,
        *,
        warnings: list[str],
        partial_failures: list[FoundationPartialFailure],
    ) -> FoundationEvidenceSummary:
        affected_sources = sorted({failure.source_service for failure in partial_failures})
        if partial_failures or warnings:
            return FoundationEvidenceSummary(
                status="partial",
                summary=(
                    "Foundation workspace remains usable, but one or more upstream sources "
                    "are degraded and should be reviewed before advisor use."
                ),
                warning_count=len(warnings),
                partial_failure_count=len(partial_failures),
                affected_sources=affected_sources,
            )
        return FoundationEvidenceSummary(
            status="ready",
            summary="Foundation workspace inputs are ready for advisor use.",
            warning_count=0,
            partial_failure_count=0,
            affected_sources=[],
        )

    def _optional_str(self, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None
