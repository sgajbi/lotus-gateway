from __future__ import annotations

from typing import Any, Protocol

from fastapi import HTTPException, status

from app.contracts.advisor_brief import (
    AdvisorBriefActionItem,
    AdvisorBriefAdvisorySupportability,
    AdvisorBriefAiSurfaceSupportability,
    AdvisorBriefAiSurfaceSupportabilityItem,
    AdvisorBriefEvidenceRef,
    AdvisorBriefNarrativeItem,
    AdvisorBriefResponse,
    AdvisorBriefSourceMetric,
    AdvisorBriefStatus,
    AdvisorBriefSupportabilityItem,
    AdvisorBriefTone,
    AdvisorBriefWorkflowPackRun,
    AdvisorBriefWorkflowPackRunFinding,
    AdvisorBriefWorkflowPackRunReviewActionRequest,
    AdvisorBriefWorkflowPackTaskFlow,
    AdvisorBriefWorkflowPackTaskFlowHandoff,
    AdvisorBriefWorkflowPackTaskFlowLineage,
)
from app.contracts.performance_workspace import (
    AttributionSummaryView,
    ContributionPositionView,
    ContributionSummaryView,
    PerformanceComparativeSummary,
    PerformanceWorkspaceResponse,
)
from app.middleware.server_timing import server_timing_span
from app.precision_policy import quantize_money, quantize_performance
from app.services.async_ttl_cache import AsyncTtlCache
from app.services.upstream_client_protocols import AdvisorBriefAdviseClient, AdvisorBriefAiClient

_TASK_ID = "explain.v1"
_EXPECTED_OUTPUT_LABEL = "EXPLANATION_ONLY"
_ADVISOR_BRIEF_TASK_FLOW_LOOKUP_LIMIT = 100


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
        async with server_timing_span("perf-advisor-brief-source"):
            workspace = await self._performance_workspace_service.get_performance_workspace(
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

        selected_performance = (
            workspace.net_performance
            if detail_basis.upper() == "NET"
            else workspace.gross_performance
        )
        source_refs = _build_source_refs(workspace=workspace)
        supportability = _build_supportability(workspace=workspace)
        status = _resolve_status(workspace=workspace, supportability=supportability)

        source_summary = _build_source_summary(
            workspace=workspace,
            selected_performance=selected_performance,
        )
        talking_points = _build_source_talking_points(
            workspace=workspace,
            selected_performance=selected_performance,
        )
        recommended_actions = _build_recommended_actions(workspace=workspace)
        risks_and_exceptions = _build_risks_and_exceptions(
            workspace=workspace,
            supportability=supportability,
        )
        ai_audit: dict[str, Any] = _normalize_ai_audit({})
        ai_evidence: dict[str, Any] = {"descriptors": []}

        if status is not AdvisorBriefStatus.UNAVAILABLE:
            task_request = {
                "task_id": _TASK_ID,
                "input_mode": "STRUCTURED_CONTEXT",
                "caller": {
                    "caller_app": "lotus-gateway",
                    "correlation_id": correlation_id,
                },
                "context": {
                    "summary": (
                        f"Advisor brief context for portfolio {workspace.portfolio_id}, "
                        f"{workspace.period} period, basis {workspace.detail_basis}."
                    ),
                    "payload": _build_ai_fact_bundle(
                        workspace=workspace,
                        selected_performance=selected_performance,
                    ),
                    "source_refs": source_refs,
                },
                "expected_output_label": _EXPECTED_OUTPUT_LABEL,
            }
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
            execution_payload = _safe_dict(ai_payload.get("execution")) if ai_status == 200 else {}
            if ai_status == 200:
                ai_audit = _normalize_ai_audit(_safe_dict(execution_payload.get("audit")))
                ai_evidence = _safe_dict(execution_payload.get("evidence")) or {"descriptors": []}
            if ai_status == 200 and execution_payload.get("status") == "COMPLETED":
                result = _safe_dict(execution_payload.get("result"))
                structured_output = _safe_dict(result.get("structured_output"))
                source_summary = (
                    _extract_ai_summary(
                        ai_payload=execution_payload,
                        structured_output=structured_output,
                    )
                    or source_summary
                )
                talking_points = (
                    _extract_ai_talking_points(
                        structured_output=structured_output,
                        route=_route_query(
                            portfolio_id=workspace.portfolio_id,
                            period=workspace.period,
                            basis=workspace.detail_basis,
                            benchmark_code=workspace.benchmark_code,
                        ),
                    )
                    or talking_points
                )
                recommended_actions = (
                    _extract_ai_recommended_actions(
                        structured_output=structured_output,
                        route=_route_query(
                            portfolio_id=workspace.portfolio_id,
                            period=workspace.period,
                            basis=workspace.detail_basis,
                            benchmark_code=workspace.benchmark_code,
                        ),
                    )
                    or recommended_actions
                )
                risks_and_exceptions = (
                    _extract_ai_risks(
                        structured_output=structured_output,
                        route=_route_query(
                            portfolio_id=workspace.portfolio_id,
                            period=workspace.period,
                            basis=workspace.detail_basis,
                            benchmark_code=workspace.benchmark_code,
                        ),
                    )
                    or risks_and_exceptions
                )
            elif ai_status == 200:
                status = AdvisorBriefStatus.PARTIAL
                risks_and_exceptions.append(
                    AdvisorBriefNarrativeItem(
                        headline="AI narrative generation is unavailable.",
                        detail=(
                            _safe_execution_detail(execution_payload)
                            or (
                                "Source-backed metrics remain available for manual review and "
                                "client prep."
                            )
                        ),
                        tone=AdvisorBriefTone.WARNING,
                        evidence_refs=[
                            _summary_evidence_ref(
                                label="Advisor Brief",
                                value="Unavailable",
                                portfolio_id=workspace.portfolio_id,
                                period=workspace.period,
                                basis=workspace.detail_basis,
                                benchmark_code=workspace.benchmark_code,
                            )
                        ],
                    )
                )
            else:
                status = AdvisorBriefStatus.PARTIAL
                ai_audit = _normalize_ai_audit(
                    {
                        "task_id": _TASK_ID,
                        "output_label": _EXPECTED_OUTPUT_LABEL,
                        "provider_mode": "unavailable",
                        "detail": _safe_error_detail(ai_payload),
                    }
                )
                risks_and_exceptions.append(
                    AdvisorBriefNarrativeItem(
                        headline="AI narrative generation is unavailable.",
                        detail=(
                            "Source-backed metrics remain available for manual review and "
                            "client prep."
                        ),
                        tone=AdvisorBriefTone.WARNING,
                        evidence_refs=[
                            _summary_evidence_ref(
                                label="Advisor Brief",
                                value="Unavailable",
                                portfolio_id=workspace.portfolio_id,
                                period=workspace.period,
                                basis=workspace.detail_basis,
                                benchmark_code=workspace.benchmark_code,
                            )
                        ],
                    )
                )
        workflow_pack_run = await _load_advisor_brief_workflow_pack_run(
            lotus_ai_client=self._lotus_ai_client,
            ai_audit=ai_audit,
            correlation_id=correlation_id,
        )
        workflow_pack_task_flow = await _load_advisor_brief_workflow_pack_task_flow(
            lotus_ai_client=self._lotus_ai_client,
            ai_audit=ai_audit,
            correlation_id=correlation_id,
        )
        ai_surface_supportability = await _load_ai_surface_supportability(
            lotus_ai_client=self._lotus_ai_client,
            correlation_id=correlation_id,
        )
        advisory_supportability = await _load_advisory_supportability(
            advise_client=self._advise_client,
            correlation_id=correlation_id,
        )

        return AdvisorBriefResponse(
            correlation_id=correlation_id,
            contract_version=workspace.contract_version,
            portfolio_id=workspace.portfolio_id,
            portfolio=workspace.portfolio,
            as_of_date=workspace.as_of_date,
            period=workspace.period,
            report_start_date=workspace.report_start_date,
            report_end_date=workspace.report_end_date,
            detail_basis=workspace.detail_basis,
            chart_frequency=workspace.chart_frequency,
            contribution_dimension=workspace.contribution_dimension,
            attribution_dimension=workspace.attribution_dimension,
            benchmark_code=workspace.benchmark_code,
            status=status,
            summary=source_summary,
            talking_points=talking_points,
            recommended_actions=recommended_actions,
            risks_and_exceptions=risks_and_exceptions,
            source_metrics=_build_source_metrics(
                workspace=workspace,
                selected_performance=selected_performance,
            ),
            supportability=supportability,
            ai_surface_supportability=ai_surface_supportability,
            advisory_supportability=advisory_supportability,
            ai_audit=ai_audit,
            ai_evidence=ai_evidence,
            workflow_pack_run=workflow_pack_run,
            workflow_pack_task_flow=workflow_pack_task_flow,
            warnings=workspace.warnings,
            partial_failures=workspace.partial_failures,
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
        run_id = _resolve_advisor_brief_workflow_pack_run_id(ai_audit=brief.ai_audit)
        if run_id is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Advisor brief workflow-pack run posture is unavailable for bounded review "
                    "actions."
                ),
            )
        _assert_advisor_brief_review_action_allowed(
            workflow_pack_run=brief.workflow_pack_run,
            run_id=run_id,
            action_type=request.action_type.value,
        )

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
                detail=_safe_error_detail(review_payload),
            )

        workflow_pack_run = await _load_advisor_brief_workflow_pack_run(
            lotus_ai_client=self._lotus_ai_client,
            ai_audit=brief.ai_audit,
            correlation_id=correlation_id,
        )
        workflow_pack_task_flow = await _load_advisor_brief_workflow_pack_task_flow(
            lotus_ai_client=self._lotus_ai_client,
            ai_audit=brief.ai_audit,
            correlation_id=correlation_id,
        )
        ai_surface_supportability = await _load_ai_surface_supportability(
            lotus_ai_client=self._lotus_ai_client,
            correlation_id=correlation_id,
        )
        advisory_supportability = await _load_advisory_supportability(
            advise_client=self._advise_client,
            correlation_id=correlation_id,
        )
        self.clear_cache()
        return brief.model_copy(
            update={
                "workflow_pack_run": workflow_pack_run,
                "workflow_pack_task_flow": workflow_pack_task_flow,
                "ai_surface_supportability": ai_surface_supportability,
                "advisory_supportability": advisory_supportability,
            }
        )


