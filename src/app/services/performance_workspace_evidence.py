from __future__ import annotations

import asyncio
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, TypeAlias

from fastapi import HTTPException

from app.contracts.performance_evidence import (
    PerformanceCalculationEvidenceView,
    PerformanceEvidenceArtifactView,
    PerformanceEvidenceStageView,
    PerformanceEvidenceUpstreamSnapshotView,
    PerformanceEvidenceView,
    PerformanceSourceSupportabilityView,
)
from app.contracts.workbench import WorkbenchPartialFailure
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

DEFAULT_LINEAGE_COMPLETION_POLL_ATTEMPTS = 3
DEFAULT_LINEAGE_COMPLETION_POLL_INTERVAL_SECONDS = 0.25


@dataclass(frozen=True)
class CalculationEvidencePayloads:
    execution_status_code: int
    lineage_status_code: int
    execution_data: dict[str, Any]
    lineage_data: dict[str, Any]


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


async def fetch_performance_evidence_artifact(
    *,
    analytics_client: PerformanceWorkspaceAnalyticsClient,
    calculation_id: str,
    artifact_name: str,
    correlation_id: str,
) -> tuple[bytes, str | None]:
    status_code, content, content_type = await analytics_client.get_lineage_artifact(
        calculation_id=calculation_id,
        artifact_name=artifact_name,
        correlation_id=correlation_id,
    )
    if status_code >= 400:
        raise HTTPException(
            status_code=status_code,
            detail=performance_evidence_artifact_failure_detail(content),
        )
    return content, content_type


def performance_evidence_artifact_failure_detail(content: bytes) -> str:
    if not content:
        return "Performance evidence artifact is unavailable."
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return "Performance evidence artifact retrieval failed."


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


def execution_is_complete(execution_result: UpstreamResult) -> bool:
    status_code, payload = execution_result
    if status_code >= 400 or not isinstance(payload, Mapping):
        return False
    return str(payload.get("status", "")).lower() == "complete"


def lineage_is_complete(lineage_result: UpstreamResult) -> bool:
    status_code, payload = lineage_result
    if status_code >= 400 or not isinstance(payload, Mapping):
        return False
    return str(payload.get("status", "")).lower() == "complete"


def lineage_is_transient(lineage_result: UpstreamResult) -> bool:
    status_code, payload = lineage_result
    if status_code >= 400 or not isinstance(payload, Mapping):
        return False
    return str(payload.get("status", "")).lower() in {"pending", "in_progress"}


def execution_lineage_stage_complete(execution_result: UpstreamResult) -> bool:
    status_code, payload = execution_result
    if status_code >= 400 or not isinstance(payload, Mapping):
        return False
    stages = payload.get("stages", [])
    if not isinstance(stages, list):
        return False
    return any(
        isinstance(stage, Mapping)
        and str(stage.get("stage_name", "")).lower() == "lineage_materialization"
        and str(stage.get("status", "")).lower() == "complete"
        for stage in stages
    )


async def refresh_execution_after_lineage_completion(
    *,
    analytics_client: PerformanceWorkspaceAnalyticsClient,
    calculation_id: str,
    correlation_id: str,
    execution_result: UpstreamResult,
) -> UpstreamResult:
    if execution_lineage_stage_complete(execution_result):
        return execution_result
    refreshed_result = await analytics_client.get_execution(
        calculation_id=calculation_id,
        correlation_id=correlation_id,
    )
    if refreshed_result[0] >= 400:
        return execution_result
    return refreshed_result


