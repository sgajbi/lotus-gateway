from typing import Any


class DpmWaveClientBaseMixin:
    def _headers(
        self,
        correlation_id: str,
        extras: dict[str, str] | None = None,
    ) -> dict[str, str]:
        raise NotImplementedError

    async def _get(
        self,
        path: str,
        params: dict[str, Any],
        headers: dict[str, str],
        operation: str,
    ) -> tuple[int, dict[str, Any]]:
        raise NotImplementedError

    async def _post(
        self,
        path: str,
        body: dict[str, Any],
        headers: dict[str, str],
        operation: str,
    ) -> tuple[int, dict[str, Any]]:
        raise NotImplementedError

    async def _put(
        self,
        path: str,
        body: dict[str, Any],
        headers: dict[str, str],
        operation: str,
    ) -> tuple[int, dict[str, Any]]:
        raise NotImplementedError

    def _clean_params(self, params: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in params.items() if value is not None}

    def _campaign_definition_workflow_path(
        self,
        campaign_id: str,
        campaign_version: str,
        suffix: str,
    ) -> str:
        return (
            "/api/v1/rebalance/waves/campaign-definitions/"
            f"{campaign_id}/versions/{campaign_version}/{suffix}"
        )

    async def _get_campaign_workflow_read(
        self,
        path: str,
        params: dict[str, Any],
        correlation_id: str,
        operation: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            path,
            params=self._clean_params(params),
            headers=self._headers(correlation_id),
            operation=operation,
        )

    async def _post_campaign_workflow_write(
        self,
        path: str,
        body: dict[str, Any],
        correlation_id: str,
        operation: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            path,
            body=body,
            headers=self._headers(correlation_id),
            operation=operation,
        )
