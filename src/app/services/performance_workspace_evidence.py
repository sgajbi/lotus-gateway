from __future__ import annotations

import asyncio
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, TypeAlias

from app.contracts.performance_evidence import (
    PerformanceCalculationEvidenceView,
    PerformanceEvidenceView,
    PerformanceSourceSupportabilityView,
)
from app.contracts.workbench import WorkbenchPartialFailure
from app.services.performance_calculation_evidence import (
    DEFAULT_LINEAGE_COMPLETION_POLL_ATTEMPTS,
    DEFAULT_LINEAGE_COMPLETION_POLL_INTERVAL_SECONDS,
    CalculationEvidencePayloads,
    await_recent_evidence_completion,
    build_calculation_evidence_view,
    build_evidence_artifact_views,
    build_evidence_stage_views,
    build_evidence_upstream_snapshot_views,
    calculation_evidence_payloads,
    calculation_evidence_reason,
    evidence_status_reason,
    execution_is_complete,
    execution_lineage_stage_complete,
    fetch_calculation_evidence,
    fetch_performance_evidence_artifact,
    gateway_evidence_artifact_url,
    lineage_is_complete,
    lineage_is_transient,
    performance_evidence_artifact_failure_detail,
    refresh_execution_after_lineage_completion,
)
from app.services.performance_workspace_capabilities import (
    SUPPORTED_ATTRIBUTION_DIMENSIONS,
    SUPPORTED_CONTRIBUTION_DIMENSIONS,
)
from app.services.performance_workspace_failures import build_performance_failure
from app.services.source_supportability import (
    extract_calculation_supportability,
    source_supportability_reason,
)
from app.services.workspace_client_protocols import PerformanceWorkspaceAnalyticsClient

UpstreamPayload: TypeAlias = dict[str, Any]
UpstreamResult: TypeAlias = tuple[int, UpstreamPayload]
GatheredResult: TypeAlias = UpstreamResult | BaseException

__all__ = [
    "DEFAULT_LINEAGE_COMPLETION_POLL_ATTEMPTS",
    "DEFAULT_LINEAGE_COMPLETION_POLL_INTERVAL_SECONDS",
    "CalculationEvidencePayloads",
    "EvidenceViewFetchState",
    "EvidenceViewRequestContext",
    "await_recent_evidence_completion",
    "build_calculation_evidence_view",
    "build_evidence_artifact_views",
    "build_evidence_stage_views",
    "build_evidence_upstream_snapshot_views",
    "build_performance_evidence_view",
    "build_source_supportability",
    "calculation_evidence_payloads",
    "calculation_evidence_reason",
    "evidence_status_reason",
    "execution_is_complete",
    "execution_lineage_stage_complete",
    "extract_calculation_id_from_result",
    "fetch_calculation_evidence",
    "fetch_evidence_view_state",
    "fetch_performance_evidence_artifact",
    "gateway_evidence_artifact_url",
    "lineage_is_complete",
    "lineage_is_transient",
    "performance_evidence_artifact_failure_detail",
    "refresh_execution_after_lineage_completion",
    "resolve_evidence_reason",
    "resolve_evidence_state",
    "resolve_evidence_view_response",
]


@dataclass(frozen=True)
class EvidenceViewRequestContext:
    portfolio_id: str
    as_of_date: str
    period: str
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


def extract_calculation_id_from_result(result: GatheredResult | None) -> str | None:
    if result is None or isinstance(result, BaseException):
        return None
    _, payload = result
    if not isinstance(payload, dict):
        return None
    calculation_id = payload.get("calculation_id")
    if calculation_id is None:
        return None
    return str(calculation_id)


def build_evidence_requested_items(
    calculations: Sequence[tuple[str, str | None]],
) -> list[tuple[str, str]]:
    return [
        (role, calculation_id)
        for role, calculation_id in calculations
        if calculation_id is not None
    ]


