from fastapi import HTTPException, status

from app.clients.reporting_client import ReportingClient
from app.contracts.reporting import (
    OutcomeReviewReportJobRequest,
    PortfolioReviewJobRequest,
    ReportJobHandleResponse,
)
from app.services.reporting_error_mapping import raise_report_job_error


class ReportingJobSubmissionService:
    def __init__(self, *, reporting_client: ReportingClient) -> None:
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
        raise_report_job_error(status_code, payload)
        return ReportJobHandleResponse.model_validate(payload)

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
        raise_report_job_error(status_code, payload)
        return ReportJobHandleResponse.model_validate(payload)

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
