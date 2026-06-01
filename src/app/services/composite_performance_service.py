from typing import Any

from app.contracts.composite_performance import CompositePerformanceGatewayResponse
from app.services.caller_context import caller_context_headers
from app.services.domain_client_protocols import CompositePerformanceClient
from app.services.upstream_envelope import raise_gateway_mapped_service_error


class CompositePerformanceService:
    def __init__(self, analytics_client: CompositePerformanceClient):
        self._analytics_client = analytics_client

    async def calculate_twr(
        self,
        *,
        payload: dict[str, Any],
        correlation_id: str,
        caller_context: dict[str, str | None],
    ) -> CompositePerformanceGatewayResponse:
        self._validate_caller_context(caller_context)
        upstream_status, upstream_payload = await self._analytics_client.post_composite_twr(
            payload=payload,
            correlation_id=correlation_id,
        )
        self._raise_upstream_error(status_code=upstream_status, payload=upstream_payload)
        return self._response(
            correlation_id=correlation_id,
            upstream_status=upstream_status,
            upstream_payload=upstream_payload,
        )

    async def inspect(
        self,
        *,
        payload: dict[str, Any],
        correlation_id: str,
        caller_context: dict[str, str | None],
    ) -> CompositePerformanceGatewayResponse:
        self._validate_caller_context(caller_context)
        (
            upstream_status,
            upstream_payload,
        ) = await self._analytics_client.post_composite_inspection(
            payload=payload,
            correlation_id=correlation_id,
        )
        self._raise_upstream_error(status_code=upstream_status, payload=upstream_payload)
        return self._response(
            correlation_id=correlation_id,
            upstream_status=upstream_status,
            upstream_payload=upstream_payload,
        )

    def _validate_caller_context(self, caller_context: dict[str, str | None]) -> None:
        caller_context_headers(
            actor_id=caller_context.get("actor_id"),
            caller_application=caller_context.get("caller_application"),
            tenant_id=caller_context.get("tenant_id"),
            region=caller_context.get("region"),
            booking_center_code=caller_context.get("booking_center_code"),
            role=caller_context.get("role"),
        )

    def _raise_upstream_error(
        self,
        *,
        status_code: int,
        payload: dict[str, Any],
    ) -> None:
        raise_gateway_mapped_service_error(
            status_code,
            payload,
            source_service="lotus-performance",
        )

    def _response(
        self,
        *,
        correlation_id: str,
        upstream_status: int,
        upstream_payload: dict[str, Any],
    ) -> CompositePerformanceGatewayResponse:
        return CompositePerformanceGatewayResponse(
            correlation_id=correlation_id,
            upstream_status=upstream_status,
            data=upstream_payload,
        )
