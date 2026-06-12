from dataclasses import dataclass
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from app.contracts.reporting_query import (
    REPORT_JOB_LIST_RESPONSE_EXAMPLE,
    ReportJobListResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.reporting_context import ReportingCallerContext
from app.routers.reporting_errors import report_job_error_response
from app.services.reporting_service_provider import reporting_job_query_service

search_router = APIRouter(prefix="/api/v1/report-jobs", tags=["Report Jobs"])


@dataclass(frozen=True)
class ReportJobSearchFilters:
    tenant_id: str | None
    region: str | None
    status: str | None
    report_type: str | None
    portfolio_id: str | None
    as_of_date: str | None
    idempotency_key: str | None
    correlation_id: str | None
    created_from: str | None
    created_to: str | None
    limit: int

    def as_query_params(self) -> dict[str, Any]:
        filters: dict[str, Any] = {
            "tenantId": self.tenant_id,
            "region": self.region,
            "status": self.status,
            "reportType": self.report_type,
            "portfolioId": self.portfolio_id,
            "asOfDate": self.as_of_date,
            "idempotencyKey": self.idempotency_key,
            "correlationId": self.correlation_id,
            "createdFrom": self.created_from,
            "createdTo": self.created_to,
            "limit": self.limit,
        }
        return {key: value for key, value in filters.items() if value is not None}


@dataclass(frozen=True)
class ReportJobScopeFilters:
    tenant_id: str | None
    region: str | None
    status: str | None
    report_type: str | None
    portfolio_id: str | None
    as_of_date: str | None


@dataclass(frozen=True)
class ReportJobTraceFilters:
    idempotency_key: str | None
    correlation_id: str | None


@dataclass(frozen=True)
class ReportJobCreatedWindow:
    created_from: str | None
    created_to: str | None


async def _list_report_jobs(
    *,
    caller_headers: dict[str, str],
    filters: ReportJobSearchFilters,
) -> ReportJobListResponse:
    return await reporting_job_query_service().list_report_jobs(
        filters=filters.as_query_params(),
        caller_headers=caller_headers,
        correlation_id=correlation_id_var.get(),
    )


def build_report_job_scope_filters(
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
) -> ReportJobScopeFilters:
    return ReportJobScopeFilters(
        tenant_id=tenant_id_filter,
        region=region_filter,
        status=status_filter,
        report_type=report_type_filter,
        portfolio_id=portfolio_id_filter,
        as_of_date=as_of_date_filter,
    )


def build_report_job_trace_filters(
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
) -> ReportJobTraceFilters:
    return ReportJobTraceFilters(
        idempotency_key=idempotency_key_filter,
        correlation_id=correlation_id_filter,
    )


def build_report_job_created_window(
    created_from: Annotated[
        str | None,
        Query(alias="createdFrom", description="Inclusive UTC lower bound for job creation time."),
    ] = None,
    created_to: Annotated[
        str | None,
        Query(alias="createdTo", description="Inclusive UTC upper bound for job creation time."),
    ] = None,
) -> ReportJobCreatedWindow:
    return ReportJobCreatedWindow(
        created_from=created_from,
        created_to=created_to,
    )


def build_report_job_search_filters(
    scope_filters: ReportJobScopeFilters = Depends(build_report_job_scope_filters),
    trace_filters: ReportJobTraceFilters = Depends(build_report_job_trace_filters),
    created_window: ReportJobCreatedWindow = Depends(build_report_job_created_window),
    limit: Annotated[
        int,
        Query(
            alias="limit",
            ge=1,
            le=100,
            description="Maximum number of report jobs returned by this bounded search.",
        ),
    ] = 25,
) -> ReportJobSearchFilters:
    return ReportJobSearchFilters(
        tenant_id=scope_filters.tenant_id,
        region=scope_filters.region,
        status=scope_filters.status,
        report_type=scope_filters.report_type,
        portfolio_id=scope_filters.portfolio_id,
        as_of_date=scope_filters.as_of_date,
        idempotency_key=trace_filters.idempotency_key,
        correlation_id=trace_filters.correlation_id,
        created_from=created_window.created_from,
        created_to=created_window.created_to,
        limit=limit,
    )


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
    filters: ReportJobSearchFilters = Depends(build_report_job_search_filters),
) -> ReportJobListResponse:
    return await _list_report_jobs(
        caller_headers=caller_headers,
        filters=filters,
    )
