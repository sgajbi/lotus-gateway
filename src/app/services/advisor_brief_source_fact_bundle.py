from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.contracts.performance_contribution import (
    ContributionPositionView,
    ContributionSummaryView,
)
from app.contracts.performance_workspace import PerformanceWorkspaceResponse
from app.services.advisor_brief_source_contributors import (
    negative_position_contributors,
    positive_position_contributors,
    top_attribution_effects,
)
from app.services.advisor_brief_source_formatting import (
    advisor_brief_benchmark_display_label,
    advisor_brief_portfolio_display_label,
    normalize_advisor_brief_position_label,
)

if TYPE_CHECKING:
    from app.services.advisor_brief_source import AdvisorBriefSourceContext


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
        "attribution": {
            "active_return_pct": attribution.active_return_pct if attribution else None,
            "sum_of_effects_pct": attribution.sum_of_effects_pct if attribution else None,
            "residual_pct": attribution.residual_pct if attribution else None,
            "top_effects": top_attribution_effects(attribution=attribution),
        },
        "supportability": [item.model_dump(mode="json") for item in source_context.supportability],
        "warnings": workspace.warnings,
        "partial_failures": [item.model_dump(mode="json") for item in workspace.partial_failures],
    }


def _build_ai_portfolio_context(*, workspace: PerformanceWorkspaceResponse) -> dict[str, Any]:
    return {
        "portfolio_id": workspace.portfolio_id,
        "display_label": advisor_brief_portfolio_display_label(workspace=workspace),
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
        "benchmark_name": advisor_brief_benchmark_display_label(workspace=workspace),
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
            for row in positive_position_contributors(contribution=contribution)[:5]
        ],
        "bottom_positions": [
            _build_ai_contribution_position(row=row)
            for row in negative_position_contributors(contribution=contribution)[:5]
        ],
    }


def _build_ai_contribution_position(*, row: ContributionPositionView) -> dict[str, Any]:
    return {
        "display_label": normalize_advisor_brief_position_label(row.position_id),
        "contribution_pct": row.contribution_pct,
        "weight_avg_pct": row.weight_avg_pct,
        "total_return_pct": row.total_return_pct,
        "local_contribution_pct": row.local_contribution_pct,
        "fx_contribution_pct": row.fx_contribution_pct,
    }
