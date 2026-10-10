from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import Literal, TypedDict

from app.config import settings
from app.services.attribution_trend_orchestration import (
    AttributionTrendAdmissionController,
    AttributionTrendOrchestrator,
)
from app.services.performance_workspace_context import AttributionTrendRequestContext
from app.services.performance_workspace_response import GatheredResult
from app.services.workspace_client_protocols import PerformanceWorkspaceAnalyticsClient

_PROCESS_ORCHESTRATOR: AttributionTrendOrchestrator[GatheredResult] | None = None
_PROCESS_ORCHESTRATOR_SIGNATURE: tuple[int, float] | None = None


def process_attribution_trend_orchestrator() -> AttributionTrendOrchestrator[GatheredResult]:
    global _PROCESS_ORCHESTRATOR, _PROCESS_ORCHESTRATOR_SIGNATURE
    signature = (
        settings.attribution_trend_concurrency_limit,
        settings.attribution_trend_deadline_seconds,
    )
    if _PROCESS_ORCHESTRATOR is None or _PROCESS_ORCHESTRATOR_SIGNATURE != signature:
        _PROCESS_ORCHESTRATOR = AttributionTrendOrchestrator(
            admission=AttributionTrendAdmissionController(signature[0]),
            deadline_seconds=signature[1],
        )
        _PROCESS_ORCHESTRATOR_SIGNATURE = signature
    return _PROCESS_ORCHESTRATOR


class AttributionTrendCompletionFields(TypedDict):
    orchestration_state: Literal["complete", "partial", "timed_out", "unavailable"]
    requested_window_count: int
    completed_window_count: int
    failed_window_count: int
    timed_out_window_count: int


async def fetch_attribution_trend_results(
    *,
    orchestrator: AttributionTrendOrchestrator,
    analytics_client: PerformanceWorkspaceAnalyticsClient,
    portfolio_id: str,
    correlation_id: str,
    detail_basis: str,
    context: AttributionTrendRequestContext,
    window_pairs: list[tuple[date, date]],
) -> Sequence[GatheredResult]:
    async def fetch_window(index: int) -> GatheredResult:
        window_start, window_end = window_pairs[index]
        return await analytics_client.get_attribution_analytics(
            portfolio_id=portfolio_id,
            report_start_date=window_start.isoformat(),
            report_end_date=window_end.isoformat(),
            period="EXPLICIT",
            metric_basis=detail_basis,
            benchmark_id=context.benchmark_code,
            dimension=context.attribution_dimension,
            correlation_id=correlation_id,
            reporting_currency=context.requested_reporting_currency,
            durable_replay=True,
        )

    return await orchestrator.run(window_count=len(window_pairs), operation=fetch_window)


def build_attribution_trend_completion_fields(
    rows: Sequence[object],
) -> AttributionTrendCompletionFields:
    states = [getattr(row, "completion_state", "failed") for row in rows]
    orchestration_state: Literal["complete", "partial", "timed_out", "unavailable"] = (
        "timed_out"
        if "timed_out" in states
        else "partial"
        if "failed" in states
        else "complete"
        if states
        else "unavailable"
    )
    return {
        "orchestration_state": orchestration_state,
        "requested_window_count": len(states),
        "completed_window_count": states.count("completed"),
        "failed_window_count": states.count("failed"),
        "timed_out_window_count": states.count("timed_out"),
    }