def _assert_advisor_brief_review_action_allowed(
    *,
    workflow_pack_run: AdvisorBriefWorkflowPackRun | None,
    run_id: str,
    action_type: str,
) -> None:
    if workflow_pack_run is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Advisor brief workflow-pack run `{run_id}` has no inspectable review posture; "
                "refresh the brief before recording a bounded review action."
            ),
        )
    allowed_actions = set(workflow_pack_run.allowed_review_actions)
    if action_type not in allowed_actions:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Advisor brief workflow-pack run `{workflow_pack_run.run_id}` does not allow "
                f"review action `{action_type}` from runtime state "
                f"`{workflow_pack_run.runtime_state}` and review state "
                f"`{workflow_pack_run.review_state}`."
            ),
        )


async def _load_advisory_supportability(
    *,
    advise_client: AdvisorBriefAdviseClient | None,
    correlation_id: str,
) -> AdvisorBriefAdvisorySupportability | None:
    if advise_client is None:
        return None
    status_code, payload = await advise_client.get_platform_capabilities(
        correlation_id=correlation_id
    )
    if status_code != 200:
        return None
    supportability = _safe_dict(payload.get("supportability"))
    if not supportability:
        return None
    return AdvisorBriefAdvisorySupportability(
        state=_safe_str(supportability.get("state")) or "unknown",
        reason=_safe_str(supportability.get("reason")),
        freshness_bucket=_safe_str(supportability.get("freshness_bucket")) or "unknown",
        dependency_count=_safe_int(supportability.get("dependency_count")),
        ready_dependency_count=_safe_int(supportability.get("ready_dependency_count")),
        degraded_dependency_count=_safe_int(supportability.get("degraded_dependency_count")),
        enabled_feature_count=_safe_int(supportability.get("enabled_feature_count")),
        ready_feature_count=_safe_int(supportability.get("ready_feature_count")),
    )


