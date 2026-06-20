from app.contracts.advisor_brief import AdvisorBriefSourceMetric
from app.contracts.performance_workspace import (
    PerformanceComparativeSummary,
    PerformanceWorkspaceResponse,
)
from app.services.advisor_brief_source_formatting import (
    format_advisor_brief_currency,
    format_advisor_brief_pct,
)


def build_return_source_metrics(
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
