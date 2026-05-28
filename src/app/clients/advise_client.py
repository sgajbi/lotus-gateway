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

    async def get_bank_demo_proof_scenario_contract(
        self,
        *,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            "/advisory/bank-demo-proof/scenario-contract",
            params={},
            headers=self._headers(correlation_id),
            operation="advise.advisory.bank-demo-proof.scenario-contract",
        )

    async def get_bank_demo_supported_claim_register(
        self,
        *,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            "/advisory/bank-demo-proof/supported-claim-register",
            params={},
            headers=self._headers(correlation_id),
            operation="advise.advisory.bank-demo-proof.supported-claim-register",
        )

    async def build_bank_demo_proof_pack(
        self,
        *,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            "/advisory/bank-demo-proof/proof-packs",
            body=body,
            headers=self._headers(correlation_id),
            operation="advise.advisory.bank-demo-proof.proof-packs",
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

    async def list_advisory_workspace_saved_versions(
        self,
        workspace_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/advisory/workspaces/{workspace_id}/saved-versions",
            params={},
            headers=self._headers(correlation_id),
            operation="advise.advisory.workspaces.saved-versions.list",
        )

    async def get_advisory_workspace_saved_version_replay_evidence(
        self,
        workspace_id: str,
        workspace_version_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/advisory/workspaces/{workspace_id}/saved-versions/"
            f"{workspace_version_id}/replay-evidence",
            params={},
            headers=self._headers(correlation_id),
            operation="advise.advisory.workspaces.saved-versions.replay-evidence",
        )

    async def resume_advisory_workspace(
        self,
        workspace_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/workspaces/{workspace_id}/resume",
            body=body,
            headers=self._headers(correlation_id),
            operation="advise.advisory.workspaces.resume",
        )

    async def compare_advisory_workspace(
        self,
        workspace_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/workspaces/{workspace_id}/compare",
            body=body,
            headers=self._headers(correlation_id),
            operation="advise.advisory.workspaces.compare",
        )

    async def request_advisory_workspace_rationale(
        self,
        workspace_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/workspaces/{workspace_id}/assistant/rationale",
            body=body,
            headers=self._headers(correlation_id),
            operation="advise.advisory.workspaces.assistant.rationale",
        )

    async def review_advisory_workspace_rationale(
        self,
        workspace_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/workspaces/{workspace_id}/assistant/rationale/review-actions",
            body=body,
            headers=self._headers(correlation_id),
            operation="advise.advisory.workspaces.assistant.rationale.review-actions",
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
            headers=self._headers(correlation_id, {"Idempotency-Key": idempotency_key}),
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
            headers=self._headers(correlation_id, {"Idempotency-Key": idempotency_key}),
            operation="advise.advisory.policy-packs.activate",
        )

    async def create_policy_evaluation(
        self,
        proposal_id: str,
        proposal_version_id: str,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/proposals/{proposal_id}/versions/{proposal_version_id}/policy-evaluations",
            body=body,
            headers=self._headers(correlation_id, {"Idempotency-Key": idempotency_key}),
            operation="advise.advisory.policy-evaluations.create",
        )

    async def get_policy_review_queue(
        self,
        evaluation_status: str | None,
        portfolio_id: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        params: dict[str, Any] = {}
        if evaluation_status is not None:
            params["evaluation_status"] = evaluation_status
        if portfolio_id is not None:
            params["portfolio_id"] = portfolio_id
        return await self._get(
            "/advisory/policy-evaluations/review-queue",
            params=params,
            headers=self._headers(correlation_id),
            operation="advise.advisory.policy-evaluations.review-queue",
        )

    async def get_policy_evaluation(
        self,
        evaluation_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/advisory/policy-evaluations/{evaluation_id}",
            params={},
            headers=self._headers(correlation_id),
            operation="advise.advisory.policy-evaluations.get",
        )

    async def replay_policy_evaluation(
        self,
        evaluation_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/policy-evaluations/{evaluation_id}/replay",
            body=body,
            headers=self._headers(correlation_id),
            operation="advise.advisory.policy-evaluations.replay",
        )

    async def record_policy_evaluation_event(
        self,
        evaluation_id: str,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/policy-evaluations/{evaluation_id}/events",
            body=body,
            headers=self._optional_idempotency_headers(correlation_id, idempotency_key),
            operation="advise.advisory.policy-evaluations.events",
        )

    async def get_policy_evaluation_lineage(
        self,
        evaluation_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/advisory/policy-evaluations/{evaluation_id}/lineage",
            params={},
            headers=self._headers(correlation_id),
            operation="advise.advisory.policy-evaluations.lineage",
        )

    async def get_policy_sign_off_package(
        self,
        evaluation_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/advisory/policy-evaluations/{evaluation_id}/sign-off-package",
            params={},
            headers=self._headers(correlation_id),
            operation="advise.advisory.policy-evaluations.sign-off-package",
        )

    async def get_policy_evaluation_workflow(
        self,
        evaluation_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/advisory/policy-evaluations/{evaluation_id}/workflow",
            params={},
            headers=self._headers(correlation_id),
            operation="advise.advisory.policy-evaluations.workflow",
        )

    async def record_policy_sign_off_decision(
        self,
        evaluation_id: str,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/policy-evaluations/{evaluation_id}/sign-off-decisions",
            body=body,
            headers=self._optional_idempotency_headers(correlation_id, idempotency_key),
            operation="advise.advisory.policy-evaluations.sign-off-decisions",
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

    async def request_policy_report_package(
        self,
        evaluation_id: str,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/policy-evaluations/{evaluation_id}/report-packages",
            body=body,
            headers=self._optional_idempotency_headers(correlation_id, idempotency_key),
            operation="advise.advisory.policy-evaluations.report-packages",
        )

    async def request_policy_ai_evidence(
        self,
        evaluation_id: str,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/policy-evaluations/{evaluation_id}/ai-evidence",
            body=body,
            headers=self._optional_idempotency_headers(correlation_id, idempotency_key),
            operation="advise.advisory.policy-evaluations.ai-evidence",
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

    async def create_execution_handoff(
        self,
        proposal_id: str,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        headers = self._headers(correlation_id)
        if idempotency_key is not None:
            headers["Idempotency-Key"] = idempotency_key
        return await self._post(
            f"/advisory/proposals/{proposal_id}/execution-handoffs",
            body=body,
            headers=headers,
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
        headers = self._headers(correlation_id)
        if idempotency_key is not None:
            headers["Idempotency-Key"] = idempotency_key
        return await self._post(
            f"/advisory/proposals/{proposal_id}/execution-updates",
            body=body,
            headers=headers,
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

    async def record_proposal_memo_report_package_event(
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
            f"/advisory/proposals/{proposal_id}/versions/{version_no}/memo/report-package-events",
            body=body,
            headers=headers,
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

    def _optional_idempotency_headers(
        self,
        correlation_id: str,
        idempotency_key: str | None,
    ) -> dict[str, str]:
        if idempotency_key is None:
            return self._headers(correlation_id)
        return self._headers(correlation_id, {"Idempotency-Key": idempotency_key})

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