async def _load_ai_surface_supportability(
    *,
    lotus_ai_client: AdvisorBriefAiClient,
    correlation_id: str,
) -> AdvisorBriefAiSurfaceSupportability | None:
    runtime_status, runtime_payload = await lotus_ai_client.get_observability_runtime_status(
        correlation_id=correlation_id
    )
    if runtime_status != 200:
        return None
    source = _safe_dict(runtime_payload.get("ai_surface_supportability"))
    if not source:
        return None
    return _parse_ai_surface_supportability(source=source)


def _parse_ai_surface_supportability(
    *,
    source: dict[str, Any],
) -> AdvisorBriefAiSurfaceSupportability:
    posture = _safe_str(source.get("posture")) or "unavailable"
    freshness = _safe_str(source.get("freshness")) or "unknown"
    return AdvisorBriefAiSurfaceSupportability(
        state=_normalize_ai_surface_supportability_state(posture),
        freshness_bucket=_normalize_ai_surface_freshness_bucket(freshness),
        posture=posture,
        freshness=freshness,
        metric_name=_safe_str(source.get("metric_name")) or "lotus_ai_surface_supportability_state",
        supported_surface_count=_safe_int(source.get("supported_surface_count")),
        executable_workflow_pack_count=_safe_int(source.get("executable_workflow_pack_count")),
        action_required_surface_count=_safe_int(source.get("action_required_surface_count")),
        unavailable_surface_count=_safe_int(source.get("unavailable_surface_count")),
        no_sensitive_content_telemetry=bool(source.get("no_sensitive_content_telemetry")),
        surfaces=[
            surface
            for surface in (
                _parse_ai_surface_supportability_item(value=value)
                for value in _safe_list(source.get("surfaces"))
            )
            if surface is not None
        ],
        status_summary=[
            summary
            for summary in (_safe_str(item) for item in _safe_list(source.get("status_summary")))
            if summary
        ],
    )


def _parse_ai_surface_supportability_item(
    *,
    value: Any,
) -> AdvisorBriefAiSurfaceSupportabilityItem | None:
    item = _safe_dict(value)
    surface_id = _safe_str(item.get("surface_id"))
    owning_service = _safe_str(item.get("owning_service"))
    workflow_authority_owner = _safe_str(item.get("workflow_authority_owner"))
    workflow_pack_ref = _safe_str(item.get("workflow_pack_ref"))
    supportability_status = _safe_str(item.get("supportability_status"))
    model_posture = _safe_str(item.get("model_posture"))
    if (
        surface_id is None
        or owning_service is None
        or workflow_authority_owner is None
        or workflow_pack_ref is None
        or supportability_status is None
        or model_posture is None
    ):
        return None
    return AdvisorBriefAiSurfaceSupportabilityItem(
        surface_id=surface_id,
        owning_service=owning_service,
        workflow_authority_owner=workflow_authority_owner,
        workflow_pack_ref=workflow_pack_ref,
        supportability_status=supportability_status,
        model_posture=model_posture,
        latest_ready_run_id=_safe_str(item.get("latest_ready_run_id")),
        latest_action_required_run_id=_safe_str(item.get("latest_action_required_run_id")),
        no_sensitive_content_telemetry=bool(item.get("no_sensitive_content_telemetry")),
        status_summary=[
            summary
            for summary in (_safe_str(item) for item in _safe_list(item.get("status_summary")))
            if summary
        ],
    )


def _normalize_ai_surface_supportability_state(posture: str) -> str:
    normalized = posture.strip().lower()
    if normalized == "healthy":
        return "ready"
    if normalized == "degraded":
        return "action_required"
    if normalized == "unavailable":
        return "unsupported"
    return "unknown"


def _normalize_ai_surface_freshness_bucket(freshness: str) -> str:
    normalized = freshness.strip().lower()
    if normalized in {"current", "fresh", "ready"}:
        return "fresh"
    if normalized == "stale":
        return "stale"
    return "unknown"


async def _load_advisor_brief_workflow_pack_run(
    *,
    lotus_ai_client: AdvisorBriefAiClient,
    ai_audit: dict[str, Any],
    correlation_id: str,
) -> AdvisorBriefWorkflowPackRun | None:
    run_id = _resolve_advisor_brief_workflow_pack_run_id(ai_audit=ai_audit)
    if run_id is None:
        return None

    consumer_status, consumer_payload = await lotus_ai_client.get_workflow_pack_run_consumer_view(
        run_id=run_id,
        correlation_id=correlation_id,
    )
    if consumer_status != 200:
        return None

    (
        operator_status,
        operator_payload,
    ) = await lotus_ai_client.get_workflow_pack_run_operator_profile(
        run_id=run_id,
        correlation_id=correlation_id,
    )
    if operator_status != 200:
        return None

    review = _safe_dict(consumer_payload.get("review"))
    lineage = _safe_dict(consumer_payload.get("lineage"))
    findings = [
        finding
        for finding in (
            _parse_workflow_pack_run_finding(value=value)
            for value in _safe_list(operator_payload.get("findings"))
        )
        if finding is not None
    ]
    return AdvisorBriefWorkflowPackRun(
        run_id=_safe_str(operator_payload.get("run_id")) or run_id,
        runtime_state=_safe_str(operator_payload.get("runtime_state")) or "UNKNOWN",
        review_state=_safe_str(operator_payload.get("review_state")) or "UNKNOWN",
        allowed_review_actions=[
            action
            for action in (_safe_str(value) for value in _safe_list(review.get("allowed_actions")))
            if action is not None
        ],
        supportability_status=_safe_str(operator_payload.get("supportability_status")) or "UNKNOWN",
        review_pending=bool(operator_payload.get("review_pending")),
        superseded=bool(operator_payload.get("superseded")),
        workflow_authority_owner=_safe_str(lineage.get("workflow_authority_owner"))
        or "lotus-gateway",
        current_summary_note=_safe_str(operator_payload.get("current_summary_note"))
        or "Workflow-pack run posture is available without a current operator summary note.",
        replacement_run_id=_safe_str(operator_payload.get("replacement_run_id")),
        findings=findings,
    )


