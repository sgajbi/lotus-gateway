from __future__ import annotations

from typing import Any

from app.clients.advise_policy_authority import (
    build_policy_control_headers,
    evidence_portfolio_id,
)
from app.clients.advise_policy_pack_client import AdvisePolicyPackClientMixin
from app.services.advisory_policy_access_policy import AdvisoryPolicyCallerContext


class AdvisePolicyClientMixin(AdvisePolicyPackClientMixin):
    async def create_policy_evaluation(
        self,
        proposal_id: str,
        proposal_version_id: str,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
        caller: AdvisoryPolicyCallerContext,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/proposals/{proposal_id}/versions/{proposal_version_id}/policy-evaluations",
            body=body,
            headers=build_policy_control_headers(
                self._headers,
                correlation_id,
                caller=caller,
                idempotency_key=idempotency_key,
                authorized_proposal_id=proposal_id,
                authorized_portfolio_id=evidence_portfolio_id(body),
            ),
            operation="advise.advisory.policy-evaluations.create",
        )

    async def get_policy_review_queue(
        self,
        evaluation_status: str | None,
        portfolio_id: str | None,
        correlation_id: str,
        caller: AdvisoryPolicyCallerContext,
    ) -> tuple[int, dict[str, Any]]:
        params: dict[str, Any] = {}
        if evaluation_status is not None:
            params["evaluation_status"] = evaluation_status
        if portfolio_id is not None:
            params["portfolio_id"] = portfolio_id
        return await self._get(
            "/advisory/policy-evaluations/review-queue",
            params=params,
            headers=build_policy_control_headers(self._headers, correlation_id, caller=caller),
            operation="advise.advisory.policy-evaluations.review-queue",
        )

    async def get_policy_evaluation(
        self,
        evaluation_id: str,
        correlation_id: str,
        caller: AdvisoryPolicyCallerContext,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get_tenant_policy_evaluation_read(
            f"/advisory/policy-evaluations/{evaluation_id}",
            "advise.advisory.policy-evaluations.get",
            correlation_id,
            caller,
        )

    async def replay_policy_evaluation(
        self,
        evaluation_id: str,
        body: dict[str, Any],
        correlation_id: str,
        caller: AdvisoryPolicyCallerContext,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/policy-evaluations/{evaluation_id}/replay",
            body=body,
            headers=build_policy_control_headers(self._headers, correlation_id, caller=caller),
            operation="advise.advisory.policy-evaluations.replay",
        )

    async def record_policy_evaluation_event(
        self,
        evaluation_id: str,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
        caller: AdvisoryPolicyCallerContext,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post_policy_evaluation_action(
            evaluation_id=evaluation_id,
            path=f"/advisory/policy-evaluations/{evaluation_id}/events",
            operation="advise.advisory.policy-evaluations.events",
            correlation_id=correlation_id,
            body=body,
            idempotency_key=idempotency_key,
            caller=caller,
        )

    async def get_policy_evaluation_lineage(
        self,
        evaluation_id: str,
        correlation_id: str,
        caller: AdvisoryPolicyCallerContext,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get_tenant_policy_evaluation_read(
            f"/advisory/policy-evaluations/{evaluation_id}/lineage",
            "advise.advisory.policy-evaluations.lineage",
            correlation_id,
            caller,
        )

    async def get_policy_sign_off_package(
        self,
        evaluation_id: str,
        correlation_id: str,
        caller: AdvisoryPolicyCallerContext,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get_tenant_policy_evaluation_read(
            f"/advisory/policy-evaluations/{evaluation_id}/sign-off-package",
            "advise.advisory.policy-evaluations.sign-off-package",
            correlation_id,
            caller,
        )

    async def get_policy_evaluation_workflow(
        self,
        evaluation_id: str,
        correlation_id: str,
        caller: AdvisoryPolicyCallerContext,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get_tenant_policy_evaluation_read(
            f"/advisory/policy-evaluations/{evaluation_id}/workflow",
            "advise.advisory.policy-evaluations.workflow",
            correlation_id,
            caller,
        )

    async def record_policy_sign_off_decision(
        self,
        evaluation_id: str,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
        caller: AdvisoryPolicyCallerContext,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post_policy_evaluation_action(
            evaluation_id=evaluation_id,
            path=f"/advisory/policy-evaluations/{evaluation_id}/sign-off-decisions",
            operation="advise.advisory.policy-evaluations.sign-off-decisions",
            correlation_id=correlation_id,
            body=body,
            idempotency_key=idempotency_key,
            caller=caller,
        )

    async def request_policy_report_package(
        self,
        evaluation_id: str,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
        caller: AdvisoryPolicyCallerContext,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post_policy_evaluation_action(
            evaluation_id=evaluation_id,
            path=f"/advisory/policy-evaluations/{evaluation_id}/report-packages",
            operation="advise.advisory.policy-evaluations.report-packages",
            correlation_id=correlation_id,
            body=body,
            idempotency_key=idempotency_key,
            caller=caller,
        )

    async def request_policy_ai_evidence(
        self,
        evaluation_id: str,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
        caller: AdvisoryPolicyCallerContext,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post_policy_evaluation_action(
            evaluation_id=evaluation_id,
            path=f"/advisory/policy-evaluations/{evaluation_id}/ai-evidence",
            operation="advise.advisory.policy-evaluations.ai-evidence",
            correlation_id=correlation_id,
            body=body,
            idempotency_key=idempotency_key,
            caller=caller,
        )

    async def _post_policy_evaluation_action(
        self,
        *,
        evaluation_id: str,
        path: str,
        operation: str,
        correlation_id: str,
        body: dict[str, Any],
        idempotency_key: str | None,
        caller: AdvisoryPolicyCallerContext,
    ) -> tuple[int, dict[str, Any]]:
        # Advise owns the durable tenant/evaluation scope assertion at each action
        # endpoint. Do not issue a generic evaluation read here: action-only callers
        # (notably POLICY_STEWARD review events) are not generic readers, and Gateway
        # must neither mint nor infer that additional authority.
        headers = build_policy_control_headers(
            self._headers,
            correlation_id=correlation_id,
            caller=caller,
            idempotency_key=idempotency_key,
        )
        return await self._post(path, body=body, headers=headers, operation=operation)

    async def _get_tenant_policy_evaluation_read(
        self,
        path: str,
        operation: str,
        correlation_id: str,
        caller: AdvisoryPolicyCallerContext,
    ) -> tuple[int, dict[str, Any]]:
        """Forward one admitted tenant read with the producer-owned read capability."""
        return await self._get(
            path,
            params={},
            headers=build_policy_control_headers(self._headers, correlation_id, caller=caller),
            operation=operation,
        )
