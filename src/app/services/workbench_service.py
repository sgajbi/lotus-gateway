import asyncio
from collections.abc import Awaitable
from dataclasses import dataclass
from datetime import date
from typing import Any, cast

from fastapi import HTTPException, status

from app.config import settings
from app.contracts.workbench import (
    WorkbenchAnalyticsBucket,
    WorkbenchAnalyticsResponse,
    WorkbenchOverviewResponse,
    WorkbenchOverviewSummary,
    WorkbenchPartialFailure,
    WorkbenchPerformanceSnapshot,
    WorkbenchPolicyFeedback,
    WorkbenchPortfolio360Response,
    WorkbenchPortfolioSummary,
    WorkbenchPositionView,
    WorkbenchProjectedPositionView,
    WorkbenchProjectedSummary,
    WorkbenchRebalanceSnapshot,
    WorkbenchSandboxStateResponse,
    WorkbenchTopChange,
)
from app.services.workbench_analytics_projection import (
    build_workbench_allocation_buckets,
    build_workbench_return_metrics,
    build_workbench_top_changes,
    with_controlled_risk_bff_gap,
)
from app.services.workbench_core_snapshot import (
    extract_current_positions,
    parse_lotus_core_snapshot,
)
from app.services.workbench_performance_snapshot import parse_performance_snapshot
from app.services.workbench_policy_feedback import (
    build_policy_idempotency_key,
    build_policy_simulation_payload,
    parse_policy_feedback_success,
    parse_policy_feedback_unavailable,
)
from app.services.workbench_projected_state import parse_projected_state
from app.services.workbench_rebalance_snapshot import parse_rebalance_snapshot
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


@dataclass(frozen=True)
class WorkbenchOverviewEnrichmentResults:
    performance_result: object
    rebalance_result: object
    rebalance_supportability_result: object


@dataclass(frozen=True)
class WorkbenchSandboxPolicyState:
    policy_feedback: WorkbenchPolicyFeedback | None
    warnings: list[str]
    partial_failures: list[WorkbenchPartialFailure]


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