def _resolve_advisor_brief_workflow_pack_run_id(*, ai_audit: dict[str, Any]) -> str | None:
    workflow_pack_run_id = _safe_str(ai_audit.get("workflow_pack_run_id"))
    if workflow_pack_run_id is not None:
        return workflow_pack_run_id
    request_id = _safe_str(ai_audit.get("request_id"))
    if request_id is None:
        return None
    return f"packrun_advisor_brief_{request_id}"


async def _load_advisor_brief_workflow_pack_task_flow(
    *,
    lotus_ai_client: AdvisorBriefAiClient,
    ai_audit: dict[str, Any],
    correlation_id: str,
) -> AdvisorBriefWorkflowPackTaskFlow | None:
    run_id = _resolve_advisor_brief_workflow_pack_run_id(ai_audit=ai_audit)
    if run_id is None:
        return None

    task_flow_status, task_flow_payload = await lotus_ai_client.list_workflow_pack_task_flows(
        correlation_id=correlation_id,
        workflow_pack_id="advisor_brief.pack",
        caller="lotus-gateway",
        workflow_surface="advisor-brief-workspace",
        limit=_ADVISOR_BRIEF_TASK_FLOW_LOOKUP_LIMIT,
    )
    if task_flow_status != 200:
        return None

    for value in _safe_list(task_flow_payload.get("task_flows")):
        task_flow = _parse_advisor_brief_workflow_pack_task_flow(value=value, run_id=run_id)
        if task_flow is not None:
            return task_flow
    return None


def _parse_advisor_brief_workflow_pack_task_flow(
    *,
    value: Any,
    run_id: str,
) -> AdvisorBriefWorkflowPackTaskFlow | None:
    item = _safe_dict(value)
    run_refs = [
        ref for ref in (_safe_str(value) for value in _safe_list(item.get("run_refs"))) if ref
    ]
    if run_id not in run_refs:
        return None

    task_flow_id = _safe_str(item.get("task_flow_id"))
    workflow_pack_id = _safe_str(item.get("workflow_pack_id"))
    version = _safe_str(item.get("workflow_pack_version")) or _safe_str(item.get("version"))
    flow_status = _safe_str(item.get("flow_status"))
    supportability_status = _safe_str(item.get("supportability_status"))
    updated_at = _safe_str(item.get("updated_at"))
    if task_flow_id is None:
        return None
    if workflow_pack_id is None:
        return None
    if version is None:
        return None
    if flow_status is None:
        return None
    if supportability_status is None:
        return None
    if updated_at is None:
        return None

    lineage = [
        lineage_item
        for lineage_item in (
            _parse_task_flow_lineage(value=value)
            for value in _safe_list(item.get("replacement_lineage"))
        )
        if lineage_item is not None
    ]
    handoff_refs = [
        handoff
        for handoff in (
            _parse_task_flow_handoff(value=value) for value in _safe_list(item.get("handoff_refs"))
        )
        if handoff is not None
    ]
    review_states = {
        str(key): str(value)
        for key, value in _safe_dict(item.get("review_states")).items()
        if key and value
    }
    return AdvisorBriefWorkflowPackTaskFlow(
        task_flow_id=task_flow_id,
        workflow_pack_id=workflow_pack_id,
        version=version,
        flow_status=flow_status,
        current_step_id=_safe_str(item.get("current_step_id")),
        run_refs=run_refs,
        review_states=review_states,
        supportability_status=supportability_status,
        replacement_lineage=lineage,
        handoff_refs=handoff_refs,
        updated_at=updated_at,
    )


def _parse_task_flow_lineage(*, value: Any) -> AdvisorBriefWorkflowPackTaskFlowLineage | None:
    item = _safe_dict(value)
    superseded_run_id = _safe_str(item.get("superseded_run_id"))
    replacement_run_id = _safe_str(item.get("replacement_run_id"))
    review_action_ref = _safe_str(item.get("review_action_ref"))
    reason = _safe_str(item.get("reason"))
    if (
        superseded_run_id is None
        or replacement_run_id is None
        or review_action_ref is None
        or reason is None
    ):
        return None
    return AdvisorBriefWorkflowPackTaskFlowLineage(
        superseded_run_id=superseded_run_id,
        replacement_run_id=replacement_run_id,
        review_action_ref=review_action_ref,
        reason=reason,
    )


def _parse_task_flow_handoff(*, value: Any) -> AdvisorBriefWorkflowPackTaskFlowHandoff | None:
    item = _safe_dict(value)
    handoff_id = _safe_str(item.get("handoff_id"))
    owner_service = _safe_str(item.get("owner_service"))
    status = _safe_str(item.get("status"))
    if handoff_id is None or owner_service is None or status is None:
        return None
    return AdvisorBriefWorkflowPackTaskFlowHandoff(
        handoff_id=handoff_id,
        owner_service=owner_service,
        status=status,
        domain_ref=_safe_str(item.get("domain_ref")),
    )


def _parse_workflow_pack_run_finding(*, value: Any) -> AdvisorBriefWorkflowPackRunFinding | None:
    item = _safe_dict(value)
    finding_id = _safe_str(item.get("finding_id"))
    severity = _safe_str(item.get("severity"))
    summary = _safe_str(item.get("summary"))
    if finding_id is None or severity is None or summary is None:
        return None
    return AdvisorBriefWorkflowPackRunFinding(
        finding_id=finding_id,
        severity=severity,
        summary=summary,
    )


