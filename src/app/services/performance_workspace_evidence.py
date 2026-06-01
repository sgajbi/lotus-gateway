from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, TypeAlias

from app.contracts.performance_workspace import (
    PerformanceCalculationEvidenceView,
    PerformanceEvidenceArtifactView,
    PerformanceEvidenceStageView,
    PerformanceEvidenceUpstreamSnapshotView,
    PerformanceEvidenceView,
    PerformanceSourceSupportabilityView,
)
from app.services.performance_workspace_capabilities import (
    SUPPORTED_ATTRIBUTION_DIMENSIONS,
    SUPPORTED_CONTRIBUTION_DIMENSIONS,
)
from app.services.source_supportability import (
    extract_calculation_supportability,
    source_supportability_reason,
)

UpstreamPayload: TypeAlias = dict[str, Any]
UpstreamResult: TypeAlias = tuple[int, UpstreamPayload]
GatheredResult: TypeAlias = UpstreamResult | BaseException


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
    source_services = sorted(
        {service for service in ["lotus-performance"] if calculations}
        | {item.source_service for item in source_supportability if item.source_service is not None}
    )
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

    unsupported_dimensions = [
        dimension
        for dimension in ("issuer",)
        if dimension not in SUPPORTED_CONTRIBUTION_DIMENSIONS
        and dimension not in SUPPORTED_ATTRIBUTION_DIMENSIONS
    ]
    calculation_versions = {"gateway_contract": contract_version}
    analytics_types = {
        item.analytics_type for item in calculations if item.analytics_type is not None
    }
    if analytics_types:
        calculation_versions["analytics_types"] = ",".join(sorted(analytics_types))

    fallbacks = [
        item.reason for item in calculations if item.reason is not None and item.reason.strip()
    ]

    return PerformanceEvidenceView(
        state=state,
        as_of_date=as_of_date,
        period=period,
        basis=basis,
        benchmark_code=benchmark_code,
        calculation_scope="performance_workspace",
        source_services=source_services,
        input_freshness=input_freshness,
        methodology_references=["lotus-performance/docs/methodologies"],
        calculation_versions=calculation_versions,
        coverage={
            "supported_dimensions": sorted(
                set(SUPPORTED_CONTRIBUTION_DIMENSIONS) | set(SUPPORTED_ATTRIBUTION_DIMENSIONS)
            ),
            "unsupported_dimensions": unsupported_dimensions,
        },
        fallbacks=fallbacks,
        limitations=limitations,
        generated_at=None,
        reason=reason,
        calculations=list(calculations),
        source_supportability=list(source_supportability),
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


def build_calculation_evidence_view(
    *,
    portfolio_id: str,
    calculation_role: str,
    calculation_id: str,
    execution_result: UpstreamResult,
    lineage_result: UpstreamResult,
) -> PerformanceCalculationEvidenceView:
    execution_status_code, execution_payload = execution_result
    lineage_status_code, lineage_payload = lineage_result

    execution_data = execution_payload if isinstance(execution_payload, dict) else {}
    lineage_data = lineage_payload if isinstance(lineage_payload, dict) else {}

    execution_available = execution_status_code < 400 and bool(execution_data)
    lineage_available = lineage_status_code < 400 and bool(lineage_data)
    reason_parts: list[str] = []
    if not execution_available:
        reason_parts.append(
            "Execution evidence unavailable "
            f"({evidence_status_reason(execution_status_code, execution_data)})."
        )
    if not lineage_available:
        reason_parts.append(
            "Lineage evidence unavailable "
            f"({evidence_status_reason(lineage_status_code, lineage_data)})."
        )
    elif str(lineage_data.get("status")) != "complete":
        reason_parts.append(
            f"Lineage is {str(lineage_data.get('status', 'unavailable'))} in lotus-performance."
        )

    stages_payload = execution_data.get("stages", [])
    snapshots_payload = execution_data.get("upstream_snapshots", [])
    artifacts_payload = lineage_data.get("artifacts", {})

    stage_statuses = []
    if isinstance(stages_payload, list):
        stage_statuses = [
            PerformanceEvidenceStageView(
                stage_name=str(stage_payload.get("stage_name", "")),
                status=str(stage_payload.get("status", "")),
                completed_at_utc=_safe_str(stage_payload.get("completed_at_utc")),
            )
            for stage_payload in stages_payload
            if isinstance(stage_payload, dict)
        ]
    upstream_snapshots = []
    if isinstance(snapshots_payload, list):
        upstream_snapshots = [
            PerformanceEvidenceUpstreamSnapshotView(
                upstream_endpoint=str(snapshot_payload.get("upstream_endpoint", "")),
                source_identifier=str(snapshot_payload.get("source_identifier", "")),
                as_of_date=str(snapshot_payload.get("as_of_date", "")),
                retrieval_status=str(snapshot_payload.get("retrieval_status", "")),
            )
            for snapshot_payload in snapshots_payload
            if isinstance(snapshot_payload, dict)
        ]
    artifacts = []
    if isinstance(artifacts_payload, Mapping):
        artifacts = [
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

    return PerformanceCalculationEvidenceView(
        calculation_role=calculation_role,
        calculation_id=calculation_id,
        analytics_type=_safe_str(execution_data.get("analytics_type")),
        execution_status=_safe_str(execution_data.get("status")),
        execution_mode=_safe_str(execution_data.get("execution_mode")),
        lineage_status=_safe_str(lineage_data.get("status")),
        stage_statuses=stage_statuses,
        upstream_snapshots=upstream_snapshots,
        artifacts=artifacts,
        reason=" ".join(reason_parts) if reason_parts else None,
    )


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
