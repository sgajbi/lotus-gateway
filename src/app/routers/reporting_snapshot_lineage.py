from typing import Annotated

from fastapi import APIRouter, Path

from app.contracts.reporting import ReportSnapshotLineageResponse
from app.middleware.correlation import correlation_id_var
from app.routers.reporting_context import ReportingCallerContext
from app.routers.reporting_errors import report_job_error_response
from app.services.reporting_service_provider import reporting_job_query_service

router = APIRouter(prefix="/api/v1/reports/snapshots", tags=["Reports"])


async def _get_report_snapshot_lineage(
    *,
    snapshot_id: str,
    caller_headers: dict[str, str],
) -> ReportSnapshotLineageResponse:
    return await reporting_job_query_service().get_report_snapshot_lineage(
        snapshot_id=snapshot_id,
        caller_headers=caller_headers,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/{snapshot_id}/lineage",
    response_model=ReportSnapshotLineageResponse,
    summary="Get snapshot lineage",
    description=(
        "Return lineage evidence for an input snapshot and all upstream calls that formed it."
    ),
    responses={
        **report_job_error_response(
            404,
            example_key="report_snapshot_not_found",
            description="Returned when snapshot lineage is unavailable for this snapshot.",
        ),
        **report_job_error_response(
            502,
            example_key="report_job_upstream_unavailable",
            description="Returned when lotus-report is unavailable or returns an unsafe failure.",
        ),
    },
)
async def get_report_snapshot_lineage(
    snapshot_id: Annotated[str, Path(description="Opaque report snapshot identifier.")],
    caller_headers: ReportingCallerContext,
) -> ReportSnapshotLineageResponse:
    return await _get_report_snapshot_lineage(
        snapshot_id=snapshot_id,
        caller_headers=caller_headers,
    )
