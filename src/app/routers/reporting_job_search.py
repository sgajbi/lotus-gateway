from typing import Annotated

from fastapi import APIRouter, Query

from app.contracts.reporting import (
    REPORT_JOB_LIST_RESPONSE_EXAMPLE,
    ReportJobListResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.reporting_context import ReportingCallerContext
from app.routers.reporting_errors import report_job_error_response
from app.services.reporting_service_provider import reporting_job_query_service

search_router = APIRouter(prefix="/api/v1/report-jobs", tags=["Report Jobs"])


@search_router.get(
    "",
    response_model=ReportJobListResponse,
    summary="Search report jobs for operations and support",
    description=(
        "Return a bounded list of report jobs through the governed gateway boundary. Use this "
        "endpoint when operators or support tooling need to find jobs by tenant, region, status, "
        "portfolio, as-of date, idempotency key, or correlation identifier before drilling into "
        "status or event history."
    ),
    openapi_extra={
        "responses": {
            "200": {
                "content": {
                    "application/json": {
                        "example": REPORT_JOB_LIST_RESPONSE_EXAMPLE,
                    }
                }
            }
        }
    },
    responses={
        **report_job_error_response(
            400,
            example_key="invalid_report_job_filters",
            description="Returned when no supported job-search filter is supplied.",
        ),
        **report_job_error_response(
            502,
            example_key="report_job_upstream_unavailable",
            description="Returned when lotus-report is unavailable or returns an unsafe failure.",
        ),
    },
)
async def list_report_jobs(
    caller_headers: ReportingCallerContext,
    tenant_id_filter: Annotated[
        str | None,
        Query(alias="tenantId", description="Return only jobs for this tenant identifier."),
    ] = None,
    region_filter: Annotated[
        str | None,
        Query(alias="region", description="Return only jobs for this operating region."),
    ] = None,
    status_filter: Annotated[
        str | None,
        Query(alias="status", description="Return only jobs in this current lifecycle status."),
    ] = None,
    report_type_filter: Annotated[
        str | None,
        Query(alias="reportType", description="Return only jobs for this report type."),
    ] = None,
    portfolio_id_filter: Annotated[
        str | None,
        Query(
            alias="portfolioId",
            description="Return only jobs whose scope includes this portfolio.",
        ),
    ] = None,
    as_of_date_filter: Annotated[
        str | None,
        Query(alias="asOfDate", description="Return only jobs for this business as-of date."),
    ] = None,
    idempotency_key_filter: Annotated[
        str | None,
        Query(alias="idempotencyKey", description="Return only jobs for this idempotency key."),
    ] = None,
    correlation_id_filter: Annotated[
        str | None,
        Query(
            alias="correlationId",
            description="Return only jobs for this correlation identifier.",
        ),
    ] = None,
    created_from: Annotated[
        str | None,
        Query(alias="createdFrom", description="Inclusive UTC lower bound for job creation time."),
    ] = None,
    created_to: Annotated[
        str | None,
        Query(alias="createdTo", description="Inclusive UTC upper bound for job creation time."),
    ] = None,
    limit: Annotated[
        int,
        Query(
            alias="limit",
            ge=1,
            le=100,
            description="Maximum number of report jobs returned by this bounded search.",
        ),
    ] = 25,
) -> ReportJobListResponse:
    filters = {
        "tenantId": tenant_id_filter,
        "region": region_filter,
        "status": status_filter,
        "reportType": report_type_filter,
        "portfolioId": portfolio_id_filter,
        "asOfDate": as_of_date_filter,
        "idempotencyKey": idempotency_key_filter,
        "correlationId": correlation_id_filter,
        "createdFrom": created_from,
        "createdTo": created_to,
        "limit": limit,
    }
    filters = {key: value for key, value in filters.items() if value is not None}
    return await reporting_job_query_service().list_report_jobs(
        filters=filters,
        caller_headers=caller_headers,
        correlation_id=correlation_id_var.get(),
    )
