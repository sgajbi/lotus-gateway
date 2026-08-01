from __future__ import annotations

from typing import Any

from app.clients.advise_policy_authority import (
    POLICY_CHECKER_ROLE,
    POLICY_PACK_ACTIVATE_CAPABILITY,
    POLICY_PACK_VALIDATE_CAPABILITY,
    POLICY_STEWARD_ROLE,
    body_actor,
    build_policy_control_headers,
)


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
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/policy-packs/{policy_pack_id}/versions/{policy_version}/validate",
            body=body,
            headers=build_policy_control_headers(
                self._headers,
                correlation_id,
                actor_id=body_actor(body, "requested_by", fallback="policy_steward_1"),
                role=POLICY_STEWARD_ROLE,
                capability=POLICY_PACK_VALIDATE_CAPABILITY,
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
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/policy-packs/{policy_pack_id}/versions/{policy_version}/activate",
            body=body,
            headers=build_policy_control_headers(
                self._headers,
                correlation_id,
                actor_id=body_actor(body, "activated_by", fallback="policy_checker_1"),
                role=POLICY_CHECKER_ROLE,
                capability=POLICY_PACK_ACTIVATE_CAPABILITY,
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
