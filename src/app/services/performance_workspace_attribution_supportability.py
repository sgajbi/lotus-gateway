from __future__ import annotations

from typing import Any

from app.contracts.performance_attribution import (
    AttributionReasonView,
    AttributionResidualMaterialityView,
    AttributionSupportabilityEvidenceView,
)
from app.services.performance_workspace_parsing import quantize_optional, safe_int, safe_str


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
