from datetime import UTC, datetime

from app.contracts import reporting
from app.contracts.reporting_jobs import (
    OutcomeReviewReportJobRequest,
    PortfolioReviewJobRequest,
    ReportJobErrorResponse,
    ReportJobHandleResponse,
    ReportJobStatusResponse,
)


def test_reporting_job_contracts_remain_compatibility_reexports() -> None:
    assert reporting.PortfolioReviewJobRequest is PortfolioReviewJobRequest
    assert reporting.OutcomeReviewReportJobRequest is OutcomeReviewReportJobRequest
    assert reporting.ReportJobErrorResponse is ReportJobErrorResponse
    assert reporting.ReportJobHandleResponse is ReportJobHandleResponse
    assert reporting.ReportJobStatusResponse is ReportJobStatusResponse


def test_portfolio_review_job_request_preserves_serialized_payload_shape() -> None:
    request = PortfolioReviewJobRequest(
        portfolio_scope={"portfolio_ids": ["PB_SG_GLOBAL_BAL_001"]},
        as_of_date="2026-04-22",
        requested_output_formats=["json"],
        reporting_currency="USD",
        options={"sections": ["OVERVIEW", "PERFORMANCE"]},
    )

    assert request.model_dump(exclude_none=True, mode="json") == {
        "portfolio_scope": {"portfolio_ids": ["PB_SG_GLOBAL_BAL_001"]},
        "as_of_date": "2026-04-22",
        "requested_output_formats": ["json"],
        "reporting_currency": "USD",
        "options": {"sections": ["OVERVIEW", "PERFORMANCE"]},
    }


def test_report_job_status_response_preserves_product_safe_status_fields() -> None:
    timestamp = datetime(2026, 4, 22, 9, 0, tzinfo=UTC)

    response = ReportJobStatusResponse(
        report_job_id="rjob_1",
        report_request_id="rrq_1",
        report_type="portfolio_review",
        portfolio_scope={"portfolio_ids": ["PB_SG_GLOBAL_BAL_001"]},
        status="accepted",
        current_step="accepted",
        retry_eligible=False,
        cancel_requested=False,
        created_at=timestamp,
        updated_at=timestamp,
        correlation_id="corr-report-job-1",
        trace_id="trace-report-job-1",
    )

    assert response.model_dump(mode="json", by_alias=True, exclude_none=True) == {
        "report_job_id": "rjob_1",
        "report_request_id": "rrq_1",
        "report_type": "portfolio_review",
        "portfolio_scope": {"portfolio_ids": ["PB_SG_GLOBAL_BAL_001"]},
        "status": "accepted",
        "current_step": "accepted",
        "retry_eligible": False,
        "cancel_requested": False,
        "created_at": "2026-04-22T09:00:00Z",
        "updated_at": "2026-04-22T09:00:00Z",
        "correlation_id": "corr-report-job-1",
        "trace_id": "trace-report-job-1",
    }
