from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Body, Header, HTTPException, Path, Query, status

from app.clients.reporting_client import ReportingClient
from app.config import settings
from app.contracts.reporting import (
    REPORT_JOB_ERROR_EXAMPLES,
    REPORT_JOB_LIST_RESPONSE_EXAMPLE,
    PortfolioReviewJobRequest,
    ReportingPortfolioRequest,
    ReportingReviewResponse,
    ReportingSnapshotResponse,
    ReportingSummaryResponse,
    ReportJobErrorResponse,
    ReportJobHandleResponse,
    ReportJobListResponse,
    ReportJobStatusEventsResponse,
    ReportJobStatusResponse,
)
from app.middleware.correlation import correlation_id_var
from app.services.caller_context import caller_context_headers

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])
jobs_router = APIRouter(prefix="/api/v1/report-jobs", tags=["Report Jobs"])

SUMMARY_REQUEST_EXAMPLES = {
    "wealthSummary": {
        "summary": "Wealth summary in portfolio base currency",
        "description": "Resolve wealth and allocation sections for one reporting date.",
        "value": {
            "asOfDate": "2026-02-24",
            "sections": ["WEALTH", "ALLOCATION"],
            "allocationDimensions": ["asset_class", "currency"],
        },
    }
}

REVIEW_REQUEST_EXAMPLES = {
    "frontOfficeReview": {
        "summary": "Front-office review payload in USD",
        "description": (
            "Resolve a review payload with holdings, transactions, performance, and risk."
        ),
        "value": {
            "asOfDate": "2026-02-24",
            "reportingCurrency": "USD",
            "sections": [
                "OVERVIEW",
                "ALLOCATION",
                "INCOME_AND_ACTIVITY",
                "HOLDINGS",
                "TRANSACTIONS",
                "PERFORMANCE",
                "RISK_ANALYTICS",
            ],
            "allocationDimensions": ["asset_class"],
            "lookThroughMode": "full",
            "benchmarkCode": "BMK_PB_GLOBAL_BALANCED_60_40",
        },
    }
}

PORTFOLIO_REVIEW_JOB_REQUEST_EXAMPLES = {
    "portfolioReviewJob": {
        "summary": "Portfolio review job request",
        "description": "Create a durable job handle for asynchronous portfolio review generation.",
        "value": {
            "portfolio_scope": {"portfolio_ids": ["PB_SG_GLOBAL_BAL_001"]},
            "as_of_date": "2026-04-22",
            "requested_output_formats": ["json"],
            "reporting_currency": "USD",
            "options": {
                "sections": ["OVERVIEW", "PERFORMANCE", "RISK_ANALYTICS"],
                "benchmark_code": "BMK_PB_GLOBAL_BALANCED_60_40",
            },
        },
    }
}


def _reporting_client() -> ReportingClient:
    return ReportingClient(
        base_url=settings.reporting_aggregation_base_url,
        timeout_seconds=settings.upstream_timeout_seconds,
        max_retries=settings.upstream_max_retries,
        retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
    )


def _raise_report_job_error(status_code: int, payload: dict[str, Any]) -> None:
    detail = payload.get("detail") if isinstance(payload, dict) else None
    error_code = detail.get("code") if isinstance(detail, dict) else None
    message = detail.get("message") if isinstance(detail, dict) else "Report job unavailable."

    if status_code == status.HTTP_400_BAD_REQUEST and error_code == "missing_idempotency_key":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "missing_idempotency_key", "message": message},
        )
    if status_code == status.HTTP_400_BAD_REQUEST and error_code in {
        "missing_caller_context",
        "invalid_report_job_filters",
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )
    if status_code == status.HTTP_404_NOT_FOUND and error_code == "report_job_not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "report_job_not_found", "message": message},
        )
    if status_code == status.HTTP_409_CONFLICT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": error_code or "report_job_conflict", "message": message},
        )
    if status_code >= status.HTTP_400_BAD_REQUEST:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": "report_job_upstream_unavailable",
                "message": "Report job service is unavailable.",
            },
        )


def _job_error_response(
    status_code: int,
    *,
    example_key: str,
    description: str,
) -> dict[int | str, dict[str, Any]]:
    return {
        status_code: {
            "model": ReportJobErrorResponse,
            "description": description,
            "content": {
                "application/json": {
                    "example": REPORT_JOB_ERROR_EXAMPLES[example_key],
                }
            },
        }
    }


def _gateway_status_url(job_id: str) -> str:
    return f"/api/v1/report-jobs/{job_id}"


