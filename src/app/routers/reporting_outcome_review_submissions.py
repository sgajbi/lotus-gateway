from typing import Annotated

from fastapi import APIRouter, Body, Header, status

from app.contracts.reporting import (
    OutcomeReviewReportJobRequest,
    ReportJobHandleResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.reporting_context import ReportingCallerHeaderInputs
from app.routers.reporting_errors import report_job_error_response
from app.routers.reporting_examples import OUTCOME_REVIEW_REPORT_JOB_REQUEST_EXAMPLES
from app.services.reporting_links import gateway_report_job_status_url
from app.services.reporting_service_provider import reporting_job_submission_service

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])


async def _submit_outcome_review_report_job(
    *,
    request: OutcomeReviewReportJobRequest,
    idempotency_key: str | None,
    caller_headers: ReportingCallerHeaderInputs,
) -> ReportJobHandleResponse:
    correlation_id = correlation_id_var.get()
    service = reporting_job_submission_service()
    required_idempotency_key = service.require_idempotency_key(idempotency_key)
    response = await service.submit_outcome_review_report_job(
        request=request,
        idempotency_key=required_idempotency_key,
        caller_headers=caller_headers.as_headers(),
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
    return await _submit_outcome_review_report_job(
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