async def fetch_evidence_view_state(
    *,
    analytics_client: PerformanceWorkspaceAnalyticsClient,
    context: EvidenceViewRequestContext,
    poll_interval_seconds: float = DEFAULT_LINEAGE_COMPLETION_POLL_INTERVAL_SECONDS,
) -> EvidenceViewFetchState:
    requested_items = build_evidence_requested_items(context.calculations)
    source_supportability = build_source_supportability(context.source_results)
    if not requested_items:
        return EvidenceViewFetchState(
            source_supportability=source_supportability,
            requested_items=[],
            evidence_items=[],
        )
    evidence_items = await asyncio.gather(
        *[
            fetch_calculation_evidence(
                analytics_client=analytics_client,
                portfolio_id=context.portfolio_id,
                calculation_role=role,
                calculation_id=calculation_id,
                correlation_id=context.correlation_id,
                poll_interval_seconds=poll_interval_seconds,
            )
            for role, calculation_id in requested_items
        ]
    )
    return EvidenceViewFetchState(
        source_supportability=source_supportability,
        requested_items=requested_items,
        evidence_items=list(evidence_items),
    )


def resolve_evidence_view_response(
    *,
    context: EvidenceViewRequestContext,
    fetch_state: EvidenceViewFetchState,
    warnings: list[str],
    partial_failures: list[WorkbenchPartialFailure],
) -> PerformanceEvidenceView:
    if not fetch_state.requested_items:
        return build_empty_evidence_view_response(
            context=context,
            source_supportability=fetch_state.source_supportability,
        )
    if fetch_state.backed_count == 0:
        warnings.append("PERFORMANCE_EVIDENCE_UNAVAILABLE")
        return build_unavailable_evidence_view_response(
            context=context,
            fetch_state=fetch_state,
        )
    if fetch_state.complete_count == len(fetch_state.evidence_items):
        return build_supported_evidence_view_response(
            context=context,
            fetch_state=fetch_state,
        )
    record_partial_evidence_view(
        warnings=warnings,
        partial_failures=partial_failures,
    )
    return build_partial_evidence_view_response(
        context=context,
        fetch_state=fetch_state,
    )


def build_empty_evidence_view_response(
    *,
    context: EvidenceViewRequestContext,
    source_supportability: Sequence[PerformanceSourceSupportabilityView],
) -> PerformanceEvidenceView:
    return build_performance_evidence_view(
        state="unavailable",
        reason="No durable calculation evidence is available for the current selection.",
        as_of_date=context.as_of_date,
        period=context.period,
        basis=context.basis,
        benchmark_code=context.benchmark_code,
        contract_version=context.contract_version,
        limitations=["No durable calculation evidence is available."],
        calculations=[],
        source_supportability=source_supportability,
    )


def build_unavailable_evidence_view_response(
    *,
    context: EvidenceViewRequestContext,
    fetch_state: EvidenceViewFetchState,
) -> PerformanceEvidenceView:
    reason = "Gateway could not resolve execution or lineage evidence from lotus-performance."
    return build_performance_evidence_view(
        state="unavailable",
        reason=reason,
        as_of_date=context.as_of_date,
        period=context.period,
        basis=context.basis,
        benchmark_code=context.benchmark_code,
        contract_version=context.contract_version,
        limitations=[reason],
        calculations=fetch_state.evidence_items,
        source_supportability=fetch_state.source_supportability,
    )


def build_supported_evidence_view_response(
    *,
    context: EvidenceViewRequestContext,
    fetch_state: EvidenceViewFetchState,
) -> PerformanceEvidenceView:
    evidence_state = resolve_evidence_state(
        evidence_state="supported",
        source_supportability=fetch_state.source_supportability,
    )
    evidence_reason = resolve_evidence_reason(
        evidence_state=evidence_state,
        supported_reason=(
            "Execution status, upstream lineage, and artifact inventory "
            "are exposed for the current performance view."
        ),
        source_supportability=fetch_state.source_supportability,
    )
    return build_performance_evidence_view(
        state=evidence_state,
        reason=evidence_reason,
        as_of_date=context.as_of_date,
        period=context.period,
        basis=context.basis,
        benchmark_code=context.benchmark_code,
        contract_version=context.contract_version,
        limitations=[] if evidence_state == "supported" else [evidence_reason],
        calculations=fetch_state.evidence_items,
        source_supportability=fetch_state.source_supportability,
    )


def build_partial_evidence_view_response(
    *,
    context: EvidenceViewRequestContext,
    fetch_state: EvidenceViewFetchState,
) -> PerformanceEvidenceView:
    reason = (
        "One or more performance calculations still have pending, failed, "
        "or unavailable lineage evidence."
    )
    return build_performance_evidence_view(
        state="partial",
        reason=reason,
        as_of_date=context.as_of_date,
        period=context.period,
        basis=context.basis,
        benchmark_code=context.benchmark_code,
        contract_version=context.contract_version,
        limitations=[reason],
        calculations=fetch_state.evidence_items,
        source_supportability=fetch_state.source_supportability,
    )


