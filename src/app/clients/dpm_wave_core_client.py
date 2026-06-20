from typing import Any

from app.clients.dpm_wave_client_base import DpmWaveClientBaseMixin


class DpmWaveCoreClientMixin(DpmWaveClientBaseMixin):
    async def preview_wave(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            "/api/v1/rebalance/waves/preview",
            body=body,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.preview",
        )

    async def create_wave(
        self,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            "/api/v1/rebalance/waves",
            body=body,
            headers=self._headers(correlation_id, {"Idempotency-Key": idempotency_key}),
            operation="manage.rebalance.waves.create",
        )

    async def list_waves(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            "/api/v1/rebalance/waves",
            params=self._clean_params(params),
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.list",
        )

    async def get_wave(
        self,
        wave_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/rebalance/waves/{wave_id}",
            params={},
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.get",
        )

    async def discover_campaigns(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            "/api/v1/rebalance/waves/campaign-discovery",
            params=self._clean_params(params),
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.campaign_discovery",
        )

    async def get_wave_items(
        self,
        wave_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/rebalance/waves/{wave_id}/items",
            params={},
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.items",
        )

    async def source_check_wave(
        self,
        wave_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/api/v1/rebalance/waves/{wave_id}/source-check",
            body=body,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.source_check",
        )

    async def simulate_wave(
        self,
        wave_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/api/v1/rebalance/waves/{wave_id}/simulate",
            body=body,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.simulate",
        )

    async def select_wave_item(
        self,
        wave_id: str,
        wave_item_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/api/v1/rebalance/waves/{wave_id}/items/{wave_item_id}/select",
            body=body,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.items.select",
        )

    async def approve_wave(
        self,
        wave_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/api/v1/rebalance/waves/{wave_id}/approve",
            body=body,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.approve",
        )

    async def stage_wave(
        self,
        wave_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/api/v1/rebalance/waves/{wave_id}/stage",
            body=body,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.stage",
        )

    async def handoff_wave(
        self,
        wave_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/api/v1/rebalance/waves/{wave_id}/handoff",
            body=body,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.handoff",
        )

    async def cancel_wave(
        self,
        wave_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/api/v1/rebalance/waves/{wave_id}/cancel",
            body=body,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.cancel",
        )

    async def get_wave_proof_pack_posture(
        self,
        wave_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/rebalance/waves/{wave_id}/proof-pack",
            params={},
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.proof_pack",
        )

    async def get_wave_supportability(
        self,
        wave_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/rebalance/waves/{wave_id}/supportability",
            params={},
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.supportability",
        )

    async def get_wave_report_input(
        self,
        wave_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/rebalance/waves/{wave_id}/report-input",
            params={},
            headers=self._headers(correlation_id),
            operation="manage.rebalance.waves.report_input",
        )
