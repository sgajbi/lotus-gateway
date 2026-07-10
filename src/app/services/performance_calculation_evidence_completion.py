from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Any, TypeAlias

from app.services.workspace_client_protocols import PerformanceWorkspaceAnalyticsClient

UpstreamPayload: TypeAlias = dict[str, Any]
UpstreamResult: TypeAlias = tuple[int, UpstreamPayload]

DEFAULT_LINEAGE_COMPLETION_POLL_ATTEMPTS = 3
DEFAULT_LINEAGE_COMPLETION_POLL_INTERVAL_SECONDS = 0.25


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
