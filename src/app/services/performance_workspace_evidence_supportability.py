from __future__ import annotations

from collections.abc import Mapping, Sequence

from app.contracts.performance_evidence import PerformanceSourceSupportabilityView
from app.services.performance_workspace_evidence_state import GatheredResult
from app.services.source_supportability import (
    extract_calculation_supportability,
    source_supportability_reason,
)


def build_source_supportability(
    source_results: Sequence[GatheredResult | None],
) -> list[PerformanceSourceSupportabilityView]:
    items: list[PerformanceSourceSupportabilityView] = []
    seen: set[tuple[str, str, str | None]] = set()
    for result in source_results:
        if result is None or isinstance(result, BaseException):
            continue
        status_code, payload = result
        if status_code >= 400 or not isinstance(payload, Mapping):
            continue
        source_supportability = extract_calculation_supportability(payload)
        if source_supportability is None:
            continue
        key = (
            source_supportability.state,
            source_supportability.reason or "",
            source_supportability.freshness_bucket,
        )
        if key in seen:
            continue
        seen.add(key)
        items.append(
            PerformanceSourceSupportabilityView(
                key="source_calculation",
                state=source_supportability.performance_evidence_state,
                reason=source_supportability_reason(
                    source_supportability,
                    default_ready_reason=(
                        "Source calculation supportability was confirmed upstream."
                    ),
                ),
                freshness_bucket=source_supportability.freshness_bucket,
                source_service=source_supportability.source_service or "lotus-performance",
            )
        )
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
