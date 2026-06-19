from typing import Any

from app.contracts.proposals import (
    ProposalStateTransitionData,
    ProposalStateTransitionEnvelopeResponse,
)
from app.services.proposal_client_protocols import ProposalClient
from app.services.upstream_envelope import build_typed_gateway_envelope


class ProposalTransitionServiceMixin:
    _advise_client: ProposalClient

    def _raise_for_upstream_error(
        self,
        upstream_status: int,
        upstream_payload: dict[str, Any],
    ) -> None:
        raise NotImplementedError

    async def submit_proposal(
        self,
        proposal_id: str,
        actor_id: str,
        expected_state: str,
        review_type: str,
        reason: dict[str, Any],
        related_version_no: int | None,
        idempotency_key: str,
        correlation_id: str,
    ) -> ProposalStateTransitionEnvelopeResponse:
        event_type = (
            "SUBMITTED_FOR_COMPLIANCE_REVIEW"
            if review_type == "COMPLIANCE"
            else "SUBMITTED_FOR_RISK_REVIEW"
        )
        transition_body: dict[str, Any] = {
            "event_type": event_type,
            "actor_id": actor_id,
            "expected_state": expected_state,
            "reason": reason,
        }
        if related_version_no is not None:
            transition_body["related_version_no"] = related_version_no

        upstream_status, upstream_payload = await self._advise_client.transition_proposal(
            proposal_id=proposal_id,
            body=transition_body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return build_typed_gateway_envelope(
            ProposalStateTransitionEnvelopeResponse,
            ProposalStateTransitionData,
            correlation_id=correlation_id,
            upstream_payload=upstream_payload,
        )

    async def approve_risk(
        self,
        proposal_id: str,
        actor_id: str,
        expected_state: str,
        details: dict[str, Any],
        related_version_no: int | None,
        idempotency_key: str,
        correlation_id: str,
    ) -> ProposalStateTransitionEnvelopeResponse:
        return await self._record_approval(
            proposal_id=proposal_id,
            approval_type="RISK",
            actor_id=actor_id,
            expected_state=expected_state,
            details=details,
            related_version_no=related_version_no,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )

    async def approve_compliance(
        self,
        proposal_id: str,
        actor_id: str,
        expected_state: str,
        details: dict[str, Any],
        related_version_no: int | None,
        idempotency_key: str,
        correlation_id: str,
    ) -> ProposalStateTransitionEnvelopeResponse:
        return await self._record_approval(
            proposal_id=proposal_id,
            approval_type="COMPLIANCE",
            actor_id=actor_id,
            expected_state=expected_state,
            details=details,
            related_version_no=related_version_no,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )

    async def record_client_consent(
        self,
        proposal_id: str,
        actor_id: str,
        expected_state: str,
        details: dict[str, Any],
        related_version_no: int | None,
        idempotency_key: str,
        correlation_id: str,
    ) -> ProposalStateTransitionEnvelopeResponse:
        return await self._record_approval(
            proposal_id=proposal_id,
            approval_type="CLIENT_CONSENT",
            actor_id=actor_id,
            expected_state=expected_state,
            details=details,
            related_version_no=related_version_no,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )

    async def _record_approval(
        self,
        proposal_id: str,
        approval_type: str,
        actor_id: str,
        expected_state: str,
        details: dict[str, Any],
        related_version_no: int | None,
        idempotency_key: str,
        correlation_id: str,
    ) -> ProposalStateTransitionEnvelopeResponse:
        payload: dict[str, Any] = {
            "approval_type": approval_type,
            "approved": True,
            "actor_id": actor_id,
            "expected_state": expected_state,
            "details": details,
        }
        if related_version_no is not None:
            payload["related_version_no"] = related_version_no

        upstream_status, upstream_payload = await self._advise_client.record_approval(
            proposal_id=proposal_id,
            body=payload,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return build_typed_gateway_envelope(
            ProposalStateTransitionEnvelopeResponse,
            ProposalStateTransitionData,
            correlation_id=correlation_id,
            upstream_payload=upstream_payload,
        )
