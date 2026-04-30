import logging
from typing import Any

from app.clients.observed_fanout import request_observed_fanout
from app.middleware.correlation import propagation_headers

logger = logging.getLogger("analytics_ui.gateway")


class DpmClient:
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

    async def simulate_proposal(
        self,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            "/api/v1/rebalance/proposals/simulate",
            body=body,
            headers=self._headers(correlation_id, {"Idempotency-Key": idempotency_key}),
            operation="manage.rebalance.proposals.simulate",
        )

    async def create_proposal(
        self,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            "/api/v1/rebalance/proposals",
            body=body,
            headers=self._headers(correlation_id, {"Idempotency-Key": idempotency_key}),
            operation="manage.rebalance.proposals.create",
        )

    async def list_proposals(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        cleaned_params = {key: value for key, value in params.items() if value is not None}
        return await self._get(
            "/api/v1/rebalance/proposals",
            params=cleaned_params,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.proposals.list",
        )

    async def list_runs(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        cleaned_params = {key: value for key, value in params.items() if value is not None}
        return await self._get(
            "/api/v1/rebalance/runs",
            params=cleaned_params,
            headers=self._headers(correlation_id),
            operation="manage.rebalance.runs.list",
        )

    async def get_supportability_summary(
        self,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            "/api/v1/rebalance/supportability/summary",
            params={},
            headers=self._headers(correlation_id),
            operation="manage.rebalance.supportability.summary",
        )

    async def get_proposal(
        self,
        proposal_id: str,
        include_evidence: bool,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/rebalance/proposals/{proposal_id}",
            params={"include_evidence": str(include_evidence).lower()},
            headers=self._headers(correlation_id),
            operation="manage.rebalance.proposals.get",
        )

    async def get_proposal_version(
        self,
        proposal_id: str,
        version_no: int,
        include_evidence: bool,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/rebalance/proposals/{proposal_id}/versions/{version_no}",
            params={"include_evidence": str(include_evidence).lower()},
            headers=self._headers(correlation_id),
            operation="manage.rebalance.proposals.versions.get",
        )

    async def create_proposal_version(
        self,
        proposal_id: str,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/api/v1/rebalance/proposals/{proposal_id}/versions",
            body=body,
            headers=self._headers(correlation_id, {"Idempotency-Key": idempotency_key}),
            operation="manage.rebalance.proposals.versions.create",
        )

    async def transition_proposal(
        self,
        proposal_id: str,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/api/v1/rebalance/proposals/{proposal_id}/transitions",
            body=body,
            headers=self._headers(correlation_id, {"Idempotency-Key": idempotency_key}),
            operation="manage.rebalance.proposals.transition",
        )

    async def record_approval(
        self,
        proposal_id: str,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/api/v1/rebalance/proposals/{proposal_id}/approvals",
            body=body,
            headers=self._headers(correlation_id, {"Idempotency-Key": idempotency_key}),
            operation="manage.rebalance.proposals.approvals.record",
        )

    async def get_workflow_events(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/rebalance/proposals/{proposal_id}/workflow-events",
            params={},
            headers=self._headers(correlation_id),
            operation="manage.rebalance.proposals.workflow-events",
        )

    async def get_approvals(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/rebalance/proposals/{proposal_id}/approvals",
            params={},
            headers=self._headers(correlation_id),
            operation="manage.rebalance.proposals.approvals.list",
        )

    async def get_proposal_lineage(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/rebalance/proposals/{proposal_id}/lineage",
            params={},
            headers=self._headers(correlation_id),
            operation="manage.rebalance.proposals.lineage",
        )

    async def get_capabilities(
        self,
        consumer_system: str,
        tenant_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            "/api/v1/platform/capabilities",
            params={"consumerSystem": consumer_system, "tenantId": tenant_id},
            headers=self._headers(correlation_id),
            operation="manage.platform.capabilities",
        )

    def _headers(
        self,
        correlation_id: str,
        extras: dict[str, str] | None = None,
    ) -> dict[str, str]:
        headers = propagation_headers(correlation_id)
        if extras:
            headers.update(extras)
        return headers

    async def _post(
        self,
        path: str,
        body: dict[str, Any],
        headers: dict[str, str],
        operation: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}{path}"
        return await request_observed_fanout(
            logger=logger,
            service="lotus-manage",
            operation=operation,
            method="POST",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
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
        url = f"{self._base_url}{path}"
        return await request_observed_fanout(
            logger=logger,
            service="lotus-manage",
            operation=operation,
            method="GET",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            params=params,
            headers=headers,
        )
