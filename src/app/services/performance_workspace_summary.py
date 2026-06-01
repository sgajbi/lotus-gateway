from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypeAlias

from app.contracts.performance_workspace import (
    AttributionSummaryView,
    ContributionSummaryView,
    MoneyWeightedReturnSummary,
    PerformanceChartPoint,
    PerformanceComparativeSummary,
)
from app.contracts.workbench import WorkbenchPartialFailure
from app.services.performance_workspace_attribution import build_workspace_attribution_summary
from app.services.performance_workspace_chart_points import build_workspace_chart_points
from app.services.performance_workspace_contribution import build_workspace_contribution_summary
from app.services.performance_workspace_failures import build_performance_failure
from app.services.performance_workspace_mwr import build_workspace_mwr_summary
from app.services.performance_workspace_parsing import safe_str
from app.services.performance_workspace_returns import (
    build_workspace_comparative_summary,
    extract_twr_workspace_block,
    resolve_results_period_key,
)

UpstreamPayload: TypeAlias = dict[str, Any]
UpstreamResult: TypeAlias = tuple[int, UpstreamPayload]
GatheredResult: TypeAlias = UpstreamResult | BaseException


@dataclass(frozen=True)
class ParsedWorkspaceSummary:
    net_performance: PerformanceComparativeSummary
    gross_performance: PerformanceComparativeSummary
    net_chart: list[PerformanceChartPoint]
    gross_chart: list[PerformanceChartPoint]
    money_weighted_return: MoneyWeightedReturnSummary | None
    contribution: ContributionSummaryView | None
    attribution: AttributionSummaryView | None
    resolved_benchmark_code: str | None

    @classmethod
    def empty(cls) -> ParsedWorkspaceSummary:
        return cls(
            net_performance=PerformanceComparativeSummary(metric_basis="NET"),
            gross_performance=PerformanceComparativeSummary(metric_basis="GROSS"),
            net_chart=[],
            gross_chart=[],
            money_weighted_return=None,
            contribution=None,
            attribution=None,
            resolved_benchmark_code=None,
        )


def parse_workspace_summary_result(
    *,
    result: GatheredResult,
    requested_period: str,
    chart_frequency: str,
    warnings: list[str],
    partial_failures: list[WorkbenchPartialFailure],
) -> ParsedWorkspaceSummary:
    empty_summary = ParsedWorkspaceSummary.empty()
    if isinstance(result, BaseException):
        warnings.append("PERFORMANCE_WORKSPACE_SUMMARY_UNAVAILABLE")
        partial_failures.append(
            build_performance_failure("lotus-performance", "UPSTREAM_EXCEPTION", str(result))
        )
        return empty_summary

    status_code, payload = result
    if not isinstance(payload, dict):
        warnings.append("PERFORMANCE_WORKSPACE_SUMMARY_INVALID")
        return empty_summary
    if status_code >= 400:
        warnings.append("PERFORMANCE_WORKSPACE_SUMMARY_UNAVAILABLE")
        partial_failures.append(
            build_performance_failure(
                "lotus-performance",
                f"HTTP_{status_code}",
                str(payload.get("detail", payload)),
            )
        )
        return empty_summary

    results_by_period = payload.get("results_by_period", {})
    if not isinstance(results_by_period, dict) or not results_by_period:
        warnings.append("PERFORMANCE_WORKSPACE_SUMMARY_INVALID")
        return empty_summary

    period_key = resolve_results_period_key(
        requested_period=requested_period,
        results_by_period=results_by_period,
    )
    period_payload = results_by_period.get(period_key, {})
    if not isinstance(period_payload, dict):
        return empty_summary

    benchmark_block = period_payload.get("benchmark", {})
    active_block = period_payload.get("active", {})
    net_block = extract_twr_workspace_block(period_payload, "net")
    gross_block = extract_twr_workspace_block(period_payload, "gross")
    money_weighted_return = build_workspace_mwr_summary(period_payload)
    contribution = build_workspace_contribution_summary(period_payload)
    attribution = build_workspace_attribution_summary(period_payload)

    net_performance = build_workspace_comparative_summary(
        metric_basis="NET",
        portfolio_block=net_block,
        benchmark_block=benchmark_block,
        active_basis_block=active_block.get("net") if isinstance(active_block, dict) else {},
    )
    gross_performance = build_workspace_comparative_summary(
        metric_basis="GROSS",
        portfolio_block=gross_block,
        benchmark_block=benchmark_block,
        active_basis_block=active_block.get("gross") if isinstance(active_block, dict) else {},
    )
    net_chart = build_workspace_chart_points(
        portfolio_block=net_block,
        benchmark_block=benchmark_block,
        chart_frequency=chart_frequency,
    )
    gross_chart = build_workspace_chart_points(
        portfolio_block=gross_block,
        benchmark_block=benchmark_block,
        chart_frequency=chart_frequency,
    )

    return ParsedWorkspaceSummary(
        net_performance=net_performance,
        gross_performance=gross_performance,
        net_chart=net_chart,
        gross_chart=gross_chart,
        money_weighted_return=money_weighted_return,
        contribution=contribution,
        attribution=attribution,
        resolved_benchmark_code=safe_str(benchmark_block.get("benchmark_id")),
    )