@router.get(
    "/{portfolio_id}/snapshot",
    response_model=ReportingSnapshotResponse,
    summary="Get reporting snapshot",
    description=(
        "Fetch report-ready aggregated snapshot rows from lotus-report for one portfolio and "
        "business date. Use this endpoint when the UI needs reporting-ready rows for a specific "
        "portfolio/date without requesting the larger summary or review payloads."
    ),
)
async def get_reporting_snapshot(
    portfolio_id: Annotated[
        str,
        Path(
            description="Canonical portfolio identifier for the requested reporting snapshot.",
            examples=["DEMO_DPM_EUR_001"],
        ),
    ],
    as_of_date: Annotated[
        str,
        Query(
            alias="asOfDate",
            description="Business as-of date in YYYY-MM-DD format for the reporting snapshot.",
            examples=["2026-02-24"],
        ),
    ],
) -> ReportingSnapshotResponse:
    client = _reporting_client()
    correlation_id = correlation_id_var.get()
    status_code, payload = await client.get_portfolio_snapshot(
        portfolio_id=portfolio_id,
        as_of_date=as_of_date,
        correlation_id=correlation_id,
    )
    if status_code >= status.HTTP_400_BAD_REQUEST:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Reporting snapshot unavailable: {payload}",
        )

    generated_at_raw = payload.get("generatedAt")
    generated_at = datetime.now(UTC)
    if isinstance(generated_at_raw, str):
        try:
            generated_at = datetime.fromisoformat(generated_at_raw.replace("Z", "+00:00"))
        except ValueError:
            generated_at = datetime.now(UTC)

    return ReportingSnapshotResponse(
        correlationId=correlation_id,
        contractVersion=settings.contract_version,
        sourceService="lotus-report",
        portfolioId=portfolio_id,
        asOfDate=as_of_date,
        generatedAt=generated_at,
        rows=payload.get("rows", []),
    )


@router.post(
    "/{portfolio_id}/summary",
    response_model=ReportingSummaryResponse,
    summary="Get reporting summary",
    description=(
        "Fetch the lotus-report-owned portfolio summary payload for one portfolio and as-of "
        "date. Use this endpoint when the UI needs the consolidated reporting summary contract "
        "rather than the lower-level snapshot rows."
    ),
)
async def get_reporting_summary(
    portfolio_id: Annotated[
        str,
        Path(
            description="Canonical portfolio identifier for the requested reporting summary.",
            examples=["DEMO_DPM_EUR_001"],
        ),
    ],
    request: Annotated[
        ReportingPortfolioRequest,
        Body(
            description=(
                "Summary request payload forwarded to lotus-report after alias normalization. "
                "Use this when the consumer needs a report-oriented summary contract for one "
                "portfolio and business date."
            ),
            openapi_examples=SUMMARY_REQUEST_EXAMPLES,
        ),
    ],
) -> ReportingSummaryResponse:
    client = _reporting_client()
    correlation_id = correlation_id_var.get()
    request_payload = request.to_upstream_payload()
    status_code, payload = await client.post_portfolio_summary(
        portfolio_id=portfolio_id,
        payload=request_payload,
        correlation_id=correlation_id,
    )
    if status_code >= status.HTTP_400_BAD_REQUEST:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Reporting summary unavailable: {payload}",
        )
    as_of_date = request.as_of_date
    return ReportingSummaryResponse(
        correlationId=correlation_id,
        contractVersion=settings.contract_version,
        sourceService="lotus-report",
        portfolioId=portfolio_id,
        asOfDate=as_of_date,
        data=payload,
    )


@router.post(
    "/{portfolio_id}/review",
    response_model=ReportingReviewResponse,
    summary="Get reporting review",
    description=(
        "Fetch the lotus-report-owned portfolio review payload for one portfolio and as-of "
        "date. Use this endpoint when the UI needs the report-review contract prepared for "
        "front-office or client-review workflows."
    ),
)
async def get_reporting_review(
    portfolio_id: Annotated[
        str,
        Path(
            description=(
                "Canonical portfolio identifier for the requested reporting review payload."
            ),
            examples=["DEMO_DPM_EUR_001"],
        ),
    ],
    request: Annotated[
        ReportingPortfolioRequest,
        Body(
            description=(
                "Review request payload forwarded to lotus-report after alias normalization. "
                "Use this when the consumer needs the full review-ready reporting contract "
                "for front-office or client-review workflows."
            ),
            openapi_examples=REVIEW_REQUEST_EXAMPLES,
        ),
    ],
) -> ReportingReviewResponse:
    client = _reporting_client()
    correlation_id = correlation_id_var.get()
    request_payload = request.to_upstream_payload()
    status_code, payload = await client.post_portfolio_review(
        portfolio_id=portfolio_id,
        payload=request_payload,
        correlation_id=correlation_id,
    )
    if status_code >= status.HTTP_400_BAD_REQUEST:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Reporting review unavailable: {payload}",
        )
    as_of_date = request.as_of_date
    return ReportingReviewResponse(
        correlationId=correlation_id,
        contractVersion=settings.contract_version,
        sourceService="lotus-report",
        portfolioId=portfolio_id,
        asOfDate=as_of_date,
        data=payload,
    )


