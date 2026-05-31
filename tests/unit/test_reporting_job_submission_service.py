import pytest
from fastapi import HTTPException

from app.contracts.reporting import OutcomeReviewReportJobRequest, PortfolioReviewJobRequest
from app.services.reporting_job_submission_service import ReportingJobSubmissionService


class _ReportingClient:
    def __init__(self) -> None:
        self.portfolio_response: tuple[int, dict[str, object]] = (
            202,
            {
                "report_request_id": "rrq_1",
                "report_job_id": "rjob_1",
                "status": "accepted",
                "status_url": "/reports/jobs/rjob_1",
                "idempotency_key": "idem-portfolio",
            },
        )
        self.outcome_response: tuple[int, dict[str, object]] = (
            202,
            {
                "report_request_id": "rrq_outcome_1",
                "report_job_id": "rjob_outcome_1",
                "status": "accepted",
                "status_url": "/reports/jobs/rjob_outcome_1",
                "idempotency_key": "idem-outcome",
            },
        )
        self.calls: list[dict[str, object]] = []

    async def submit_portfolio_review_job(
        self,
        *,
        payload: dict[str, object],
        idempotency_key: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(
            {
                "operation": "portfolio",
                "payload": payload,
                "idempotency_key": idempotency_key,
                "caller_headers": caller_headers,
                "correlation_id": correlation_id,
            }
        )
        return self.portfolio_response

    async def submit_outcome_review_report_job(
        self,
        *,
        payload: dict[str, object],
        idempotency_key: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(
            {
                "operation": "outcome",
                "payload": payload,
                "idempotency_key": idempotency_key,
                "caller_headers": caller_headers,
                "correlation_id": correlation_id,
            }
        )
        return self.outcome_response


def _caller_headers() -> dict[str, str]:
    return {
        "X-Actor-Id": "advisor-123",
        "X-Caller-Application": "lotus-workbench",
        "X-Tenant-Id": "tenant-sg",
        "X-Region": "APAC",
        "X-Booking-Center-Code": "SG",
        "X-Role": "advisor",
    }


def _portfolio_request() -> PortfolioReviewJobRequest:
    return PortfolioReviewJobRequest.model_validate(
        {
            "portfolio_scope": {"portfolio_ids": ["PB_SG_GLOBAL_BAL_001"]},
            "as_of_date": "2026-04-22",
            "requested_output_formats": ["json"],
            "reporting_currency": "USD",
            "options": {"sections": ["OVERVIEW"]},
        }
    )


def _outcome_request() -> OutcomeReviewReportJobRequest:
    return OutcomeReviewReportJobRequest.model_validate(
        {
            "outcome_report_input": {
                "contract_version": "1.0",
                "outcome_review_id": "dor_001",
                "outcome_review_content_hash": "sha256:outcome-review",
                "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                "proof_pack_id": "dpp_001",
                "review_window": {
                    "start_date": "2026-04-22",
                    "end_date": "2026-04-23",
                },
                "report_title": "Post-Trade Outcome Review - PB_SG_GLOBAL_BAL_001",
                "state": "READY",
                "overall_outcome": "Execution outcome aligned with proof.",
                "dimensions": [],
                "source_lineage": [],
                "source_hashes": {"realized": "sha256:realized"},
                "section_hashes": {"proof_pack": "sha256:proof-pack"},
                "redaction_policy": "NO_RAW_PAYLOADS",
                "content_hash": "sha256:report-input",
            },
            "requested_output_formats": ["pdf"],
            "reporting_currency": "USD",
            "options": {"retention_policy_id": "generated-report-standard"},
        }
    )


@pytest.mark.asyncio
async def test_reporting_job_submission_service_submits_portfolio_review_job() -> None:
    reporting_client = _ReportingClient()
    service = ReportingJobSubmissionService(reporting_client=reporting_client)

    response = await service.submit_portfolio_review_job(
        request=_portfolio_request(),
        idempotency_key="idem-portfolio",
        caller_headers=_caller_headers(),
        correlation_id="corr-portfolio",
    )

    assert response.report_job_id == "rjob_1"
    assert reporting_client.calls == [
        {
            "operation": "portfolio",
            "payload": _portfolio_request().model_dump(exclude_none=True, mode="json"),
            "idempotency_key": "idem-portfolio",
            "caller_headers": _caller_headers(),
            "correlation_id": "corr-portfolio",
        }
    ]


@pytest.mark.asyncio
async def test_reporting_job_submission_service_submits_outcome_review_job() -> None:
    reporting_client = _ReportingClient()
    service = ReportingJobSubmissionService(reporting_client=reporting_client)

    response = await service.submit_outcome_review_report_job(
        request=_outcome_request(),
        idempotency_key="idem-outcome",
        caller_headers=_caller_headers(),
        correlation_id="corr-outcome",
    )

    assert response.report_job_id == "rjob_outcome_1"
    assert reporting_client.calls == [
        {
            "operation": "outcome",
            "payload": _outcome_request().model_dump(exclude_none=True, mode="json"),
            "idempotency_key": "idem-outcome",
            "caller_headers": _caller_headers(),
            "correlation_id": "corr-outcome",
        }
    ]


@pytest.mark.asyncio
async def test_reporting_job_submission_service_requires_idempotency_key() -> None:
    service = ReportingJobSubmissionService(reporting_client=_ReportingClient())

    with pytest.raises(HTTPException) as exc_info:
        service.require_idempotency_key(None)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["code"] == "missing_idempotency_key"


@pytest.mark.asyncio
async def test_reporting_job_submission_service_maps_upstream_job_error() -> None:
    reporting_client = _ReportingClient()
    reporting_client.portfolio_response = (
        409,
        {
            "detail": {
                "code": "idempotency_conflict",
                "message": "Idempotency key conflicts with another request.",
            }
        },
    )
    service = ReportingJobSubmissionService(reporting_client=reporting_client)

    with pytest.raises(HTTPException) as exc_info:
        await service.submit_portfolio_review_job(
            request=_portfolio_request(),
            idempotency_key="idem-conflict",
            caller_headers=_caller_headers(),
            correlation_id="corr-conflict",
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == {
        "code": "idempotency_conflict",
        "message": "Idempotency key conflicts with another request.",
    }
