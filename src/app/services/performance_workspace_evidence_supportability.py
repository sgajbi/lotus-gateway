from __future__ import annotations

from collections.abc import Mapping, Sequence

from app.contracts.performance_evidence import PerformanceSourceSupportabilityView
from app.services.performance_workspace_evidence_state import GatheredResult
from app.services.source_supportability import (
    SourceCalculationSupportability,
    extract_calculation_supportability,
    source_supportability_reason,
)

UNVERIFIED_CALCULATION_REASON = (
    "Source calculation supportability is missing or invalid; "
    "calculation qualification is unverified."
)
UNVERIFIED_CALCULATION_SUPPORTABILITY = SourceCalculationSupportability(
    state="partial",
    reason=UNVERIFIED_CALCULATION_REASON,
    freshness_bucket="unknown",
    source_service="lotus-performance",
)


def build_source_supportability(
    source_results: Sequence[GatheredResult | None],
    *,
    calculations: Sequence[tuple[str, str | None]] = (),
    metric_basis: str | None = None,
) -> list[PerformanceSourceSupportabilityView]:
    """Qualify successful calculation results, not execution, lineage, or artifact reads."""
    items: list[PerformanceSourceSupportabilityView] = []
    seen: set[str] = set()
    for index, result in enumerate(source_results):
        if result is None or isinstance(result, BaseException):
            continue
        status_code, payload = result
        if status_code == 204 or status_code >= 400 or not isinstance(payload, Mapping):
            continue
        source_supportability = (
            extract_calculation_supportability(payload) or UNVERIFIED_CALCULATION_SUPPORTABILITY
        )
        source_state = source_supportability.state
        item = PerformanceSourceSupportabilityView(
            calculation_role=calculations[index][0] if index < len(calculations) else None,
            calculation_id=str(payload["calculation_id"])
            if payload.get("calculation_id")
            else None,
            period_keys=list(payload["results_by_period"])
            if isinstance(payload.get("results_by_period"), dict)
            else [],
            metric_basis=metric_basis,
            history_coverage=source_supportability.history_coverage,
            key="source_calculation",
            state=source_supportability.performance_evidence_state,
            reason=source_supportability_reason(
                source_supportability,
                default_ready_reason=(
                    "Source calculation supportability was confirmed upstream."
                    if source_supportability.performance_evidence_state == "supported"
                    else f"Source calculation supportability is {source_state} upstream."
                ),
            ),
            freshness_bucket=source_supportability.freshness_bucket,
            source_service=source_supportability.source_service or "lotus-performance",
        )
        if (key := item.model_dump_json()) not in seen:
            seen.add(key)
            items.append(item)
    return items


def resolve_evidence_state(
    *,
    evidence_state: str,
    source_supportability: Sequence[PerformanceSourceSupportabilityView],
) -> str:
    states = {item.state for item in source_supportability}
    if states & {"unavailable"}:
        return "unavailable"
    if states - {"supported"}:
        return "partial"
    return evidence_state


def resolve_evidence_reason(
    *,
    evidence_state: str,
    supported_reason: str,
    source_supportability: Sequence[PerformanceSourceSupportabilityView],
) -> str:
    if evidence_state == "supported":
        return supported_reason
    for item in source_supportability:
        if item.state != "supported" and item.reason:
            return item.reason
    return "Source calculation supportability is partial or unavailable upstream."
