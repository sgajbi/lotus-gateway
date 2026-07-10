from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from fastapi import HTTPException, status

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
    safe_advisor_brief_error_detail,
)
from app.services.advisor_brief_response import (
    assemble_advisor_brief_response,
    with_advisor_brief_runtime_context,
)
from app.services.advisor_brief_runtime_context import (
    load_advisor_brief_runtime_context,
)
from app.services.advisor_brief_source import (
    AdvisorBriefSourceContext,
    build_advisor_brief_source_context,
)
from app.services.advisor_brief_workflow_pack import (
    assert_advisor_brief_review_action_allowed,
    resolve_advisor_brief_workflow_pack_run_id,
)
from app.services.async_ttl_cache import AsyncTtlCache


@dataclass(frozen=True)
class AdvisorBriefReviewActionContext:
    brief: AdvisorBriefResponse
    run_id: str


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
        )
        source_context = build_advisor_brief_source_context(
            workspace=workspace,
            detail_basis=detail_basis,
        )
        narrative_state = await self._build_advisor_brief_narrative_state(
            correlation_id=correlation_id,
            source_context=source_context,
        )
        runtime_context = await load_advisor_brief_runtime_context(
            lotus_ai_client=self._lotus_ai_client,
            advise_client=self._advise_client,
            correlation_id=correlation_id,
            ai_audit=narrative_state.ai_audit,
        )
        return assemble_advisor_brief_response(
            correlation_id=correlation_id,
            source_context=source_context,
            narrative_state=narrative_state,
            runtime_context=runtime_context,
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
    ) -> AdvisorBriefResponse:
        review_context = await self._load_advisor_brief_review_action_context(
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
        )
        await self._apply_advisor_brief_review_action(
            run_id=review_context.run_id,
            correlation_id=correlation_id,
            request=request,
        )
        runtime_context = await load_advisor_brief_runtime_context(
            lotus_ai_client=self._lotus_ai_client,
            advise_client=self._advise_client,
            correlation_id=correlation_id,
            ai_audit=review_context.brief.ai_audit,
        )
        self.clear_cache()
        return with_advisor_brief_runtime_context(
            review_context.brief,
            runtime_context,
        )

    async def _load_advisor_brief_review_action_context(
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
        explicit_start_date: str | None,
        explicit_end_date: str | None,
    ) -> AdvisorBriefReviewActionContext:
        brief = await self.get_performance_advisor_brief(
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
        )
        run_id = resolve_advisor_brief_workflow_pack_run_id(ai_audit=brief.ai_audit)
        if run_id is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Advisor brief workflow-pack run posture is unavailable for bounded review "
                    "actions."
                ),
            )
        assert_advisor_brief_review_action_allowed(
            workflow_pack_run=brief.workflow_pack_run,
            run_id=run_id,
            action_type=request.action_type.value,
        )
        return AdvisorBriefReviewActionContext(brief=brief, run_id=run_id)

    async def _apply_advisor_brief_review_action(
        self,
        *,
        run_id: str,
        correlation_id: str,
        request: AdvisorBriefWorkflowPackRunReviewActionRequest,
    ) -> None:
        (
            review_status,
            review_payload,
        ) = await self._lotus_ai_client.apply_workflow_pack_run_review_action(
            run_id=run_id,
            correlation_id=correlation_id,
            request_payload={
                "action_type": request.action_type.value,
                "caller_app": "lotus-gateway",
                "reviewed_by": request.reviewed_by,
                "reason": request.reason,
                "replacement_run_id": request.replacement_run_id,
            },
        )
        if review_status != 200:
            raise HTTPException(
                status_code=review_status,
                detail=safe_advisor_brief_error_detail(review_payload),
            )
