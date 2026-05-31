from typing import Any, TypeVar

from pydantic import BaseModel

from app.clients.reporting_client import ReportingClient
from app.contracts.reporting import (
    ReportInputSnapshotRecord,
    ReportJobListResponse,
    ReportJobStatusEventsResponse,
    ReportJobStatusResponse,
    ReportSnapshotLineageResponse,
)
from app.routers.reporting_errors import raise_report_job_error

ResponseModel = TypeVar("ResponseModel", bound=BaseModel)


class ReportingJobQueryService:
    def __init__(self, *, reporting_client: ReportingClient) -> None:
        self._reporting_client = reporting_client

    async def list_report_jobs(
        self,
        *,
        filters: dict[str, Any],
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> ReportJobListResponse:
        status_code, payload = await self._reporting_client.list_report_jobs(
            filters=filters,
            caller_headers=caller_headers,
            correlation_id=correlation_id,
        )
        return self._validate_response(ReportJobListResponse, status_code, payload)

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
        return self._validate_response(ReportJobStatusResponse, status_code, payload)

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
        return self._validate_response(ReportJobStatusEventsResponse, status_code, payload)

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
        return self._validate_response(ReportSnapshotLineageResponse, status_code, payload)

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
        return self._validate_response(ReportJobStatusResponse, status_code, payload)

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
        return self._validate_response(ReportInputSnapshotRecord, status_code, payload)

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
        return self._validate_response(ReportSnapshotLineageResponse, status_code, payload)

    def _validate_response(
        self,
        model_type: type[ResponseModel],
        status_code: int,
        payload: dict[str, Any],
    ) -> ResponseModel:
        raise_report_job_error(status_code, payload)
        return model_type.model_validate(payload)