def record_partial_evidence_view(
    *,
    warnings: list[str],
    partial_failures: list[WorkbenchPartialFailure],
) -> None:
    warnings.append("PERFORMANCE_EVIDENCE_PARTIAL")
    partial_failures.append(
        build_performance_failure(
            "lotus-performance",
            "PERFORMANCE_EVIDENCE_PARTIAL",
            (
                "Gateway resolved only partial execution or lineage evidence "
                "for one or more performance calculations."
            ),
        )
    )


def build_performance_evidence_view(
    *,
    state: str,
    reason: str,
    as_of_date: str,
    period: str,
    basis: str,
    benchmark_code: str | None,
    contract_version: str,
    limitations: list[str],
    calculations: Sequence[PerformanceCalculationEvidenceView],
    source_supportability: Sequence[PerformanceSourceSupportabilityView],
) -> PerformanceEvidenceView:
    return PerformanceEvidenceView(
        state=state,
        as_of_date=as_of_date,
        period=period,
        basis=basis,
        benchmark_code=benchmark_code,
        calculation_scope="performance_workspace",
        source_services=build_evidence_source_services(
            calculations=calculations,
            source_supportability=source_supportability,
        ),
        input_freshness=build_evidence_input_freshness(
            as_of_date=as_of_date,
            benchmark_code=benchmark_code,
            calculations=calculations,
        ),
        methodology_references=["lotus-performance/docs/methodologies"],
        calculation_versions=build_evidence_calculation_versions(
            contract_version=contract_version,
            calculations=calculations,
        ),
        coverage=build_evidence_coverage(),
        fallbacks=build_evidence_fallbacks(calculations),
        limitations=limitations,
        generated_at=None,
        reason=reason,
        calculations=list(calculations),
        source_supportability=list(source_supportability),
    )


def build_evidence_source_services(
    *,
    calculations: Sequence[PerformanceCalculationEvidenceView],
    source_supportability: Sequence[PerformanceSourceSupportabilityView],
) -> list[str]:
    return sorted(
        {service for service in ["lotus-performance"] if calculations}
        | {item.source_service for item in source_supportability if item.source_service is not None}
    )


def build_evidence_input_freshness(
    *,
    as_of_date: str,
    benchmark_code: str | None,
    calculations: Sequence[PerformanceCalculationEvidenceView],
) -> dict[str, str]:
    upstream_dates = {
        snapshot.as_of_date
        for item in calculations
        for snapshot in item.upstream_snapshots
        if snapshot.as_of_date
    }
    performance_freshness = (
        "fresh" if as_of_date in upstream_dates or not upstream_dates else "stale"
    )
    input_freshness = {"performance": performance_freshness}
    if benchmark_code:
        input_freshness["benchmark"] = input_freshness["performance"]
    return input_freshness


def build_evidence_calculation_versions(
    *,
    contract_version: str,
    calculations: Sequence[PerformanceCalculationEvidenceView],
) -> dict[str, str]:
    calculation_versions = {"gateway_contract": contract_version}
    analytics_types = {
        item.analytics_type for item in calculations if item.analytics_type is not None
    }
    if analytics_types:
        calculation_versions["analytics_types"] = ",".join(sorted(analytics_types))
    return calculation_versions


def build_evidence_coverage() -> dict[str, list[str]]:
    return {
        "supported_dimensions": sorted(
            set(SUPPORTED_CONTRIBUTION_DIMENSIONS) | set(SUPPORTED_ATTRIBUTION_DIMENSIONS)
        ),
        "unsupported_dimensions": [
            dimension
            for dimension in ("issuer",)
            if dimension not in SUPPORTED_CONTRIBUTION_DIMENSIONS
            and dimension not in SUPPORTED_ATTRIBUTION_DIMENSIONS
        ],
    }


def build_evidence_fallbacks(
    calculations: Sequence[PerformanceCalculationEvidenceView],
) -> list[str]:
    return [item.reason for item in calculations if item.reason is not None and item.reason.strip()]


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
