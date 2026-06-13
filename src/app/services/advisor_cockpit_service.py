from typing import Any

from app.contracts.advisor_cockpit import AdvisorCockpitEnvelopeResponse
from app.services.advisory_client_protocols import AdvisorCockpitClient
from app.services.upstream_envelope import (
    ProductSafeServiceErrorConfig,
    build_gateway_envelope,
    raise_configured_product_safe_service_error,
)

ADVISOR_COCKPIT_ERROR_CONFIG = ProductSafeServiceErrorConfig(
    source_service="lotus-advise",
    error_code="ADVISE_COCKPIT_UPSTREAM_ERROR",
    default_detail="lotus-advise advisor cockpit request failed.",
)


class AdvisorCockpitService:
    def __init__(self, advise_client: AdvisorCockpitClient):
        self._advise_client = advise_client

    async def list_actions(
        self,
        *,
        params: dict[str, Any],
        correlation_id: str,
    ) -> AdvisorCockpitEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.list_advisor_cockpit_actions(
            params=params,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def list_preparation_packets(
        self,
        *,
        params: dict[str, Any],
        correlation_id: str,
    ) -> AdvisorCockpitEnvelopeResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._advise_client.list_advisor_cockpit_preparation_packets(
            params=params,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def get_action(
        self,
        *,
        action_item_id: str,
        params: dict[str, Any],
        correlation_id: str,
    ) -> AdvisorCockpitEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.get_advisor_cockpit_action(
            action_item_id=action_item_id,
            params=params,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def get_snapshot(
        self,
        *,
        params: dict[str, Any],
        correlation_id: str,
    ) -> AdvisorCockpitEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.get_advisor_cockpit_snapshot(
            params=params,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def get_supportability(
        self,
        *,
        params: dict[str, Any],
        correlation_id: str,
    ) -> AdvisorCockpitEnvelopeResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._advise_client.get_advisor_cockpit_supportability(
            params=params,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def acknowledge_action(
        self,
        *,
        action_item_id: str,
        body: dict[str, Any],
        params: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> AdvisorCockpitEnvelopeResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._advise_client.acknowledge_advisor_cockpit_action(
            action_item_id=action_item_id,
            body=body,
            params=params,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def evaluate_house_view_cohort(
        self,
        *,
        body: dict[str, Any],
        correlation_id: str,
    ) -> AdvisorCockpitEnvelopeResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._advise_client.evaluate_advisor_cockpit_house_view_cohort(
            body=body,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    def _envelope(
        self,
        correlation_id: str,
        upstream_payload: dict[str, Any],
    ) -> AdvisorCockpitEnvelopeResponse:
        return build_gateway_envelope(
            AdvisorCockpitEnvelopeResponse,
            correlation_id=correlation_id,
            upstream_payload=upstream_payload,
        )

    def _raise_for_upstream_error(
        self,
        upstream_status: int,
        upstream_payload: dict[str, Any],
    ) -> None:
        raise_configured_product_safe_service_error(
            upstream_status,
            upstream_payload,
            config=ADVISOR_COCKPIT_ERROR_CONFIG,
        )
