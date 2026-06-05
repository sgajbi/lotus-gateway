from __future__ import annotations

from typing import Any

from app.contracts.performance_workspace import (
    ContributionLevelView,
    ContributionPositionView,
    ContributionRowView,
    ContributionSmoothingEvidenceView,
    ContributionSourceEconomicsEvidenceView,
    ContributionSummaryView,
)
from app.contracts.workbench import WorkbenchPartialFailure
from app.precision_policy import quantize_performance
from app.services.performance_workspace_failures import build_performance_failure
from app.services.performance_workspace_parsing import (
    format_key_label,
    quantize_optional,
    safe_int,
    safe_str,
    safe_str_list,
    sum_optional,
    weight_to_pct,
)
from app.services.performance_workspace_returns import resolve_results_period_key
from app.services.upstream_envelope import safe_upstream_detail

ContributionResult = tuple[int, dict[str, Any]] | BaseException


def build_workspace_contribution_summary(
    period_payload: dict[str, Any],
) -> ContributionSummaryView | None:
    contribution_payload = period_payload.get("contribution", {})
    if not isinstance(contribution_payload, dict):
        return None
    summary_payload = contribution_payload.get("summary", {})
    if not isinstance(summary_payload, dict):
        summary_payload = {}

    return ContributionSummaryView(
        metric_basis=safe_str(contribution_payload.get("metric_basis")) or "NET",
        weighting_scheme=safe_str(summary_payload.get("weighting_scheme")),
        portfolio_contribution_pct=quantize_optional(summary_payload.get("portfolio_contribution")),
        total_portfolio_return_pct=quantize_optional(period_payload.get("total_portfolio_return")),
        coverage_mv_pct=quantize_optional(summary_payload.get("coverage_mv_pct")),
        portfolio_local_contribution_pct=quantize_optional(
            summary_payload.get("local_contribution")
        ),
        portfolio_fx_contribution_pct=quantize_optional(summary_payload.get("fx_contribution")),
        position_rows=_build_position_rows(
            contribution_payload.get("position_contributions", []),
            quantize_with_policy=False,
        ),
        levels=_build_workspace_contribution_levels(
            levels_payload=contribution_payload.get("levels", []),
            summary_payload=summary_payload,
            period_payload=period_payload,
        ),
        smoothing_evidence=parse_contribution_smoothing_evidence(
            period_payload.get("smoothing_evidence")
        ),
        source_economics_evidence=parse_contribution_source_economics_evidence(
            contribution_payload.get("source_economics_evidence")
        ),
    )


def build_detail_contribution_summary(
    *,
    period_payload: dict[str, Any],
    metric_basis: str,
    source_economics_payload: Any,
) -> ContributionSummaryView | None:
    summary_payload = period_payload.get("summary", {})
    if not isinstance(summary_payload, dict):
        summary_payload = {}

    return ContributionSummaryView(
        metric_basis=metric_basis,
        weighting_scheme=safe_str(summary_payload.get("weighting_scheme")),
        portfolio_contribution_pct=quantize_optional(summary_payload.get("portfolio_contribution")),
        total_portfolio_return_pct=quantize_optional(period_payload.get("total_portfolio_return")),
        coverage_mv_pct=quantize_optional(summary_payload.get("coverage_mv_pct")),
        portfolio_local_contribution_pct=quantize_optional(
            summary_payload.get("local_contribution")
        ),
        portfolio_fx_contribution_pct=quantize_optional(summary_payload.get("fx_contribution")),
        position_rows=_build_position_rows(
            period_payload.get("position_contributions", []),
            quantize_with_policy=True,
        ),
        levels=_build_detail_contribution_levels(period_payload),
        smoothing_evidence=parse_contribution_smoothing_evidence(
            period_payload.get("smoothing_evidence")
        ),
        source_economics_evidence=parse_contribution_source_economics_evidence(
            source_economics_payload
        ),
    )


