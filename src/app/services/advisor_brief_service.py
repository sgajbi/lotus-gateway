from __future__ import annotations

from typing import Any, Protocol

from app.contracts.advisor_brief import (
    AdvisorBriefResponse,
    AdvisorBriefStatus,
    AdvisorBriefWorkflowPackRunReviewActionRequest,
)
from app.contracts.performance_workspace import PerformanceWorkspaceResponse
from app.middleware.server_timing import server_timing_span
from app.services.advisor_brief_client_protocols import (
    AdvisorBriefAdviseClient,
    AdvisorBriefAiClient,
)
from app.services.advisor_brief_narrative import (
    AdvisorBriefNarrativeState,
    build_advisor_brief_ai_task_request,
    build_ai_advisor_brief_narrative_state,
    build_source_advisor_brief_narrative_state,
)
from app.services.advisor_brief_response import (
    assemble_advisor_brief_response,
    with_advisor_brief_runtime_context,
)
from app.services.advisor_brief_review_actions import (
    apply_advisor_brief_review_action,
    load_advisor_brief_review_action_context,
)
from app.services.advisor_brief_runtime_context import (
    AdvisorBriefRuntimeContext,
    load_advisor_brief_runtime_context,
)
from app.services.advisor_brief_source import (
    AdvisorBriefSourceContext,
    build_advisor_brief_source_context,
)
from app.services.async_ttl_cache import AsyncTtlCache


class AdvisorBriefPerformanceWorkspaceService(Protocol):
    async def get_performance_workspace(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        period: str,
        chart_frequency: str,
        contribution_dimension: str,
        attribution_dimension: str,
        detail_basis: str,
        benchmark_code: str | None,
        explicit_start_date: str | None = None,
        explicit_end_date: str | None = None,
        requested_as_of_date: str | None = None,
        requested_reporting_currency: str | None = None,
    ) -> PerformanceWorkspaceResponse: ...


