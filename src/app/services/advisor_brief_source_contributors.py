from __future__ import annotations

from typing import Any

from app.contracts.performance_attribution import AttributionSummaryView
from app.contracts.performance_contribution import (
    ContributionPositionView,
    ContributionSummaryView,
)


def positive_position_contributors(
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


def negative_position_contributors(
    *,
    contribution: ContributionSummaryView | None,
) -> list[ContributionPositionView]:
    if not contribution:
        return []
    return sorted(
        [row for row in contribution.position_rows if row.contribution_pct < 0],
        key=lambda row: row.contribution_pct,
    )


def top_attribution_effects(
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
