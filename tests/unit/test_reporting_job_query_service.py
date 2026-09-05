import pytest
from fastapi import HTTPException

from app.services.reporting_job_query_service import ReportingJobQueryService


class _ReportingClient:
    def __init__(self) -> None:
        self.list_response: tuple[int, dict[str, object]] = (200, _job_list_payload())
        self.status_response: tuple[int, dict[str, object]] = (200, _job_status_payload())
        self.events_response: tuple[int, dict[str, object]] = (200, _job_events_payload())
        self.lineage_response: tuple[int, dict[str, object]] = (200, _lineage_payload())
        self.snapshot_response: tuple[int, dict[str, object]] = (200, _snapshot_payload())
        self.calls: list[dict[str, object]] = []

    async def list_report_jobs(
        self,
        *,
        filters: dict[str, object],
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(
            {
                "operation": "list",
                "filters": filters,
                "caller_headers": caller_headers,
                "correlation_id": correlation_id,
            }
        )
        return self.list_response

    async def get_report_job(
        self,
        *,
        job_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(_job_call("get", job_id, caller_headers, correlation_id))
        return self.status_response

    async def get_report_job_events(
        self,
        *,
        job_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(_job_call("events", job_id, caller_headers, correlation_id))
        return self.events_response

    async def get_report_job_lineage(
        self,
        *,
        job_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(_job_call("job_lineage", job_id, caller_headers, correlation_id))
        return self.lineage_response

    async def cancel_report_job(
        self,
        *,
        job_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(_job_call("cancel", job_id, caller_headers, correlation_id))
        return self.status_response

    async def get_report_snapshot(
        self,
        *,
        snapshot_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(_snapshot_call("snapshot", snapshot_id, caller_headers, correlation_id))
        return self.snapshot_response

    async def get_report_snapshot_lineage(
        self,
        *,
        snapshot_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(
            _snapshot_call("snapshot_lineage", snapshot_id, caller_headers, correlation_id)
        )
        return self.lineage_response


def _caller_headers() -> dict[str, str]:
    return {
        "X-Actor-Id": "advisor-123",
        "X-Caller-Application": "lotus-workbench",
        "X-Tenant-Id": "tenant-sg",
        "X-Region": "APAC",
        "X-Booking-Center-Code": "SG",
        "X-Role": "advisor",
    }


def _job_call(
    operation: str,
    job_id: str,
    caller_headers: dict[str, str],
    correlation_id: str,
) -> dict[str, object]:
    return {
        "operation": operation,
        "job_id": job_id,
        "caller_headers": caller_headers,
        "correlation_id": correlation_id,
    }


def _snapshot_call(
    operation: str,
    snapshot_id: str,
    caller_headers: dict[str, str],
    correlation_id: str,
) -> dict[str, object]:
    return {
        "operation": operation,
        "snapshot_id": snapshot_id,
        "caller_headers": caller_headers,
        "correlation_id": correlation_id,
    }


def _job_status_payload(*, status: str = "accepted") -> dict[str, object]:
    return {
        "report_job_id": "rjob_1",
        "report_request_id": "rrq_1",
        "report_type": "portfolio_review",
        "portfolio_scope": {"portfolio_ids": ["PB_SG_GLOBAL_BAL_001"]},
        "status": status,
        "failure_category": None,
        "failure_message": None,
        "current_step": status,
        "retry_eligible": False,
        "cancel_requested": status == "cancelled",
        "created_at": "2026-04-22T09:00:00Z",
        "updated_at": "2026-04-22T09:00:00Z",
        "started_at": None,
        "completed_at": None,
        "cancelled_at": None,
        "correlation_id": "corr-report-job",
        "trace_id": "trace-job",
    }


def _job_list_payload() -> dict[str, object]:
    return {
        "count": 1,
        "appliedFilters": {
            "tenantId": "tenant-sg",
            "region": "APAC",
            "status": "accepted",
            "reportType": None,
            "portfolioId": "PB_SG_GLOBAL_BAL_001",
            "asOfDate": None,
            "idempotencyKey": None,
            "correlationId": "corr-report-job",
            "createdFrom": None,
            "createdTo": None,
            "limit": 25,
        },
        "items": [
            {
                "reportJobId": "rjob_1",
                "reportRequestId": "rrq_1",
                "reportType": "portfolio_review",
                "tenantId": "tenant-sg",
                "region": "APAC",
                "portfolioScope": {"portfolio_ids": ["PB_SG_GLOBAL_BAL_001"]},
                "asOfDate": "2026-04-22",
                "status": "accepted",
                "failureCategory": None,
                "currentStep": "accepted",
                "retryEligible": False,
                "cancelRequested": False,
                "idempotencyKey": "idem-gateway-1",
                "correlationId": "corr-report-job",
                "createdAt": "2026-04-22T09:00:00Z",
                "updatedAt": "2026-04-22T09:00:00Z",
            }
        ],
    }


def _job_events_payload() -> dict[str, object]:
    return {
        "report_job_id": "rjob_1",
        "events": [
            {
                "status_event_id": "rse_1",
                "report_job_id": "rjob_1",
                "from_status": None,
                "to_status": "accepted",
                "event_type": "job_accepted",
                "message": "Portfolio review report job accepted.",
                "actor": "advisor-123",
                "created_at": "2026-04-22T09:00:00Z",
                "correlation_id": "corr-report-job",
                "trace_id": "trace-job",
            }
        ],
    }


def _snapshot_payload() -> dict[str, object]:
    return {
        "snapshot_id": "rsnap_1",
        "report_job_id": "rjob_1",
        "report_type": "portfolio_review",
        "report_data_contract_version": "v1",
        "portfolio_scope": {"portfolio_ids": ["PB_SG_GLOBAL_BAL_001"]},
        "as_of_date": "2026-04-22",
        "snapshot_payload": {"report_id": "portfolio-review:PB_SG_GLOBAL_BAL_001:2026-04-22"},
        "snapshot_hash": "sha256:snapshot",
        "snapshot_storage_ref": None,
        "supportability_status": "complete",
        "completeness_status": "complete",
        "lineage_summary": {
            "sourceServices": ["lotus-core"],
            "callCount": 1,
            "supportability_status": "complete",
            "partialCallCount": 0,
            "unavailableCallCount": 0,
            "notSupportedCallCount": 0,
            "redactedCallCount": 0,
        },
        "captured_at": "2026-04-22T09:00:03Z",
        "created_at": "2026-04-22T09:00:03Z",
        "correlation_id": "corr-report-job",
        "trace_id": "trace-job",
    }


def _lineage_payload() -> dict[str, object]:
    return {
        "snapshot": _snapshot_payload(),
        "upstream_calls": [
            {
                "upstream_call_id": "ruc_1",
                "snapshot_id": "rsnap_1",
                "service_name": "lotus-core",
                "endpoint": "/reporting/portfolio-summary/query",
                "method": "POST",
                "contract_version": "v1",
                "request_hash": "sha256:request",
                "response_hash": "sha256:response",
                "response_ref": None,
                "status_code": 200,
                "latency_ms": 184,
                "supportability_status": "complete",
                "completeness_status": "complete",
                "failure_category": "none",
                "failure_message": None,
                "captured_at": "2026-04-22T09:00:03Z",
                "created_at": "2026-04-22T09:00:03Z",
                "correlation_id": "corr-report-job",
                "trace_id": "trace-job",
            }
        ],
    }


@pytest.mark.asyncio
async def test_reporting_job_query_service_lists_jobs_with_filters() -> None:
    reporting_client = _ReportingClient()
    service = ReportingJobQueryService(reporting_client=reporting_client)

    response = await service.list_report_jobs(
        filters={"portfolioId": "PB_SG_GLOBAL_BAL_001", "limit": 25},
        caller_headers=_caller_headers(),
        correlation_id="corr-report-job",
    )

    assert response.count == 1
    assert response.items[0].report_job_id == "rjob_1"
    assert reporting_client.calls == [
        {
            "operation": "list",
            # The admitted tenant/region fence is always sent to the source.
            "filters": {
                "portfolioId": "PB_SG_GLOBAL_BAL_001",
                "limit": 25,
                "tenantId": "tenant-sg",
                "region": "APAC",
            },
            "caller_headers": _caller_headers(),
            "correlation_id": "corr-report-job",
        }
    ]


@pytest.mark.asyncio
async def test_reporting_job_query_service_gets_status_events_and_cancel() -> None:
    reporting_client = _ReportingClient()
    reporting_client.status_response = (200, _job_status_payload(status="cancelled"))
    service = ReportingJobQueryService(reporting_client=reporting_client)

    status_response = await service.get_report_job_status(
        job_id="rjob_1",
        caller_headers=_caller_headers(),
        correlation_id="corr-report-job",
    )
    events_response = await service.get_report_job_events(
        job_id="rjob_1",
        caller_headers=_caller_headers(),
        correlation_id="corr-report-job",
    )
    cancel_response = await service.cancel_report_job(
        job_id="rjob_1",
        caller_headers=_caller_headers(),
        correlation_id="corr-report-job",
    )

    assert status_response.status == "cancelled"
    assert events_response.events[0].event_type == "job_accepted"
    assert cancel_response.cancel_requested is True
    assert [call["operation"] for call in reporting_client.calls] == [
        "get",
        "events",
        "cancel",
    ]


@pytest.mark.asyncio
async def test_reporting_job_query_service_gets_snapshot_and_lineage() -> None:
    reporting_client = _ReportingClient()
    service = ReportingJobQueryService(reporting_client=reporting_client)

    job_lineage = await service.get_report_job_lineage(
        job_id="rjob_1",
        caller_headers=_caller_headers(),
        correlation_id="corr-report-job",
    )
    snapshot = await service.get_report_snapshot(
        snapshot_id="rsnap_1",
        caller_headers=_caller_headers(),
        correlation_id="corr-report-job",
    )
    snapshot_lineage = await service.get_report_snapshot_lineage(
        snapshot_id="rsnap_1",
        caller_headers=_caller_headers(),
        correlation_id="corr-report-job",
    )

    assert job_lineage.snapshot.snapshot_id == "rsnap_1"
    assert snapshot.snapshot_id == "rsnap_1"
    assert snapshot_lineage.upstream_calls[0].upstream_call_id == "ruc_1"
    assert [call["operation"] for call in reporting_client.calls] == [
        "job_lineage",
        "snapshot",
        "snapshot_lineage",
    ]


@pytest.mark.asyncio
async def test_reporting_job_query_service_maps_upstream_errors_without_leaking_payload() -> None:
    reporting_client = _ReportingClient()
    reporting_client.status_response = (
        500,
        {"detail": "sqlite traceback internal-host report.dev.lotus"},
    )
    service = ReportingJobQueryService(reporting_client=reporting_client)

    with pytest.raises(HTTPException) as exc_info:
        await service.get_report_job_status(
            job_id="rjob_500",
            caller_headers=_caller_headers(),
            correlation_id="corr-report-job",
        )

    assert exc_info.value.status_code == 502
    assert exc_info.value.detail == {
        "code": "report_job_upstream_unavailable",
        "message": "Report job service is unavailable.",
    }
    assert "sqlite" not in str(exc_info.value.detail).lower()
    assert "report.dev.lotus" not in str(exc_info.value.detail)


def _identity_mismatch_code(exc_info: pytest.ExceptionInfo[HTTPException]) -> str:
    assert exc_info.value.status_code == 502
    return exc_info.value.detail["code"]


@pytest.mark.asyncio
async def test_reporting_job_query_service_refuses_status_for_a_different_job() -> None:
    reporting_client = _ReportingClient()
    service = ReportingJobQueryService(reporting_client=reporting_client)

    with pytest.raises(HTTPException) as exc_info:
        await service.get_report_job_status(
            job_id="rjob_other",
            caller_headers=_caller_headers(),
            correlation_id="corr-report-job",
        )

    assert _identity_mismatch_code(exc_info) == "report_job_source_identity_mismatch"


@pytest.mark.asyncio
async def test_reporting_job_query_service_refuses_events_for_a_different_job() -> None:
    reporting_client = _ReportingClient()
    service = ReportingJobQueryService(reporting_client=reporting_client)

    with pytest.raises(HTTPException) as exc_info:
        await service.get_report_job_events(
            job_id="rjob_other",
            caller_headers=_caller_headers(),
            correlation_id="corr-report-job",
        )

    assert _identity_mismatch_code(exc_info) == "report_job_source_identity_mismatch"


@pytest.mark.asyncio
async def test_reporting_job_query_service_refuses_cancel_evidence_for_a_different_job() -> None:
    reporting_client = _ReportingClient()
    service = ReportingJobQueryService(reporting_client=reporting_client)

    with pytest.raises(HTTPException) as exc_info:
        await service.cancel_report_job(
            job_id="rjob_other",
            caller_headers=_caller_headers(),
            correlation_id="corr-report-job",
        )

    assert _identity_mismatch_code(exc_info) == "report_job_source_identity_mismatch"


@pytest.mark.asyncio
async def test_reporting_job_query_service_refuses_lineage_owned_by_a_different_job() -> None:
    reporting_client = _ReportingClient()
    service = ReportingJobQueryService(reporting_client=reporting_client)

    with pytest.raises(HTTPException) as exc_info:
        await service.get_report_job_lineage(
            job_id="rjob_other",
            caller_headers=_caller_headers(),
            correlation_id="corr-report-job",
        )

    assert _identity_mismatch_code(exc_info) == "report_job_source_identity_mismatch"


@pytest.mark.asyncio
async def test_reporting_job_query_service_refuses_a_different_snapshot() -> None:
    reporting_client = _ReportingClient()
    service = ReportingJobQueryService(reporting_client=reporting_client)

    with pytest.raises(HTTPException) as exc_info:
        await service.get_report_snapshot(
            snapshot_id="rsnap_other",
            caller_headers=_caller_headers(),
            correlation_id="corr-report-job",
        )

    assert _identity_mismatch_code(exc_info) == "report_job_source_identity_mismatch"


@pytest.mark.asyncio
async def test_reporting_job_query_service_refuses_snapshot_lineage_for_a_different_snapshot() -> (
    None
):
    reporting_client = _ReportingClient()
    service = ReportingJobQueryService(reporting_client=reporting_client)

    with pytest.raises(HTTPException) as exc_info:
        await service.get_report_snapshot_lineage(
            snapshot_id="rsnap_other",
            caller_headers=_caller_headers(),
            correlation_id="corr-report-job",
        )

    assert _identity_mismatch_code(exc_info) == "report_job_source_identity_mismatch"


@pytest.mark.asyncio
async def test_reporting_job_query_service_maps_a_malformed_success_to_a_bounded_502() -> None:
    reporting_client = _ReportingClient()
    payload = _job_status_payload()
    del payload["report_job_id"]
    reporting_client.status_response = (200, payload)
    service = ReportingJobQueryService(reporting_client=reporting_client)

    with pytest.raises(HTTPException) as exc_info:
        await service.get_report_job_status(
            job_id="rjob_1",
            caller_headers=_caller_headers(),
            correlation_id="corr-report-job",
        )

    assert exc_info.value.status_code == 502
    assert exc_info.value.detail["code"] == "report_job_source_contract_invalid"


@pytest.mark.asyncio
async def test_reporting_job_query_service_maps_a_malformed_list_success_to_a_bounded_502() -> None:
    reporting_client = _ReportingClient()
    reporting_client.list_response = (200, {"count": "not-a-number"})
    service = ReportingJobQueryService(reporting_client=reporting_client)

    with pytest.raises(HTTPException) as exc_info:
        await service.list_report_jobs(
            filters={},
            caller_headers=_caller_headers(),
            correlation_id="corr-report-job",
        )

    assert exc_info.value.status_code == 502
    assert exc_info.value.detail["code"] == "report_job_source_contract_invalid"
