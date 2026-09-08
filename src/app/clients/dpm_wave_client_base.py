"""The campaign helpers every wave-campaign client call goes through.

lotus-manage guards its campaign routes with `campaign_trusted_context_required`,
a dependency that reads `X-Tenant-Id` straight off the request and refuses a blank
one -- 44 references across 18 routers. Because it is a dependency rather than a
declared parameter, that requirement never reaches the served OpenAPI, so a client
generated from the published contract omits the header and is refused with nothing
in the spec to explain why. Gateway sent nothing here for the same reason.

The tenant is threaded through these two helpers rather than through each of the
twenty-two call sites: every campaign read and write already funnels through them,
so this is the one place the header can be forgotten, and the one place a test can
prove it is not.
"""

from typing import Any

from app.clients.dpm_client_call_surface import DpmClientCallSurfaceMixin


class DpmWaveClientBaseMixin(DpmClientCallSurfaceMixin):
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
        tenant_id: str,
        operation: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            path,
            params=self._clean_params(params),
            headers=self._headers(correlation_id, extras={"X-Tenant-Id": tenant_id}),
            operation=operation,
        )

    async def _post_campaign_workflow_write(
        self,
        path: str,
        body: dict[str, Any],
        correlation_id: str,
        tenant_id: str,
        operation: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            path,
            body=body,
            headers=self._headers(correlation_id, extras={"X-Tenant-Id": tenant_id}),
            operation=operation,
        )
