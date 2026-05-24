from typing import Any

from fastapi import HTTPException, status

from app.clients.advise_client import AdviseClient
from app.config import settings
from app.contracts.proposals import (
    ProposalApprovalsData,
    ProposalApprovalsEnvelopeResponse,
    ProposalCreateData,
    ProposalCreateEnvelopeResponse,
    ProposalDeliveryEventsEnvelopeResponse,
    ProposalDeliverySummaryEnvelopeResponse,
    ProposalDetailData,
    ProposalDetailEnvelopeResponse,
    ProposalLineageData,
    ProposalLineageEnvelopeResponse,
    ProposalListData,
    ProposalListEnvelopeResponse,
    ProposalMemoAiCommentaryEnvelopeResponse,
    ProposalMemoEnvelopeResponse,
    ProposalMemoLineageEnvelopeResponse,
    ProposalMemoProjectionEnvelopeResponse,
    ProposalMemoReplayEvidenceEnvelopeResponse,
    ProposalMemoReportPackageEnvelopeResponse,
    ProposalMemoReviewEnvelopeResponse,
    ProposalNarrativeReviewEnvelopeResponse,
    ProposalReportRequestEnvelopeResponse,
    ProposalSimulateResponse,
    ProposalSimulationData,
    ProposalStateTransitionData,
    ProposalStateTransitionEnvelopeResponse,
    ProposalVersionData,
    ProposalVersionEnvelopeResponse,
    ProposalWorkflowEventsData,
    ProposalWorkflowEventsEnvelopeResponse,
)


def _normalize_proposal_context_payload(
    upstream_payload: dict[str, Any],
    *,
    proposal_id: str,
) -> dict[str, Any]:
    if upstream_payload.get("proposal_id"):
        return upstream_payload

    proposal = upstream_payload.get("proposal")
    if not isinstance(proposal, dict):
        return upstream_payload

    normalized = dict(upstream_payload)
    normalized["proposal_id"] = proposal.get("proposal_id") or proposal_id
    normalized["current_state"] = upstream_payload.get("current_state") or proposal.get(
        "current_state"
    )
    return normalized


