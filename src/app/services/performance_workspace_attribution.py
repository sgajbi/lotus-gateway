from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import Any

from app.contracts.performance_workspace import (
    AttributionLevelView,
    AttributionReasonView,
    AttributionResidualMaterialityView,
    AttributionRowView,
    AttributionSummaryView,
    AttributionSupportabilityEvidenceView,
    PerformanceAttributionTrendRow,
)
from app.contracts.workbench import WorkbenchPartialFailure
from app.services.performance_workspace_failures import build_performance_failure
from app.services.performance_workspace_parsing import (
    format_attribution_trend_label,
    format_key_label,
    quantize_optional,
    safe_int,
    safe_str,
    safe_str_list,
    weight_to_pct,
)
from app.services.performance_workspace_returns import resolve_results_period_key
from app.services.upstream_envelope import safe_upstream_detail

AttributionResult = tuple[int, dict[str, Any]] | BaseException
AttributionTrendResult = tuple[int, dict[str, Any]] | BaseException


@dataclass(frozen=True)
class AttributionTrendPeriodPayload:
    period_payload: dict[str, Any]
    reconciliation_payload: dict[str, Any]
    totals_payload: dict[str, Any]
    supportability_evidence_payload: Any


@dataclass(frozen=True)
class AttributionDetailPayload:
    period_payload: dict[str, Any]
    benchmark_context: dict[str, Any]
    model: Any
    linking: Any


def build_workspace_attribution_summary(
    period_payload: dict[str, Any],
) -> AttributionSummaryView | None:
    attribution_payload = period_payload.get("attribution", {})
    if not isinstance(attribution_payload, dict):
        return None
    result_payload = attribution_payload.get("result", {})
    benchmark_context = attribution_payload.get("benchmark_context", {})
    if not isinstance(result_payload, dict):
        result_payload = {}
    if not isinstance(benchmark_context, dict):
        benchmark_context = {}
    reconciliation_payload = result_payload.get("reconciliation", {})
    if not isinstance(reconciliation_payload, dict):
        reconciliation_payload = {}

    return AttributionSummaryView(
        status=safe_str(result_payload.get("status")) or "valid",
        reason_codes=safe_str_list(result_payload.get("reason_codes")),
        reasons=parse_attribution_reasons(result_payload.get("reasons")),
        metric_basis=safe_str(attribution_payload.get("metric_basis")) or "NET",
        model=safe_str(attribution_payload.get("model")),
        linking=safe_str(attribution_payload.get("linking")),
        benchmark_id=safe_str(benchmark_context.get("benchmark_id")),
        benchmark_return_source=safe_str(benchmark_context.get("return_source")),
        active_return_pct=quantize_optional(reconciliation_payload.get("total_active_return")),
        sum_of_effects_pct=quantize_optional(reconciliation_payload.get("sum_of_effects")),
        residual_pct=quantize_optional(reconciliation_payload.get("residual")),
        residual_materiality=parse_attribution_residual_materiality(
            reconciliation_payload.get("residual_materiality")
        ),
        supportability_evidence=parse_attribution_supportability_evidence(
            result_payload.get("supportability_evidence")
        ),
        levels=_build_attribution_levels(
            levels_payload=result_payload.get("levels", []),
            row_key="rows",
            quantize_effects_with_policy=False,
        ),
    )


def build_detail_attribution_summary(
    *,
    period_payload: dict[str, Any],
    metric_basis: str,
    benchmark_context: dict[str, Any],
    model: Any,
    linking: Any,
) -> AttributionSummaryView:
    reconciliation_payload = period_payload.get("reconciliation", {})
    if not isinstance(reconciliation_payload, dict):
        reconciliation_payload = {}

    return AttributionSummaryView(
        status=safe_str(period_payload.get("status")) or "valid",
        reason_codes=safe_str_list(period_payload.get("reason_codes")),
        reasons=parse_attribution_reasons(period_payload.get("reasons")),
        metric_basis=metric_basis,
        model=safe_str(model),
        linking=safe_str(linking),
        benchmark_id=safe_str(benchmark_context.get("benchmark_id")),
        benchmark_return_source=safe_str(benchmark_context.get("return_source")),
        active_return_pct=quantize_optional(reconciliation_payload.get("total_active_return")),
        sum_of_effects_pct=quantize_optional(reconciliation_payload.get("sum_of_effects")),
        residual_pct=quantize_optional(reconciliation_payload.get("residual")),
        residual_materiality=parse_attribution_residual_materiality(
            reconciliation_payload.get("residual_materiality")
        ),
        supportability_evidence=parse_attribution_supportability_evidence(
            period_payload.get("supportability_evidence")
        ),
        levels=_build_attribution_levels(
            levels_payload=period_payload.get("levels", []),
            row_key="groups",
            quantize_effects_with_policy=True,
        ),
    )


