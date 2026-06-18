from __future__ import annotations

from dataclasses import dataclass

from app.contracts.advisor_brief import (
    AdvisorBriefActionItem,
    AdvisorBriefEvidenceRef,
    AdvisorBriefNarrativeItem,
    AdvisorBriefSourceMetric,
    AdvisorBriefStatus,
    AdvisorBriefSupportabilityItem,
    AdvisorBriefTone,
)
from app.contracts.performance_contribution import (
    ContributionPositionView,
    ContributionSummaryView,
)
from app.contracts.performance_workspace import (
    PerformanceComparativeSummary,
    PerformanceWorkspaceResponse,
)
from app.services.advisor_brief_source_contributors import (
    negative_position_contributors,
    positive_position_contributors,
)
from app.services.advisor_brief_source_fact_bundle import build_advisor_brief_ai_fact_bundle
from app.services.advisor_brief_source_formatting import (
    advisor_brief_analysis_evidence_ref,
    advisor_brief_benchmark_display_label,
    advisor_brief_portfolio_display_label,
    advisor_brief_route_query,
    advisor_brief_summary_evidence_ref,
    format_advisor_brief_currency,
    format_advisor_brief_pct,
    normalize_advisor_brief_position_label,
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
    supportability = _build_supportability(workspace=workspace)
    return AdvisorBriefSourceContext(
        workspace=workspace,
        selected_performance=selected_performance,
        source_refs=_build_source_refs(workspace=workspace),
        supportability=supportability,
        status=_resolve_status(workspace=workspace, supportability=supportability),
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
    return _build_return_source_metrics(
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
    portfolio_return = format_advisor_brief_pct(selected_performance.portfolio_return_pct)
    benchmark_return = format_advisor_brief_pct(selected_performance.benchmark_return_pct)
    active_return = format_advisor_brief_pct(selected_performance.active_return_pct)
    if (
        selected_performance.portfolio_return_pct is None
        and selected_performance.benchmark_return_pct is None
    ):
        return (
            "No source-backed advisor brief can be generated from the current performance "
            "selection."
        )
    return (
        f"{workspace.period} portfolio return for "
        f"{advisor_brief_portfolio_display_label(workspace=workspace)} "
        f"is {portfolio_return} versus "
        f"{advisor_brief_benchmark_display_label(workspace=workspace) or 'benchmark'} "
        f"{benchmark_return}, "
        f"with active return {active_return}."
    )


def _build_source_talking_points(
    *,
    workspace: PerformanceWorkspaceResponse,
    selected_performance: PerformanceComparativeSummary,
) -> list[AdvisorBriefNarrativeItem]:
    points: list[AdvisorBriefNarrativeItem] = []
    return_talking_point = _build_return_talking_point(
        workspace=workspace,
        selected_performance=selected_performance,
    )
    if return_talking_point is not None:
        points.append(return_talking_point)
    _add_position_talking_points(points=points, workspace=workspace)
    return points


def _add_position_talking_points(
    *,
    points: list[AdvisorBriefNarrativeItem],
    workspace: PerformanceWorkspaceResponse,
) -> None:
    top_position = _first_positive_position_contributor(workspace.contribution)
    if top_position is not None:
        points.append(
            _build_position_talking_point(
                position=top_position,
                workspace=workspace,
                headline_prefix="Top contributor",
                label="Top Contributor",
                tone=AdvisorBriefTone.POSITIVE,
            )
        )
    bottom_position = _first_negative_position_contributor(workspace.contribution)
    if bottom_position is not None:
        points.append(
            _build_position_talking_point(
                position=bottom_position,
                workspace=workspace,
                headline_prefix="Top detractor",
                label="Top Detractor",
                tone=AdvisorBriefTone.WARNING,
            )
        )


def _build_return_talking_point(
    *,
    workspace: PerformanceWorkspaceResponse,
    selected_performance: PerformanceComparativeSummary,
) -> AdvisorBriefNarrativeItem | None:
    if (
        selected_performance.portfolio_return_pct is None
        and selected_performance.benchmark_return_pct is None
        and selected_performance.active_return_pct is None
    ):
        return None
    return AdvisorBriefNarrativeItem(
        headline=(
            "Portfolio return is "
            f"{format_advisor_brief_pct(selected_performance.portfolio_return_pct)} "
            "versus benchmark "
            f"{format_advisor_brief_pct(selected_performance.benchmark_return_pct)}."
        ),
        detail=(
            f"Active return is {format_advisor_brief_pct(selected_performance.active_return_pct)} "
            f"for the selected {workspace.period} period."
        ),
        tone=(
            AdvisorBriefTone.POSITIVE
            if (selected_performance.active_return_pct or 0) >= 0
            else AdvisorBriefTone.WARNING
        ),
        evidence_refs=[
            advisor_brief_summary_evidence_ref(
                label="Active Return",
                value=format_advisor_brief_pct(selected_performance.active_return_pct),
                portfolio_id=workspace.portfolio_id,
                period=workspace.period,
                basis=workspace.detail_basis,
                benchmark_code=workspace.benchmark_code,
            )
        ],
    )


def _first_positive_position_contributor(
    contribution: ContributionSummaryView | None,
) -> ContributionPositionView | None:
    contributors = positive_position_contributors(contribution=contribution)
    return contributors[0] if contributors else None


def _first_negative_position_contributor(
    contribution: ContributionSummaryView | None,
) -> ContributionPositionView | None:
    contributors = negative_position_contributors(contribution=contribution)
    return contributors[0] if contributors else None


def _build_position_talking_point(
    *,
    position: ContributionPositionView,
    workspace: PerformanceWorkspaceResponse,
    headline_prefix: str,
    label: str,
    tone: AdvisorBriefTone,
) -> AdvisorBriefNarrativeItem:
    position_label = normalize_advisor_brief_position_label(position.position_id)
    return AdvisorBriefNarrativeItem(
        headline=f"{headline_prefix} is {position_label}.",
        detail=(
            f"{position_label} contributed "
            f"{format_advisor_brief_pct(position.contribution_pct)} "
            f"with return {format_advisor_brief_pct(position.total_return_pct)}."
        ),
        tone=tone,
        evidence_refs=[
            advisor_brief_analysis_evidence_ref(
                label=label,
                value=position_label,
                portfolio_id=workspace.portfolio_id,
                period=workspace.period,
                basis=workspace.detail_basis,
                benchmark_code=workspace.benchmark_code,
            )
        ],
    )


def _build_recommended_actions(
    *,
    workspace: PerformanceWorkspaceResponse,
) -> list[AdvisorBriefActionItem]:
    route = advisor_brief_route_query(
        portfolio_id=workspace.portfolio_id,
        period=workspace.period,
        basis=workspace.detail_basis,
        benchmark_code=workspace.benchmark_code,
    )
    return [
        AdvisorBriefActionItem(label="Open Return Path", target_mode="summary", route=route),
        AdvisorBriefActionItem(label="Open Contribution", target_mode="analysis", route=route),
        AdvisorBriefActionItem(label="Open Attribution", target_mode="analysis", route=route),
    ]


def _build_risks_and_exceptions(
    *,
    workspace: PerformanceWorkspaceResponse,
    supportability: list[AdvisorBriefSupportabilityItem],
) -> list[AdvisorBriefNarrativeItem]:
    risks: list[AdvisorBriefNarrativeItem] = []
    for item in supportability:
        if item.tone not in {"warn", "danger"} or item.label == "Advisor Brief":
            continue
        risks.append(_build_supportability_risk(workspace=workspace, supportability_item=item))
    return risks


def _build_supportability_risk(
    *,
    workspace: PerformanceWorkspaceResponse,
    supportability_item: AdvisorBriefSupportabilityItem,
) -> AdvisorBriefNarrativeItem:
    return AdvisorBriefNarrativeItem(
        headline=f"{supportability_item.label} is {supportability_item.value.lower()}.",
        detail=(
            supportability_item.reason or "Source detail is not fully available for this selection."
        ),
        tone=AdvisorBriefTone.WARNING,
        evidence_refs=[
            AdvisorBriefEvidenceRef(
                metric_label=supportability_item.label,
                metric_value=supportability_item.value,
                source_surface=f"performance.{supportability_item.label.lower().replace(' ', '_')}",
                target_mode=(
                    "analysis"
                    if supportability_item.label in {"Contribution", "Attribution"}
                    else "summary"
                ),
                route=advisor_brief_route_query(
                    portfolio_id=workspace.portfolio_id,
                    period=workspace.period,
                    basis=workspace.detail_basis,
                    benchmark_code=workspace.benchmark_code,
                ),
            )
        ],
    )


def _build_return_source_metrics(
    *,
    workspace: PerformanceWorkspaceResponse,
    selected_performance: PerformanceComparativeSummary,
    route: str,
) -> list[AdvisorBriefSourceMetric]:
    return [
        _source_metric(
            label="Portfolio Return",
            value=format_advisor_brief_pct(selected_performance.portfolio_return_pct),
            support_label=f"{workspace.period} {workspace.detail_basis}",
            route=route,
            state=workspace.capabilities.summary_kpis.state,
        ),
        _source_metric(
            label="Benchmark Return",
            value=format_advisor_brief_pct(selected_performance.benchmark_return_pct),
            support_label=workspace.benchmark_code or "Unassigned",
            route=route,
            state=workspace.capabilities.benchmark_comparison.state,
        ),
        _source_metric(
            label="Active Return",
            value=format_advisor_brief_pct(selected_performance.active_return_pct),
            support_label=f"{workspace.report_start_date} to {workspace.report_end_date}",
            route=route,
            state=workspace.capabilities.benchmark_comparison.state,
        ),
        _source_metric(
            label="Net Flow",
            value=format_advisor_brief_currency(selected_performance.net_cash_flow),
            support_label=workspace.portfolio.base_currency or "Portfolio currency",
            route=route,
            state=workspace.capabilities.summary_kpis.state,
        ),
        _source_metric(
            label="Ending MV",
            value=format_advisor_brief_currency(selected_performance.end_market_value),
            support_label=workspace.report_end_date,
            route=route,
            state=workspace.capabilities.summary_kpis.state,
        ),
    ]


def _source_metric(
    *,
    label: str,
    value: str,
    support_label: str,
    route: str,
    state: str,
) -> AdvisorBriefSourceMetric:
    return AdvisorBriefSourceMetric(
        label=label,
        value=value,
        support_label=support_label,
        target_mode="summary",
        route=route,
        state=state,
    )


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
    items.append(_advisor_brief_supportability_item(source_items=items))
    return items


def _advisor_brief_supportability_item(
    *,
    source_items: list[AdvisorBriefSupportabilityItem],
) -> AdvisorBriefSupportabilityItem:
    value = "Ready"
    tone = "success"
    if any(item.tone == "danger" for item in source_items[:2]):
        value = "Unavailable"
        tone = "danger"
    elif any(item.tone in {"warn", "danger"} for item in source_items):
        value = "Partial"
        tone = "warn"
    return AdvisorBriefSupportabilityItem(
        label="Advisor Brief",
        value=value,
        tone=tone,
        reason=None,
    )


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
