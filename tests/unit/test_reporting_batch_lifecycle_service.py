import pytest
from fastapi import HTTPException

from app.contracts.reporting_batches import BatchCreateRequest
from app.services.reporting_batch_lifecycle_service import ReportingBatchLifecycleService


class _ReportingClient:
    def __init__(self) -> None:
        self.create_response: tuple[int, dict[str, object]] = (
            202,
            {
                "batch_id": "rbch_1",
                "status": "materialized",
                "status_url": "/reports/batches/rbch_1",
                "idempotency_key": "idem-batch",
                "item_count": 1,
            },
        )
        self.status_response: tuple[int, dict[str, object]] = (200, _batch_status_payload())
        self.create_calls: list[dict[str, object]] = []
        self.status_calls: list[dict[str, object]] = []
        self.capability_calls: list[dict[str, str]] = []

    async def create_report_batch(
        self,
        *,
        payload: dict[str, object],
        idempotency_key: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.create_calls.append(
            {
                "payload": payload,
                "idempotency_key": idempotency_key,
                "caller_headers": caller_headers,
                "correlation_id": correlation_id,
            }
        )
        return self.create_response

    async def get_report_batch(
        self,
        *,
        batch_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.status_calls.append(
            {
                "batch_id": batch_id,
                "caller_headers": caller_headers,
                "correlation_id": correlation_id,
            }
        )
        return self.status_response

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


def _batch_request() -> BatchCreateRequest:
    return BatchCreateRequest.model_validate(
        {
            "selector_mode": "explicit_portfolio_list",
            "portfolio_ids": ["PB_SG_GLOBAL_BAL_001"],
            "as_of_date": "2026-04-22",
            "requested_output_formats": ["pdf"],
            "reporting_currency": "USD",
            "options": {"sections": ["OVERVIEW"]},
            "max_batch_size": 250,
        }
    )


def _batch_status_payload() -> dict[str, object]:
    return {
        "batch_id": "rbch_1",
        "selector_mode": "explicit_portfolio_list",
        "tenant_id": "tenant-sg",
        "region": "APAC",
        "materialized_portfolio_ids": ["PB_SG_GLOBAL_BAL_001"],
        "as_of_date": "2026-04-22",
        "requested_output_formats": ["pdf"],
        "reporting_currency": "USD",
        "status": "materialized",
        "item_count": 1,
        "status_counts": {"materialized": 1},
        "items": [
            {
                "batch_item_id": "rbci_1",
                "item_position": 1,
                "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                "status": "materialized",
                "report_job_id": None,
                "attempt_count": 0,
                "retry_eligible": False,
                "next_retry_at": None,
                "last_error_category": None,
                "last_error_summary": None,
                "created_at": "2026-04-22T09:00:00Z",
                "started_at": None,
                "completed_at": None,
                "cancelled_at": None,
            }
        ],
        "created_at": "2026-04-22T09:00:00Z",
        "updated_at": "2026-04-22T09:00:00Z",
        "started_at": None,
        "completed_at": None,
        "cancelled_at": None,
        "failed_at": None,
        "correlation_id": "corr-batch",
        "trace_id": "trace-batch",
    }


def _service(
    reporting_client: _ReportingClient,
    render_client: _RenderClient | None = None,
) -> ReportingBatchLifecycleService:
    return ReportingBatchLifecycleService(
        reporting_client=reporting_client,
        render_client=render_client or _RenderClient(),
    )


@pytest.mark.asyncio
async def test_reporting_batch_lifecycle_service_creates_batch_with_supportability() -> None:
    reporting_client = _ReportingClient()
    render_client = _RenderClient()
    service = _service(reporting_client, render_client)

    response = await service.create_batch(
        request=_batch_request(),
        idempotency_key="idem-batch",
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
    assert reporting_client.create_calls == [
        {
            "payload": _batch_request().model_dump(exclude_none=True, mode="json"),
            "idempotency_key": "idem-batch",
            "caller_headers": _caller_headers(),
            "correlation_id": "corr-batch",
        }
    ]
    assert reporting_client.capability_calls == [
        {
            "consumer_system": "lotus-gateway",
            "tenant_id": "tenant-sg",
            "correlation_id": "corr-batch",
        }
    ]
    assert render_client.metadata_calls == [{"correlation_id": "corr-batch"}]


@pytest.mark.asyncio
async def test_reporting_batch_lifecycle_service_gets_batch_status_with_supportability() -> None:
    reporting_client = _ReportingClient()
    service = _service(reporting_client)

    response = await service.get_batch_status(
        batch_id="rbch_1",
        caller_headers=_caller_headers(),
        correlation_id="corr-batch",
        tenant_id="tenant-sg",
    )

    assert response.batch_id == "rbch_1"
    assert response.items[0].portfolio_id == "PB_SG_GLOBAL_BAL_001"
    assert response.supportability is not None
    assert response.render_supportability is not None
    assert response.supportability.state == "ready"
    assert response.render_supportability.state == "ready"
    assert reporting_client.status_calls == [
        {
            "batch_id": "rbch_1",
            "caller_headers": _caller_headers(),
            "correlation_id": "corr-batch",
        }
    ]


def test_reporting_batch_lifecycle_service_requires_idempotency_key() -> None:
    service = _service(_ReportingClient())

    with pytest.raises(HTTPException) as exc_info:
        service.require_idempotency_key(None)

    assert exc_info.value.status_code == 400
    assert isinstance(exc_info.value.detail, dict)
    assert exc_info.value.detail["code"] == "missing_idempotency_key"


@pytest.mark.asyncio
async def test_reporting_batch_lifecycle_service_maps_batch_errors() -> None:
    reporting_client = _ReportingClient()
    reporting_client.status_response = (
        404,
        {"detail": {"code": "report_batch_not_found", "message": "missing batch"}},
    )
    service = _service(reporting_client)

    with pytest.raises(HTTPException) as exc_info:
        await service.get_batch_status(
            batch_id="rbch_missing",
            caller_headers=_caller_headers(),
            correlation_id="corr-batch",
            tenant_id="tenant-sg",
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == {
        "code": "report_batch_not_found",
        "message": "missing batch",
    }