class ProposalService:
    def __init__(self, advise_client: AdviseClient):
        self._advise_client = advise_client

    async def simulate_proposal(
        self,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> ProposalSimulateResponse:
        upstream_status, upstream_payload = await self._advise_client.simulate_proposal(
            body=body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )

        if upstream_status >= status.HTTP_400_BAD_REQUEST:
            detail: str | dict[str, Any] = upstream_payload
            if not isinstance(detail, str):
                detail = str(detail)
            raise HTTPException(status_code=upstream_status, detail=detail)

        return ProposalSimulateResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            data=ProposalSimulationData.model_validate(upstream_payload),
        )

    async def create_proposal(
        self,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> ProposalCreateEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.create_proposal(
            body=body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return ProposalCreateEnvelopeResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            data=ProposalCreateData.model_validate(upstream_payload),
        )

    async def list_proposals(
        self,
        filters: dict[str, Any],
        correlation_id: str,
    ) -> ProposalListEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.list_proposals(
            params=filters,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return ProposalListEnvelopeResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            data=ProposalListData.model_validate(upstream_payload),
        )

    async def get_proposal(
        self,
        proposal_id: str,
        include_evidence: bool,
        correlation_id: str,
    ) -> ProposalDetailEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.get_proposal(
            proposal_id=proposal_id,
            include_evidence=include_evidence,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return ProposalDetailEnvelopeResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            data=ProposalDetailData.model_validate(upstream_payload),
        )

    async def get_proposal_version(
        self,
        proposal_id: str,
        version_no: int,
        include_evidence: bool,
        correlation_id: str,
    ) -> ProposalVersionEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.get_proposal_version(
            proposal_id=proposal_id,
            version_no=version_no,
            include_evidence=include_evidence,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return ProposalVersionEnvelopeResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            data=ProposalVersionData.model_validate(upstream_payload),
        )

    async def create_proposal_version(
        self,
        proposal_id: str,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> ProposalCreateEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.create_proposal_version(
            proposal_id=proposal_id,
            body=body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return ProposalCreateEnvelopeResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            data=ProposalCreateData.model_validate(upstream_payload),
        )

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
        return ProposalStateTransitionEnvelopeResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            data=ProposalStateTransitionData.model_validate(upstream_payload),
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

    async def get_workflow_events(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> ProposalWorkflowEventsEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.get_workflow_events(
            proposal_id=proposal_id,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return ProposalWorkflowEventsEnvelopeResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            data=ProposalWorkflowEventsData.model_validate(
                _normalize_proposal_context_payload(
                    upstream_payload,
                    proposal_id=proposal_id,
                )
            ),
        )

    async def get_approvals(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> ProposalApprovalsEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.get_approvals(
            proposal_id=proposal_id,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return ProposalApprovalsEnvelopeResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            data=ProposalApprovalsData.model_validate(
                _normalize_proposal_context_payload(
                    upstream_payload,
                    proposal_id=proposal_id,
                )
            ),
        )

    async def get_proposal_lineage(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> ProposalLineageEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.get_proposal_lineage(
            proposal_id=proposal_id,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return ProposalLineageEnvelopeResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            data=ProposalLineageData.model_validate(upstream_payload),
        )

    async def review_proposal_narrative(
        self,
        proposal_id: str,
        version_no: int,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> ProposalNarrativeReviewEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.review_proposal_narrative(
            proposal_id=proposal_id,
            version_no=version_no,
            body=body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return ProposalNarrativeReviewEnvelopeResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            data=upstream_payload,
        )

    async def create_report_request(
        self,
        proposal_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> ProposalReportRequestEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.create_report_request(
            proposal_id=proposal_id,
            body=body,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return ProposalReportRequestEnvelopeResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            data=upstream_payload,
        )

    async def get_delivery_summary(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> ProposalDeliverySummaryEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.get_delivery_summary(
            proposal_id=proposal_id,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return ProposalDeliverySummaryEnvelopeResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            data=upstream_payload,
        )

    async def get_delivery_events(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> ProposalDeliveryEventsEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.get_delivery_events(
            proposal_id=proposal_id,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return ProposalDeliveryEventsEnvelopeResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            data=upstream_payload,
        )

    async def create_proposal_memo(
        self,
        proposal_id: str,
        version_no: int,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> ProposalMemoEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.create_proposal_memo(
            proposal_id=proposal_id,
            version_no=version_no,
            body=body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return ProposalMemoEnvelopeResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            data=upstream_payload,
        )

    async def get_proposal_memo(
        self,
        proposal_id: str,
        version_no: int,
        correlation_id: str,
    ) -> ProposalMemoEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.get_proposal_memo(
            proposal_id=proposal_id,
            version_no=version_no,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return ProposalMemoEnvelopeResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            data=upstream_payload,
        )

    async def get_proposal_memo_projection(
        self,
        proposal_id: str,
        version_no: int,
        audience: str | None,
        correlation_id: str,
    ) -> ProposalMemoProjectionEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.get_proposal_memo_projection(
            proposal_id=proposal_id,
            version_no=version_no,
            audience=audience,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return ProposalMemoProjectionEnvelopeResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            data=upstream_payload,
        )

    async def review_proposal_memo(
        self,
        proposal_id: str,
        version_no: int,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> ProposalMemoReviewEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.review_proposal_memo(
            proposal_id=proposal_id,
            version_no=version_no,
            body=body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return ProposalMemoReviewEnvelopeResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            data=upstream_payload,
        )

    async def request_proposal_memo_report_package(
        self,
        proposal_id: str,
        version_no: int,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> ProposalMemoReportPackageEnvelopeResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._advise_client.request_proposal_memo_report_package(
            proposal_id=proposal_id,
            version_no=version_no,
            body=body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return ProposalMemoReportPackageEnvelopeResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            data=upstream_payload,
        )

    async def request_proposal_memo_ai_commentary(
        self,
        proposal_id: str,
        version_no: int,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> ProposalMemoAiCommentaryEnvelopeResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._advise_client.request_proposal_memo_ai_commentary(
            proposal_id=proposal_id,
            version_no=version_no,
            body=body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return ProposalMemoAiCommentaryEnvelopeResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            data=upstream_payload,
        )

    async def get_proposal_memo_lineage(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> ProposalMemoLineageEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.get_proposal_memo_lineage(
            proposal_id=proposal_id,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return ProposalMemoLineageEnvelopeResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            data=upstream_payload,
        )

    async def get_proposal_memo_replay_evidence(
        self,
        proposal_id: str,
        version_no: int,
        correlation_id: str,
    ) -> ProposalMemoReplayEvidenceEnvelopeResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._advise_client.get_proposal_memo_replay_evidence(
            proposal_id=proposal_id,
            version_no=version_no,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return ProposalMemoReplayEvidenceEnvelopeResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            data=upstream_payload,
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
        return ProposalStateTransitionEnvelopeResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            data=ProposalStateTransitionData.model_validate(upstream_payload),
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
