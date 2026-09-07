from typing import Any

from app.clients.dpm_client_call_surface import DpmClientCallSurfaceMixin


class DpmConstructionClientMixin(DpmClientCallSurfaceMixin):
    async def generate_construction_alternative_set(
        self,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            "/api/v1/construction/alternative-sets/generate",
            body=body,
            headers=self._headers(correlation_id, {"Idempotency-Key": idempotency_key}),
            operation="manage.construction.alternative_sets.generate",
        )

    async def get_construction_alternative_set(
        self,
        alternative_set_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/construction/alternative-sets/{alternative_set_id}",
            params={},
            headers=self._headers(correlation_id),
            operation="manage.construction.alternative_sets.get",
        )

    async def select_construction_alternative(
        self,
        alternative_set_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/api/v1/construction/alternative-sets/{alternative_set_id}/selections",
            body=body,
            headers=self._headers(correlation_id),
            operation="manage.construction.alternative_sets.select",
        )
