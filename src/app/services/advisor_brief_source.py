from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.contracts.advisor_brief import (
    AdvisorBriefActionItem,
    AdvisorBriefEvidenceRef,
    AdvisorBriefNarrativeItem,
    AdvisorBriefSourceMetric,
    AdvisorBriefStatus,
    AdvisorBriefSupportabilityItem,
    AdvisorBriefTone,
)
from app.contracts.performance_attribution import AttributionSummaryView
from app.contracts.performance_contribution import (
    ContributionPositionView,
    ContributionSummaryView,
)
from app.contracts.performance_workspace import (
    PerformanceComparativeSummary,
    PerformanceWorkspaceResponse,
)
from app.precision_policy import quantize_money, quantize_performance


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


def build_advisor_brief_ai_fact_bundle(
    *,
    source_context: AdvisorBriefSourceContext,
) -> dict[str, Any]:
    workspace = source_context.workspace
    contribution = workspace.contribution
    attribution = workspace.attribution
    return {
        "portfolio": _build_ai_portfolio_context(workspace=workspace),
        "period": _build_ai_period_context(workspace=workspace),
        "benchmark": _build_ai_benchmark_context(source_context=source_context),
        "performance": _build_ai_performance_context(source_context=source_context),
        "contribution": _build_ai_contribution_context(contribution=contribution),
        "attribution": _build_ai_attribution_context(attribution=attribution),
        "supportability": [item.model_dump(mode="json") for item in source_context.supportability],
        "warnings": workspace.warnings,
        "partial_failures": [item.model_dump(mode="json") for item in workspace.partial_failures],
    }


def build_advisor_brief_source_route(*, source_context: AdvisorBriefSourceContext) -> str:
    workspace = source_context.workspace
    return _route_query(
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
    return _summary_evidence_ref(
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
            f"lotus-performance:benchmark:{workspace.portfolio_id}:{workspace.benchmark_code}:{workspace.period}"
        )
    return refs


def _build_ai_portfolio_context(*, workspace: PerformanceWorkspaceResponse) -> dict[str, Any]:
    return {
        "portfolio_id": workspace.portfolio_id,
        "display_label": _portfolio_display_label(workspace=workspace),
        "base_currency": workspace.portfolio.base_currency,
        "booking_center_code": workspace.portfolio.booking_center_code,
        "client_id": workspace.portfolio.client_id,
    }


def _build_ai_period_context(*, workspace: PerformanceWorkspaceResponse) -> dict[str, Any]:
    return {
        "period": workspace.period,
        "report_start_date": workspace.report_start_date,
        "report_end_date": workspace.report_end_date,
        "as_of_date": workspace.as_of_date,
        "detail_basis": workspace.detail_basis,
    }


def _build_ai_benchmark_context(
    *,
    source_context: AdvisorBriefSourceContext,
) -> dict[str, Any]:
    workspace = source_context.workspace
    return {
        "benchmark_code": workspace.benchmark_code,
        "benchmark_name": _benchmark_display_label(workspace=workspace),
        "benchmark_return_pct": source_context.selected_performance.benchmark_return_pct,
    }


def _build_ai_performance_context(
    *,
    source_context: AdvisorBriefSourceContext,
) -> dict[str, Any]:
    workspace = source_context.workspace
    selected_performance = source_context.selected_performance
    return {
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
    }


def _build_ai_contribution_context(
    *,
    contribution: ContributionSummaryView | None,
) -> dict[str, Any]:
    return {
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
    }


def _build_ai_attribution_context(
    *,
    attribution: AttributionSummaryView | None,
) -> dict[str, Any]:
    return {
        "active_return_pct": attribution.active_return_pct if attribution else None,
        "sum_of_effects_pct": attribution.sum_of_effects_pct if attribution else None,
        "residual_pct": attribution.residual_pct if attribution else None,
        "top_effects": _top_attribution_effects(attribution=attribution),
    }


def _build_ai_contribution_position(*, row: ContributionPositionView) -> dict[str, Any]:
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


def _first_positive_position_contributor(
    contribution: ContributionSummaryView | None,
) -> ContributionPositionView | None:
    contributors = _positive_position_contributors(contribution=contribution)
    return contributors[0] if contributors else None


def _first_negative_position_contributor(
    contribution: ContributionSummaryView | None,
) -> ContributionPositionView | None:
    contributors = _negative_position_contributors(contribution=contribution)
    return contributors[0] if contributors else None


def _build_position_talking_point(
    *,
    position: ContributionPositionView,
    workspace: PerformanceWorkspaceResponse,
    headline_prefix: str,
    label: str,
    tone: AdvisorBriefTone,
) -> AdvisorBriefNarrativeItem:
    position_label = _normalize_position_label(position.position_id)
    return AdvisorBriefNarrativeItem(
        headline=f"{headline_prefix} is {position_label}.",
        detail=(
            f"{position_label} contributed {_format_pct(position.contribution_pct)} "
            f"with return {_format_pct(position.total_return_pct)}."
        ),
        tone=tone,
        evidence_refs=[
            _analysis_evidence_ref(
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
    route = _route_query(
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
                route=_route_query(
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
            value=_format_pct(selected_performance.portfolio_return_pct),
            support_label=f"{workspace.period} {workspace.detail_basis}",
            route=route,
            state=workspace.capabilities.summary_kpis.state,
        ),
        _source_metric(
            label="Benchmark Return",
            value=_format_pct(selected_performance.benchmark_return_pct),
            support_label=workspace.benchmark_code or "Unassigned",
            route=route,
            state=workspace.capabilities.benchmark_comparison.state,
        ),
        _source_metric(
            label="Active Return",
            value=_format_pct(selected_performance.active_return_pct),
            support_label=f"{workspace.report_start_date} to {workspace.report_end_date}",
            route=route,
            state=workspace.capabilities.benchmark_comparison.state,
        ),
        _source_metric(
            label="Net Flow",
            value=_format_currency(selected_performance.net_cash_flow),
            support_label=workspace.portfolio.base_currency or "Portfolio currency",
            route=route,
            state=workspace.capabilities.summary_kpis.state,
        ),
        _source_metric(
            label="Ending MV",
            value=_format_currency(selected_performance.end_market_value),
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
        for row in sorted(rows, key=lambda row: abs(row.total_effect_pct), reverse=True)[:5]
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
