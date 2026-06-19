from typing import Any

from app.contracts.dpm_waves import (
    DpmWaveErrorDetail,
    DpmWaveGatewayResponse,
)
from app.services.ai_client_protocols import LotusAiWorkflowClient
from app.services.dpm_wave_ai_handoff import (
    DpmWaveAiHandoffMixin,
    _supportability_from,
)
from app.services.dpm_wave_campaign_definitions import DpmWaveCampaignDefinitionMixin
from app.services.dpm_wave_campaign_workflow import DpmWaveCampaignWorkflowMixin
from app.services.dpm_wave_client_protocols import DpmWaveClient
from app.services.upstream_envelope import (
    build_product_safe_upstream_status_gateway_envelope,
)


class DpmWaveService(
    DpmWaveCampaignDefinitionMixin,
    DpmWaveCampaignWorkflowMixin,
    DpmWaveAiHandoffMixin,
):
    def __init__(
        self,
        dpm_client: DpmWaveClient,
        lotus_ai_client: LotusAiWorkflowClient | None = None,
    ):
        self._dpm_client = dpm_client
        self._lotus_ai_client = lotus_ai_client

    async def preview_wave(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmWaveGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.preview_wave(
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def create_wave(
        self,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> DpmWaveGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.create_wave(
            body=body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def list_waves(
        self,
        filters: dict[str, Any],
        correlation_id: str,
    ) -> DpmWaveGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.list_waves(
            params=filters,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def get_wave(
        self,
        wave_id: str,
        correlation_id: str,
    ) -> DpmWaveGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_wave(
            wave_id=wave_id,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def get_wave_items(
        self,
        wave_id: str,
        correlation_id: str,
    ) -> DpmWaveGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_wave_items(
            wave_id=wave_id,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def source_check_wave(
        self,
        wave_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmWaveGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.source_check_wave(
            wave_id=wave_id,
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def simulate_wave(
        self,
        wave_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmWaveGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.simulate_wave(
            wave_id=wave_id,
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def select_wave_item(
        self,
        wave_id: str,
        wave_item_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmWaveGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.select_wave_item(
            wave_id=wave_id,
            wave_item_id=wave_item_id,
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def approve_wave(
        self,
        wave_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmWaveGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.approve_wave(
            wave_id=wave_id,
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def stage_wave(
        self,
        wave_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmWaveGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.stage_wave(
            wave_id=wave_id,
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def handoff_wave(
        self,
        wave_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmWaveGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.handoff_wave(
            wave_id=wave_id,
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def cancel_wave(
        self,
        wave_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmWaveGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.cancel_wave(
            wave_id=wave_id,
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def get_wave_proof_pack_posture(
        self,
        wave_id: str,
        correlation_id: str,
    ) -> DpmWaveGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_wave_proof_pack_posture(
            wave_id=wave_id,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def get_wave_supportability(
        self,
        wave_id: str,
        correlation_id: str,
    ) -> DpmWaveGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_wave_supportability(
            wave_id=wave_id,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def get_wave_report_input(
        self,
        wave_id: str,
        correlation_id: str,
    ) -> DpmWaveGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_wave_report_input(
            wave_id=wave_id,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    def _compose_response(
        self,
        upstream_status: int,
        upstream_payload: dict[str, Any],
        correlation_id: str,
    ) -> DpmWaveGatewayResponse:
        return build_product_safe_upstream_status_gateway_envelope(
            DpmWaveGatewayResponse,
            correlation_id=correlation_id,
            upstream_status=upstream_status,
            supportability=_supportability_from(upstream_payload),
            upstream_payload=upstream_payload,
            error_model=DpmWaveErrorDetail,
            error_code="MANAGE_WAVE_UPSTREAM_ERROR",
            default_detail="lotus-manage rebalance-wave request failed",
        )
