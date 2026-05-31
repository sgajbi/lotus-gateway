from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, status

from app.clients.lotus_analytics_client import LotusAnalyticsClient
from app.contracts.composite_performance import (
    CompositePerformanceGatewayResponse,
    CompositePerformanceInspectionRequest,
    CompositePerformanceTwrRequest,
)
from app.middleware.correlation import correlation_id_var
from app.services.analytics_client_factory import build_performance_analytics_client
from app.services.caller_context import caller_context_headers

router = APIRouter(prefix="/api/v1/performance/composites", tags=["Composite Performance"])


def _analytics_client() -> LotusAnalyticsClient:
    return build_performance_analytics_client()


def _required_caller_context(
    *,
    actor_id: str | None,
    caller_application: str | None,
    tenant_id: str | None,
    region: str | None,
    booking_center_code: str | None,
    role: str | None,
) -> dict[str, str]:
    return caller_context_headers(
        actor_id=actor_id,
        caller_application=caller_application,
        tenant_id=tenant_id,
        region=region,
        booking_center_code=booking_center_code,
        role=role,
    )


def _raise_upstream_error(*, status_code: int, payload: dict[str, object]) -> None:
    if status_code < 400:
        return
    detail = {
        "source_service": "lotus-performance",
        "upstream_status": status_code,
        "error": payload,
    }
    if status_code == status.HTTP_404_NOT_FOUND:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
    if status_code in {status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_CONTENT}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail)


@router.post(
    "/twr",
    response_model=CompositePerformanceGatewayResponse,
    summary="Calculate Persisted Composite TWR",
    description=(
        "Calculates an asset-weighted composite time-weighted return through lotus-performance "
        "from persisted member-return facts. Gateway is only the governed experience boundary: "
        "it propagates caller context and correlation, preserves the source-owned payload, and "
        "does not calculate returns, member weights, dispersion, lineage, or restatement truth."
    ),
)
async def calculate_composite_twr(
    request: CompositePerformanceTwrRequest,
    actor_id: Annotated[str | None, Header(alias="X-Actor-Id")] = None,
    caller_application: Annotated[str | None, Header(alias="X-Caller-Application")] = None,
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    region: Annotated[str | None, Header(alias="X-Region")] = None,
    booking_center_code: Annotated[str | None, Header(alias="X-Booking-Center-Code")] = None,
    role: Annotated[str | None, Header(alias="X-Role")] = None,
) -> CompositePerformanceGatewayResponse:
    _required_caller_context(
        actor_id=actor_id,
        caller_application=caller_application,
        tenant_id=tenant_id,
        region=region,
        booking_center_code=booking_center_code,
        role=role,
    )
    correlation_id = correlation_id_var.get()
    payload = request.model_dump(exclude_none=True)
    upstream_status, upstream_payload = await _analytics_client().post_composite_twr(
        payload=payload,
        correlation_id=correlation_id,
    )
    _raise_upstream_error(status_code=upstream_status, payload=upstream_payload)
    return CompositePerformanceGatewayResponse(
        correlation_id=correlation_id,
        upstream_status=upstream_status,
        data=upstream_payload,
    )


@router.post(
    "/inspect",
    response_model=CompositePerformanceGatewayResponse,
    summary="Inspect Composite Performance Evidence",
    description=(
        "Runs lotus-performance composite inspection for support, audit, and methodology evidence. "
        "The response carries source-owned findings, evidence summaries, and classified artifacts "
        "such as member inputs, period weights, composite returns, lineage manifest, and support "
        "brief content. Gateway preserves the artifact payloads and does not generate audit truth."
    ),
)
async def inspect_composite_performance(
    request: CompositePerformanceInspectionRequest,
    actor_id: Annotated[str | None, Header(alias="X-Actor-Id")] = None,
    caller_application: Annotated[str | None, Header(alias="X-Caller-Application")] = None,
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    region: Annotated[str | None, Header(alias="X-Region")] = None,
    booking_center_code: Annotated[str | None, Header(alias="X-Booking-Center-Code")] = None,
    role: Annotated[str | None, Header(alias="X-Role")] = None,
) -> CompositePerformanceGatewayResponse:
    _required_caller_context(
        actor_id=actor_id,
        caller_application=caller_application,
        tenant_id=tenant_id,
        region=region,
        booking_center_code=booking_center_code,
        role=role,
    )
    correlation_id = correlation_id_var.get()
    payload = request.model_dump(exclude_none=True)
    upstream_status, upstream_payload = await _analytics_client().post_composite_inspection(
        payload=payload,
        correlation_id=correlation_id,
    )
    _raise_upstream_error(status_code=upstream_status, payload=upstream_payload)
    return CompositePerformanceGatewayResponse(
        correlation_id=correlation_id,
        upstream_status=upstream_status,
        data=upstream_payload,
    )