def parse_contribution_result(
    *,
    result: ContributionResult,
    metric_basis: str,
    requested_period: str,
    warnings: list[str],
    partial_failures: list[WorkbenchPartialFailure],
) -> ContributionSummaryView | None:
    if isinstance(result, BaseException):
        warnings.append("CONTRIBUTION_UNAVAILABLE")
        partial_failures.append(
            build_performance_failure("lotus-performance", "UPSTREAM_EXCEPTION", str(result))
        )
        return None
    status_code, payload = result
    if not isinstance(payload, dict):
        warnings.append("CONTRIBUTION_INVALID")
        return None
    if status_code >= 400:
        warnings.append("CONTRIBUTION_UNAVAILABLE")
        partial_failures.append(
            build_performance_failure(
                "lotus-performance",
                f"HTTP_{status_code}",
                safe_upstream_detail(payload, default_detail="contribution unavailable"),
            )
        )
        return None
    results_by_period = payload.get("results_by_period", {})
    if not isinstance(results_by_period, dict) or not results_by_period:
        return None
    period_key = resolve_results_period_key(
        requested_period=requested_period,
        results_by_period=results_by_period,
    )
    period_payload = results_by_period.get(period_key, {})
    if not isinstance(period_payload, dict):
        return None
    return build_detail_contribution_summary(
        period_payload=period_payload,
        metric_basis=metric_basis,
        source_economics_payload=payload.get("source_economics_evidence"),
    )


def merge_contribution_summary_views(
    *,
    summary_contribution: ContributionSummaryView | None,
    detail_contribution: ContributionSummaryView | None,
) -> ContributionSummaryView | None:
    if detail_contribution is None:
        return summary_contribution
    if summary_contribution is None:
        return detail_contribution

    return ContributionSummaryView(
        **_merged_contribution_metric_fields(
            detail_contribution=detail_contribution,
            summary_contribution=summary_contribution,
        ),
        **_merged_contribution_detail_fields(
            detail_contribution=detail_contribution,
            summary_contribution=summary_contribution,
        ),
    )


def _merged_contribution_metric_fields(
    *,
    detail_contribution: ContributionSummaryView,
    summary_contribution: ContributionSummaryView,
) -> dict[str, Any]:
    return {
        "metric_basis": detail_contribution.metric_basis or summary_contribution.metric_basis,
        "weighting_scheme": _prefer_populated(
            detail_contribution.weighting_scheme,
            summary_contribution.weighting_scheme,
        ),
        "portfolio_contribution_pct": _prefer_present(
            detail_contribution.portfolio_contribution_pct,
            summary_contribution.portfolio_contribution_pct,
        ),
        "total_portfolio_return_pct": _prefer_present(
            detail_contribution.total_portfolio_return_pct,
            summary_contribution.total_portfolio_return_pct,
        ),
        "coverage_mv_pct": _prefer_present(
            detail_contribution.coverage_mv_pct,
            summary_contribution.coverage_mv_pct,
        ),
        "portfolio_local_contribution_pct": _prefer_present(
            detail_contribution.portfolio_local_contribution_pct,
            summary_contribution.portfolio_local_contribution_pct,
        ),
        "portfolio_fx_contribution_pct": _prefer_present(
            detail_contribution.portfolio_fx_contribution_pct,
            summary_contribution.portfolio_fx_contribution_pct,
        ),
    }


def _merged_contribution_detail_fields(
    *,
    detail_contribution: ContributionSummaryView,
    summary_contribution: ContributionSummaryView,
) -> dict[str, Any]:
    return {
        "position_rows": _prefer_populated(
            detail_contribution.position_rows,
            summary_contribution.position_rows,
        ),
        "levels": _prefer_populated(detail_contribution.levels, summary_contribution.levels),
        "smoothing_evidence": _prefer_populated(
            detail_contribution.smoothing_evidence,
            summary_contribution.smoothing_evidence,
        ),
        "source_economics_evidence": _prefer_populated(
            detail_contribution.source_economics_evidence,
            summary_contribution.source_economics_evidence,
        ),
    }


def _prefer_present(detail_value: Any, summary_value: Any) -> Any:
    if detail_value is not None:
        return detail_value
    return summary_value


def _prefer_populated(detail_value: Any, summary_value: Any) -> Any:
    return detail_value or summary_value


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


def _build_workspace_contribution_levels(
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
        rows = _build_contribution_rows(
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


def _build_detail_contribution_levels(
    period_payload: dict[str, Any],
) -> list[ContributionLevelView]:
    levels_payload = period_payload.get("levels", [])
    levels: list[ContributionLevelView] = []
    if not isinstance(levels_payload, list):
        return levels
    for level_payload in levels_payload:
        if not isinstance(level_payload, dict):
            continue
        rows = _build_contribution_rows(
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


def _build_contribution_rows(
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


def _build_position_rows(
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
