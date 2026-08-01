from __future__ import annotations

from typing import Any

from app.clients.advise_policy_authority import (
    ADVISOR_ROLE,
    COMPLIANCE_REVIEWER_ROLE,
    POLICY_CHECKER_ROLE,
    POLICY_EVALUATION_AI_EVIDENCE_CAPABILITY,
    POLICY_EVALUATION_FINALIZE_CAPABILITY,
    POLICY_EVALUATION_REPORT_PACKAGE_CAPABILITY,
    POLICY_EVALUATION_REVIEW_EVENT_CAPABILITY,
    POLICY_EVALUATION_SIGN_OFF_CAPABILITY,
    body_actor,
    build_policy_control_headers,
    build_policy_evaluation_control_headers,
    evidence_portfolio_id,
)
from app.clients.advise_policy_pack_client import AdvisePolicyPackClientMixin


class AdvisePolicyClientMixin(AdvisePolicyPackClientMixin):
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
            headers=build_policy_control_headers(
                self._headers,
                correlation_id,
                actor_id=body_actor(body, "created_by", fallback="advisor_1"),
                role=ADVISOR_ROLE,
                capability=POLICY_EVALUATION_FINALIZE_CAPABILITY,
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
        return await self._post_policy_evaluation_action(
            evaluation_id=evaluation_id,
            path=f"/advisory/policy-evaluations/{evaluation_id}/events",
            operation="advise.advisory.policy-evaluations.events",
            correlation_id=correlation_id,
            body=body,
            idempotency_key=idempotency_key,
            actor_key="actor_id",
            actor_fallback="compliance_1",
            role=COMPLIANCE_REVIEWER_ROLE,
            capability=POLICY_EVALUATION_REVIEW_EVENT_CAPABILITY,
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
        return await self._post_policy_evaluation_action(
            evaluation_id=evaluation_id,
            path=f"/advisory/policy-evaluations/{evaluation_id}/sign-off-decisions",
            operation="advise.advisory.policy-evaluations.sign-off-decisions",
            correlation_id=correlation_id,
            body=body,
            idempotency_key=idempotency_key,
            actor_key="decided_by",
            actor_fallback="policy_checker_1",
            role=POLICY_CHECKER_ROLE,
            capability=POLICY_EVALUATION_SIGN_OFF_CAPABILITY,
        )

    async def request_policy_report_package(
        self,
        evaluation_id: str,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post_policy_evaluation_action(
            evaluation_id=evaluation_id,
            path=f"/advisory/policy-evaluations/{evaluation_id}/report-packages",
            operation="advise.advisory.policy-evaluations.report-packages",
            correlation_id=correlation_id,
            body=body,
            idempotency_key=idempotency_key,
            actor_key="requested_by",
            actor_fallback="policy_checker_1",
            role=POLICY_CHECKER_ROLE,
            capability=POLICY_EVALUATION_REPORT_PACKAGE_CAPABILITY,
        )

    async def request_policy_ai_evidence(
        self,
        evaluation_id: str,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post_policy_evaluation_action(
            evaluation_id=evaluation_id,
            path=f"/advisory/policy-evaluations/{evaluation_id}/ai-evidence",
            operation="advise.advisory.policy-evaluations.ai-evidence",
            correlation_id=correlation_id,
            body=body,
            idempotency_key=idempotency_key,
            actor_key="requested_by",
            actor_fallback="compliance_1",
            role=COMPLIANCE_REVIEWER_ROLE,
            capability=POLICY_EVALUATION_AI_EVIDENCE_CAPABILITY,
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
        actor_key: str,
        actor_fallback: str,
        role: str,
        capability: str,
    ) -> tuple[int, dict[str, Any]]:
        headers = await build_policy_evaluation_control_headers(
            read_policy_evaluation=self.get_policy_evaluation,
            headers_factory=self._headers,
            evaluation_id=evaluation_id,
            correlation_id=correlation_id,
            actor_id=body_actor(body, actor_key, fallback=actor_fallback),
            role=role,
            capability=capability,
            idempotency_key=idempotency_key,
        )
        if isinstance(headers, tuple):
            return headers
        return await self._post(path, body=body, headers=headers, operation=operation)

    def _headers(
        self,
        correlation_id: str,
        extras: dict[str, str] | None = None,
    ) -> dict[str, str]:
        raise NotImplementedError

    def _optional_idempotency_headers(
        self,
        correlation_id: str,
        idempotency_key: str | None,
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
