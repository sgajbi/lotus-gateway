from typing import Any

from app.contracts.source_products import ExternalOrderExecutionAcknowledgementResponse
from app.services.domain_client_protocols import SourceProductExecutionClient
from app.services.upstream_envelope import raise_gateway_mapped_service_error


class SourceProductExecutionService:
    def __init__(self, lotus_core_query_client: SourceProductExecutionClient) -> None:
        self._lotus_core_query_client = lotus_core_query_client

    async def get_external_order_execution_acknowledgement(
        self,
        *,
        portfolio_id: str,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> ExternalOrderExecutionAcknowledgementResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._lotus_core_query_client.get_external_order_execution_acknowledgement(
            portfolio_id=portfolio_id,
            payload=payload,
            correlation_id=correlation_id,
        )
        self._raise_core_error(upstream_status=upstream_status, payload=upstream_payload)
        return ExternalOrderExecutionAcknowledgementResponse.model_validate(upstream_payload)

    def _raise_core_error(
        self,
        *,
        upstream_status: int,
        payload: dict[str, Any],
    ) -> None:
        raise_gateway_mapped_service_error(
            upstream_status,
            payload,
            source_service="lotus-core",
        )
