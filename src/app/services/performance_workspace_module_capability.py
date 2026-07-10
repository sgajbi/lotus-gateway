from __future__ import annotations

from collections.abc import Sequence

from app.contracts.performance_workspace import PerformanceModuleCapability


def build_module_capability(
    state: str,
    reason: str | None = None,
    *,
    coverage_level: str | None = None,
    fallback_available: bool | None = None,
    earliest_available_date: str | None = None,
    latest_available_date: str | None = None,
    supported_dimensions: Sequence[str] | None = None,
    supported_frequencies: Sequence[str] | None = None,
) -> PerformanceModuleCapability:
    return PerformanceModuleCapability(
        state=state,
        reason=reason,
        coverage_level=coverage_level,
        fallback_available=fallback_available,
        earliest_available_date=earliest_available_date,
        latest_available_date=latest_available_date,
        supported_dimensions=list(supported_dimensions) if supported_dimensions else None,
        supported_frequencies=list(supported_frequencies) if supported_frequencies else None,
    )
