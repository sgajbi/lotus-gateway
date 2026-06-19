from __future__ import annotations

import asyncio
from collections.abc import Sequence

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
from app.services.performance_workspace_evidence_response import (
    build_performance_evidence_view as build_performance_evidence_view,
)
from app.services.performance_workspace_evidence_response import (
    build_source_supportability as build_source_supportability,
)
from app.services.performance_workspace_evidence_response import (
    resolve_evidence_reason as resolve_evidence_reason,
)
from app.services.performance_workspace_evidence_response import (
    resolve_evidence_state as resolve_evidence_state,
)
from app.services.performance_workspace_evidence_response import (
    resolve_evidence_view_response as resolve_evidence_view_response,
)
from app.services.performance_workspace_evidence_state import (
    EvidenceViewFetchState as EvidenceViewFetchState,
)
from app.services.performance_workspace_evidence_state import (
    EvidenceViewRequestContext as EvidenceViewRequestContext,
)
from app.services.performance_workspace_evidence_state import (
    GatheredResult as GatheredResult,
)
from app.services.workspace_client_protocols import PerformanceWorkspaceAnalyticsClient

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
