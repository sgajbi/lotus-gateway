from __future__ import annotations

from typing import Any

from app.clients.advise_policy_authority import build_policy_control_headers
from app.services.advisory_policy_access_policy import AdvisoryPolicyCallerContext


class AdvisePolicyPackClientMixin:
    async def list_policy_packs(
        self,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            "/advisory/policy-packs",
            params={},
            headers=self._headers(correlation_id),
            operation="advise.advisory.policy-packs.list",
        )

    async def get_policy_pack_version(
        self,
        policy_pack_id: str,
        policy_version: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/advisory/policy-packs/{policy_pack_id}/versions/{policy_version}",
            params={},
            headers=self._headers(correlation_id),
            operation="advise.advisory.policy-packs.get",
        )

    async def validate_policy_pack_version(
        self,
        policy_pack_id: str,
        policy_version: str,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
        caller: AdvisoryPolicyCallerContext,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/policy-packs/{policy_pack_id}/versions/{policy_version}/validate",
            body=body,
            headers=build_policy_control_headers(
                self._headers,
                correlation_id,
                caller=caller,
                idempotency_key=idempotency_key,
            ),
            operation="advise.advisory.policy-packs.validate",
        )

    async def activate_policy_pack_version(
        self,
        policy_pack_id: str,
        policy_version: str,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
        caller: AdvisoryPolicyCallerContext,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/policy-packs/{policy_pack_id}/versions/{policy_version}/activate",
            body=body,
            headers=build_policy_control_headers(
                self._headers,
                correlation_id,
                caller=caller,
                idempotency_key=idempotency_key,
            ),
            operation="advise.advisory.policy-packs.activate",
        )

    def _headers(
        self,
        correlation_id: str,
        extras: dict[str, str] | None = None,
    ) -> dict[str, str]:
        raise NotImplementedError

    async def _post(
        self,
        path: str,
        body: dict[str, Any],
        headers: dict[str, str],
        operation: str,
        params: dict[str, Any] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        raise NotImplementedError

    async def _get(
        self,
        path: str,
        params: dict[str, Any],
        headers: dict[str, str],
        operation: str,
    ) -> tuple[int, dict[str, Any]]:
        raise NotImplementedError
