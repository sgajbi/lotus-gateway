from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.contracts.performance_workspace import PerformanceModuleCapability
from app.services.performance_workspace_controls import SUPPORTED_WORKSPACE_FREQUENCIES
from app.services.performance_workspace_module_capability import build_module_capability

SUPPORTED_CONTRIBUTION_DIMENSIONS = ("asset_class", "sector", "country")
SUPPORTED_ATTRIBUTION_DIMENSIONS = ("asset_class", "sector", "country", "currency")


class PerformanceDetailCapabilityInputs(Protocol):
    @property
    def has_contribution_detail(self) -> bool: ...

    @property
    def has_position_ranking(self) -> bool: ...

    @property
    def has_attribution_detail(self) -> bool: ...

    @property
    def has_attribution_summary(self) -> bool: ...


@dataclass(frozen=True)
class PerformanceDetailCapabilities:
    contribution_ranking: PerformanceModuleCapability
    attribution_detail: PerformanceModuleCapability
    contribution_detail: PerformanceModuleCapability


def build_detail_capabilities(
    *,
    inputs: PerformanceDetailCapabilityInputs,
    include_detail_blocks: bool,
) -> PerformanceDetailCapabilities:
    return PerformanceDetailCapabilities(
        contribution_ranking=build_contribution_capability(
            include_detail_blocks=include_detail_blocks,
            has_position_ranking=inputs.has_position_ranking,
            has_contribution_detail=inputs.has_contribution_detail,
            supported_reason="Position-level contribution ranking is available.",
            aggregate_reason="Contribution exists, but only aggregate rows are available.",
            unavailable_reason=(
                "Contribution analytics are not available for the current selection."
            ),
        ),
        attribution_detail=build_attribution_capability(
            include_detail_blocks=include_detail_blocks,
            has_attribution_detail=inputs.has_attribution_detail,
            has_attribution_summary=inputs.has_attribution_summary,
        ),
        contribution_detail=build_contribution_capability(
            include_detail_blocks=include_detail_blocks,
            has_position_ranking=inputs.has_position_ranking,
            has_contribution_detail=inputs.has_contribution_detail,
            supported_reason="Contribution detail is available for the current selection.",
            aggregate_reason="Contribution exists, but only aggregate rows are available.",
            unavailable_reason="Contribution detail is not available for the current selection.",
        ),
    )


def build_contribution_capability(
    *,
    include_detail_blocks: bool,
    has_position_ranking: bool,
    has_contribution_detail: bool,
    supported_reason: str,
    aggregate_reason: str,
    unavailable_reason: str,
) -> PerformanceModuleCapability:
    if not include_detail_blocks or has_position_ranking:
        return build_module_capability(
            "supported",
            supported_reason,
            coverage_level="position",
            supported_dimensions=SUPPORTED_CONTRIBUTION_DIMENSIONS,
        )
    if has_contribution_detail:
        return build_module_capability(
            "partial",
            aggregate_reason,
            coverage_level="aggregate",
            fallback_available=True,
            supported_dimensions=SUPPORTED_CONTRIBUTION_DIMENSIONS,
        )
    return build_module_capability(
        "unavailable",
        unavailable_reason,
        supported_dimensions=SUPPORTED_CONTRIBUTION_DIMENSIONS,
    )


def build_attribution_capability(
    *,
    include_detail_blocks: bool,
    has_attribution_detail: bool,
    has_attribution_summary: bool,
) -> PerformanceModuleCapability:
    if not include_detail_blocks or has_attribution_detail:
        return build_module_capability(
            "supported",
            "Benchmark-relative attribution detail is available.",
            coverage_level="detail",
            supported_dimensions=SUPPORTED_ATTRIBUTION_DIMENSIONS,
            supported_frequencies=SUPPORTED_WORKSPACE_FREQUENCIES,
        )
    if has_attribution_summary:
        return build_module_capability(
            "partial",
            (
                "Benchmark-relative attribution is available only at summary level "
                "for the current selection."
            ),
            coverage_level="summary",
            fallback_available=True,
            supported_dimensions=SUPPORTED_ATTRIBUTION_DIMENSIONS,
            supported_frequencies=SUPPORTED_WORKSPACE_FREQUENCIES,
        )
    return build_module_capability(
        "unavailable",
        "Attribution detail is not available for the current selection.",
        supported_dimensions=SUPPORTED_ATTRIBUTION_DIMENSIONS,
        supported_frequencies=SUPPORTED_WORKSPACE_FREQUENCIES,
    )