async def await_recent_evidence_completion(
    *,
    analytics_client: PerformanceWorkspaceAnalyticsClient,
    calculation_id: str,
    correlation_id: str,
    execution_result: UpstreamResult,
    lineage_result: UpstreamResult,
    poll_attempts: int = DEFAULT_LINEAGE_COMPLETION_POLL_ATTEMPTS,
    poll_interval_seconds: float = DEFAULT_LINEAGE_COMPLETION_POLL_INTERVAL_SECONDS,
) -> tuple[UpstreamResult, UpstreamResult]:
    if not execution_is_complete(execution_result):
        return execution_result, lineage_result
    if lineage_is_complete(lineage_result):
        refreshed_execution = await refresh_execution_after_lineage_completion(
            analytics_client=analytics_client,
            calculation_id=calculation_id,
            correlation_id=correlation_id,
            execution_result=execution_result,
        )
        return refreshed_execution, lineage_result
    if not lineage_is_transient(lineage_result):
        return execution_result, lineage_result

    latest_result = lineage_result
    for _ in range(poll_attempts):
        if poll_interval_seconds > 0:
            await asyncio.sleep(poll_interval_seconds)
        latest_result = await analytics_client.get_lineage(
            calculation_id=calculation_id,
            correlation_id=correlation_id,
        )
        if lineage_is_complete(latest_result):
            refreshed_execution = await refresh_execution_after_lineage_completion(
                analytics_client=analytics_client,
                calculation_id=calculation_id,
                correlation_id=correlation_id,
                execution_result=execution_result,
            )
            return refreshed_execution, latest_result
        if not lineage_is_transient(latest_result):
            return execution_result, latest_result
    return execution_result, latest_result


async def fetch_calculation_evidence(
    *,
    analytics_client: PerformanceWorkspaceAnalyticsClient,
    portfolio_id: str,
    calculation_role: str,
    calculation_id: str,
    correlation_id: str,
    poll_attempts: int = DEFAULT_LINEAGE_COMPLETION_POLL_ATTEMPTS,
    poll_interval_seconds: float = DEFAULT_LINEAGE_COMPLETION_POLL_INTERVAL_SECONDS,
) -> PerformanceCalculationEvidenceView:
    execution_result, lineage_result = await asyncio.gather(
        analytics_client.get_execution(
            calculation_id=calculation_id,
            correlation_id=correlation_id,
        ),
        analytics_client.get_lineage(
            calculation_id=calculation_id,
            correlation_id=correlation_id,
        ),
    )
    execution_result, lineage_result = await await_recent_evidence_completion(
        analytics_client=analytics_client,
        calculation_id=calculation_id,
        correlation_id=correlation_id,
        execution_result=execution_result,
        lineage_result=lineage_result,
        poll_attempts=poll_attempts,
        poll_interval_seconds=poll_interval_seconds,
    )
    return build_calculation_evidence_view(
        portfolio_id=portfolio_id,
        calculation_role=calculation_role,
        calculation_id=calculation_id,
        execution_result=execution_result,
        lineage_result=lineage_result,
    )


def build_calculation_evidence_view(
    *,
    portfolio_id: str,
    calculation_role: str,
    calculation_id: str,
    execution_result: UpstreamResult,
    lineage_result: UpstreamResult,
) -> PerformanceCalculationEvidenceView:
    payloads = calculation_evidence_payloads(
        execution_result=execution_result,
        lineage_result=lineage_result,
    )

    return PerformanceCalculationEvidenceView(
        calculation_role=calculation_role,
        calculation_id=calculation_id,
        analytics_type=_safe_str(payloads.execution_data.get("analytics_type")),
        execution_status=_safe_str(payloads.execution_data.get("status")),
        execution_mode=_safe_str(payloads.execution_data.get("execution_mode")),
        lineage_status=_safe_str(payloads.lineage_data.get("status")),
        stage_statuses=build_evidence_stage_views(payloads.execution_data),
        upstream_snapshots=build_evidence_upstream_snapshot_views(payloads.execution_data),
        artifacts=build_evidence_artifact_views(
            portfolio_id=portfolio_id,
            calculation_id=calculation_id,
            lineage_data=payloads.lineage_data,
        ),
        reason=calculation_evidence_reason(payloads),
    )