class WorkbenchService:
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
    ) -> WorkbenchOverviewResponse:
        context = await self._load_workbench_snapshot_context(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
        )
        (
            performance_snapshot,
            rebalance_snapshot,
            warnings,
            partial_failures,
        ) = await self._load_overview_enrichment(
            portfolio_id=portfolio_id,
            as_of_date=context.as_of_date,
            correlation_id=correlation_id,
            include_performance_snapshot=include_performance_snapshot,
            include_rebalance_snapshot=include_rebalance_snapshot,
        )

        return WorkbenchOverviewResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            as_of_date=context.as_of_date,
            portfolio=context.portfolio,
            overview=context.overview,
            performance_snapshot=performance_snapshot,
            rebalance_snapshot=rebalance_snapshot,
            warnings=warnings,
            partial_failures=partial_failures,
        )

    async def _empty_async_result(self) -> tuple[int, dict[str, Any]]:
        return 204, {}

    async def _resolve_performance_snapshot_end_date(
        self,
        *,
        portfolio_id: str,
        as_of_date: str,
        correlation_id: str,
    ) -> str:
        (
            status_code,
            payload,
        ) = await self._lotus_core_query_client.get_portfolio_analytics_reference(
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
        return performance_end_date

    async def get_portfolio_360(
        self,
        portfolio_id: str,
        correlation_id: str,
        session_id: str | None = None,
    ) -> WorkbenchPortfolio360Response:
        context = await self._load_workbench_snapshot_context(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
        )
        (
            performance_snapshot,
            rebalance_snapshot,
            warnings,
            partial_failures,
        ) = await self._load_overview_enrichment(
            portfolio_id=portfolio_id,
            as_of_date=context.as_of_date,
            correlation_id=correlation_id,
            include_performance_snapshot=True,
            include_rebalance_snapshot=True,
        )

        projected_positions: list[WorkbenchProjectedPositionView] = []
        projected_summary: WorkbenchProjectedSummary | None = None
        if session_id:
            projected_positions, projected_summary = await self._load_projected_state(
                session_id=session_id,
                correlation_id=correlation_id,
            )

        return WorkbenchPortfolio360Response(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            as_of_date=context.as_of_date,
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

    async def create_sandbox_session(
        self,
        portfolio_id: str,
        correlation_id: str,
        created_by: str | None,
        ttl_hours: int,
    ) -> WorkbenchSandboxStateResponse:
        status_code, payload = await self._lotus_core_query_client.create_simulation_session(
            portfolio_id=portfolio_id,
            created_by=created_by,
            ttl_hours=ttl_hours,
            correlation_id=correlation_id,
        )
        if status_code >= status.HTTP_400_BAD_REQUEST:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"lotus-core simulation session create failed: {payload}",
            )

        session_payload = payload.get("session", {})
        session_id = str(session_payload.get("session_id", ""))
        session_version = int(session_payload.get("version", 1))
        projected_positions, projected_summary = await self._load_projected_state(
            session_id=session_id,
            correlation_id=correlation_id,
        )
        return WorkbenchSandboxStateResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            portfolio_id=portfolio_id,
            session_id=session_id,
            session_version=session_version,
            projected_positions=projected_positions,
            projected_summary=projected_summary,
            policy_feedback=None,
            warnings=[],
            partial_failures=[],
        )

    async def apply_sandbox_changes(
        self,
        portfolio_id: str,
        session_id: str,
        correlation_id: str,
        changes: list[dict[str, Any]],
        evaluate_policy: bool,
    ) -> WorkbenchSandboxStateResponse:
        status_code, payload = await self._lotus_core_query_client.add_simulation_changes(
            session_id=session_id,
            changes=changes,
            correlation_id=correlation_id,
        )
        if status_code >= status.HTTP_400_BAD_REQUEST:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"lotus-core simulation change apply failed: {payload}",
            )

        session_version = int(payload.get("version", 1))
        projected_positions, projected_summary = await self._load_projected_state(
            session_id=session_id,
            correlation_id=correlation_id,
        )

        policy_state = await self._build_sandbox_policy_state(
            portfolio_id=portfolio_id,
            session_id=session_id,
            session_version=session_version,
            projected_positions=projected_positions,
            correlation_id=correlation_id,
            evaluate_policy=evaluate_policy,
        )

        return WorkbenchSandboxStateResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            portfolio_id=portfolio_id,
            session_id=session_id,
            session_version=session_version,
            projected_positions=projected_positions,
            projected_summary=projected_summary,
            policy_feedback=policy_state.policy_feedback,
            warnings=policy_state.warnings,
            partial_failures=policy_state.partial_failures,
        )

    async def _build_sandbox_policy_state(
        self,
        *,
        portfolio_id: str,
        session_id: str,
        session_version: int,
        projected_positions: list[WorkbenchProjectedPositionView],
        correlation_id: str,
        evaluate_policy: bool,
    ) -> WorkbenchSandboxPolicyState:
        warnings: list[str] = []
        partial_failures: list[WorkbenchPartialFailure] = []
        if not evaluate_policy:
            return WorkbenchSandboxPolicyState(
                policy_feedback=None,
                warnings=warnings,
                partial_failures=partial_failures,
            )
        policy_feedback = await self._evaluate_policy_feedback(
            portfolio_id=portfolio_id,
            session_id=session_id,
            session_version=session_version,
            projected_positions=projected_positions,
            correlation_id=correlation_id,
            warnings=warnings,
            partial_failures=partial_failures,
        )
        return WorkbenchSandboxPolicyState(
            policy_feedback=policy_feedback,
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
    ) -> "_WorkbenchSnapshotContext":
        fallback_as_of_date = date.today().isoformat()
        (
            portfolio_result,
            snapshot_result,
        ) = await asyncio.gather(
            self._lotus_core_query_client.get_portfolio(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
            ),
            self._lotus_core_query_client.get_core_snapshot(
                portfolio_id=portfolio_id,
                as_of_date=fallback_as_of_date,
                sections=["positions_baseline", "portfolio_totals", "instrument_enrichment"],
                consumer_system="lotus-gateway",
                correlation_id=correlation_id,
            ),
        )
        portfolio_status, portfolio_payload = portfolio_result
        snapshot_status, snapshot_payload = snapshot_result
        self._raise_for_lotus_core_error(portfolio_status, portfolio_payload)
        self._raise_for_lotus_core_error(snapshot_status, snapshot_payload)

        portfolio, overview, as_of_date = parse_lotus_core_snapshot(
            fallback_portfolio_id=portfolio_id,
            portfolio_payload=portfolio_payload,
            snapshot_payload=snapshot_payload,
            fallback_as_of_date=fallback_as_of_date,
        )
        return _WorkbenchSnapshotContext(
            portfolio=portfolio,
            overview=overview,
            as_of_date=as_of_date,
            current_positions=extract_current_positions(snapshot_payload),
        )

    async def _load_overview_enrichment(
        self,
        *,
        portfolio_id: str,
        as_of_date: str,
        correlation_id: str,
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
        performance_snapshot = None
        rebalance_snapshot = None

        if include_performance_snapshot or include_rebalance_snapshot:
            gathered = await self._gather_overview_enrichment_results(
                portfolio_id=portfolio_id,
                as_of_date=as_of_date,
                correlation_id=correlation_id,
                include_performance_snapshot=include_performance_snapshot,
                include_rebalance_snapshot=include_rebalance_snapshot,
            )
            if include_performance_snapshot:
                performance_snapshot = parse_performance_snapshot(
                    result=gathered.performance_result,
                    partial_failures=partial_failures,
                    warnings=warnings,
                )
            if include_rebalance_snapshot:
                rebalance_snapshot = parse_rebalance_snapshot(
                    result=gathered.rebalance_result,
                    supportability_result=gathered.rebalance_supportability_result,
                    partial_failures=partial_failures,
                    warnings=warnings,
                )

        return performance_snapshot, rebalance_snapshot, warnings, partial_failures

    async def _gather_overview_enrichment_results(
        self,
        *,
        portfolio_id: str,
        as_of_date: str,
        correlation_id: str,
        include_performance_snapshot: bool,
        include_rebalance_snapshot: bool,
    ) -> WorkbenchOverviewEnrichmentResults:
        performance_task = await self._build_performance_snapshot_task(
            portfolio_id=portfolio_id,
            as_of_date=as_of_date,
            correlation_id=correlation_id,
            include_performance_snapshot=include_performance_snapshot,
        )
        dpm_runs_task, dpm_supportability_task = self._build_rebalance_snapshot_tasks(
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
        self,
        *,
        portfolio_id: str,
        as_of_date: str,
        correlation_id: str,
        include_performance_snapshot: bool,
    ) -> Awaitable[tuple[int, dict[str, Any]]]:
        if not include_performance_snapshot:
            return self._empty_async_result()
        performance_end_date = await self._resolve_performance_snapshot_end_date(
            portfolio_id=portfolio_id,
            as_of_date=as_of_date,
            correlation_id=correlation_id,
        )
        return self._analytics_client.get_twr_analytics(
            portfolio_id=portfolio_id,
            report_end_date=performance_end_date,
            report_start_date=None,
            period="YTD",
            metric_basis="NET",
            benchmark_id=None,
            correlation_id=correlation_id,
        )

    def _build_rebalance_snapshot_tasks(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        include_rebalance_snapshot: bool,
    ) -> tuple[Awaitable[tuple[int, dict[str, Any]]], Awaitable[tuple[int, dict[str, Any]]]]:
        if not include_rebalance_snapshot:
            return self._empty_async_result(), self._empty_async_result()
        return (
            self._dpm_client.list_runs(
                params={"portfolio_id": portfolio_id, "limit": 5},
                correlation_id=correlation_id,
            ),
            self._dpm_client.get_supportability_summary(correlation_id=correlation_id),
        )

    def _raise_for_lotus_core_error(self, upstream_status: int, payload: dict[str, Any]) -> None:
        if upstream_status < status.HTTP_400_BAD_REQUEST:
            return
        detail = str(payload.get("detail", payload))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"lotus-core core snapshot unavailable: {detail}",
        )

    async def _load_projected_state(
        self,
        session_id: str,
        correlation_id: str,
    ) -> tuple[list[WorkbenchProjectedPositionView], WorkbenchProjectedSummary]:
        (
            positions_status,
            positions_payload,
        ) = await self._lotus_core_query_client.get_projected_positions(
            session_id=session_id,
            correlation_id=correlation_id,
        )
        if positions_status >= status.HTTP_400_BAD_REQUEST:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"lotus-core projected positions unavailable: {positions_payload}",
            )

        summary_status, summary_payload = await self._lotus_core_query_client.get_projected_summary(
            session_id=session_id,
            correlation_id=correlation_id,
        )
        if summary_status >= status.HTTP_400_BAD_REQUEST:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"lotus-core projected summary unavailable: {summary_payload}",
            )

        return parse_projected_state(
            positions_payload=positions_payload,
            summary_payload=summary_payload,
        )

    async def _evaluate_policy_feedback(
        self,
        portfolio_id: str,
        session_id: str,
        session_version: int,
        projected_positions: list[WorkbenchProjectedPositionView],
        correlation_id: str,
        warnings: list[str],
        partial_failures: list[WorkbenchPartialFailure],
    ) -> WorkbenchPolicyFeedback:
        overview = await self.get_workbench_overview(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
        )
        simulate_payload = build_policy_simulation_payload(
            portfolio_id=portfolio_id,
            base_currency=overview.portfolio.base_currency,
            projected_positions=projected_positions,
        )
        idempotency_key = build_policy_idempotency_key(
            session_id=session_id,
            session_version=session_version,
        )
        advise_status, advise_payload = await self._advise_client.simulate_proposal(
            body=simulate_payload,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        if advise_status >= status.HTTP_400_BAD_REQUEST:
            warnings.append("ADVISE_PROPOSAL_SIMULATION_UNAVAILABLE")
            partial_failures.append(
                WorkbenchPartialFailure(
                    source_service="lotus-advise",
                    error_code=f"HTTP_{advise_status}",
                    detail=str(advise_payload.get("detail", advise_payload)),
                )
            )
            return parse_policy_feedback_unavailable(advise_payload)

        return parse_policy_feedback_success(advise_payload)


@dataclass(slots=True)
class _WorkbenchSnapshotContext:
    portfolio: WorkbenchPortfolioSummary
    overview: WorkbenchOverviewSummary
    as_of_date: str
    current_positions: list[WorkbenchPositionView]
