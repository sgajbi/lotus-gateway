from typing import Any

from app.clients.dpm_wave_client_base import DpmWaveClientBaseMixin


class DpmWaveCampaignDefinitionClientMixin(DpmWaveClientBaseMixin):
    async def put_campaign_definition(
        self,
        campaign_id: str,
        campaign_version: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._put(
            f"/api/v1/rebalance/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}",
            body=body,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.campaign_definitions.put",
        )

    async def list_campaign_definitions(
        self,
        params: dict[str, Any],
        correlation_id: str,
        tenant_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            "/api/v1/rebalance/waves/campaign-definitions",
            params=self._clean_params(params),
            headers=self._headers(
                correlation_id,
                extras={"X-Tenant-Id": tenant_id},
            ),
            operation="manage.rebalance.waves.campaign_definitions.list",
        )

    async def get_campaign_definition(
        self,
        campaign_id: str,
        campaign_version: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/rebalance/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}",
            params={},
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.campaign_definitions.get",
        )

    async def get_campaign_definition_lifecycle_events(
        self,
        campaign_id: str,
        campaign_version: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/rebalance/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/lifecycle-events",
            params={},
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.campaign_definitions.lifecycle_events",
        )

    async def get_campaign_definition_preview_readiness(
        self,
        campaign_id: str,
        campaign_version: str,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/rebalance/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/preview-readiness",
            params=self._clean_params(params),
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.campaign_definitions.preview_readiness",
        )

    async def get_campaign_definition_launch_history(
        self,
        campaign_id: str,
        campaign_version: str,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/rebalance/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/launch-history",
            params=self._clean_params(params),
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.campaign_definitions.launch_history",
        )

    async def get_campaign_definition_launch_package(
        self,
        campaign_id: str,
        campaign_version: str,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/rebalance/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/launch-package",
            params=self._clean_params(params),
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.campaign_definitions.launch_package",
        )

    async def launch_campaign_definition(
        self,
        campaign_id: str,
        campaign_version: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/api/v1/rebalance/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/launch",
            body=body,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.campaign_definitions.launch",
        )

    async def retire_campaign_definition(
        self,
        campaign_id: str,
        campaign_version: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/api/v1/rebalance/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/retire",
            body=body,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.campaign_definitions.retire",
        )

    async def supersede_campaign_definition(
        self,
        campaign_id: str,
        campaign_version: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/api/v1/rebalance/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/supersede",
            body=body,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.campaign_definitions.supersede",
        )
