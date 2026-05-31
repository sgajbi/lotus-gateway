import pytest
from fastapi import HTTPException

from app.contracts.reporting import BatchWorkerRunRequest
from app.services.reporting_batch_control_service import ReportingBatchControlService


class _ReportingClient:
    def __init__(self) -> None:
        self.control_response: tuple[int, dict[str, object]] = (
            200,
            {
                "batch_id": "rbch_1",
                "status": "paused",
                "affected_count": 1,
                "status_url": "/reports/batches/rbch_1",
            },
        )
        self.calls: list[dict[str, object]] = []
        self.capability_calls: list[dict[str, str]] = []

    async def control_report_batch(
        self,
        *,
        batch_id: str,
        action: str,
        caller_headers: dict[str, str],
        correlation_id: str,
        payload: dict[str, object] | None = None,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(
            {
                "batch_id": batch_id,
                "action": action,
                "caller_headers": caller_headers,
                "correlation_id": correlation_id,
                "payload": payload,
            }
        )
        return self.control_response

    async def get_capabilities(
        self,
        *,
        consumer_system: str,
        tenant_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.capability_calls.append(
            {
                "consumer_system": consumer_system,
                "tenant_id": tenant_id,
                "correlation_id": correlation_id,
            }
        )
        return 200, {
            "supportability": {
                "state": "ready",
                "reason": "evidence_surface_ready",
                "freshness_bucket": "current",
                "evidence_feature_count": 3,
                "ready_evidence_feature_count": 3,
                "degraded_evidence_feature_count": 0,
                "workflow_count": 1,
                "ready_workflow_count": 1,
            }
        }


class _RenderClient:
    def __init__(self) -> None:
        self.metadata_calls: list[dict[str, str]] = []

    async def get_metadata(self, *, correlation_id: str) -> tuple[int, dict[str, object]]:
        self.metadata_calls.append({"correlation_id": correlation_id})
        return 200, {
            "supportability": {
                "state": "ready",
                "reason": "render_supportability_ready",
                "freshness_bucket": "current",
                "deterministic_output_supported": True,
                "render_store_ready": True,
                "template_registry_ready": True,
                "default_output_format": "pdf",
                "supported_output_formats": ["pdf"],
            }
        }


def _caller_headers() -> dict[str, str]:
    return {
        "X-Actor-Id": "operator-123",
        "X-Caller-Application": "lotus-workbench",
        "X-Tenant-Id": "tenant-sg",
        "X-Region": "APAC",
    }


def _service(reporting_client: _ReportingClient) -> ReportingBatchControlService:
    return ReportingBatchControlService(
        reporting_client=reporting_client,
        render_client=_RenderClient(),
    )


@pytest.mark.asyncio
async def test_reporting_batch_control_service_controls_batch() -> None:
    reporting_client = _ReportingClient()
    service = _service(reporting_client)

    response = await service.control_batch(
        batch_id="rbch_1",
        action="pause",
        caller_headers=_caller_headers(),
        correlation_id="corr-batch",
    )

    assert response.batch_id == "rbch_1"
    assert response.status == "paused"
    assert response.status_url == "/api/v1/report-batches/rbch_1"
    assert reporting_client.calls == [
        {
            "batch_id": "rbch_1",
            "action": "pause",
            "caller_headers": _caller_headers(),
            "correlation_id": "corr-batch",
            "payload": None,
        }
    ]


@pytest.mark.asyncio
async def test_reporting_batch_control_service_recovers_expired_leases() -> None:
    reporting_client = _ReportingClient()
    reporting_client.control_response = (
        200,
        {
            "batch_id": "rbch_1",
            "status": "running",
            "recovered_count": 1,
            "recovery_pending_item_ids": ["rbci_1"],
            "status_url": "/reports/batches/rbch_1",
        },
    )
    service = _service(reporting_client)

    response = await service.recover_expired_leases(
        batch_id="rbch_1",
        caller_headers=_caller_headers(),
        correlation_id="corr-batch",
    )

    assert response.recovered_count == 1
    assert response.recovery_pending_item_ids == ["rbci_1"]
    assert reporting_client.calls[0]["action"] == "recover-expired-leases"


@pytest.mark.asyncio
async def test_reporting_batch_control_service_runs_batch_once_with_supportability() -> None:
    reporting_client = _ReportingClient()
    render_client = _RenderClient()
    reporting_client.control_response = (
        200,
        {
            "batch_id": "rbch_1",
            "status": "completed",
            "batch_status_before": "materialized",
            "batch_status_after": "completed",
            "recovered_count": 1,
            "leased_count": 1,
            "dispatched_count": 1,
            "executed_count": 1,
            "report_job_ids": ["rjob_1"],
            "back_pressure_reasons": [],
            "skipped_reason": None,
            "execution_results": [
                {
                    "batch_item_id": "rbci_1",
                    "report_job_id": "rjob_1",
                    "item_status": "succeeded",
                    "report_job_status": "archived",
                    "failure_category": None,
                    "retry_eligible": False,
                }
            ],
            "status_url": "/reports/batches/rbch_1",
        },
    )
    service = ReportingBatchControlService(
        reporting_client=reporting_client,
        render_client=render_client,
    )

    response = await service.run_batch_once(
        batch_id="rbch_1",
        request=BatchWorkerRunRequest.model_validate(
            {"worker_id": "worker-1", "recover_expired_leases": True}
        ),
        caller_headers=_caller_headers(),
        correlation_id="corr-batch",
        tenant_id="tenant-sg",
    )

    assert response.batch_id == "rbch_1"
    assert response.status_url == "/api/v1/report-batches/rbch_1"
    assert response.supportability is not None
    assert response.render_supportability is not None
    assert response.supportability.state == "ready"
    assert response.render_supportability.state == "ready"
    assert reporting_client.calls[0]["action"] == "run-once"
    assert reporting_client.calls[0]["payload"] == {
        "worker_id": "worker-1",
        "recover_expired_leases": True,
    }
    assert reporting_client.capability_calls == [
        {
            "consumer_system": "lotus-gateway",
            "tenant_id": "tenant-sg",
            "correlation_id": "corr-batch",
        }
    ]
    assert render_client.metadata_calls == [{"correlation_id": "corr-batch"}]


@pytest.mark.asyncio
async def test_reporting_batch_control_service_maps_batch_errors() -> None:
    reporting_client = _ReportingClient()
    reporting_client.control_response = (
        404,
        {"detail": {"code": "report_batch_not_found", "message": "missing batch"}},
    )
    service = _service(reporting_client)

    with pytest.raises(HTTPException) as exc_info:
        await service.control_batch(
            batch_id="rbch_missing",
            action="pause",
            caller_headers=_caller_headers(),
            correlation_id="corr-batch",
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == {
        "code": "report_batch_not_found",
        "message": "missing batch",
    }
