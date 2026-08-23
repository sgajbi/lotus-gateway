from __future__ import annotations

from dataclasses import dataclass

from app.contracts.advisor_brief import (
    AdvisorBriefActionItem,
    AdvisorBriefEvidenceRef,
    AdvisorBriefNarrativeItem,
    AdvisorBriefSourceMetric,
    AdvisorBriefStatus,
    AdvisorBriefSupportabilityItem,
)
from app.contracts.performance_workspace import (
    PerformanceComparativeSummary,
    PerformanceWorkspaceResponse,
)
from app.services.advisor_brief_source_fact_bundle import build_advisor_brief_ai_fact_bundle
from app.services.advisor_brief_source_formatting import (
    advisor_brief_route_query,
    advisor_brief_summary_evidence_ref,
)
from app.services.advisor_brief_source_metrics import build_return_source_metrics
from app.services.advisor_brief_source_narrative import (
    build_recommended_actions,
    build_risks_and_exceptions,
    build_source_summary,
    build_source_talking_points,
)
from app.services.advisor_brief_supportability import (
    build_advisor_brief_source_supportability,
    resolve_advisor_brief_source_status,
)

__all__ = [
    "AdvisorBriefSourceContext",
    "build_advisor_brief_ai_fact_bundle",
    "build_advisor_brief_source_context",
    "build_advisor_brief_source_metrics",
    "build_advisor_brief_source_route",
    "build_advisor_brief_summary_evidence_ref",
]


@dataclass(frozen=True)
class AdvisorBriefSourceContext:
    workspace: PerformanceWorkspaceResponse
    selected_performance: PerformanceComparativeSummary
    source_refs: list[str]
    supportability: list[AdvisorBriefSupportabilityItem]
    status: AdvisorBriefStatus
    summary: str
    talking_points: list[AdvisorBriefNarrativeItem]
    recommended_actions: list[AdvisorBriefActionItem]
    risks_and_exceptions: list[AdvisorBriefNarrativeItem]


def build_advisor_brief_source_context(
    *,
    workspace: PerformanceWorkspaceResponse,
    detail_basis: str,
) -> AdvisorBriefSourceContext:
    selected_performance = (
        workspace.net_performance if detail_basis.upper() == "NET" else workspace.gross_performance
    )
    supportability = build_advisor_brief_source_supportability(workspace=workspace)
    return AdvisorBriefSourceContext(
        workspace=workspace,
        selected_performance=selected_performance,
        source_refs=_build_source_refs(workspace=workspace),
        supportability=supportability,
        status=resolve_advisor_brief_source_status(
            workspace=workspace,
            supportability=supportability,
        ),
        summary=_build_source_summary(
            workspace=workspace,
            selected_performance=selected_performance,
        ),
        talking_points=_build_source_talking_points(
            workspace=workspace,
            selected_performance=selected_performance,
        ),
        recommended_actions=_build_recommended_actions(workspace=workspace),
        risks_and_exceptions=_build_risks_and_exceptions(
            workspace=workspace,
            supportability=supportability,
        ),
    )


def build_advisor_brief_source_metrics(
    *,
    source_context: AdvisorBriefSourceContext,
) -> list[AdvisorBriefSourceMetric]:
    workspace = source_context.workspace
    route = build_advisor_brief_source_route(source_context=source_context)
    return build_return_source_metrics(
        workspace=workspace,
        selected_performance=source_context.selected_performance,
        route=route,
    )


def build_advisor_brief_source_route(*, source_context: AdvisorBriefSourceContext) -> str:
    workspace = source_context.workspace
    return advisor_brief_route_query(
        portfolio_id=workspace.portfolio_id,
        period=workspace.period,
        basis=workspace.detail_basis,
        benchmark_code=workspace.benchmark_code,
        requested_as_of_date=workspace.requested_as_of_date,
        requested_reporting_currency=workspace.requested_reporting_currency,
    )


def build_advisor_brief_summary_evidence_ref(
    *,
    label: str,
    value: str,
    source_context: AdvisorBriefSourceContext,
) -> AdvisorBriefEvidenceRef:
    workspace = source_context.workspace
    return advisor_brief_summary_evidence_ref(
        label=label,
        value=value,
        portfolio_id=workspace.portfolio_id,
        period=workspace.period,
        basis=workspace.detail_basis,
        benchmark_code=workspace.benchmark_code,
        requested_as_of_date=workspace.requested_as_of_date,
        requested_reporting_currency=workspace.requested_reporting_currency,
    )


def _build_source_refs(*, workspace: PerformanceWorkspaceResponse) -> list[str]:
    refs = [
        f"lotus-gateway:workbench:{workspace.portfolio_id}:performance-summary:{workspace.period}",
        f"lotus-gateway:workbench:{workspace.portfolio_id}:performance-details:{workspace.period}",
    ]
    if workspace.benchmark_code:
        refs.append(
            "lotus-performance:benchmark:"
            f"{workspace.portfolio_id}:{workspace.benchmark_code}:{workspace.period}"
        )
    return refs


def _build_source_summary(
    *,
    workspace: PerformanceWorkspaceResponse,
    selected_performance: PerformanceComparativeSummary,
) -> str:
    return build_source_summary(
        workspace=workspace,
        selected_performance=selected_performance,
    )


def _build_source_talking_points(
    *,
    workspace: PerformanceWorkspaceResponse,
    selected_performance: PerformanceComparativeSummary,
) -> list[AdvisorBriefNarrativeItem]:
    return build_source_talking_points(
        workspace=workspace,
        selected_performance=selected_performance,
    )


def _build_recommended_actions(
    *,
    workspace: PerformanceWorkspaceResponse,
) -> list[AdvisorBriefActionItem]:
    return build_recommended_actions(workspace=workspace)


def _build_risks_and_exceptions(
    *,
    workspace: PerformanceWorkspaceResponse,
    supportability: list[AdvisorBriefSupportabilityItem],
) -> list[AdvisorBriefNarrativeItem]:
    return build_risks_and_exceptions(
        workspace=workspace,
        supportability=supportability,
    )
