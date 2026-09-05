from typing import Any

from app.contracts.reporting import ReportJobStatusResponse
from app.contracts.reporting_query import (
    ReportInputSnapshotRecord,
    ReportJobListResponse,
    ReportJobStatusEventsResponse,
    ReportSnapshotLineageResponse,
)
from app.services.reporting_client_protocols import ReportingJobQueryClient
from app.services.reporting_response_admission import (
    admit_report_source_response,
    assert_report_response_identity,
)
from app.services.reporting_search_scope import (
    assert_search_result_within_scope,
    resolve_search_scope_params,
)


class ReportingJobQueryService:
    def __init__(self, *, reporting_client: ReportingJobQueryClient) -> None:
        self._reporting_client = reporting_client

    async def list_report_jobs(
        self,
        *,
        filters: dict[str, Any],
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> ReportJobListResponse:
        fenced_filters = resolve_search_scope_params(
            caller_headers=caller_headers,
            query_params=filters,
        )
        status_code, payload = await self._reporting_client.list_report_jobs(
            filters=fenced_filters,
            caller_headers=caller_headers,
            correlation_id=correlation_id,
        )
        response = admit_report_source_response(ReportJobListResponse, status_code, payload)
        assert_search_result_within_scope(response, caller_headers=caller_headers)
        return response

    async def get_report_job_status(
        self,
        *,
        job_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> ReportJobStatusResponse:
        status_code, payload = await self._reporting_client.get_report_job(
            job_id=job_id,
            caller_headers=caller_headers,
            correlation_id=correlation_id,
        )
        response = admit_report_source_response(ReportJobStatusResponse, status_code, payload)
        assert_report_response_identity(
            operation="report job status",
            expected={"report_job_id": job_id},
            actual={"report_job_id": response.report_job_id},
        )
        return response

    async def get_report_job_events(
        self,
        *,
        job_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> ReportJobStatusEventsResponse:
        status_code, payload = await self._reporting_client.get_report_job_events(
            job_id=job_id,
            caller_headers=caller_headers,
            correlation_id=correlation_id,
        )
        response = admit_report_source_response(ReportJobStatusEventsResponse, status_code, payload)
        assert_report_response_identity(
            operation="report job events",
            expected={"report_job_id": job_id},
            actual={"report_job_id": response.report_job_id},
        )
        return response

    async def get_report_job_lineage(
        self,
        *,
        job_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> ReportSnapshotLineageResponse:
        status_code, payload = await self._reporting_client.get_report_job_lineage(
            job_id=job_id,
            caller_headers=caller_headers,
            correlation_id=correlation_id,
        )
        response = admit_report_source_response(ReportSnapshotLineageResponse, status_code, payload)
        assert_report_response_identity(
            operation="report job lineage",
            expected={"report_job_id": job_id},
            actual={"report_job_id": response.snapshot.report_job_id},
        )
        return response

    async def cancel_report_job(
        self,
        *,
        job_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> ReportJobStatusResponse:
        status_code, payload = await self._reporting_client.cancel_report_job(
            job_id=job_id,
            caller_headers=caller_headers,
            correlation_id=correlation_id,
        )
        response = admit_report_source_response(ReportJobStatusResponse, status_code, payload)
        assert_report_response_identity(
            operation="report job cancel",
            expected={"report_job_id": job_id},
            actual={"report_job_id": response.report_job_id},
        )
        return response

    async def get_report_snapshot(
        self,
        *,
        snapshot_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> ReportInputSnapshotRecord:
        status_code, payload = await self._reporting_client.get_report_snapshot(
            snapshot_id=snapshot_id,
            caller_headers=caller_headers,
            correlation_id=correlation_id,
        )
        response = admit_report_source_response(ReportInputSnapshotRecord, status_code, payload)
        assert_report_response_identity(
            operation="report snapshot",
            expected={"snapshot_id": snapshot_id},
            actual={"snapshot_id": response.snapshot_id},
        )
        return response

    async def get_report_snapshot_lineage(
        self,
        *,
        snapshot_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> ReportSnapshotLineageResponse:
        status_code, payload = await self._reporting_client.get_report_snapshot_lineage(
            snapshot_id=snapshot_id,
            caller_headers=caller_headers,
            correlation_id=correlation_id,
        )
        response = admit_report_source_response(ReportSnapshotLineageResponse, status_code, payload)
        assert_report_response_identity(
            operation="report snapshot lineage",
            expected={"snapshot_id": snapshot_id},
            actual={"snapshot_id": response.snapshot.snapshot_id},
        )
        return response
