from __future__ import annotations

from typing import Any

from app.contracts.performance_contribution import ContributionSummaryView
from app.contracts.workbench import WorkbenchPartialFailure
from app.services.performance_workspace_contribution_payloads import (
    build_detail_contribution_levels,
    build_position_rows,
    build_workspace_contribution_levels,
    parse_contribution_smoothing_evidence,
    parse_contribution_source_economics_evidence,
)
from app.services.performance_workspace_failures import build_performance_failure
from app.services.performance_workspace_parsing import (
    quantize_optional,
    safe_str,
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
        position_rows=build_position_rows(
            contribution_payload.get("position_contributions", []),
            quantize_with_policy=False,
        ),
        levels=build_workspace_contribution_levels(
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
        position_rows=build_position_rows(
            period_payload.get("position_contributions", []),
            quantize_with_policy=True,
        ),
        levels=build_detail_contribution_levels(period_payload),
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