def _normalize_ai_audit(audit: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(audit)
    normalized.setdefault("task_id", _TASK_ID)
    normalized.setdefault("output_label", _EXPECTED_OUTPUT_LABEL)
    normalized.setdefault("provider_mode", "unknown")
    normalized.setdefault("provider_id", None)
    normalized.setdefault("adapter_kind", None)
    normalized.setdefault("model_id", None)
    normalized.setdefault("generated_at", None)
    normalized.setdefault("stubbed", True)
    normalized.setdefault("source_refs", [])
    return normalized


def _build_source_refs(*, workspace: PerformanceWorkspaceResponse) -> list[str]:
    refs = [
        f"lotus-gateway:workbench:{workspace.portfolio_id}:performance-summary:{workspace.period}",
        f"lotus-gateway:workbench:{workspace.portfolio_id}:performance-details:{workspace.period}",
    ]
    if workspace.benchmark_code:
        refs.append(
            f"lotus-performance:benchmark:{workspace.portfolio_id}:{workspace.benchmark_code}:{workspace.period}"
        )
    return refs


def _build_ai_fact_bundle(
    *,
    workspace: PerformanceWorkspaceResponse,
    selected_performance: PerformanceComparativeSummary,
) -> dict[str, Any]:
    contribution = workspace.contribution
    attribution = workspace.attribution
    return {
        "portfolio": _build_ai_portfolio_context(workspace=workspace),
        "period": {
            "period": workspace.period,
            "report_start_date": workspace.report_start_date,
            "report_end_date": workspace.report_end_date,
            "as_of_date": workspace.as_of_date,
            "detail_basis": workspace.detail_basis,
        },
        "benchmark": {
            "benchmark_code": workspace.benchmark_code,
            "benchmark_name": _benchmark_display_label(workspace=workspace),
            "benchmark_return_pct": selected_performance.benchmark_return_pct,
        },
        "performance": {
            "portfolio_return_pct": selected_performance.portfolio_return_pct,
            "benchmark_return_pct": selected_performance.benchmark_return_pct,
            "active_return_pct": selected_performance.active_return_pct,
            "net_cash_flow": selected_performance.net_cash_flow,
            "end_market_value": selected_performance.end_market_value,
            "money_weighted_return_pct": (
                workspace.money_weighted_return.money_weighted_return_pct
                if workspace.money_weighted_return
                else None
            ),
        },
        "contribution": {
            "portfolio_contribution_pct": (
                contribution.portfolio_contribution_pct if contribution else None
            ),
            "coverage_mv_pct": contribution.coverage_mv_pct if contribution else None,
            "top_positions": [
                _build_ai_contribution_position(row=row)
                for row in _positive_position_contributors(contribution=contribution)[:5]
            ],
            "bottom_positions": [
                _build_ai_contribution_position(row=row)
                for row in _negative_position_contributors(contribution=contribution)[:5]
            ],
        },
        "attribution": {
            "active_return_pct": attribution.active_return_pct if attribution else None,
            "sum_of_effects_pct": attribution.sum_of_effects_pct if attribution else None,
            "residual_pct": attribution.residual_pct if attribution else None,
            "top_effects": _top_attribution_effects(attribution=attribution),
        },
        "supportability": [
            item.model_dump(mode="json") for item in _build_supportability(workspace=workspace)
        ],
        "warnings": workspace.warnings,
        "partial_failures": [item.model_dump(mode="json") for item in workspace.partial_failures],
    }


def _build_ai_portfolio_context(
    *,
    workspace: PerformanceWorkspaceResponse,
) -> dict[str, Any]:
    return {
        "portfolio_id": workspace.portfolio_id,
        "display_label": _portfolio_display_label(workspace=workspace),
        "base_currency": workspace.portfolio.base_currency,
        "booking_center_code": workspace.portfolio.booking_center_code,
        "client_id": workspace.portfolio.client_id,
    }


def _build_ai_contribution_position(
    *,
    row: ContributionPositionView,
) -> dict[str, Any]:
    return {
        "display_label": _normalize_position_label(row.position_id),
        "contribution_pct": row.contribution_pct,
        "weight_avg_pct": row.weight_avg_pct,
        "total_return_pct": row.total_return_pct,
        "local_contribution_pct": row.local_contribution_pct,
        "fx_contribution_pct": row.fx_contribution_pct,
    }


def _build_source_summary(
    *,
    workspace: PerformanceWorkspaceResponse,
    selected_performance: PerformanceComparativeSummary,
) -> str:
    portfolio_return = _format_pct(selected_performance.portfolio_return_pct)
    benchmark_return = _format_pct(selected_performance.benchmark_return_pct)
    active_return = _format_pct(selected_performance.active_return_pct)
    if (
        selected_performance.portfolio_return_pct is None
        and selected_performance.benchmark_return_pct is None
    ):
        return (
            "No source-backed advisor brief can be generated from the current performance "
            "selection."
        )
    return (
        f"{workspace.period} portfolio return for {_portfolio_display_label(workspace=workspace)} "
        f"is {portfolio_return} versus "
        f"{_benchmark_display_label(workspace=workspace) or 'benchmark'} {benchmark_return}, "
        f"with active return {active_return}."
    )


def _extract_ai_summary(
    *,
    ai_payload: dict[str, Any],
    structured_output: dict[str, Any] | None = None,
) -> str | None:
    output_payload = structured_output or _safe_dict(
        _safe_dict(ai_payload.get("result")).get("structured_output")
    )
    summary = output_payload.get("grounded_summary")
    if isinstance(summary, str) and summary.strip():
        return summary.strip()
    result = _safe_dict(ai_payload.get("result"))
    message = result.get("message")
    if isinstance(message, str) and message.strip():
        return message.strip()
    return None


def _extract_ai_talking_points(
    *,
    structured_output: dict[str, Any],
    route: str,
) -> list[AdvisorBriefNarrativeItem]:
    return [
        item
        for item in (
            _parse_ai_narrative_item(value=value, route=route, default_mode="summary")
            for value in _safe_list(structured_output.get("talking_points"))
        )
        if item is not None
    ]


def _extract_ai_risks(
    *,
    structured_output: dict[str, Any],
    route: str,
) -> list[AdvisorBriefNarrativeItem]:
    return [
        item
        for item in (
            _parse_ai_narrative_item(value=value, route=route, default_mode="analysis")
            for value in _safe_list(structured_output.get("risks_and_exceptions"))
        )
        if item is not None
    ]


def _extract_ai_recommended_actions(
    *,
    structured_output: dict[str, Any],
    route: str,
) -> list[AdvisorBriefActionItem]:
    actions: list[AdvisorBriefActionItem] = []
    for value in _safe_list(structured_output.get("recommended_actions")):
        item = _safe_dict(value)
        label = item.get("label")
        if not isinstance(label, str) or not label.strip():
            continue
        actions.append(
            AdvisorBriefActionItem(
                label=label.strip(),
                target_mode=_infer_target_mode_from_text(label),
                route=route,
            )
        )
    return actions


def _parse_ai_narrative_item(
    *,
    value: Any,
    route: str,
    default_mode: str,
) -> AdvisorBriefNarrativeItem | None:
    item = _safe_dict(value)
    headline = item.get("headline")
    detail = item.get("detail")
    if not isinstance(headline, str) or not headline.strip():
        return None
    if not isinstance(detail, str) or not detail.strip():
        return None
    tone = _normalize_narrative_tone(item.get("tone"))
    evidence_refs = [
        ref
        for ref in (
            _parse_ai_evidence_ref(value=ref_value, route=route, default_mode=default_mode)
            for ref_value in _safe_list(item.get("evidence_refs"))
        )
        if ref is not None
    ]
    if not evidence_refs:
        evidence_refs = [
            AdvisorBriefEvidenceRef(
                metric_label="Advisor Brief",
                metric_value="Source-Grounded",
                source_surface="performance.advisor_brief",
                target_mode=default_mode,
                route=route,
            )
        ]
    return AdvisorBriefNarrativeItem(
        headline=headline.strip(),
        detail=detail.strip(),
        tone=tone,
        evidence_refs=evidence_refs,
    )


def _parse_ai_evidence_ref(
    *,
    value: Any,
    route: str,
    default_mode: str,
) -> AdvisorBriefEvidenceRef | None:
    item = _safe_dict(value)
    metric_label = item.get("metric_label")
    metric_value = item.get("metric_value")
    if not isinstance(metric_label, str) or not metric_label.strip():
        return None
    if not isinstance(metric_value, str) or not metric_value.strip():
        return None
    source_ref = _safe_str(item.get("source_ref")) or _safe_str(item.get("source_surface"))
    source_surface = (
        _infer_source_surface(source_ref) if source_ref else "performance.advisor_brief"
    )
    return AdvisorBriefEvidenceRef(
        metric_label=metric_label.strip(),
        metric_value=metric_value.strip(),
        source_surface=source_surface,
        target_mode=_infer_target_mode(source_surface=source_surface, default_mode=default_mode),
        route=route,
    )


def _normalize_narrative_tone(value: Any) -> AdvisorBriefTone:
    if value == AdvisorBriefTone.POSITIVE.value:
        return AdvisorBriefTone.POSITIVE
    if value == AdvisorBriefTone.WARNING.value:
        return AdvisorBriefTone.WARNING
    return AdvisorBriefTone.NEUTRAL


def _infer_target_mode(*, source_surface: str, default_mode: str) -> str:
    return "summary" if source_surface == "performance.return_path" else default_mode


def _infer_target_mode_from_text(label: str) -> str:
    normalized = label.strip().lower()
    if "return" in normalized:
        return "summary"
    return "analysis"


def _infer_source_surface(source_ref: str | None) -> str:
    if not source_ref:
        return "performance.advisor_brief"
    normalized = source_ref.lower()
    if "performance-summary" in normalized:
        return "performance.return_path"
    if "performance-details" in normalized or "contribution" in normalized:
        return "performance.contribution"
    if "benchmark" in normalized or "attribution" in normalized:
        return "performance.attribution"
    return "performance.advisor_brief"


def _build_source_talking_points(
    *,
    workspace: PerformanceWorkspaceResponse,
    selected_performance: PerformanceComparativeSummary,
) -> list[AdvisorBriefNarrativeItem]:
    points: list[AdvisorBriefNarrativeItem] = []
    if (
        selected_performance.portfolio_return_pct is not None
        or selected_performance.benchmark_return_pct is not None
        or selected_performance.active_return_pct is not None
    ):
        points.append(
            AdvisorBriefNarrativeItem(
                headline=(
                    f"Portfolio return is {_format_pct(selected_performance.portfolio_return_pct)} "
                    f"versus benchmark {_format_pct(selected_performance.benchmark_return_pct)}."
                ),
                detail=(
                    f"Active return is {_format_pct(selected_performance.active_return_pct)} "
                    f"for the selected {workspace.period} period."
                ),
                tone=(
                    AdvisorBriefTone.POSITIVE
                    if (selected_performance.active_return_pct or 0) >= 0
                    else AdvisorBriefTone.WARNING
                ),
                evidence_refs=[
                    _summary_evidence_ref(
                        label="Active Return",
                        value=_format_pct(selected_performance.active_return_pct),
                        portfolio_id=workspace.portfolio_id,
                        period=workspace.period,
                        basis=workspace.detail_basis,
                        benchmark_code=workspace.benchmark_code,
                    )
                ],
            )
        )

    top_position = _positive_position_contributors(contribution=workspace.contribution)[:1]
    if top_position:
        points.append(
            AdvisorBriefNarrativeItem(
                headline=(
                    f"Top contributor is {_normalize_position_label(top_position[0].position_id)}."
                ),
                detail=(
                    f"{_normalize_position_label(top_position[0].position_id)} contributed "
                    f"{_format_pct(top_position[0].contribution_pct)} with return "
                    f"{_format_pct(top_position[0].total_return_pct)}."
                ),
                tone=AdvisorBriefTone.POSITIVE,
                evidence_refs=[
                    _analysis_evidence_ref(
                        label="Top Contributor",
                        value=_normalize_position_label(top_position[0].position_id),
                        portfolio_id=workspace.portfolio_id,
                        period=workspace.period,
                        basis=workspace.detail_basis,
                        benchmark_code=workspace.benchmark_code,
                    )
                ],
            )
        )

    bottom_position = _negative_position_contributors(contribution=workspace.contribution)[:1]
    if bottom_position:
        points.append(
            AdvisorBriefNarrativeItem(
                headline=(
                    f"Top detractor is {_normalize_position_label(bottom_position[0].position_id)}."
                ),
                detail=(
                    f"{_normalize_position_label(bottom_position[0].position_id)} contributed "
                    f"{_format_pct(bottom_position[0].contribution_pct)} with return "
                    f"{_format_pct(bottom_position[0].total_return_pct)}."
                ),
                tone=AdvisorBriefTone.WARNING,
                evidence_refs=[
                    _analysis_evidence_ref(
                        label="Top Detractor",
                        value=_normalize_position_label(bottom_position[0].position_id),
                        portfolio_id=workspace.portfolio_id,
                        period=workspace.period,
                        basis=workspace.detail_basis,
                        benchmark_code=workspace.benchmark_code,
                    )
                ],
            )
        )

    return points


def _build_recommended_actions(
    *,
    workspace: PerformanceWorkspaceResponse,
) -> list[AdvisorBriefActionItem]:
    return [
        AdvisorBriefActionItem(
            label="Open Return Path",
            target_mode="summary",
            route=_route_query(
                portfolio_id=workspace.portfolio_id,
                period=workspace.period,
                basis=workspace.detail_basis,
                benchmark_code=workspace.benchmark_code,
            ),
        ),
        AdvisorBriefActionItem(
            label="Open Contribution",
            target_mode="analysis",
            route=_route_query(
                portfolio_id=workspace.portfolio_id,
                period=workspace.period,
                basis=workspace.detail_basis,
                benchmark_code=workspace.benchmark_code,
            ),
        ),
        AdvisorBriefActionItem(
            label="Open Attribution",
            target_mode="analysis",
            route=_route_query(
                portfolio_id=workspace.portfolio_id,
                period=workspace.period,
                basis=workspace.detail_basis,
                benchmark_code=workspace.benchmark_code,
            ),
        ),
    ]


def _build_risks_and_exceptions(
    *,
    workspace: PerformanceWorkspaceResponse,
    supportability: list[AdvisorBriefSupportabilityItem],
) -> list[AdvisorBriefNarrativeItem]:
    risks: list[AdvisorBriefNarrativeItem] = []
    for item in supportability:
        if item.tone not in {"warn", "danger"}:
            continue
        if item.label == "Advisor Brief":
            continue
        risks.append(
            AdvisorBriefNarrativeItem(
                headline=f"{item.label} is {item.value.lower()}.",
                detail=item.reason or "Source detail is not fully available for this selection.",
                tone=AdvisorBriefTone.WARNING,
                evidence_refs=[
                    AdvisorBriefEvidenceRef(
                        metric_label=item.label,
                        metric_value=item.value,
                        source_surface=f"performance.{item.label.lower().replace(' ', '_')}",
                        target_mode="analysis"
                        if item.label in {"Contribution", "Attribution"}
                        else "summary",
                        route=_route_query(
                            portfolio_id=workspace.portfolio_id,
                            period=workspace.period,
                            basis=workspace.detail_basis,
                            benchmark_code=workspace.benchmark_code,
                        ),
                    )
                ],
            )
        )
    return risks


def _build_source_metrics(
    *,
    workspace: PerformanceWorkspaceResponse,
    selected_performance: PerformanceComparativeSummary,
) -> list[AdvisorBriefSourceMetric]:
    route = _route_query(
        portfolio_id=workspace.portfolio_id,
        period=workspace.period,
        basis=workspace.detail_basis,
        benchmark_code=workspace.benchmark_code,
    )
    return [
        AdvisorBriefSourceMetric(
            label="Portfolio Return",
            value=_format_pct(selected_performance.portfolio_return_pct),
            support_label=f"{workspace.period} {workspace.detail_basis}",
            target_mode="summary",
            route=route,
            state=workspace.capabilities.summary_kpis.state,
        ),
        AdvisorBriefSourceMetric(
            label="Benchmark Return",
            value=_format_pct(selected_performance.benchmark_return_pct),
            support_label=workspace.benchmark_code or "Unassigned",
            target_mode="summary",
            route=route,
            state=workspace.capabilities.benchmark_comparison.state,
        ),
        AdvisorBriefSourceMetric(
            label="Active Return",
            value=_format_pct(selected_performance.active_return_pct),
            support_label=f"{workspace.report_start_date} to {workspace.report_end_date}",
            target_mode="summary",
            route=route,
            state=workspace.capabilities.benchmark_comparison.state,
        ),
        AdvisorBriefSourceMetric(
            label="Net Flow",
            value=_format_currency(selected_performance.net_cash_flow),
            support_label=workspace.portfolio.base_currency or "Portfolio currency",
            target_mode="summary",
            route=route,
            state=workspace.capabilities.summary_kpis.state,
        ),
        AdvisorBriefSourceMetric(
            label="Ending MV",
            value=_format_currency(selected_performance.end_market_value),
            support_label=workspace.report_end_date,
            target_mode="summary",
            route=route,
            state=workspace.capabilities.summary_kpis.state,
        ),
    ]


def _build_supportability(
    *,
    workspace: PerformanceWorkspaceResponse,
) -> list[AdvisorBriefSupportabilityItem]:
    items = [
        _to_supportability_item("Portfolio", workspace.capabilities.summary_kpis.state, None),
        _to_supportability_item(
            "Return History",
            workspace.capabilities.return_path.state,
            workspace.capabilities.return_path.reason,
        ),
        _to_supportability_item(
            "Contribution",
            workspace.capabilities.contribution_detail.state,
            workspace.capabilities.contribution_detail.reason,
        ),
        _to_supportability_item(
            "Attribution",
            workspace.capabilities.attribution_detail.state,
            workspace.capabilities.attribution_detail.reason,
        ),
    ]
    advisor_brief_value = "Ready"
    advisor_brief_tone = "success"
    if any(item.tone == "danger" for item in items[:2]):
        advisor_brief_value = "Unavailable"
        advisor_brief_tone = "danger"
    elif any(item.tone in {"warn", "danger"} for item in items):
        advisor_brief_value = "Partial"
        advisor_brief_tone = "warn"

    items.append(
        AdvisorBriefSupportabilityItem(
            label="Advisor Brief",
            value=advisor_brief_value,
            tone=advisor_brief_tone,
            reason=None,
        )
    )
    return items


def _to_supportability_item(
    label: str,
    state: str,
    reason: str | None,
) -> AdvisorBriefSupportabilityItem:
    normalized_state = state.strip().lower()
    if normalized_state in {"ready", "supported"}:
        return AdvisorBriefSupportabilityItem(
            label=label,
            value="Ready",
            tone="success",
            reason=reason,
        )
    if normalized_state == "partial":
        return AdvisorBriefSupportabilityItem(
            label=label,
            value="Partial",
            tone="warn",
            reason=reason,
        )
    return AdvisorBriefSupportabilityItem(
        label=label,
        value="Unavailable",
        tone="danger",
        reason=reason,
    )


def _resolve_status(
    *,
    workspace: PerformanceWorkspaceResponse,
    supportability: list[AdvisorBriefSupportabilityItem],
) -> AdvisorBriefStatus:
    if workspace.capabilities.summary_kpis.state == "unavailable":
        return AdvisorBriefStatus.UNAVAILABLE
    if any(item.tone in {"warn", "danger"} for item in supportability):
        return AdvisorBriefStatus.PARTIAL
    return AdvisorBriefStatus.READY


def _positive_position_contributors(
    *,
    contribution: ContributionSummaryView | None,
) -> list[ContributionPositionView]:
    if not contribution:
        return []
    return sorted(
        [row for row in contribution.position_rows if row.contribution_pct > 0],
        key=lambda row: row.contribution_pct,
        reverse=True,
    )


def _negative_position_contributors(
    *,
    contribution: ContributionSummaryView | None,
) -> list[ContributionPositionView]:
    if not contribution:
        return []
    return sorted(
        [row for row in contribution.position_rows if row.contribution_pct < 0],
        key=lambda row: row.contribution_pct,
    )


def _top_attribution_effects(
    *,
    attribution: AttributionSummaryView | None,
) -> list[dict[str, Any]]:
    if not attribution:
        return []
    rows = [
        row
        for level in attribution.levels
        for row in level.rows
        if row.total_effect_pct is not None
    ]
    return [
        {
            "segment_label": row.key_label,
            "total_effect_pct": row.total_effect_pct,
            "allocation_pct": row.allocation_pct,
            "selection_pct": row.selection_pct,
            "interaction_pct": row.interaction_pct,
            "portfolio_weight_avg_pct": row.portfolio_weight_avg_pct,
            "benchmark_weight_avg_pct": row.benchmark_weight_avg_pct,
            "portfolio_return_pct": row.portfolio_return_pct,
            "benchmark_return_pct": row.benchmark_return_pct,
        }
        for row in sorted(
            rows,
            key=lambda row: abs(row.total_effect_pct),
            reverse=True,
        )[:5]
    ]


def _summary_evidence_ref(
    *,
    label: str,
    value: str,
    portfolio_id: str,
    period: str,
    basis: str,
    benchmark_code: str | None,
) -> AdvisorBriefEvidenceRef:
    return AdvisorBriefEvidenceRef(
        metric_label=label,
        metric_value=value,
        source_surface="performance.return_path",
        target_mode="summary",
        route=_route_query(
            portfolio_id=portfolio_id,
            period=period,
            basis=basis,
            benchmark_code=benchmark_code,
        ),
    )


def _analysis_evidence_ref(
    *,
    label: str,
    value: str,
    portfolio_id: str,
    period: str,
    basis: str,
    benchmark_code: str | None,
) -> AdvisorBriefEvidenceRef:
    return AdvisorBriefEvidenceRef(
        metric_label=label,
        metric_value=value,
        source_surface="performance.contribution",
        target_mode="analysis",
        route=_route_query(
            portfolio_id=portfolio_id,
            period=period,
            basis=basis,
            benchmark_code=benchmark_code,
        ),
    )


def _route_query(
    *,
    portfolio_id: str,
    period: str,
    basis: str,
    benchmark_code: str | None,
) -> str:
    route = f"/performance?portfolioId={portfolio_id}&period={period}&detailBasis={basis}"
    if benchmark_code:
        route += f"&benchmark={benchmark_code}"
    return route


def _format_pct(value: Any) -> str:
    if value is None:
        return "N/A"
    return f"{quantize_performance(value):.2f}%"


def _format_currency(value: Any) -> str:
    if value is None:
        return "N/A"
    return f"${quantize_money(value):,.0f}"


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _safe_str(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _safe_int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return max(value, 0)
    return 0


def _safe_error_detail(payload: dict[str, Any]) -> str:
    detail = payload.get("detail")
    if isinstance(detail, str) and detail.strip():
        return detail.strip()
    return "lotus-ai task execution did not return a completed advisor brief."


def _safe_execution_detail(payload: dict[str, Any]) -> str | None:
    result = _safe_dict(payload.get("result"))
    message = _safe_str(result.get("message"))
    if message is not None:
        return message
    audit = _safe_dict(payload.get("audit"))
    detail = _safe_str(audit.get("detail"))
    if detail is not None:
        return detail
    return None


def _normalize_position_label(position_id: str) -> str:
    display_label = position_id.rsplit(":", 1)[-1].strip()
    for prefix in ("FO_EQ_", "FO_FI_", "FO_CASH_", "FO_ALT_", "FO_FX_"):
        if display_label.startswith(prefix):
            display_label = display_label[len(prefix) :]
            break
    return display_label.replace("_", " ").strip() or position_id


def _portfolio_display_label(*, workspace: PerformanceWorkspaceResponse) -> str:
    return _normalize_position_label(workspace.portfolio.portfolio_id)


def _benchmark_display_label(*, workspace: PerformanceWorkspaceResponse) -> str | None:
    if not workspace.benchmark_code:
        return None
    for option in workspace.benchmark_options:
        if option.benchmark_code == workspace.benchmark_code:
            return option.benchmark_name.strip() or workspace.benchmark_code
    return workspace.benchmark_code
