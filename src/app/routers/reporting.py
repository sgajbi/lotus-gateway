from typing import Annotated

from fastapi import APIRouter, Body, Header, Path, Query, status

from app.contracts.reporting import (
    OutcomeReviewReportJobRequest,
    PortfolioReviewJobRequest,
    ReportingPortfolioRequest,
    ReportingReviewResponse,
    ReportingSnapshotResponse,
    ReportingSummaryResponse,
    ReportJobHandleResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.reporting_context import reporting_context_headers
from app.routers.reporting_errors import report_job_error_response
from app.routers.reporting_examples import (
    OUTCOME_REVIEW_REPORT_JOB_REQUEST_EXAMPLES,
    PORTFOLIO_REVIEW_JOB_REQUEST_EXAMPLES,
    REVIEW_REQUEST_EXAMPLES,
    SUMMARY_REQUEST_EXAMPLES,
)
from app.services.reporting_links import gateway_report_job_status_url
from app.services.reporting_service_provider import (
    reporting_job_submission_service,
    reporting_portfolio_service,
)

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])


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
    correlation_id = correlation_id_var.get()
    return await reporting_portfolio_service().get_snapshot(
        portfolio_id=portfolio_id,
        as_of_date=as_of_date,
        correlation_id=correlation_id,
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
    correlation_id = correlation_id_var.get()
    return await reporting_portfolio_service().get_summary(
        portfolio_id=portfolio_id,
        request=request,
        correlation_id=correlation_id,
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
    correlation_id = correlation_id_var.get()
    return await reporting_portfolio_service().get_review(
        portfolio_id=portfolio_id,
        request=request,
        correlation_id=correlation_id,
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
        **report_job_error_response(
            400,
            example_key="missing_idempotency_key",
            description="Returned when idempotency or required caller context is missing.",
        ),
        **report_job_error_response(
            409,
            example_key="idempotency_conflict",
            description="Returned when the idempotency key conflicts with a different request.",
        ),
        **report_job_error_response(
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
    service = reporting_job_submission_service()
    required_idempotency_key = service.require_idempotency_key(idempotency_key)
    response = await service.submit_portfolio_review_job(
        request=request,
        idempotency_key=required_idempotency_key,
        caller_headers=reporting_context_headers(
            actor_id=actor_id,
            caller_application=caller_application,
            tenant_id=tenant_id,
            region=region,
            booking_center_code=booking_center_code,
            role=role,
        ),
        correlation_id=correlation_id,
    )
    return response.model_copy(
        update={"status_url": gateway_report_job_status_url(response.report_job_id)}
    )


@router.post(
    "/outcome-reviews",
    response_model=ReportJobHandleResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit outcome-review report job",
    description=(
        "Create a durable post-trade outcome-review report job through the governed gateway "
        "boundary. Use this endpoint when Workbench or another product client needs a rendered "
        "outcome-review artifact from manage-owned report input without calling lotus-report "
        "directly or recomputing outcome facts."
    ),
    responses={
        **report_job_error_response(
            400,
            example_key="missing_idempotency_key",
            description="Returned when idempotency or required caller context is missing.",
        ),
        **report_job_error_response(
            409,
            example_key="idempotency_conflict",
            description="Returned when the idempotency key conflicts with a different request.",
        ),
        **report_job_error_response(
            502,
            example_key="report_job_upstream_unavailable",
            description="Returned when lotus-report is unavailable or returns an unsafe failure.",
        ),
    },
)
async def submit_outcome_review_report_job(
    request: Annotated[
        OutcomeReviewReportJobRequest,
        Body(
            description="Outcome-review report job request.",
            openapi_examples=OUTCOME_REVIEW_REPORT_JOB_REQUEST_EXAMPLES,
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
    service = reporting_job_submission_service()
    required_idempotency_key = service.require_idempotency_key(idempotency_key)
    response = await service.submit_outcome_review_report_job(
        request=request,
        idempotency_key=required_idempotency_key,
        caller_headers=reporting_context_headers(
            actor_id=actor_id,
            caller_application=caller_application,
            tenant_id=tenant_id,
            region=region,
            booking_center_code=booking_center_code,
            role=role,
        ),
        correlation_id=correlation_id,
    )
    return response.model_copy(
        update={"status_url": gateway_report_job_status_url(response.report_job_id)}
    )
