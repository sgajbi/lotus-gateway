from typing import Annotated

from fastapi import APIRouter, Body, Header, status

from app.contracts.reporting import (
    PortfolioReviewJobRequest,
    ReportJobHandleResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.reporting_context import ReportingCallerHeaderInputs
from app.routers.reporting_errors import report_job_submission_error_responses
from app.routers.reporting_examples import PORTFOLIO_REVIEW_JOB_REQUEST_EXAMPLES
from app.services.reporting_links import gateway_report_job_status_url
from app.services.reporting_service_provider import reporting_job_submission_service

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])


async def _submit_portfolio_review_report_job(
    *,
    request: PortfolioReviewJobRequest,
    idempotency_key: str | None,
    caller_headers: ReportingCallerHeaderInputs,
) -> ReportJobHandleResponse:
    correlation_id = correlation_id_var.get()
    service = reporting_job_submission_service()
    required_idempotency_key = service.require_idempotency_key(idempotency_key)
    response = await service.submit_portfolio_review_job(
        request=request,
        idempotency_key=required_idempotency_key,
        caller_headers=caller_headers.as_headers(),
        correlation_id=correlation_id,
    )
    return response.model_copy(
        update={"status_url": gateway_report_job_status_url(response.report_job_id)}
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
    responses=report_job_submission_error_responses(),
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
    return await _submit_portfolio_review_report_job(
        request=request,
        idempotency_key=idempotency_key,
        caller_headers=ReportingCallerHeaderInputs(
            actor_id=actor_id,
            caller_application=caller_application,
            tenant_id=tenant_id,
            region=region,
            booking_center_code=booking_center_code,
            role=role,
        ),
    )
