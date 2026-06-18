from __future__ import annotations

import asyncio
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, TypeAlias

from fastapi import HTTPException

from app.contracts.performance_evidence import (
    PerformanceCalculationEvidenceView,
    PerformanceEvidenceArtifactView,
    PerformanceEvidenceStageView,
    PerformanceEvidenceUpstreamSnapshotView,
)
from app.services.workspace_client_protocols import PerformanceWorkspaceAnalyticsClient

UpstreamPayload: TypeAlias = dict[str, Any]
UpstreamResult: TypeAlias = tuple[int, UpstreamPayload]

DEFAULT_LINEAGE_COMPLETION_POLL_ATTEMPTS = 3
DEFAULT_LINEAGE_COMPLETION_POLL_INTERVAL_SECONDS = 0.25


@dataclass(frozen=True)
class CalculationEvidencePayloads:
    execution_status_code: int
    lineage_status_code: int
    execution_data: dict[str, Any]
    lineage_data: dict[str, Any]


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
