from __future__ import annotations

from collections.abc import Sequence

from app.contracts.performance_workspace import (
    AttributionSummaryView,
    ContributionSummaryView,
    PerformanceChartPoint,
    PerformanceComparativeSummary,
    PerformanceEvidenceView,
    PerformanceModuleCapability,
    PerformanceWorkspaceCapabilities,
)
from app.services.performance_workspace_controls import SUPPORTED_WORKSPACE_FREQUENCIES

SUPPORTED_CONTRIBUTION_DIMENSIONS = ("asset_class", "sector", "country")
SUPPORTED_ATTRIBUTION_DIMENSIONS = ("asset_class", "sector", "country", "currency")


def build_module_capability(
    state: str,
    reason: str | None = None,
    *,
    coverage_level: str | None = None,
    fallback_available: bool | None = None,
    earliest_available_date: str | None = None,
    latest_available_date: str | None = None,
    supported_dimensions: Sequence[str] | None = None,
    supported_frequencies: Sequence[str] | None = None,
) -> PerformanceModuleCapability:
    return PerformanceModuleCapability(
        state=state,
        reason=reason,
        coverage_level=coverage_level,
        fallback_available=fallback_available,
        earliest_available_date=earliest_available_date,
        latest_available_date=latest_available_date,
        supported_dimensions=list(supported_dimensions) if supported_dimensions else None,
        supported_frequencies=list(supported_frequencies) if supported_frequencies else None,
    )


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
    has_return_history = len(net_chart) > 0
    has_benchmark = bool(benchmark_code)
    has_benchmark_returns = (
        net_performance.benchmark_return_pct is not None
        and net_performance.active_return_pct is not None
    )
    has_contribution_detail = bool(
        contribution and (contribution.levels or contribution.position_rows)
    )
    has_position_ranking = bool(contribution and contribution.position_rows)
    has_attribution_detail = bool(attribution and any(level.rows for level in attribution.levels))
    has_attribution_summary = bool(
        attribution
        and (
            attribution.levels
            or attribution.active_return_pct is not None
            or attribution.sum_of_effects_pct is not None
            or attribution.residual_pct is not None
        )
    )
    dated_history = [
        point
        for point in net_chart
        if point.period_start is not None or point.period_end is not None
    ]
    earliest_history_date = (
        min(point.period_start or point.period_end or "" for point in dated_history)
        if dated_history
        else None
    )
    latest_history_date = (
        max(point.period_end or point.period_start or "" for point in dated_history)
        if dated_history
        else None
    )

    return PerformanceWorkspaceCapabilities(
        summary_kpis=build_module_capability(
            "supported",
            "The performance workspace contract supports executive summary metrics.",
        ),
        return_path=(
            build_module_capability(
                "supported",
                "Time-series return observations are available for the selected horizon.",
                earliest_available_date=earliest_history_date,
                latest_available_date=latest_history_date,
                supported_frequencies=SUPPORTED_WORKSPACE_FREQUENCIES,
            )
            if has_return_history
            else build_module_capability(
                "unavailable",
                "Published return observations are not available for the selected horizon.",
                supported_frequencies=SUPPORTED_WORKSPACE_FREQUENCIES,
            )
        ),
        benchmark_comparison=(
            build_module_capability(
                "supported",
                "Benchmark-relative return metrics are available.",
                earliest_available_date=earliest_history_date,
                latest_available_date=latest_history_date,
            )
            if has_benchmark and has_benchmark_returns
            else build_module_capability(
                "partial",
                "A benchmark is assigned, but benchmark-relative returns are incomplete.",
                earliest_available_date=earliest_history_date,
                latest_available_date=latest_history_date,
            )
            if has_benchmark
            else build_module_capability(
                "unavailable",
                "No benchmark is assigned to this mandate.",
            )
        ),
        multi_horizon_returns=(
            build_module_capability(
                "supported",
                "The workspace supports benchmark-aware horizon comparisons.",
                supported_frequencies=SUPPORTED_WORKSPACE_FREQUENCIES,
            )
            if has_benchmark
            else build_module_capability(
                "partial",
                (
                    "Horizon comparisons remain available, "
                    "but benchmark-relative output is unavailable."
                ),
                supported_frequencies=SUPPORTED_WORKSPACE_FREQUENCIES,
            )
        ),
        contribution_ranking=build_contribution_capability(
            include_detail_blocks=include_detail_blocks,
            has_position_ranking=has_position_ranking,
            has_contribution_detail=has_contribution_detail,
            supported_reason="Position-level contribution ranking is available.",
            aggregate_reason="Contribution exists, but only aggregate rows are available.",
            unavailable_reason=(
                "Contribution analytics are not available for the current selection."
            ),
        ),
        attribution_detail=build_attribution_capability(
            include_detail_blocks=include_detail_blocks,
            has_attribution_detail=has_attribution_detail,
            has_attribution_summary=has_attribution_summary,
        ),
        contribution_detail=build_contribution_capability(
            include_detail_blocks=include_detail_blocks,
            has_position_ranking=has_position_ranking,
            has_contribution_detail=has_contribution_detail,
            supported_reason="Contribution detail is available for the current selection.",
            aggregate_reason="Contribution exists, but only aggregate rows are available.",
            unavailable_reason="Contribution detail is not available for the current selection.",
        ),
        evidence=build_evidence_capability(evidence_view=evidence_view),
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


def build_contribution_capability(
    *,
    include_detail_blocks: bool,
    has_position_ranking: bool,
    has_contribution_detail: bool,
    supported_reason: str,
    aggregate_reason: str,
    unavailable_reason: str,
) -> PerformanceModuleCapability:
    if not include_detail_blocks or has_position_ranking:
        return build_module_capability(
            "supported",
            supported_reason,
            coverage_level="position",
            supported_dimensions=SUPPORTED_CONTRIBUTION_DIMENSIONS,
        )
    if has_contribution_detail:
        return build_module_capability(
            "partial",
            aggregate_reason,
            coverage_level="aggregate",
            fallback_available=True,
            supported_dimensions=SUPPORTED_CONTRIBUTION_DIMENSIONS,
        )
    return build_module_capability(
        "unavailable",
        unavailable_reason,
        supported_dimensions=SUPPORTED_CONTRIBUTION_DIMENSIONS,
    )


def build_attribution_capability(
    *,
    include_detail_blocks: bool,
    has_attribution_detail: bool,
    has_attribution_summary: bool,
) -> PerformanceModuleCapability:
    if not include_detail_blocks or has_attribution_detail:
        return build_module_capability(
            "supported",
            "Benchmark-relative attribution detail is available.",
            coverage_level="detail",
            supported_dimensions=SUPPORTED_ATTRIBUTION_DIMENSIONS,
            supported_frequencies=SUPPORTED_WORKSPACE_FREQUENCIES,
        )
    if has_attribution_summary:
        return build_module_capability(
            "partial",
            (
                "Benchmark-relative attribution is available only at summary level "
                "for the current selection."
            ),
            coverage_level="summary",
            fallback_available=True,
            supported_dimensions=SUPPORTED_ATTRIBUTION_DIMENSIONS,
            supported_frequencies=SUPPORTED_WORKSPACE_FREQUENCIES,
        )
    return build_module_capability(
        "unavailable",
        "Attribution detail is not available for the current selection.",
        supported_dimensions=SUPPORTED_ATTRIBUTION_DIMENSIONS,
        supported_frequencies=SUPPORTED_WORKSPACE_FREQUENCIES,
    )
