import pytest
from fastapi import HTTPException

from app.contracts.advisor_book import AdvisorBookPortfolio
from app.contracts.reporting_batches import BatchCreateRequest
from app.services.advisor_book_service import AdvisorBookServiceError, ResolvedAdvisorBookSelection
from app.services.reporting_batch_lifecycle_service import ReportingBatchLifecycleService
from app.services.reporting_batch_scope import ReportingBatchScopeResolver


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


class _ArchiveAccessClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []
        self.response: tuple[int, dict[str, object]] = (200, {"items": []})

    async def preflight_document_access(self, **kwargs) -> tuple[int, dict[str, object]]:
        self.calls.append(kwargs)
        return self.response


class _PortfolioResolver:
    def __init__(self, *, error: AdvisorBookServiceError | None = None) -> None:
        self.calls: list[dict[str, object]] = []
        self.error = error

    async def resolve_portfolios(self, **kwargs) -> ResolvedAdvisorBookSelection:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return ResolvedAdvisorBookSelection(
            tenant_id="tenant-sg",
            portfolios=(
                AdvisorBookPortfolio(
                    portfolio_id="PB_SG_GLOBAL_BAL_001",
                    display_name="PB_SG_GLOBAL_BAL_001",
                    client_id="CIF_SG_001",
                    base_currency="USD",
                    booking_center_code="SG",
                    mandate_type="DISCRETIONARY",
                    status="ACTIVE",
                    opened_on="2025-03-31",
                    closed_on=None,
                    membership_source="PortfolioManagerBookMembership:v1",
                    membership_reference="portfolio:PB_SG_GLOBAL_BAL_001",
                    membership_basis="governed_role_assignment",
                ),
            ),
        )


def _caller_headers() -> dict[str, str]:
    return {
        "X-Actor-Id": "operator-123",
        "X-Caller-Application": "lotus-workbench",
        "X-Tenant-Id": "tenant-sg",
        "X-Region": "APAC",
        "X-Booking-Center-Code": "SG",
        "X-Role": "ADVISOR",
        "X-Caller-Capabilities": "advisor.book.read",
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
    portfolio_resolver: _PortfolioResolver | None = None,
    archive_access_client: _ArchiveAccessClient | None = None,
) -> ReportingBatchLifecycleService:
    return ReportingBatchLifecycleService(
        reporting_client=reporting_client,
        archive_access_client=archive_access_client or _ArchiveAccessClient(),
        render_client=render_client or _RenderClient(),
        scope_resolver=ReportingBatchScopeResolver(
            portfolio_resolver=portfolio_resolver or _PortfolioResolver()
        ),
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
            "payload": {
                **_batch_request().model_dump(exclude_none=True, mode="json"),
                "source_candidates": [
                    {
                        "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                        "tenant_id": "tenant-sg",
                        "region": "APAC",
                        "active": True,
                        "selected": True,
                        "source_system": "lotus-core",
                        "source_object": "PortfolioManagerBookMembership:v1",
                    }
                ],
            },
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
async def test_reporting_batch_lifecycle_service_never_calls_report_for_out_of_book_selection() -> (
    None
):
    reporting_client = _ReportingClient()
    portfolio_resolver = _PortfolioResolver(
        error=AdvisorBookServiceError(
            code="advisor_book_portfolio_not_available",
            message="unsafe source detail",
            status_code=403,
        )
    )
    service = _service(reporting_client, portfolio_resolver=portfolio_resolver)

    with pytest.raises(HTTPException) as raised:
        await service.create_batch(
            request=_batch_request(),
            idempotency_key="idem-hostile-selection",
            caller_headers=_caller_headers(),
            correlation_id="corr-hostile-selection",
            tenant_id="tenant-sg",
        )

    assert raised.value.status_code == 403
    assert raised.value.detail == {
        "code": "report_batch_portfolio_not_entitled",
        "message": "One or more selected portfolios are not available in the authenticated book.",
    }
    assert reporting_client.create_calls == []
    assert reporting_client.capability_calls == []


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


@pytest.mark.asyncio
async def test_reporting_batch_lifecycle_service_keeps_archive_preflight_advisory() -> None:
    reporting_client = _ReportingClient()
    archive_access_client = _ArchiveAccessClient()
    archive_access_client.response = (503, {"detail": "archive timeout"})
    reporting_client.status_response = (
        200,
        {
            **_batch_status_payload(),
            "items": [
                {
                    **_batch_status_payload()["items"][0],
                    "status": "succeeded",
                    "report_job_id": "rjob_1",
                    "report_job_status": "archived",
                    "archive_document_id": "doc_timeout",
                }
            ],
        },
    )
    service = _service(reporting_client, archive_access_client=archive_access_client)

    response = await service.get_batch_status(
        batch_id="rbch_1",
        caller_headers=_caller_headers(),
        correlation_id="corr-batch",
        tenant_id="tenant-sg",
    )

    assert response.items[0].archive_state == "unavailable"
    assert response.items[0].archive_document_id is None
    assert response.items[0].archive_metadata_url is None
    assert len(archive_access_client.calls) == 1


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
