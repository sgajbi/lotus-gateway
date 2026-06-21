from typing import Any

from app.contracts.proposals import (
    ProposalApprovalsData,
    ProposalApprovalsEnvelopeResponse,
    ProposalLineageData,
    ProposalLineageEnvelopeResponse,
    ProposalWorkflowEventsData,
    ProposalWorkflowEventsEnvelopeResponse,
)
from app.services.proposal_client_protocols import ProposalClient
from app.services.upstream_envelope import build_typed_gateway_envelope


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


class ProposalLifecycleQueryServiceMixin:
    _advise_client: ProposalClient

    def _raise_for_upstream_error(
        self,
        upstream_status: int,
        upstream_payload: dict[str, Any],
    ) -> None:
        raise NotImplementedError

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
        return build_typed_gateway_envelope(
            ProposalWorkflowEventsEnvelopeResponse,
            ProposalWorkflowEventsData,
            correlation_id=correlation_id,
            upstream_payload=_normalize_proposal_context_payload(
                upstream_payload,
                proposal_id=proposal_id,
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
        return build_typed_gateway_envelope(
            ProposalApprovalsEnvelopeResponse,
            ProposalApprovalsData,
            correlation_id=correlation_id,
            upstream_payload=_normalize_proposal_context_payload(
                upstream_payload,
                proposal_id=proposal_id,
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
        return build_typed_gateway_envelope(
            ProposalLineageEnvelopeResponse,
            ProposalLineageData,
            correlation_id=correlation_id,
            upstream_payload=upstream_payload,
        )