@router.post(
    "/portfolio-reviews",
    response_model=ReportJobHandleResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit portfolio review report job",
    description=(
        "Create a durable portfolio review report job through the governed gateway boundary. "
        "Use this endpoint when Workbench or another product client needs asynchronous report "
        "generation with idempotency and supportable status tracking. The response is a job "
        "handle, not a rendered document."
    ),
    responses={
        **_job_error_response(
            400,
            example_key="missing_idempotency_key",
            description="Returned when idempotency or required caller context is missing.",
        ),
        **_job_error_response(
            409,
            example_key="idempotency_conflict",
            description="Returned when the idempotency key conflicts with a different request.",
        ),
        **_job_error_response(
            502,
            example_key="report_job_upstream_unavailable",
            description="Returned when lotus-report is unavailable or returns an unsafe failure.",
        ),
    },
)
async def submit_portfolio_review_report_job(
    request: Annotated[
        PortfolioReviewJobRequest,
        Body(
            description="Portfolio review report job request.",
            openapi_examples=PORTFOLIO_REVIEW_JOB_REQUEST_EXAMPLES,
        ),
    ],
    idempotency_key: Annotated[
        str | None,
        Header(
            alias="Idempotency-Key",
            description="Required caller idempotency key for job creation.",
        ),
    ] = None,
    actor_id: Annotated[str | None, Header(alias="X-Actor-Id")] = None,
    caller_application: Annotated[str | None, Header(alias="X-Caller-Application")] = None,
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    region: Annotated[str | None, Header(alias="X-Region")] = None,
    booking_center_code: Annotated[str | None, Header(alias="X-Booking-Center-Code")] = None,
    role: Annotated[str | None, Header(alias="X-Role")] = None,
) -> ReportJobHandleResponse:
    correlation_id = correlation_id_var.get()
    if not idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "missing_idempotency_key",
                "message": "Idempotency-Key is required.",
            },
        )

    status_code, payload = await _reporting_client().submit_portfolio_review_job(
        payload=request.model_dump(exclude_none=True, mode="json"),
        idempotency_key=idempotency_key,
        caller_headers=caller_context_headers(
            actor_id=actor_id,
            caller_application=caller_application,
            tenant_id=tenant_id,
            region=region,
            booking_center_code=booking_center_code,
            role=role,
        ),
        correlation_id=correlation_id,
    )
    _raise_report_job_error(status_code, payload)
    response = ReportJobHandleResponse.model_validate(payload)
    return response.model_copy(update={"status_url": _gateway_status_url(response.report_job_id)})


