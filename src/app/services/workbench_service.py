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
    WorkbenchPolicyFeedback,
    WorkbenchPortfolio360Response,
    WorkbenchProjectedPositionView,
    WorkbenchProjectedSummary,
    WorkbenchRebalanceSnapshot,
    WorkbenchSandboxStateResponse,
    WorkbenchTopChange,
)
from app.services.upstream_envelope import (
    raise_product_safe_gateway_unavailable_error,
    safe_upstream_detail,
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
from app.services.workbench_policy_feedback import (
    build_policy_idempotency_key,
    build_policy_simulation_payload,
    parse_policy_feedback_success,
    parse_policy_feedback_unavailable,
)
from app.services.workbench_projected_state import parse_projected_state
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
            benchmark_code=benchmark_code,
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
        raise_product_safe_gateway_unavailable_error(
            status_code,
            payload,
            source_service="lotus-core",
            error_code="LOTUS_CORE_SIMULATION_SESSION_CREATE_FAILED",
            default_detail="Lotus Core simulation session creation failed.",
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
        payload = await self._apply_sandbox_changes_payload(
            session_id=session_id,
            changes=changes,
            correlation_id=correlation_id,
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

    async def _apply_sandbox_changes_payload(
        self,
        *,
        session_id: str,
        changes: list[dict[str, Any]],
        correlation_id: str,
    ) -> dict[str, Any]:
        status_code, payload = await self._lotus_core_query_client.add_simulation_changes(
            session_id=session_id,
            changes=changes,
            correlation_id=correlation_id,
        )
        raise_product_safe_gateway_unavailable_error(
            status_code,
            payload,
            source_service="lotus-core",
            error_code="LOTUS_CORE_SIMULATION_CHANGE_APPLY_FAILED",
            default_detail="Lotus Core simulation change application failed.",
        )
        return payload

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
    ) -> WorkbenchSnapshotContext:
        return await load_workbench_snapshot_context(
            core_client=self._lotus_core_query_client,
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
        )

    async def _load_overview_enrichment(
        self,
        *,
        portfolio_id: str,
        as_of_date: str,
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
            raise_product_safe_gateway_unavailable_error(
                positions_status,
                positions_payload,
                source_service="lotus-core",
                error_code="LOTUS_CORE_PROJECTED_POSITIONS_UNAVAILABLE",
                default_detail="Lotus Core projected positions are unavailable.",
            )

        summary_status, summary_payload = await self._lotus_core_query_client.get_projected_summary(
            session_id=session_id,
            correlation_id=correlation_id,
        )
        if summary_status >= status.HTTP_400_BAD_REQUEST:
            raise_product_safe_gateway_unavailable_error(
                summary_status,
                summary_payload,
                source_service="lotus-core",
                error_code="LOTUS_CORE_PROJECTED_SUMMARY_UNAVAILABLE",
                default_detail="Lotus Core projected summary is unavailable.",
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
                    detail=safe_upstream_detail(
                        advise_payload,
                        default_detail="proposal simulation unavailable",
                    ),
                )
            )
            return parse_policy_feedback_unavailable(advise_payload)

        return parse_policy_feedback_success(advise_payload)
