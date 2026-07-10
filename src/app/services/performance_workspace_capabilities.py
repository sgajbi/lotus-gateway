from __future__ import annotations

from dataclasses import dataclass

from app.contracts.performance_attribution import AttributionSummaryView
from app.contracts.performance_contribution import ContributionSummaryView
from app.contracts.performance_evidence import PerformanceEvidenceView
from app.contracts.performance_workspace import (
    PerformanceChartPoint,
    PerformanceComparativeSummary,
    PerformanceModuleCapability,
    PerformanceWorkspaceCapabilities,
)
from app.services.performance_workspace_controls import SUPPORTED_WORKSPACE_FREQUENCIES
from app.services.performance_workspace_detail_capabilities import (
    SUPPORTED_ATTRIBUTION_DIMENSIONS,
    SUPPORTED_CONTRIBUTION_DIMENSIONS,
    PerformanceDetailCapabilities,
    build_attribution_capability,
    build_contribution_capability,
    build_detail_capabilities,
)
from app.services.performance_workspace_module_capability import build_module_capability

__all__ = (
    "SUPPORTED_ATTRIBUTION_DIMENSIONS",
    "SUPPORTED_CONTRIBUTION_DIMENSIONS",
    "PerformanceCapabilityInputs",
    "PerformanceDetailCapabilities",
    "build_attribution_capability",
    "build_benchmark_comparison_capability",
    "build_contribution_capability",
    "build_detail_capabilities",
    "build_evidence_capability",
    "build_module_capability",
    "build_multi_horizon_capability",
    "build_performance_capability_inputs",
    "build_return_path_capability",
    "build_workspace_capabilities",
    "resolve_history_date_range",
)


@dataclass(frozen=True)
class PerformanceCapabilityInputs:
    has_return_history: bool
    has_benchmark: bool
    has_benchmark_returns: bool
    has_contribution_detail: bool
    has_position_ranking: bool
    has_attribution_detail: bool
    has_attribution_summary: bool
    earliest_history_date: str | None
    latest_history_date: str | None


def build_workspace_capabilities(
    *,
    benchmark_code: str | None,
    net_performance: PerformanceComparativeSummary,
    net_chart: list[PerformanceChartPoint],
    contribution: ContributionSummaryView | None,
    attribution: AttributionSummaryView | None,
    evidence_view: PerformanceEvidenceView | None,
    include_detail_blocks: bool = True,
) -> PerformanceWorkspaceCapabilities:
    inputs = build_performance_capability_inputs(
        benchmark_code=benchmark_code,
        net_performance=net_performance,
        net_chart=net_chart,
        contribution=contribution,
        attribution=attribution,
    )
    detail_capabilities = build_detail_capabilities(
        inputs=inputs,
        include_detail_blocks=include_detail_blocks,
    )

    return PerformanceWorkspaceCapabilities(
        summary_kpis=build_module_capability(
            "supported",
            "The performance workspace contract supports executive summary metrics.",
        ),
        return_path=build_return_path_capability(inputs),
        benchmark_comparison=build_benchmark_comparison_capability(inputs),
        multi_horizon_returns=build_multi_horizon_capability(inputs),
        contribution_ranking=detail_capabilities.contribution_ranking,
        attribution_detail=detail_capabilities.attribution_detail,
        contribution_detail=detail_capabilities.contribution_detail,
        evidence=build_evidence_capability(evidence_view=evidence_view),
    )


def build_return_path_capability(
    inputs: PerformanceCapabilityInputs,
) -> PerformanceModuleCapability:
    if inputs.has_return_history:
        return build_module_capability(
            "supported",
            "Time-series return observations are available for the selected horizon.",
            earliest_available_date=inputs.earliest_history_date,
            latest_available_date=inputs.latest_history_date,
            supported_frequencies=SUPPORTED_WORKSPACE_FREQUENCIES,
        )
    return build_module_capability(
        "unavailable",
        "Published return observations are not available for the selected horizon.",
        supported_frequencies=SUPPORTED_WORKSPACE_FREQUENCIES,
    )