@jobs_router.get(
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
        **_job_error_response(
            400,
            example_key="invalid_report_job_filters",
            description="Returned when no supported job-search filter is supplied.",
        ),
        **_job_error_response(
            502,
            example_key="report_job_upstream_unavailable",
            description="Returned when lotus-report is unavailable or returns an unsafe failure.",
        ),
    },
)
async def list_report_jobs(
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
    actor_id: Annotated[str | None, Header(alias="X-Actor-Id")] = None,
    caller_application: Annotated[str | None, Header(alias="X-Caller-Application")] = None,
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    region: Annotated[str | None, Header(alias="X-Region")] = None,
    booking_center_code: Annotated[str | None, Header(alias="X-Booking-Center-Code")] = None,
    role: Annotated[str | None, Header(alias="X-Role")] = None,
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
    status_code, payload = await _reporting_client().list_report_jobs(
        filters=filters,
        caller_headers=caller_context_headers(
            actor_id=actor_id,
            caller_application=caller_application,
            tenant_id=tenant_id,
            region=region,
            booking_center_code=booking_center_code,
            role=role,
        ),
        correlation_id=correlation_id_var.get(),
    )
    _raise_report_job_error(status_code, payload)
    return ReportJobListResponse.model_validate(payload)


@jobs_router.get(
    "/{job_id}",
    response_model=ReportJobStatusResponse,
    summary="Get report job status",
    description=(
        "Return product-safe report job status and diagnostics from lotus-report. Use this "
        "endpoint after submit or search when a caller needs current lifecycle state for one job."
    ),
    responses={
        **_job_error_response(
            404,
            example_key="report_job_not_found",
            description="Returned when the requested report job does not exist.",
        ),
        **_job_error_response(
            502,
            example_key="report_job_upstream_unavailable",
            description="Returned when lotus-report is unavailable or returns an unsafe failure.",
        ),
    },
)
async def get_report_job_status(
    job_id: Annotated[str, Path(description="Opaque report job identifier.")],
    actor_id: Annotated[str | None, Header(alias="X-Actor-Id")] = None,
    caller_application: Annotated[str | None, Header(alias="X-Caller-Application")] = None,
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    region: Annotated[str | None, Header(alias="X-Region")] = None,
    booking_center_code: Annotated[str | None, Header(alias="X-Booking-Center-Code")] = None,
    role: Annotated[str | None, Header(alias="X-Role")] = None,
) -> ReportJobStatusResponse:
    status_code, payload = await _reporting_client().get_report_job(
        job_id=job_id,
        caller_headers=caller_context_headers(
            actor_id=actor_id,
            caller_application=caller_application,
            tenant_id=tenant_id,
            region=region,
            booking_center_code=booking_center_code,
            role=role,
        ),
        correlation_id=correlation_id_var.get(),
    )
    _raise_report_job_error(status_code, payload)
    return ReportJobStatusResponse.model_validate(payload)


@jobs_router.get(
    "/{job_id}/events",
    response_model=ReportJobStatusEventsResponse,
    summary="Get report job event history",
    description=(
        "Return append-only report job lifecycle events through the governed gateway boundary. "
        "Use this endpoint for operational support when current status alone is insufficient."
    ),
    responses={
        **_job_error_response(
            404,
            example_key="report_job_not_found",
            description="Returned when the requested report job does not exist.",
        ),
        **_job_error_response(
            502,
            example_key="report_job_upstream_unavailable",
            description="Returned when lotus-report is unavailable or returns an unsafe failure.",
        ),
    },
)
async def get_report_job_events(
    job_id: Annotated[str, Path(description="Opaque report job identifier.")],
    actor_id: Annotated[str | None, Header(alias="X-Actor-Id")] = None,
    caller_application: Annotated[str | None, Header(alias="X-Caller-Application")] = None,
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    region: Annotated[str | None, Header(alias="X-Region")] = None,
    booking_center_code: Annotated[str | None, Header(alias="X-Booking-Center-Code")] = None,
    role: Annotated[str | None, Header(alias="X-Role")] = None,
) -> ReportJobStatusEventsResponse:
    status_code, payload = await _reporting_client().get_report_job_events(
        job_id=job_id,
        caller_headers=caller_context_headers(
            actor_id=actor_id,
            caller_application=caller_application,
            tenant_id=tenant_id,
            region=region,
            booking_center_code=booking_center_code,
            role=role,
        ),
        correlation_id=correlation_id_var.get(),
    )
    _raise_report_job_error(status_code, payload)
    return ReportJobStatusEventsResponse.model_validate(payload)


@jobs_router.post(
    "/{job_id}/cancel",
    response_model=ReportJobStatusResponse,
    summary="Cancel report job before render or archive",
    description=(
        "Cancel a report job while it is still before render, archive, or completion. Use this "
        "endpoint only for bounded pre-render cancellation; rerender, reissue, archive, and legal "
        "hold semantics are owned by later reporting RFCs."
    ),
    responses={
        **_job_error_response(
            404,
            example_key="report_job_not_found",
            description="Returned when the requested report job does not exist.",
        ),
        **_job_error_response(
            409,
            example_key="report_job_cannot_be_cancelled",
            description="Returned when the job has completed or was already cancelled.",
        ),
        **_job_error_response(
            502,
            example_key="report_job_upstream_unavailable",
            description="Returned when lotus-report is unavailable or returns an unsafe failure.",
        ),
    },
)
async def cancel_report_job(
    job_id: Annotated[str, Path(description="Opaque report job identifier.")],
    actor_id: Annotated[str | None, Header(alias="X-Actor-Id")] = None,
    caller_application: Annotated[str | None, Header(alias="X-Caller-Application")] = None,
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    region: Annotated[str | None, Header(alias="X-Region")] = None,
    booking_center_code: Annotated[str | None, Header(alias="X-Booking-Center-Code")] = None,
    role: Annotated[str | None, Header(alias="X-Role")] = None,
) -> ReportJobStatusResponse:
    status_code, payload = await _reporting_client().cancel_report_job(
        job_id=job_id,
        caller_headers=caller_context_headers(
            actor_id=actor_id,
            caller_application=caller_application,
            tenant_id=tenant_id,
            region=region,
            booking_center_code=booking_center_code,
            role=role,
        ),
        correlation_id=correlation_id_var.get(),
    )
    _raise_report_job_error(status_code, payload)
    return ReportJobStatusResponse.model_validate(payload)
