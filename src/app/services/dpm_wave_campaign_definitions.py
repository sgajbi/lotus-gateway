from typing import Any

from app.contracts.dpm_waves import (
    DpmCampaignDefinitionGatewayResponse,
    DpmWaveErrorDetail,
    DpmWaveGatewayResponse,
)
from app.services.dpm_client_protocols import DpmWaveClient
from app.services.upstream_envelope import (
    build_product_safe_upstream_status_payload_gateway_envelope,
)


class DpmWaveCampaignDefinitionMixin:
    _dpm_client: DpmWaveClient

    async def put_campaign_definition(
        self,
        campaign_id: str,
        campaign_version: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmCampaignDefinitionGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.put_campaign_definition(
            campaign_id=campaign_id,
            campaign_version=campaign_version,
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_campaign_definition_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def list_campaign_definitions(
        self,
        filters: dict[str, Any],
        correlation_id: str,
    ) -> DpmCampaignDefinitionGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.list_campaign_definitions(
            params=filters,
            correlation_id=correlation_id,
        )
        return self._compose_campaign_definition_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def get_campaign_definition(
        self,
        campaign_id: str,
        campaign_version: str,
        correlation_id: str,
    ) -> DpmCampaignDefinitionGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_campaign_definition(
            campaign_id=campaign_id,
            campaign_version=campaign_version,
            correlation_id=correlation_id,
        )
        return self._compose_campaign_definition_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def get_campaign_definition_lifecycle_events(
        self,
        campaign_id: str,
        campaign_version: str,
        correlation_id: str,
    ) -> DpmCampaignDefinitionGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.get_campaign_definition_lifecycle_events(
            campaign_id=campaign_id,
            campaign_version=campaign_version,
            correlation_id=correlation_id,
        )
        return self._compose_campaign_definition_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def get_campaign_definition_preview_readiness(
        self,
        campaign_id: str,
        campaign_version: str,
        filters: dict[str, Any],
        correlation_id: str,
    ) -> DpmCampaignDefinitionGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.get_campaign_definition_preview_readiness(
            campaign_id=campaign_id,
            campaign_version=campaign_version,
            params=filters,
            correlation_id=correlation_id,
        )
        return self._compose_campaign_definition_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def get_campaign_definition_launch_history(
        self,
        campaign_id: str,
        campaign_version: str,
        filters: dict[str, Any],
        correlation_id: str,
    ) -> DpmCampaignDefinitionGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.get_campaign_definition_launch_history(
            campaign_id=campaign_id,
            campaign_version=campaign_version,
            params=filters,
            correlation_id=correlation_id,
        )
        return self._compose_campaign_definition_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def get_campaign_definition_launch_package(
        self,
        campaign_id: str,
        campaign_version: str,
        filters: dict[str, Any],
        correlation_id: str,
    ) -> DpmCampaignDefinitionGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.get_campaign_definition_launch_package(
            campaign_id=campaign_id,
            campaign_version=campaign_version,
            params=filters,
            correlation_id=correlation_id,
        )
        return self._compose_campaign_definition_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def launch_campaign_definition(
        self,
        campaign_id: str,
        campaign_version: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmWaveGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.launch_campaign_definition(
            campaign_id=campaign_id,
            campaign_version=campaign_version,
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def retire_campaign_definition(
        self,
        campaign_id: str,
        campaign_version: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmCampaignDefinitionGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.retire_campaign_definition(
            campaign_id=campaign_id,
            campaign_version=campaign_version,
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_campaign_definition_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def supersede_campaign_definition(
        self,
        campaign_id: str,
        campaign_version: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmCampaignDefinitionGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.supersede_campaign_definition(
            campaign_id=campaign_id,
            campaign_version=campaign_version,
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_campaign_definition_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def discover_campaigns(
        self,
        filters: dict[str, Any],
        correlation_id: str,
    ) -> DpmCampaignDefinitionGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.discover_campaigns(
            params=filters,
            correlation_id=correlation_id,
        )
        return self._compose_campaign_definition_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    def _compose_response(
        self,
        upstream_status: int,
        upstream_payload: dict[str, Any],
        correlation_id: str,
    ) -> DpmWaveGatewayResponse:
        raise NotImplementedError

    def _compose_campaign_definition_response(
        self,
        upstream_status: int,
        upstream_payload: dict[str, Any],
        correlation_id: str,
    ) -> DpmCampaignDefinitionGatewayResponse:
        return build_product_safe_upstream_status_payload_gateway_envelope(
            DpmCampaignDefinitionGatewayResponse,
            correlation_id=correlation_id,
            upstream_status=upstream_status,
            upstream_payload=upstream_payload,
            error_model=DpmWaveErrorDetail,
            error_code="MANAGE_WAVE_UPSTREAM_ERROR",
            default_detail="lotus-manage rebalance-wave request failed",
        )
