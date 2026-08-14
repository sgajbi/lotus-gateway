from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, TypeAlias

from app.contracts.performance_evidence import (
    PerformanceCalculationEvidenceView,
    PerformanceSourceSupportabilityView,
)

UpstreamPayload: TypeAlias = dict[str, Any]
UpstreamResult: TypeAlias = tuple[int, UpstreamPayload]
GatheredResult: TypeAlias = UpstreamResult | BaseException


@dataclass(frozen=True)
class EvidenceViewRequestContext:
    portfolio_id: str
    as_of_date: str
    period: str
    report_start_date: str
    report_end_date: str
    basis: str
    benchmark_code: str | None
    contract_version: str
    correlation_id: str
    calculations: Sequence[tuple[str, str | None]]
    source_results: Sequence[GatheredResult | None]


@dataclass(frozen=True)
class EvidenceViewFetchState:
    source_supportability: list[PerformanceSourceSupportabilityView]
    requested_items: list[tuple[str, str]]
    evidence_items: list[PerformanceCalculationEvidenceView]

    @property
    def backed_count(self) -> int:
        return sum(
            1
            for item in self.evidence_items
            if item.execution_status is not None or item.lineage_status is not None
        )

    @property
    def complete_count(self) -> int:
        return sum(
            1
            for item in self.evidence_items
            if item.execution_status == "complete" and item.lineage_status == "complete"
        )
