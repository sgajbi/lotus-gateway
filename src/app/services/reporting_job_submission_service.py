from fastapi import HTTPException, status

from app.contracts.reporting import (
    OutcomeReviewReportJobRequest,
    PortfolioReviewJobRequest,
    ReportJobHandleResponse,
)
from app.services.reporting_client_protocols import ReportingJobSubmissionClient
from app.services.reporting_response_admission import (
    admit_report_source_response,
    assert_report_response_identity,
)


def _admit_submission_handle(
    *,
    operation: str,
    status_code: int,
    payload: dict[str, object],
    idempotency_key: str,
) -> ReportJobHandleResponse:
    response = admit_report_source_response(ReportJobHandleResponse, status_code, payload)
    # The handle is only publishable when it answers this submission: the
    # echoed key binds it to the caller's replay identity, and the source
    # status URL must name the same job as the handle (lotus-report builds it
    # as /reports/jobs/{job_id}; the router later republishes the gateway
    # form, which would silently mask a producer mismatch).
    assert_report_response_identity(
        operation=operation,
        expected={
            "idempotency_key": idempotency_key,
            "status_url": response.report_job_id,
        },
        actual={
            "idempotency_key": response.idempotency_key,
            "status_url": response.status_url.rstrip("/").rsplit("/", 1)[-1],
        },
    )
    return response


class ReportingJobSubmissionService:
    def __init__(self, *, reporting_client: ReportingJobSubmissionClient) -> None:
        self._reporting_client = reporting_client

    async def submit_portfolio_review_job(
        self,
        *,
        request: PortfolioReviewJobRequest,
        idempotency_key: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> ReportJobHandleResponse:
        status_code, payload = await self._reporting_client.submit_portfolio_review_job(
            payload=request.model_dump(exclude_none=True, mode="json"),
            idempotency_key=idempotency_key,
            caller_headers=caller_headers,
            correlation_id=correlation_id,
        )
        return _admit_submission_handle(
            operation="portfolio review submission",
            status_code=status_code,
            payload=payload,
            idempotency_key=idempotency_key,
        )

    async def submit_outcome_review_report_job(
        self,
        *,
        request: OutcomeReviewReportJobRequest,
        idempotency_key: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> ReportJobHandleResponse:
        status_code, payload = await self._reporting_client.submit_outcome_review_report_job(
            payload=request.model_dump(exclude_none=True, mode="json"),
            idempotency_key=idempotency_key,
            caller_headers=caller_headers,
            correlation_id=correlation_id,
        )
        return _admit_submission_handle(
            operation="outcome review submission",
            status_code=status_code,
            payload=payload,
            idempotency_key=idempotency_key,
        )

    def require_idempotency_key(self, idempotency_key: str | None) -> str:
        if idempotency_key:
            return idempotency_key
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "missing_idempotency_key",
                "message": "Idempotency-Key is required.",
            },
        )
