from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from app.contracts.performance_evidence import PerformanceHistoryCoverageView


@dataclass(frozen=True)
class SourceCalculationSupportability:
    state: str
    reason: str | None
    freshness_bucket: str | None
    source_service: str | None
    history_coverage: PerformanceHistoryCoverageView | None = None

    @property
    def risk_contract_state(self) -> str:
        if self.state in {"ready", "supported"}:
            return "ready"
        if self.state in {"blocked"}:
            return "blocked"
        if self.state in {"unavailable", "error"}:
            return "unavailable"
        return "partial"

    @property
    def performance_evidence_state(self) -> str:
        if self.state in {"unavailable", "error"}:
            return "unavailable"
        if self.history_coverage is not None and self.history_coverage.status != "complete":
            return "partial"
        if self.state in {"ready", "supported"}:
            return "supported"
        return "partial"


def extract_calculation_supportability(
    payload: Mapping[str, Any],
) -> SourceCalculationSupportability | None:
    raw = payload.get("calculation_supportability")
    if not isinstance(raw, Mapping):
        metadata = payload.get("metadata")
        if isinstance(metadata, Mapping):
            raw = metadata.get("calculation_supportability")

    if not isinstance(raw, Mapping):
        return None

    state = _normalize_state(raw.get("state") or raw.get("supportability_state"))
    if state is None:
        return None

    history = raw.get("history_coverage")
    try:
        history_coverage = (
            PerformanceHistoryCoverageView.model_validate(history) if history is not None else None
        )
    except ValidationError:
        return None

    return SourceCalculationSupportability(
        state=state,
        reason=_safe_text(raw.get("reason") or raw.get("message")),
        freshness_bucket=_safe_text(raw.get("freshness_bucket")),
        source_service=_safe_text(raw.get("source_service")),
        history_coverage=history_coverage,
    )


def source_supportability_reason(
    supportability: SourceCalculationSupportability,
    *,
    default_ready_reason: str,
) -> str:
    if supportability.reason:
        return supportability.reason
    if supportability.freshness_bucket:
        return f"Source calculation supportability freshness is {supportability.freshness_bucket}."
    return default_ready_reason


def _normalize_state(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower().replace("-", "_")
    if normalized in {"supported", "ok", "complete"}:
        return "ready"
    if normalized in {
        "ready",
        "partial",
        "stale",
        "degraded",
        "unavailable",
        "unsupported",
        "blocked",
        "error",
    }:
        return normalized
    return None


def _safe_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None
