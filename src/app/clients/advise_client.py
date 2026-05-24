from __future__ import annotations

import logging
from typing import Any

from app.clients.observed_fanout import request_observed_fanout
from app.middleware.correlation import propagation_headers

logger = logging.getLogger("analytics_ui.gateway")


class AdviseClient:
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
            headers=propagation_headers(correlation_id),
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

    async def simulate_proposal(
        self,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            "/advisory/proposals/simulate",
            body=body,
            headers=self._headers(correlation_id, {"Idempotency-Key": idempotency_key}),
            operation="advise.advisory.proposals.simulate",
        )

    async def create_advisory_workspace(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            "/advisory/workspaces",
            body=body,
            headers=self._headers(correlation_id),
            operation="advise.advisory.workspaces.create",
        )

    async def get_advisory_workspace(
        self,
        workspace_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/advisory/workspaces/{workspace_id}",
            params={},
            headers=self._headers(correlation_id),
            operation="advise.advisory.workspaces.get",
        )

    async def apply_advisory_workspace_draft_action(
        self,
        workspace_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/workspaces/{workspace_id}/draft-actions",
            body=body,
            headers=self._headers(correlation_id),
            operation="advise.advisory.workspaces.draft-action",
        )

    async def evaluate_advisory_workspace(
        self,
        workspace_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/workspaces/{workspace_id}/evaluate",
            body={},
            headers=self._headers(correlation_id),
            operation="advise.advisory.workspaces.evaluate",
        )

    async def save_advisory_workspace(
        self,
        workspace_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/workspaces/{workspace_id}/save",
            body=body,
            headers=self._headers(correlation_id),
            operation="advise.advisory.workspaces.save",
        )

    async def handoff_advisory_workspace(
        self,
        workspace_id: str,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        headers = self._headers(correlation_id)
        if idempotency_key is not None:
            headers["Idempotency-Key"] = idempotency_key
        return await self._post(
            f"/advisory/workspaces/{workspace_id}/handoff",
            body=body,
            headers=headers,
            operation="advise.advisory.workspaces.handoff",
        )

    async def create_proposal(
        self,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            "/advisory/proposals",
            body=body,
            headers=self._headers(correlation_id, {"Idempotency-Key": idempotency_key}),
            operation="advise.advisory.proposals.create",
        )

    async def list_proposals(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        cleaned_params = {key: value for key, value in params.items() if value is not None}
        return await self._get(
            "/advisory/proposals",
            params=cleaned_params,
            headers=self._headers(correlation_id),
            operation="advise.advisory.proposals.list",
        )

    async def get_proposal(
        self,
        proposal_id: str,
        include_evidence: bool,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/advisory/proposals/{proposal_id}",
            params={"include_evidence": str(include_evidence).lower()},
            headers=self._headers(correlation_id),
            operation="advise.advisory.proposals.get",
        )

    async def get_proposal_version(
        self,
        proposal_id: str,
        version_no: int,
        include_evidence: bool,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/advisory/proposals/{proposal_id}/versions/{version_no}",
            params={"include_evidence": str(include_evidence).lower()},
            headers=self._headers(correlation_id),
            operation="advise.advisory.proposals.versions.get",
        )

    async def create_proposal_version(
        self,
        proposal_id: str,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/proposals/{proposal_id}/versions",
            body=body,
            headers=self._headers(correlation_id, {"Idempotency-Key": idempotency_key}),
            operation="advise.advisory.proposals.versions.create",
        )

    async def transition_proposal(
        self,
        proposal_id: str,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/proposals/{proposal_id}/transitions",
            body=body,
            headers=self._headers(correlation_id, {"Idempotency-Key": idempotency_key}),
            operation="advise.advisory.proposals.transition",
        )

    async def record_approval(
        self,
        proposal_id: str,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/proposals/{proposal_id}/approvals",
            body=body,
            headers=self._headers(correlation_id, {"Idempotency-Key": idempotency_key}),
            operation="advise.advisory.proposals.approvals.record",
        )

    async def get_workflow_events(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/advisory/proposals/{proposal_id}/workflow-events",
            params={},
            headers=self._headers(correlation_id),
            operation="advise.advisory.proposals.workflow-events",
        )

    async def get_approvals(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/advisory/proposals/{proposal_id}/approvals",
            params={},
            headers=self._headers(correlation_id),
            operation="advise.advisory.proposals.approvals.list",
        )

    async def get_proposal_lineage(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/advisory/proposals/{proposal_id}/lineage",
            params={},
            headers=self._headers(correlation_id),
            operation="advise.advisory.proposals.lineage",
        )

    async def review_proposal_narrative(
        self,
        proposal_id: str,
        version_no: int,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        headers = self._headers(correlation_id)
        if idempotency_key is not None:
            headers["Idempotency-Key"] = idempotency_key
        return await self._post(
            f"/advisory/proposals/{proposal_id}/versions/{version_no}/narrative/review",
            body=body,
            headers=headers,
            operation="advise.advisory.proposals.narrative.review",
        )

    async def create_report_request(
        self,
        proposal_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/proposals/{proposal_id}/report-requests",
            body=body,
            headers=self._headers(correlation_id),
            operation="advise.advisory.proposals.report-requests.create",
        )

    async def get_delivery_summary(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/advisory/proposals/{proposal_id}/delivery-summary",
            params={},
            headers=self._headers(correlation_id),
            operation="advise.advisory.proposals.delivery-summary",
        )

    async def get_delivery_events(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/advisory/proposals/{proposal_id}/delivery-events",
            params={},
            headers=self._headers(correlation_id),
            operation="advise.advisory.proposals.delivery-events",
        )

    async def create_proposal_memo(
        self,
        proposal_id: str,
        version_no: int,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/proposals/{proposal_id}/versions/{version_no}/memo",
            body=body,
            headers=self._headers(correlation_id, {"Idempotency-Key": idempotency_key}),
            operation="advise.advisory.proposals.memo.create",
        )

    async def get_proposal_memo(
        self,
        proposal_id: str,
        version_no: int,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/advisory/proposals/{proposal_id}/versions/{version_no}/memo",
            params={},
            headers=self._headers(correlation_id),
            operation="advise.advisory.proposals.memo.get",
        )

    async def get_proposal_memo_projection(
        self,
        proposal_id: str,
        version_no: int,
        audience: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        params: dict[str, Any] = {}
        if audience:
            params["audience"] = audience
        return await self._get(
            f"/advisory/proposals/{proposal_id}/versions/{version_no}/memo/projection",
            params=params,
            headers=self._headers(correlation_id),
            operation="advise.advisory.proposals.memo.projection",
        )

    async def review_proposal_memo(
        self,
        proposal_id: str,
        version_no: int,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        headers = self._headers(correlation_id)
        if idempotency_key is not None:
            headers["Idempotency-Key"] = idempotency_key
        return await self._post(
            f"/advisory/proposals/{proposal_id}/versions/{version_no}/memo/review",
            body=body,
            headers=headers,
            operation="advise.advisory.proposals.memo.review",
        )

    async def request_proposal_memo_report_package(
        self,
        proposal_id: str,
        version_no: int,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        headers = self._headers(correlation_id)
        if idempotency_key is not None:
            headers["Idempotency-Key"] = idempotency_key
        return await self._post(
            f"/advisory/proposals/{proposal_id}/versions/{version_no}/memo/report-packages",
            body=body,
            headers=headers,
            operation="advise.advisory.proposals.memo.report-packages",
        )

    async def request_proposal_memo_ai_commentary(
        self,
        proposal_id: str,
        version_no: int,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        headers = self._headers(correlation_id)
        if idempotency_key is not None:
            headers["Idempotency-Key"] = idempotency_key
        return await self._post(
            f"/advisory/proposals/{proposal_id}/versions/{version_no}/memo/ai-commentary",
            body=body,
            headers=headers,
            operation="advise.advisory.proposals.memo.ai-commentary",
        )

    async def get_proposal_memo_lineage(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/advisory/proposals/{proposal_id}/memos/lineage",
            params={},
            headers=self._headers(correlation_id),
            operation="advise.advisory.proposals.memo.lineage",
        )

    async def get_proposal_memo_replay_evidence(
        self,
        proposal_id: str,
        version_no: int,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/advisory/proposals/{proposal_id}/versions/{version_no}/memo/replay-evidence",
            params={},
            headers=self._headers(correlation_id),
            operation="advise.advisory.proposals.memo.replay-evidence",
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
        return await request_observed_fanout(
            logger=logger,
            service="lotus-advise",
            operation=operation,
            method="POST",
            url=f"{self._base_url}{path}",
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
