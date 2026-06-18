from __future__ import annotations

import logging
from typing import Any

from app.clients.advise_advisory_copilot_client import AdviseAdvisoryCopilotClientMixin
from app.clients.advise_bank_demo_proof_client import AdviseBankDemoProofClientMixin
from app.clients.advise_policy_client import AdvisePolicyClientMixin
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

    async def create_proposal_artifact(
        self,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            "/advisory/proposals/artifact",
            body=body,
            headers=self._headers(correlation_id, {"Idempotency-Key": idempotency_key}),
            operation="advise.advisory.proposals.artifact",
        )

    async def list_advisor_cockpit_actions(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            "/advisory/cockpit/actions",
            params=self._clean_params(params),
            headers=self._headers(correlation_id),
            operation="advise.advisory.cockpit.actions.list",
        )

    async def list_advisor_cockpit_preparation_packets(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            "/advisory/cockpit/preparation-packets",
            params=self._clean_params(params),
            headers=self._headers(correlation_id),
            operation="advise.advisory.cockpit.preparation-packets.list",
        )

    async def get_advisor_cockpit_action(
        self,
        action_item_id: str,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/advisory/cockpit/actions/{action_item_id}",
            params=self._clean_params(params),
            headers=self._headers(correlation_id),
            operation="advise.advisory.cockpit.actions.get",
        )

    async def get_advisor_cockpit_snapshot(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            "/advisory/cockpit/snapshot",
            params=self._clean_params(params),
            headers=self._headers(correlation_id),
            operation="advise.advisory.cockpit.snapshot",
        )

    async def get_advisor_cockpit_supportability(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            "/advisory/cockpit/supportability",
            params=self._clean_params(params),
            headers=self._headers(correlation_id),
            operation="advise.advisory.cockpit.supportability",
        )

    async def acknowledge_advisor_cockpit_action(
        self,
        action_item_id: str,
        body: dict[str, Any],
        params: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/cockpit/actions/{action_item_id}/acknowledgements",
            body=body,
            headers=self._headers(correlation_id, {"Idempotency-Key": idempotency_key}),
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

    async def create_proposal_async(
        self,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            "/advisory/proposals/async",
            body=body,
            headers=self._headers(correlation_id, {"Idempotency-Key": idempotency_key}),
            operation="advise.advisory.proposals.async.create",
        )

    async def create_proposal_version_async(
        self,
        proposal_id: str,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/proposals/{proposal_id}/versions/async",
            body=body,
            headers=self._headers(correlation_id, {"Idempotency-Key": idempotency_key}),
            operation="advise.advisory.proposals.versions.async.create",
        )

    async def get_proposal_operation(
        self,
        operation_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/advisory/proposals/operations/{operation_id}",
            params={},
            headers=self._headers(correlation_id),
            operation="advise.advisory.proposals.operations.get",
        )

    async def get_proposal_operation_by_correlation(
        self,
        operation_correlation_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/advisory/proposals/operations/by-correlation/{operation_correlation_id}",
            params={},
            headers=self._headers(correlation_id),
            operation="advise.advisory.proposals.operations.by-correlation",
        )

    async def get_proposal_operation_replay_evidence(
        self,
        operation_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/advisory/proposals/operations/{operation_id}/replay-evidence",
            params={},
            headers=self._headers(correlation_id),
            operation="advise.advisory.proposals.operations.replay-evidence",
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

    async def get_proposal_version_replay_evidence(
        self,
        proposal_id: str,
        version_no: int,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/advisory/proposals/{proposal_id}/versions/{version_no}/replay-evidence",
            params={},
            headers=self._headers(correlation_id),
            operation="advise.advisory.proposals.versions.replay-evidence",
        )

    async def get_proposal_idempotency_record(
        self,
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/advisory/proposals/idempotency/{idempotency_key}",
            params={},
            headers=self._headers(correlation_id),
            operation="advise.advisory.proposals.idempotency.get",
        )

    async def regenerate_proposal_narrative(
        self,
        proposal_id: str,
        version_no: int,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/proposals/{proposal_id}/versions/{version_no}/narrative/regenerate",
            body=body,
            headers=self._headers(correlation_id),
            operation="advise.advisory.proposals.narrative.regenerate",
        )

    async def get_proposal_narrative(
        self,
        proposal_id: str,
        version_no: int,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/advisory/proposals/{proposal_id}/versions/{version_no}/narrative",
            params={},
            headers=self._headers(correlation_id),
            operation="advise.advisory.proposals.narrative.get",
        )

    async def review_proposal_narrative(
        self,
        proposal_id: str,
        version_no: int,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/proposals/{proposal_id}/versions/{version_no}/narrative/review",
            body=body,
            headers=self._optional_idempotency_headers(correlation_id, idempotency_key),
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

    async def create_execution_handoff(
        self,
        proposal_id: str,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/proposals/{proposal_id}/execution-handoffs",
            body=body,
            headers=self._optional_idempotency_headers(correlation_id, idempotency_key),
            operation="advise.advisory.proposals.execution-handoffs.create",
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

    async def get_execution_status(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/advisory/proposals/{proposal_id}/execution-status",
            params={},
            headers=self._headers(correlation_id),
            operation="advise.advisory.proposals.execution-status",
        )

    async def record_execution_update(
        self,
        proposal_id: str,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/proposals/{proposal_id}/execution-updates",
            body=body,
            headers=self._optional_idempotency_headers(correlation_id, idempotency_key),
            operation="advise.advisory.proposals.execution-updates.record",
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
            headers=build_idempotent_upstream_headers(correlation_id, idempotency_key),
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
        return await self._post(
            f"/advisory/proposals/{proposal_id}/versions/{version_no}/memo/review",
            body=body,
            headers=self._optional_idempotency_headers(correlation_id, idempotency_key),
            operation="advise.advisory.proposals.memo.review",
        )

    async def record_proposal_memo_report_package_event(
        self,
        proposal_id: str,
        version_no: int,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/proposals/{proposal_id}/versions/{version_no}/memo/report-package-events",
            body=body,
            headers=self._optional_idempotency_headers(correlation_id, idempotency_key),
            operation="advise.advisory.proposals.memo.report-package-events",
        )

    async def request_proposal_memo_report_package(
        self,
        proposal_id: str,
        version_no: int,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/proposals/{proposal_id}/versions/{version_no}/memo/report-packages",
            body=body,
            headers=self._optional_idempotency_headers(correlation_id, idempotency_key),
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
        return await self._post(
            f"/advisory/proposals/{proposal_id}/versions/{version_no}/memo/ai-commentary",
            body=body,
            headers=self._optional_idempotency_headers(correlation_id, idempotency_key),
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
