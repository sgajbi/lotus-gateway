from __future__ import annotations

import logging
from typing import Any

from app.clients.advise_advisory_copilot_client import AdviseAdvisoryCopilotClientMixin
from app.clients.advise_bank_demo_proof_client import AdviseBankDemoProofClientMixin
from app.clients.advise_policy_client import AdvisePolicyClientMixin
from app.clients.advise_proposal_client import AdviseProposalClientMixin
from app.clients.advise_workspace_client import AdviseWorkspaceClientMixin
from app.clients.observed_fanout import request_observed_fanout
from app.clients.upstream_headers import (
    build_idempotent_upstream_headers,
    build_upstream_headers,
)

logger = logging.getLogger("analytics_ui.gateway")


class AdviseClient(
    AdviseWorkspaceClientMixin,
    AdviseBankDemoProofClientMixin,
    AdviseAdvisoryCopilotClientMixin,
    AdvisePolicyClientMixin,
    AdviseProposalClientMixin,
):
    def __init__(
        self,
        base_url: str,
        timeout_seconds: float,
        max_retries: int = 2,
        retry_backoff_seconds: float = 0.2,
    ):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._max_retries = max_retries
        self._retry_backoff_seconds = retry_backoff_seconds

    async def get_platform_capabilities(
        self,
        *,
        consumer_system: str = "lotus-gateway",
        tenant_id: str = "default",
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await request_observed_fanout(
            logger=logger,
            service="lotus-advise",
            operation="advise.platform.capabilities",
            method="GET",
            url=f"{self._base_url}/platform/capabilities",
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            params={"consumer_system": consumer_system, "tenant_id": tenant_id},
            headers=build_upstream_headers(correlation_id),
        )

    async def get_capabilities(
        self,
        consumer_system: str,
        tenant_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        _ = consumer_system
        return await self.get_platform_capabilities(
            consumer_system="lotus-gateway",
            tenant_id=tenant_id,
            correlation_id=correlation_id,
        )

    async def list_advisor_cockpit_actions(
        self,
        params: dict[str, Any],
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            "/advisory/cockpit/actions",
            params=self._clean_params(params),
            headers=self._headers(correlation_id, caller_headers),
            operation="advise.advisory.cockpit.actions.list",
        )

    async def list_advisor_cockpit_preparation_packets(
        self,
        params: dict[str, Any],
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            "/advisory/cockpit/preparation-packets",
            params=self._clean_params(params),
            headers=self._headers(correlation_id, caller_headers),
            operation="advise.advisory.cockpit.preparation-packets.list",
        )

    async def get_advisor_cockpit_action(
        self,
        action_item_id: str,
        params: dict[str, Any],
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/advisory/cockpit/actions/{action_item_id}",
            params=self._clean_params(params),
            headers=self._headers(correlation_id, caller_headers),
            operation="advise.advisory.cockpit.actions.get",
        )

    async def get_advisor_cockpit_snapshot(
        self,
        params: dict[str, Any],
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            "/advisory/cockpit/snapshot",
            params=self._clean_params(params),
            headers=self._headers(correlation_id, caller_headers),
            operation="advise.advisory.cockpit.snapshot",
        )

    async def get_advisor_cockpit_supportability(
        self,
        params: dict[str, Any],
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            "/advisory/cockpit/supportability",
            params=self._clean_params(params),
            headers=self._headers(correlation_id, caller_headers),
            operation="advise.advisory.cockpit.supportability",
        )

    async def acknowledge_advisor_cockpit_action(
        self,
        action_item_id: str,
        body: dict[str, Any],
        params: dict[str, Any],
        caller_headers: dict[str, str],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/cockpit/actions/{action_item_id}/acknowledgements",
            body=body,
            headers=self._headers(
                correlation_id,
                {**caller_headers, "Idempotency-Key": idempotency_key},
            ),
            operation="advise.advisory.cockpit.actions.acknowledge",
            params=self._clean_params(params),
        )

    async def evaluate_advisor_cockpit_house_view_cohort(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            "/advisory/tactical-house-view/cohorts/evaluate",
            body=body,
            headers=self._headers(correlation_id),
            operation="advise.advisory.tactical-house-view.cohorts.evaluate",
        )

    def _headers(
        self,
        correlation_id: str,
        extras: dict[str, str] | None = None,
    ) -> dict[str, str]:
        return build_upstream_headers(correlation_id, extras=extras)

    def _optional_idempotency_headers(
        self,
        correlation_id: str,
        idempotency_key: str | None,
    ) -> dict[str, str]:
        if idempotency_key is None:
            return self._headers(correlation_id)
        return build_idempotent_upstream_headers(correlation_id, idempotency_key)

    async def _post(
        self,
        path: str,
        body: dict[str, Any],
        headers: dict[str, str],
        operation: str,
        params: dict[str, Any] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        return await request_observed_fanout(
            logger=logger,
            service="lotus-advise",
            operation=operation,
            method="POST",
            url=f"{self._base_url}{path}",
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            params=params,
            json_body=body,
            headers=headers,
        )

    async def _get(
        self,
        path: str,
        params: dict[str, Any],
        headers: dict[str, str],
        operation: str,
    ) -> tuple[int, dict[str, Any]]:
        return await request_observed_fanout(
            logger=logger,
            service="lotus-advise",
            operation=operation,
            method="GET",
            url=f"{self._base_url}{path}",
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            params=params,
            headers=headers,
        )

    def _clean_params(self, params: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in params.items() if value is not None}
