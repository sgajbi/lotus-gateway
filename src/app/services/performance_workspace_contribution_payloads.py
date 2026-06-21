from __future__ import annotations

from typing import Any

from app.contracts.performance_contribution import (
    ContributionLevelView,
    ContributionPositionView,
    ContributionRowView,
    ContributionSmoothingEvidenceView,
    ContributionSourceEconomicsEvidenceView,
)
from app.precision_policy import quantize_performance
from app.services.performance_workspace_parsing import (
    format_key_label,
    quantize_optional,
    safe_int,
    safe_str,
    safe_str_list,
    sum_optional,
    weight_to_pct,
)


def parse_contribution_smoothing_evidence(
    payload: Any,
) -> ContributionSmoothingEvidenceView | None:
    if not isinstance(payload, dict):
        return None
    return ContributionSmoothingEvidenceView(
        status=safe_str(payload.get("status")),
        reason_codes=safe_str_list(payload.get("reason_codes")),
        raw_contribution_pct=quantize_optional(payload.get("raw_contribution")),
        final_contribution_pct=quantize_optional(payload.get("final_contribution")),
        linked_return_pct=quantize_optional(payload.get("linked_return")),
        smoothing_residual_pct=quantize_optional(payload.get("smoothing_residual")),
    )


def parse_contribution_source_economics_evidence(
    payload: Any,
) -> ContributionSourceEconomicsEvidenceView | None:
    if not isinstance(payload, dict):
        return None
    return ContributionSourceEconomicsEvidenceView(
        status=safe_str(payload.get("status")),
        reason_codes=safe_str_list(payload.get("reason_codes")),
        source_contracts=safe_str_list(payload.get("source_contracts")),
        available_economics=safe_str_list(payload.get("available_economics")),
        unsupported_economics=safe_str_list(payload.get("unsupported_economics")),
        degraded_economics=safe_str_list(payload.get("degraded_economics")),
        source_snapshot_count=safe_int(payload.get("source_snapshot_count")),
    )


def build_workspace_contribution_levels(
    *,
    levels_payload: Any,
    summary_payload: dict[str, Any],
    period_payload: dict[str, Any],
) -> list[ContributionLevelView]:
    levels: list[ContributionLevelView] = []
    if not isinstance(levels_payload, list):
        return levels
    for level_payload in levels_payload:
        if not isinstance(level_payload, dict):
            continue
        rows = build_contribution_rows(
            level_payload.get("rows", []),
            quantize_contribution_with_policy=False,
            include_total_return=True,
        )
        source_level_return = quantize_optional(level_payload.get("total_portfolio_return"))
        if source_level_return is None:
            source_level_return = quantize_optional(period_payload.get("total_portfolio_return"))
        levels.append(
            ContributionLevelView(
                level=int(level_payload.get("level", len(levels) + 1)),
                name=str(level_payload.get("name", "Level")),
                rows=rows,
                total_contribution_pct=quantize_optional(
                    summary_payload.get("portfolio_contribution")
                ),
                total_weight_avg_pct=sum_optional([row.weight_avg_pct for row in rows]),
                total_portfolio_return_pct=source_level_return,
            )
        )
    return levels


def build_detail_contribution_levels(
    period_payload: dict[str, Any],
) -> list[ContributionLevelView]:
    levels_payload = period_payload.get("levels", [])
    levels: list[ContributionLevelView] = []
    if not isinstance(levels_payload, list):
        return levels
    for level_payload in levels_payload:
        if not isinstance(level_payload, dict):
            continue
        rows = build_contribution_rows(
            level_payload.get("rows", []),
            quantize_contribution_with_policy=True,
            include_total_return=False,
        )
        source_level_total = quantize_optional(level_payload.get("total_contribution"))
        if source_level_total is None:
            source_level_total = quantize_optional(period_payload.get("total_contribution"))
        source_level_return = quantize_optional(level_payload.get("total_portfolio_return"))
        if source_level_return is None:
            source_level_return = quantize_optional(period_payload.get("total_portfolio_return"))
        levels.append(
            ContributionLevelView(
                level=int(level_payload.get("level", len(levels) + 1)),
                name=str(level_payload.get("name", "Level")),
                rows=rows,
                total_contribution_pct=source_level_total
                if source_level_total is not None
                else (
                    quantize_optional(sum(row.contribution_pct for row in rows)) if rows else None
                ),
                total_portfolio_return_pct=source_level_return,
            )
        )
    return levels


def build_contribution_rows(
    rows_payload: Any,
    *,
    quantize_contribution_with_policy: bool,
    include_total_return: bool,
) -> list[ContributionRowView]:
    rows: list[ContributionRowView] = []
    if not isinstance(rows_payload, list):
        return rows
    for row_payload in rows_payload:
        if not isinstance(row_payload, dict):
            continue
        contribution = row_payload.get("contribution", 0.0)
        contribution_pct = (
            float(quantize_performance(contribution))
            if quantize_contribution_with_policy
            else quantize_optional(contribution) or 0.0
        )
        rows.append(
            ContributionRowView(
                key_label=format_key_label(row_payload.get("key")),
                contribution_pct=contribution_pct,
                weight_avg_pct=weight_to_pct(row_payload.get("weight_avg")),
                total_return_pct=(
                    quantize_optional(row_payload.get("return")) if include_total_return else None
                ),
                local_contribution_pct=quantize_optional(row_payload.get("local_contribution")),
                fx_contribution_pct=quantize_optional(row_payload.get("fx_contribution")),
                is_other=bool(row_payload.get("is_other", False)),
            )
        )
    return rows


def build_position_rows(
    position_payloads: Any,
    *,
    quantize_with_policy: bool,
) -> list[ContributionPositionView]:
    position_rows: list[ContributionPositionView] = []
    if not isinstance(position_payloads, list):
        return position_rows
    for position_payload in position_payloads:
        if not isinstance(position_payload, dict):
            continue
        total_contribution = position_payload.get("total_contribution", 0.0)
        contribution_pct = (
            float(quantize_performance(total_contribution))
            if quantize_with_policy
            else quantize_optional(total_contribution) or 0.0
        )
        position_rows.append(
            ContributionPositionView(
                position_id=str(position_payload.get("position_id", "Unknown Position")),
                contribution_pct=contribution_pct,
                weight_avg_pct=weight_to_pct(position_payload.get("average_weight")),
                total_return_pct=quantize_optional(position_payload.get("total_return")),
                local_contribution_pct=quantize_optional(
                    position_payload.get("local_contribution")
                ),
                fx_contribution_pct=quantize_optional(position_payload.get("fx_contribution")),
            )
        )
    return position_rows