def parse_attribution_result(
    *,
    result: AttributionResult,
    metric_basis: str,
    requested_period: str,
    warnings: list[str],
    partial_failures: list[WorkbenchPartialFailure],
) -> AttributionSummaryView | None:
    detail_payload = _extract_attribution_detail_payload(
        result=result,
        requested_period=requested_period,
        warnings=warnings,
        partial_failures=partial_failures,
    )
    if detail_payload is None:
        return None

    return build_detail_attribution_summary(
        period_payload=detail_payload.period_payload,
        metric_basis=metric_basis,
        benchmark_context=detail_payload.benchmark_context,
        model=detail_payload.model,
        linking=detail_payload.linking,
    )


def _extract_attribution_detail_payload(
    *,
    result: AttributionResult,
    requested_period: str,
    warnings: list[str],
    partial_failures: list[WorkbenchPartialFailure],
) -> AttributionDetailPayload | None:
    if isinstance(result, BaseException):
        warnings.append("ATTRIBUTION_UNAVAILABLE")
        partial_failures.append(
            build_performance_failure("lotus-performance", "UPSTREAM_EXCEPTION", str(result))
        )
        return None
    status_code, payload = result
    if not isinstance(payload, dict):
        warnings.append("ATTRIBUTION_INVALID")
        return None
    if status_code >= 400:
        warnings.append("ATTRIBUTION_UNAVAILABLE")
        partial_failures.append(
            build_performance_failure(
                "lotus-performance",
                f"HTTP_{status_code}",
                safe_upstream_detail(payload, default_detail="attribution unavailable"),
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
    benchmark_context = payload.get("benchmark_context", {})
    if not isinstance(benchmark_context, dict):
        benchmark_context = {}
    return AttributionDetailPayload(
        period_payload=period_payload,
        benchmark_context=benchmark_context,
        model=payload.get("model"),
        linking=payload.get("linking"),
    )


def parse_attribution_trend_results(
    *,
    results: Sequence[AttributionTrendResult],
    window_pairs: list[tuple[date, date]],
    chart_frequency: str,
    requested_period: str,
    warnings: list[str],
    partial_failures: list[WorkbenchPartialFailure],
) -> list[PerformanceAttributionTrendRow]:
    rows: list[PerformanceAttributionTrendRow] = []
    cumulative_total_effect = 0.0

    for index, result in enumerate(results):
        window_start, window_end = window_pairs[index]
        parsed_row = parse_single_attribution_trend_row(
            result=result,
            window_start=window_start,
            window_end=window_end,
            chart_frequency=chart_frequency,
            requested_period=requested_period,
            warnings=warnings,
            partial_failures=partial_failures,
        )
        if parsed_row is None:
            continue

        cumulative_total_effect += parsed_row.total_effect_pct or 0.0
        row_payload = parsed_row.model_dump()
        row_payload["cumulative_total_effect_pct"] = quantize_optional(cumulative_total_effect)
        rows.append(PerformanceAttributionTrendRow(**row_payload))

    return rows


def parse_single_attribution_trend_row(
    *,
    result: AttributionTrendResult,
    window_start: date,
    window_end: date,
    chart_frequency: str,
    requested_period: str,
    warnings: list[str],
    partial_failures: list[WorkbenchPartialFailure],
) -> PerformanceAttributionTrendRow | None:
    payload = unpack_attribution_trend_payload(
        result=result,
        warnings=warnings,
        partial_failures=partial_failures,
    )
    if payload is None:
        return None

    trend_period_payload = select_attribution_trend_period_payload(
        payload=payload,
        requested_period=requested_period,
    )
    if trend_period_payload is None:
        return None

    return build_attribution_trend_row(
        window_start=window_start,
        window_end=window_end,
        chart_frequency=chart_frequency,
        trend_period_payload=trend_period_payload,
    )


def unpack_attribution_trend_payload(
    *,
    result: AttributionTrendResult,
    warnings: list[str],
    partial_failures: list[WorkbenchPartialFailure],
) -> dict[str, Any] | None:
    if isinstance(result, BaseException):
        warnings.append("ATTRIBUTION_TREND_PERIOD_UNAVAILABLE")
        partial_failures.append(
            build_performance_failure("lotus-performance", "UPSTREAM_EXCEPTION", str(result))
        )
        return None

    status_code, payload = result
    if status_code < 400 and isinstance(payload, dict):
        return payload
    warnings.append("ATTRIBUTION_TREND_PERIOD_UNAVAILABLE")
    partial_failures.append(
        build_performance_failure(
            "lotus-performance",
            f"HTTP_{status_code}" if isinstance(status_code, int) else "INVALID_UPSTREAM_PAYLOAD",
            str(payload),
        )
    )
    return None


def select_attribution_trend_period_payload(
    *,
    payload: dict[str, Any],
    requested_period: str,
) -> AttributionTrendPeriodPayload | None:
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

    return build_attribution_trend_period_payload(period_payload)


def build_attribution_trend_period_payload(
    period_payload: dict[str, Any],
) -> AttributionTrendPeriodPayload | None:
    levels_payload = period_payload.get("levels", [])
    reconciliation_payload = period_payload.get("reconciliation", {})
    if not isinstance(levels_payload, list) or not levels_payload:
        return None
    if not isinstance(reconciliation_payload, dict):
        reconciliation_payload = {}
    supportability_evidence_payload = period_payload.get("supportability_evidence")

    level_payload = levels_payload[0]
    if not isinstance(level_payload, dict):
        return None
    totals_payload = level_payload.get("totals", {})
    if not isinstance(totals_payload, dict):
        totals_payload = {}
    return AttributionTrendPeriodPayload(
        period_payload=period_payload,
        reconciliation_payload=reconciliation_payload,
        totals_payload=totals_payload,
        supportability_evidence_payload=supportability_evidence_payload,
    )


def build_attribution_trend_row(
    *,
    window_start: date,
    window_end: date,
    chart_frequency: str,
    trend_period_payload: AttributionTrendPeriodPayload,
) -> PerformanceAttributionTrendRow:
    return PerformanceAttributionTrendRow(
        period_label=format_attribution_trend_label(
            window_start=window_start,
            window_end=window_end,
            chart_frequency=chart_frequency,
        ),
        period_start=window_start.isoformat(),
        period_end=window_end.isoformat(),
        frequency=chart_frequency,
        allocation_pct=quantize_optional(trend_period_payload.totals_payload.get("allocation")),
        selection_pct=quantize_optional(trend_period_payload.totals_payload.get("selection")),
        interaction_pct=quantize_optional(trend_period_payload.totals_payload.get("interaction")),
        total_effect_pct=quantize_optional(trend_period_payload.totals_payload.get("total_effect")),
        active_return_pct=quantize_optional(
            trend_period_payload.reconciliation_payload.get("total_active_return")
        ),
        residual_pct=quantize_optional(trend_period_payload.reconciliation_payload.get("residual")),
        status=safe_str(trend_period_payload.period_payload.get("status")) or "valid",
        reason_codes=safe_str_list(trend_period_payload.period_payload.get("reason_codes")),
        residual_materiality=parse_attribution_residual_materiality(
            trend_period_payload.reconciliation_payload.get("residual_materiality")
        ),
        supportability_evidence=parse_attribution_supportability_evidence(
            trend_period_payload.supportability_evidence_payload
        ),
    )


def parse_attribution_reasons(payload: Any) -> list[AttributionReasonView]:
    if not isinstance(payload, list):
        return []
    reasons: list[AttributionReasonView] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        reasons.append(
            AttributionReasonView(
                code=safe_str(item.get("code")) or "unknown",
                severity=safe_str(item.get("severity")) or "warning",
                message=safe_str(item.get("message")) or "Attribution supportability reason.",
                affected_group_count=safe_int(item.get("affected_group_count")) or 0,
            )
        )
    return reasons


def parse_attribution_residual_materiality(
    payload: Any,
) -> AttributionResidualMaterialityView | None:
    if not isinstance(payload, dict):
        return None
    absolute_residual = quantize_optional(payload.get("absolute_residual"))
    warning_threshold = quantize_optional(payload.get("warning_threshold"))
    material_threshold = quantize_optional(payload.get("material_threshold"))
    if absolute_residual is None or warning_threshold is None or material_threshold is None:
        return None
    return AttributionResidualMaterialityView(
        classification=safe_str(payload.get("classification")) or "immaterial",
        treatment=safe_str(payload.get("treatment")) or "no_action",
        absolute_residual_pct=absolute_residual,
        warning_threshold_pct=warning_threshold,
        material_threshold_pct=material_threshold,
    )


def parse_attribution_supportability_evidence(
    payload: Any,
) -> AttributionSupportabilityEvidenceView | None:
    if not isinstance(payload, dict):
        return None
    return AttributionSupportabilityEvidenceView(
        portfolio_only_group_count=safe_int(payload.get("portfolio_only_group_count")) or 0,
        benchmark_only_group_count=safe_int(payload.get("benchmark_only_group_count")) or 0,
        unclassified_group_count=safe_int(payload.get("unclassified_group_count")) or 0,
        missing_benchmark_return_count=safe_int(payload.get("missing_benchmark_return_count")) or 0,
        negative_weight_count=safe_int(payload.get("negative_weight_count")) or 0,
        zero_portfolio_exposure_count=safe_int(payload.get("zero_portfolio_exposure_count")) or 0,
        currency_attribution_status=safe_str(payload.get("currency_attribution_status"))
        or "not_requested",
        linking_status=safe_str(payload.get("linking_status")) or "not_requested",
    )


def _build_attribution_levels(
    *,
    levels_payload: Any,
    row_key: str,
    quantize_effects_with_policy: bool,
) -> list[AttributionLevelView]:
    levels: list[AttributionLevelView] = []
    if not isinstance(levels_payload, list):
        return levels
    for level_payload in levels_payload:
        if not isinstance(level_payload, dict):
            continue
        totals_payload = level_payload.get("totals", {})
        if not isinstance(totals_payload, dict):
            totals_payload = {}
        total_effect = quantize_optional(totals_payload.get("total_effect"))
        levels.append(
            AttributionLevelView(
                dimension=str(level_payload.get("dimension", "Dimension")),
                allocation_total_pct=quantize_optional(totals_payload.get("allocation")),
                selection_total_pct=quantize_optional(totals_payload.get("selection")),
                interaction_total_pct=quantize_optional(totals_payload.get("interaction")),
                total_effect_pct=total_effect or 0.0,
                rows=_build_attribution_rows(
                    rows_payload=level_payload.get(row_key, []),
                    quantize_effects_with_policy=quantize_effects_with_policy,
                ),
            )
        )
    return levels


def _build_attribution_rows(
    *,
    rows_payload: Any,
    quantize_effects_with_policy: bool,
) -> list[AttributionRowView]:
    rows: list[AttributionRowView] = []
    if not isinstance(rows_payload, list):
        return rows
    for row_payload in rows_payload:
        if not isinstance(row_payload, dict):
            continue
        rows.append(
            AttributionRowView(
                key_label=format_key_label(row_payload.get("key")),
                portfolio_weight_avg_pct=weight_to_pct(row_payload.get("portfolio_weight_avg")),
                benchmark_weight_avg_pct=weight_to_pct(row_payload.get("benchmark_weight_avg")),
                portfolio_return_pct=quantize_optional(row_payload.get("portfolio_return")),
                benchmark_return_pct=quantize_optional(row_payload.get("benchmark_return")),
                allocation_pct=_effect_pct(
                    row_payload.get("allocation", 0.0),
                    quantize_with_policy=quantize_effects_with_policy,
                ),
                selection_pct=_effect_pct(
                    row_payload.get("selection", 0.0),
                    quantize_with_policy=quantize_effects_with_policy,
                ),
                interaction_pct=_effect_pct(
                    row_payload.get("interaction", 0.0),
                    quantize_with_policy=quantize_effects_with_policy,
                ),
                total_effect_pct=_effect_pct(
                    row_payload.get("total_effect", 0.0),
                    quantize_with_policy=quantize_effects_with_policy,
                ),
            )
        )
    return rows


def _effect_pct(value: Any, *, quantize_with_policy: bool):
    if quantize_with_policy:
        return quantize_optional(value) or 0.0
    return quantize_optional(value) or 0.0
