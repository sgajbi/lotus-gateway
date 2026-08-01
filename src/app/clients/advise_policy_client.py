from __future__ import annotations

from typing import Any

_POLICY_CONTROL_SERVICE_IDENTITY = "lotus-gateway"
_POLICY_CONTROL_TENANT_ID = "tenant_sg_001"
_POLICY_CONTROL_LEGAL_ENTITY_CODE = "REFERENCE"
_POLICY_STEWARD_ROLE = "POLICY_STEWARD"
_POLICY_CHECKER_ROLE = "POLICY_CHECKER"
_ADVISOR_ROLE = "ADVISOR"
_COMPLIANCE_REVIEWER_ROLE = "COMPLIANCE_REVIEWER"
_POLICY_PACK_VALIDATE_CAPABILITY = "advisory.policy_pack.validate"
_POLICY_PACK_ACTIVATE_CAPABILITY = "advisory.policy_pack.activate"
_POLICY_EVALUATION_FINALIZE_CAPABILITY = "advisory.policy_evaluation.finalize"
_POLICY_EVALUATION_REVIEW_EVENT_CAPABILITY = "advisory.policy_evaluation.review_event"
_POLICY_EVALUATION_SIGN_OFF_CAPABILITY = "advisory.policy_evaluation.sign_off"
_POLICY_EVALUATION_REPORT_PACKAGE_CAPABILITY = "advisory.policy_evaluation.report_package"
_POLICY_EVALUATION_AI_EVIDENCE_CAPABILITY = "advisory.policy_evaluation.ai_evidence"


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
            headers=self._policy_control_headers(
                correlation_id,
                actor_id=_body_actor(body, "requested_by", fallback="policy_steward_1"),
                role=_POLICY_STEWARD_ROLE,
                capability=_POLICY_PACK_VALIDATE_CAPABILITY,
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
            headers=self._policy_control_headers(
                correlation_id,
                actor_id=_body_actor(body, "activated_by", fallback="policy_checker_1"),
                role=_POLICY_CHECKER_ROLE,
                capability=_POLICY_PACK_ACTIVATE_CAPABILITY,
                idempotency_key=idempotency_key,
            ),
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
            headers=self._policy_control_headers(
                correlation_id,
                actor_id=_body_actor(body, "created_by", fallback="advisor_1"),
                role=_ADVISOR_ROLE,
                capability=_POLICY_EVALUATION_FINALIZE_CAPABILITY,
                idempotency_key=idempotency_key,
                authorized_proposal_id=proposal_id,
                authorized_portfolio_id=_evidence_portfolio_id(body),
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
        headers = await self._policy_evaluation_control_headers(
            evaluation_id=evaluation_id,
            correlation_id=correlation_id,
            actor_id=_body_actor(body, "actor_id", fallback="compliance_1"),
            role=_COMPLIANCE_REVIEWER_ROLE,
            capability=_POLICY_EVALUATION_REVIEW_EVENT_CAPABILITY,
            idempotency_key=idempotency_key,
        )
        if isinstance(headers, tuple):
            return headers
        return await self._post(
            f"/advisory/policy-evaluations/{evaluation_id}/events",
            body=body,
            headers=headers,
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
        headers = await self._policy_evaluation_control_headers(
            evaluation_id=evaluation_id,
            correlation_id=correlation_id,
            actor_id=_body_actor(body, "decided_by", fallback="policy_checker_1"),
            role=_POLICY_CHECKER_ROLE,
            capability=_POLICY_EVALUATION_SIGN_OFF_CAPABILITY,
            idempotency_key=idempotency_key,
        )
        if isinstance(headers, tuple):
            return headers
        return await self._post(
            f"/advisory/policy-evaluations/{evaluation_id}/sign-off-decisions",
            body=body,
            headers=headers,
            operation="advise.advisory.policy-evaluations.sign-off-decisions",
        )

    async def request_policy_report_package(
        self,
        evaluation_id: str,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        headers = await self._policy_evaluation_control_headers(
            evaluation_id=evaluation_id,
            correlation_id=correlation_id,
            actor_id=_body_actor(body, "requested_by", fallback="policy_checker_1"),
            role=_POLICY_CHECKER_ROLE,
            capability=_POLICY_EVALUATION_REPORT_PACKAGE_CAPABILITY,
            idempotency_key=idempotency_key,
        )
        if isinstance(headers, tuple):
            return headers
        return await self._post(
            f"/advisory/policy-evaluations/{evaluation_id}/report-packages",
            body=body,
            headers=headers,
            operation="advise.advisory.policy-evaluations.report-packages",
        )

    async def request_policy_ai_evidence(
        self,
        evaluation_id: str,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        headers = await self._policy_evaluation_control_headers(
            evaluation_id=evaluation_id,
            correlation_id=correlation_id,
            actor_id=_body_actor(body, "requested_by", fallback="compliance_1"),
            role=_COMPLIANCE_REVIEWER_ROLE,
            capability=_POLICY_EVALUATION_AI_EVIDENCE_CAPABILITY,
            idempotency_key=idempotency_key,
        )
        if isinstance(headers, tuple):
            return headers
        return await self._post(
            f"/advisory/policy-evaluations/{evaluation_id}/ai-evidence",
            body=body,
            headers=headers,
            operation="advise.advisory.policy-evaluations.ai-evidence",
        )

    async def _policy_evaluation_control_headers(
        self,
        *,
        evaluation_id: str,
        correlation_id: str,
        actor_id: str,
        role: str,
        capability: str,
        idempotency_key: str | None,
    ) -> dict[str, str] | tuple[int, dict[str, Any]]:
        status_code, record = await self.get_policy_evaluation(
            evaluation_id=evaluation_id,
            correlation_id=correlation_id,
        )
        if status_code >= 400:
            return status_code, record
        return self._policy_control_headers(
            correlation_id,
            actor_id=actor_id,
            role=role,
            capability=capability,
            idempotency_key=idempotency_key,
            authorized_proposal_id=_record_value(record, "proposal_id"),
            authorized_portfolio_id=_record_value(record, "portfolio_id"),
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

    def _policy_control_headers(
        self,
        correlation_id: str,
        *,
        actor_id: str,
        role: str,
        capability: str,
        idempotency_key: str | None = None,
        authorized_proposal_id: str | None = None,
        authorized_portfolio_id: str | None = None,
    ) -> dict[str, str]:
        extras = {
            "X-Actor-Id": actor_id,
            "X-Role": role,
            "X-Tenant-Id": _POLICY_CONTROL_TENANT_ID,
            "X-Legal-Entity-Code": _POLICY_CONTROL_LEGAL_ENTITY_CODE,
            "X-Service-Identity": _POLICY_CONTROL_SERVICE_IDENTITY,
            "X-Capabilities": capability,
        }
        if idempotency_key is not None:
            extras["Idempotency-Key"] = idempotency_key
        if authorized_proposal_id is not None:
            extras["X-Authorized-Proposal-Id"] = authorized_proposal_id
        if authorized_portfolio_id is not None:
            extras["X-Authorized-Portfolio-Id"] = authorized_portfolio_id
        return self._headers(correlation_id, extras)

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


def _body_actor(body: dict[str, Any], key: str, *, fallback: str) -> str:
    actor = str(body.get(key) or "").strip()
    return actor or fallback


def _evidence_portfolio_id(body: dict[str, Any]) -> str | None:
    evidence_bundle = body.get("evidence_bundle")
    if not isinstance(evidence_bundle, dict):
        return None
    inputs = evidence_bundle.get("inputs")
    if not isinstance(inputs, dict):
        return None
    portfolio_snapshot = inputs.get("portfolio_snapshot")
    if not isinstance(portfolio_snapshot, dict):
        return None
    portfolio_id = str(portfolio_snapshot.get("portfolio_id") or "").strip()
    return portfolio_id or None


def _record_value(record: dict[str, Any], key: str) -> str | None:
    value = str(record.get(key) or "").strip()
    return value or None
