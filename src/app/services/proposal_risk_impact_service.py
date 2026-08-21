from typing import Any

from app.contracts.proposal_risk_impact import ProposalRiskImpactEnvelopeResponse
from app.services.proposal_client_protocols import ProposalClient
from app.services.proposal_risk_impact_projection import project_proposal_risk_impact


class ProposalRiskImpactServiceMixin:
    _advise_client: ProposalClient

    def _raise_for_upstream_error(
        self,
        upstream_status: int,
        upstream_payload: dict[str, Any],
    ) -> None:
        raise NotImplementedError

    async def get_proposal_risk_impact(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> ProposalRiskImpactEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.get_proposal(
            proposal_id=proposal_id,
            include_evidence=False,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return ProposalRiskImpactEnvelopeResponse(
            correlation_id=correlation_id,
            data=project_proposal_risk_impact(
                upstream_payload,
                expected_proposal_id=proposal_id,
            ),
        )


__all__ = ["ProposalRiskImpactServiceMixin"]