def calculation_evidence_payloads(
    *,
    execution_result: UpstreamResult,
    lineage_result: UpstreamResult,
) -> CalculationEvidencePayloads:
    execution_status_code, execution_payload = execution_result
    lineage_status_code, lineage_payload = lineage_result
    return CalculationEvidencePayloads(
        execution_status_code=execution_status_code,
        lineage_status_code=lineage_status_code,
        execution_data=execution_payload if isinstance(execution_payload, dict) else {},
        lineage_data=lineage_payload if isinstance(lineage_payload, dict) else {},
    )


def calculation_evidence_reason(payloads: CalculationEvidencePayloads) -> str | None:
    execution_available = payloads.execution_status_code < 400 and bool(payloads.execution_data)
    lineage_available = payloads.lineage_status_code < 400 and bool(payloads.lineage_data)
    reason_parts: list[str] = []
    if not execution_available:
        reason_parts.append(
            "Execution evidence unavailable "
            f"({evidence_status_reason(payloads.execution_status_code, payloads.execution_data)})."
        )
    if not lineage_available:
        reason_parts.append(
            "Lineage evidence unavailable "
            f"({evidence_status_reason(payloads.lineage_status_code, payloads.lineage_data)})."
        )
    elif str(payloads.lineage_data.get("status")) != "complete":
        reason_parts.append(
            "Lineage is "
            f"{str(payloads.lineage_data.get('status', 'unavailable'))} in lotus-performance."
        )
    return " ".join(reason_parts) if reason_parts else None


def build_evidence_stage_views(
    execution_data: Mapping[str, Any],
) -> list[PerformanceEvidenceStageView]:
    stages_payload = execution_data.get("stages", [])
    if not isinstance(stages_payload, list):
        return []
    return [
        PerformanceEvidenceStageView(
            stage_name=str(stage_payload.get("stage_name", "")),
            status=str(stage_payload.get("status", "")),
            completed_at_utc=_safe_str(stage_payload.get("completed_at_utc")),
        )
        for stage_payload in stages_payload
        if isinstance(stage_payload, dict)
    ]


def build_evidence_upstream_snapshot_views(
    execution_data: Mapping[str, Any],
) -> list[PerformanceEvidenceUpstreamSnapshotView]:
    snapshots_payload = execution_data.get("upstream_snapshots", [])
    if not isinstance(snapshots_payload, list):
        return []
    return [
        PerformanceEvidenceUpstreamSnapshotView(
            upstream_endpoint=str(snapshot_payload.get("upstream_endpoint", "")),
            source_identifier=str(snapshot_payload.get("source_identifier", "")),
            as_of_date=str(snapshot_payload.get("as_of_date", "")),
            retrieval_status=str(snapshot_payload.get("retrieval_status", "")),
        )
        for snapshot_payload in snapshots_payload
        if isinstance(snapshot_payload, dict)
    ]


def build_evidence_artifact_views(
    *,
    portfolio_id: str,
    calculation_id: str,
    lineage_data: Mapping[str, Any],
) -> list[PerformanceEvidenceArtifactView]:
    artifacts_payload = lineage_data.get("artifacts", {})
    if not isinstance(artifacts_payload, Mapping):
        return []
    return [
        PerformanceEvidenceArtifactView(
            artifact_name=artifact_name,
            url=gateway_evidence_artifact_url(
                portfolio_id=portfolio_id,
                calculation_id=calculation_id,
                artifact_name=artifact_name,
            ),
        )
        for artifact_name in sorted(str(name) for name in artifacts_payload)
    ]


def gateway_evidence_artifact_url(
    *,
    portfolio_id: str,
    calculation_id: str,
    artifact_name: str,
) -> str:
    return (
        f"/api/v1/workbench/{portfolio_id}/performance/evidence/artifacts/"
        f"{calculation_id}/{artifact_name}"
    )


def evidence_status_reason(status_code: int, payload: Mapping[str, Any]) -> str:
    if status_code >= 400:
        detail = payload.get("detail")
        return str(detail) if detail is not None else f"HTTP_{status_code}"
    return "missing payload"


def _safe_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
