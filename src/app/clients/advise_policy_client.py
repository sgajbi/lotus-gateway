from __future__ import annotations

from typing import Any


class AdvisePolicyClientMixin:
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
