from typing import Any

from fastapi import HTTPException, status

from app.clients.advise_client import AdviseClient
from app.config import settings
from app.contracts.advisor_cockpit import AdvisorCockpitEnvelopeResponse


class AdvisorCockpitService:
    def __init__(self, advise_client: AdviseClient):
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

    def _envelope(
        self,
        correlation_id: str,
        upstream_payload: dict[str, Any],
    ) -> AdvisorCockpitEnvelopeResponse:
        return AdvisorCockpitEnvelopeResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            data=upstream_payload,
        )

    def _raise_for_upstream_error(
        self,
        upstream_status: int,
        upstream_payload: dict[str, Any],
    ) -> None:
        if upstream_status >= status.HTTP_400_BAD_REQUEST:
            raise HTTPException(status_code=upstream_status, detail=upstream_payload)
