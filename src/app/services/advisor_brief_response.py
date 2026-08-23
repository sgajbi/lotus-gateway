from __future__ import annotations

from app.contracts.advisor_brief import AdvisorBriefResponse
from app.services.advisor_brief_narrative import AdvisorBriefNarrativeState
from app.services.advisor_brief_runtime_context import AdvisorBriefRuntimeContext
from app.services.advisor_brief_source import (
    AdvisorBriefSourceContext,
    build_advisor_brief_source_metrics,
)


def assemble_advisor_brief_response(
    *,
    correlation_id: str,
    source_context: AdvisorBriefSourceContext,
    narrative_state: AdvisorBriefNarrativeState,
    runtime_context: AdvisorBriefRuntimeContext,
) -> AdvisorBriefResponse:
    workspace = source_context.workspace
    return AdvisorBriefResponse(
        correlation_id=correlation_id,
        contract_version=workspace.contract_version,
        portfolio_id=workspace.portfolio_id,
        portfolio=workspace.portfolio,
        as_of_date=workspace.effective_as_of_date,
        requested_as_of_date=workspace.requested_as_of_date,
        effective_as_of_date=workspace.effective_as_of_date,
        period=workspace.period,
        report_start_date=workspace.report_start_date,
        report_end_date=workspace.report_end_date,
        detail_basis=workspace.detail_basis,
        chart_frequency=workspace.chart_frequency,
        contribution_dimension=workspace.contribution_dimension,
        attribution_dimension=workspace.attribution_dimension,
        benchmark_code=workspace.benchmark_code,
        requested_reporting_currency=workspace.requested_reporting_currency,
        effective_reporting_currency=workspace.effective_reporting_currency,
        reporting_currency_state=workspace.reporting_currency_state,
        status=narrative_state.status,
        summary=narrative_state.summary,
        talking_points=narrative_state.talking_points,
        recommended_actions=narrative_state.recommended_actions,
        risks_and_exceptions=narrative_state.risks_and_exceptions,
        source_metrics=build_advisor_brief_source_metrics(source_context=source_context),
        supportability=source_context.supportability,
        ai_surface_supportability=runtime_context.ai_surface_supportability,
        advisory_supportability=runtime_context.advisory_supportability,
        ai_audit=narrative_state.ai_audit,
        ai_evidence=narrative_state.ai_evidence,
        workflow_pack_run=runtime_context.workflow_pack_run,
        workflow_pack_task_flow=runtime_context.workflow_pack_task_flow,
        warnings=workspace.warnings,
        partial_failures=workspace.partial_failures,
    )


def with_advisor_brief_runtime_context(
    brief: AdvisorBriefResponse,
    runtime_context: AdvisorBriefRuntimeContext,
) -> AdvisorBriefResponse:
    return brief.model_copy(
        update={
            "workflow_pack_run": runtime_context.workflow_pack_run,
            "workflow_pack_task_flow": runtime_context.workflow_pack_task_flow,
            "ai_surface_supportability": runtime_context.ai_surface_supportability,
            "advisory_supportability": runtime_context.advisory_supportability,
        }
    )
