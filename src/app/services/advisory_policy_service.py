from typing import Any

from fastapi import HTTPException, status

from app.clients.advise_client import AdviseClient
from app.config import settings
from app.contracts.advisory_policy import AdvisoryPolicyEnvelopeResponse


class AdvisoryPolicyService:
    def __init__(self, advise_client: AdviseClient):
        self._advise_client = advise_client

    async def list_policy_packs(self, correlation_id: str) -> AdvisoryPolicyEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.list_policy_packs(
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def get_policy_pack_version(
        self,
        *,
        policy_pack_id: str,
        policy_version: str,
        correlation_id: str,
    ) -> AdvisoryPolicyEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.get_policy_pack_version(
            policy_pack_id=policy_pack_id,
            policy_version=policy_version,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def validate_policy_pack_version(
        self,
        *,
        policy_pack_id: str,
        policy_version: str,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> AdvisoryPolicyEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.validate_policy_pack_version(
            policy_pack_id=policy_pack_id,
            policy_version=policy_version,
            body=body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def activate_policy_pack_version(
        self,
        *,
        policy_pack_id: str,
        policy_version: str,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> AdvisoryPolicyEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.activate_policy_pack_version(
            policy_pack_id=policy_pack_id,
            policy_version=policy_version,
            body=body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def create_policy_evaluation(
        self,
        *,
        proposal_id: str,
        proposal_version_id: str,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> AdvisoryPolicyEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.create_policy_evaluation(
            proposal_id=proposal_id,
            proposal_version_id=proposal_version_id,
            body=body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def get_policy_review_queue(
        self,
        *,
        evaluation_status: str | None,
        correlation_id: str,
    ) -> AdvisoryPolicyEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.get_policy_review_queue(
            evaluation_status=evaluation_status,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def get_policy_evaluation(
        self,
        *,
        evaluation_id: str,
        correlation_id: str,
    ) -> AdvisoryPolicyEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.get_policy_evaluation(
            evaluation_id=evaluation_id,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def replay_policy_evaluation(
        self,
        *,
        evaluation_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> AdvisoryPolicyEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.replay_policy_evaluation(
            evaluation_id=evaluation_id,
            body=body,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def record_policy_evaluation_event(
        self,
        *,
        evaluation_id: str,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> AdvisoryPolicyEnvelopeResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._advise_client.record_policy_evaluation_event(
            evaluation_id=evaluation_id,
            body=body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def get_policy_evaluation_lineage(
        self,
        *,
        evaluation_id: str,
        correlation_id: str,
    ) -> AdvisoryPolicyEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.get_policy_evaluation_lineage(
            evaluation_id=evaluation_id,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def get_policy_sign_off_package(
        self,
        *,
        evaluation_id: str,
        correlation_id: str,
    ) -> AdvisoryPolicyEnvelopeResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._advise_client.get_policy_sign_off_package(
            evaluation_id=evaluation_id,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def get_policy_evaluation_workflow(
        self,
        *,
        evaluation_id: str,
        correlation_id: str,
    ) -> AdvisoryPolicyEnvelopeResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._advise_client.get_policy_evaluation_workflow(
            evaluation_id=evaluation_id,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def record_policy_sign_off_decision(
        self,
        *,
        evaluation_id: str,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> AdvisoryPolicyEnvelopeResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._advise_client.record_policy_sign_off_decision(
            evaluation_id=evaluation_id,
            body=body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def request_policy_report_package(
        self,
        *,
        evaluation_id: str,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> AdvisoryPolicyEnvelopeResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._advise_client.request_policy_report_package(
            evaluation_id=evaluation_id,
            body=body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    async def request_policy_ai_evidence(
        self,
        *,
        evaluation_id: str,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> AdvisoryPolicyEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.request_policy_ai_evidence(
            evaluation_id=evaluation_id,
            body=body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._envelope(correlation_id, upstream_payload)

    def _envelope(
        self,
        correlation_id: str,
        upstream_payload: dict[str, Any],
    ) -> AdvisoryPolicyEnvelopeResponse:
        return AdvisoryPolicyEnvelopeResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            data=upstream_payload,
        )

    def _raise_for_upstream_error(
        self,
        upstream_status: int,
        upstream_payload: dict[str, Any],
    ) -> None:
        if upstream_status >= status.HTTP_400_BAD_REQUEST:
            detail: str | dict[str, Any] = upstream_payload
            if not isinstance(detail, str):
                detail = str(detail)
            raise HTTPException(status_code=upstream_status, detail=detail)