def build_benchmark_comparison_capability(
    inputs: PerformanceCapabilityInputs,
) -> PerformanceModuleCapability:
    if inputs.has_benchmark and inputs.has_benchmark_returns:
        return build_module_capability(
            "supported",
            "Benchmark-relative return metrics are available.",
            earliest_available_date=inputs.earliest_history_date,
            latest_available_date=inputs.latest_history_date,
        )
    if inputs.has_benchmark:
        return build_module_capability(
            "partial",
            "A benchmark is assigned, but benchmark-relative returns are incomplete.",
            earliest_available_date=inputs.earliest_history_date,
            latest_available_date=inputs.latest_history_date,
        )
    return build_module_capability(
        "unavailable",
        "No benchmark is assigned to this mandate.",
    )


def build_multi_horizon_capability(
    inputs: PerformanceCapabilityInputs,
) -> PerformanceModuleCapability:
    if inputs.has_benchmark:
        return build_module_capability(
            "supported",
            "The workspace supports benchmark-aware horizon comparisons.",
            supported_frequencies=SUPPORTED_WORKSPACE_FREQUENCIES,
        )
    return build_module_capability(
        "partial",
        "Horizon comparisons remain available, but benchmark-relative output is unavailable.",
        supported_frequencies=SUPPORTED_WORKSPACE_FREQUENCIES,
    )


def build_performance_capability_inputs(
    *,
    benchmark_code: str | None,
    net_performance: PerformanceComparativeSummary,
    net_chart: list[PerformanceChartPoint],
    contribution: ContributionSummaryView | None,
    attribution: AttributionSummaryView | None,
) -> PerformanceCapabilityInputs:
    earliest_history_date, latest_history_date = resolve_history_date_range(net_chart)
    return PerformanceCapabilityInputs(
        has_return_history=bool(net_chart),
        has_benchmark=bool(benchmark_code),
        has_benchmark_returns=(
            net_performance.benchmark_return_pct is not None
            and net_performance.active_return_pct is not None
        ),
        has_contribution_detail=bool(
            contribution and (contribution.levels or contribution.position_rows)
        ),
        has_position_ranking=bool(contribution and contribution.position_rows),
        has_attribution_detail=bool(
            attribution and any(level.rows for level in attribution.levels)
        ),
        has_attribution_summary=bool(
            attribution
            and (
                attribution.levels
                or attribution.active_return_pct is not None
                or attribution.sum_of_effects_pct is not None
                or attribution.residual_pct is not None
            )
        ),
        earliest_history_date=earliest_history_date,
        latest_history_date=latest_history_date,
    )


def resolve_history_date_range(
    net_chart: list[PerformanceChartPoint],
) -> tuple[str | None, str | None]:
    dated_history = [
        point
        for point in net_chart
        if point.period_start is not None or point.period_end is not None
    ]
    if not dated_history:
        return None, None
    return (
        min(point.period_start or point.period_end or "" for point in dated_history),
        max(point.period_end or point.period_start or "" for point in dated_history),
    )


def build_evidence_capability(
    *,
    evidence_view: PerformanceEvidenceView | None,
) -> PerformanceModuleCapability:
    if evidence_view is None:
        return build_module_capability(
            "unavailable",
            "No evidence posture is available for the current selection.",
        )
    if evidence_view.state == "supported":
        return build_module_capability(
            "supported",
            evidence_view.reason,
            coverage_level="calculation",
            fallback_available=True,
        )
    if evidence_view.state == "partial":
        return build_module_capability(
            "partial",
            evidence_view.reason,
            coverage_level="calculation",
            fallback_available=True,
        )
    return build_module_capability(
        "unavailable",
        evidence_view.reason,
        coverage_level="calculation",
    )
