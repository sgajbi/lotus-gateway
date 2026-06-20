from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import Any

from app.contracts.performance_attribution import PerformanceAttributionTrendRow
from app.contracts.workbench import WorkbenchPartialFailure
from app.services.performance_workspace_attribution_supportability import (
    parse_attribution_residual_materiality,
    parse_attribution_supportability_evidence,
)
from app.services.performance_workspace_failures import build_performance_failure
from app.services.performance_workspace_parsing import (
    format_attribution_trend_label,
    quantize_optional,
    safe_str,
    safe_str_list,
)
from app.services.performance_workspace_returns import resolve_results_period_key

AttributionTrendResult = tuple[int, dict[str, Any]] | BaseException


@dataclass(frozen=True)
class AttributionTrendPeriodPayload:
    period_payload: dict[str, Any]
    reconciliation_payload: dict[str, Any]
    totals_payload: dict[str, Any]
    supportability_evidence_payload: Any


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