class AdvisorBriefService:
    def __init__(
        self,
        *,
        performance_workspace_service: AdvisorBriefPerformanceWorkspaceService,
        lotus_ai_client: AdvisorBriefAiClient,
        advise_client: AdvisorBriefAdviseClient | None = None,
        cache_ttl_seconds: float = 30.0,
    ):
        self._performance_workspace_service = performance_workspace_service
        self._lotus_ai_client = lotus_ai_client
        self._advise_client = advise_client
        self._response_cache = AsyncTtlCache[AdvisorBriefResponse](ttl_seconds=cache_ttl_seconds)

    def clear_cache(self) -> None:
        self._response_cache.clear()

    async def get_performance_advisor_brief(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        period: str,
        chart_frequency: str,
        contribution_dimension: str,
        attribution_dimension: str,
        detail_basis: str,
        benchmark_code: str | None,
        explicit_start_date: str | None = None,
        explicit_end_date: str | None = None,
        requested_as_of_date: str | None = None,
        requested_reporting_currency: str | None = None,
    ) -> AdvisorBriefResponse:
        cache_key = (
            "advisor_brief",
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
        return await self._response_cache.get_or_set(
            key=cache_key,
            factory=lambda: self._build_performance_advisor_brief(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                period=period,
                chart_frequency=chart_frequency,
                contribution_dimension=contribution_dimension,
                attribution_dimension=attribution_dimension,
                detail_basis=detail_basis,
                benchmark_code=benchmark_code,
                explicit_start_date=explicit_start_date,
                explicit_end_date=explicit_end_date,
                requested_as_of_date=requested_as_of_date,
                requested_reporting_currency=requested_reporting_currency,
            ),
        )

    async def _build_performance_advisor_brief(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        period: str,
        chart_frequency: str,
        contribution_dimension: str,
        attribution_dimension: str,
        detail_basis: str,
        benchmark_code: str | None,
        explicit_start_date: str | None = None,
        explicit_end_date: str | None = None,
        requested_as_of_date: str | None = None,
        requested_reporting_currency: str | None = None,
    ) -> AdvisorBriefResponse:
        workspace = await self._load_performance_workspace(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            period=period,
            chart_frequency=chart_frequency,
            contribution_dimension=contribution_dimension,
            attribution_dimension=attribution_dimension,
            detail_basis=detail_basis,
            benchmark_code=benchmark_code,
            explicit_start_date=explicit_start_date,
            explicit_end_date=explicit_end_date,
            requested_as_of_date=requested_as_of_date,
            requested_reporting_currency=requested_reporting_currency,
        )
        source_context = build_advisor_brief_source_context(
            workspace=workspace,
            detail_basis=detail_basis,
        )
        narrative_state = await self._build_advisor_brief_narrative_state(
            correlation_id=correlation_id,
            source_context=source_context,
        )
        runtime_context = await self._load_runtime_context(
            correlation_id=correlation_id,
            ai_audit=narrative_state.ai_audit,
        )
        return assemble_advisor_brief_response(
            correlation_id=correlation_id,
            source_context=source_context,
            narrative_state=narrative_state,
            runtime_context=runtime_context,
        )

    async def _load_runtime_context(
        self,
        *,
        correlation_id: str,
        ai_audit: dict[str, Any],
    ) -> AdvisorBriefRuntimeContext:
        return await load_advisor_brief_runtime_context(
            lotus_ai_client=self._lotus_ai_client,
            advise_client=self._advise_client,
            correlation_id=correlation_id,
            ai_audit=ai_audit,
        )

    async def _load_performance_workspace(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
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
    ) -> PerformanceWorkspaceResponse:
        async with server_timing_span("perf-advisor-brief-source"):
            return await self._performance_workspace_service.get_performance_workspace(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                period=period,
                chart_frequency=chart_frequency,
                contribution_dimension=contribution_dimension,
                attribution_dimension=attribution_dimension,
                detail_basis=detail_basis,
                benchmark_code=benchmark_code,
                explicit_start_date=explicit_start_date,
                explicit_end_date=explicit_end_date,
                requested_as_of_date=requested_as_of_date,
                requested_reporting_currency=requested_reporting_currency,
            )

    async def _build_advisor_brief_narrative_state(
        self,
        *,
        correlation_id: str,
        source_context: AdvisorBriefSourceContext,
    ) -> AdvisorBriefNarrativeState:
        narrative_state = build_source_advisor_brief_narrative_state(source_context=source_context)
        if narrative_state.status is AdvisorBriefStatus.UNAVAILABLE:
            return narrative_state

        task_request = build_advisor_brief_ai_task_request(
            correlation_id=correlation_id,
            source_context=source_context,
        )
        async with server_timing_span("perf-advisor-brief-ai"):
            ai_status, ai_payload = await self._lotus_ai_client.execute_workflow_pack(
                pack_id="advisor_brief.pack",
                version="v1",
                environment="DEVELOPMENT",
                caller_identity_class="BANKER_PRODUCT",
                workflow_surface="advisor-brief-workspace",
                task_request=task_request,
                correlation_id=correlation_id,
            )
        return build_ai_advisor_brief_narrative_state(
            source_context=source_context,
            narrative_state=narrative_state,
            ai_status=ai_status,
            ai_payload=ai_payload,
        )

    async def apply_performance_advisor_brief_review_action(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        period: str,
        chart_frequency: str,
        contribution_dimension: str,
        attribution_dimension: str,
        detail_basis: str,
        benchmark_code: str | None,
        request: AdvisorBriefWorkflowPackRunReviewActionRequest,
        explicit_start_date: str | None = None,
        explicit_end_date: str | None = None,
        requested_as_of_date: str | None = None,
        requested_reporting_currency: str | None = None,
    ) -> AdvisorBriefResponse:
        review_context = await load_advisor_brief_review_action_context(
            advisor_brief_loader=self,
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            period=period,
            chart_frequency=chart_frequency,
            contribution_dimension=contribution_dimension,
            attribution_dimension=attribution_dimension,
            detail_basis=detail_basis,
            benchmark_code=benchmark_code,
            request=request,
            explicit_start_date=explicit_start_date,
            explicit_end_date=explicit_end_date,
            requested_as_of_date=requested_as_of_date,
            requested_reporting_currency=requested_reporting_currency,
        )
        await apply_advisor_brief_review_action(
            lotus_ai_client=self._lotus_ai_client,
            run_id=review_context.run_id,
            correlation_id=correlation_id,
            request=request,
        )
        runtime_context = await self._load_runtime_context(
            correlation_id=correlation_id,
            ai_audit=review_context.brief.ai_audit,
        )
        self.clear_cache()
        return with_advisor_brief_runtime_context(
            review_context.brief,
            runtime_context,
        )
