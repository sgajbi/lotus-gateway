from typing import Annotated

from fastapi import APIRouter, Header, Path

from app.contracts.reporting import (
    ReportInputSnapshotRecord,
    ReportSnapshotLineageResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.reporting_context import reporting_context_headers
from app.routers.reporting_errors import report_job_error_response
from app.services.reporting_service_provider import reporting_job_query_service

router = APIRouter(prefix="/api/v1/reports/snapshots", tags=["Reports"])


@router.get(
    "/{snapshot_id}",
    response_model=ReportInputSnapshotRecord,
    summary="Get report input snapshot",
    description=(
        "Return a stable report input snapshot for audit and diagnostics using the "
        "governed gateway boundary."
    ),
    responses={
        **report_job_error_response(
            404,
            example_key="report_snapshot_not_found",
            description="Returned when the requested snapshot identifier does not exist.",
        ),
        **report_job_error_response(
            502,
            example_key="report_job_upstream_unavailable",
            description="Returned when lotus-report is unavailable or returns an unsafe failure.",
        ),
    },
)
async def get_report_snapshot(
    snapshot_id: Annotated[str, Path(description="Opaque report snapshot identifier.")],
    actor_id: Annotated[str | None, Header(alias="X-Actor-Id")] = None,
    caller_application: Annotated[str | None, Header(alias="X-Caller-Application")] = None,
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    region: Annotated[str | None, Header(alias="X-Region")] = None,
    booking_center_code: Annotated[str | None, Header(alias="X-Booking-Center-Code")] = None,
    role: Annotated[str | None, Header(alias="X-Role")] = None,
) -> ReportInputSnapshotRecord:
    return await reporting_job_query_service().get_report_snapshot(
        snapshot_id=snapshot_id,
        caller_headers=reporting_context_headers(
            actor_id=actor_id,
            caller_application=caller_application,
            tenant_id=tenant_id,
            region=region,
            booking_center_code=booking_center_code,
            role=role,
        ),
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
    actor_id: Annotated[str | None, Header(alias="X-Actor-Id")] = None,
    caller_application: Annotated[str | None, Header(alias="X-Caller-Application")] = None,
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    region: Annotated[str | None, Header(alias="X-Region")] = None,
    booking_center_code: Annotated[str | None, Header(alias="X-Booking-Center-Code")] = None,
    role: Annotated[str | None, Header(alias="X-Role")] = None,
) -> ReportSnapshotLineageResponse:
    return await reporting_job_query_service().get_report_snapshot_lineage(
        snapshot_id=snapshot_id,
        caller_headers=reporting_context_headers(
            actor_id=actor_id,
            caller_application=caller_application,
            tenant_id=tenant_id,
            region=region,
            booking_center_code=booking_center_code,
            role=role,
        ),
        correlation_id=correlation_id_var.get(),
    )
