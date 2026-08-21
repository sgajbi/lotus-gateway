from fastapi import APIRouter, Path

from app.contracts.proposal_risk_impact import ProposalRiskImpactEnvelopeResponse
from app.middleware.correlation import correlation_id_var
from app.services.advisory_service_provider import proposal_service

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


async def _get_proposal_risk_impact(
    *,
    proposal_id: str,
) -> ProposalRiskImpactEnvelopeResponse:
    return await proposal_service().get_proposal_risk_impact(
        proposal_id=proposal_id,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/{proposal_id}/risk-impact",
    response_model=ProposalRiskImpactEnvelopeResponse,
    summary="Get Proposal Risk and Impact",
    description=(
        "Returns a typed Workbench decision projection for one selected proposal. Gateway "
        "preserves lotus-advise, lotus-core, and lotus-risk source authority; it does not "
        "recalculate risk, infer approval, or manufacture unsupported benchmark, limit, "
        "scenario, or valuation-date evidence."
    ),
)
async def get_proposal_risk_impact(
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_001"],
    ),
) -> ProposalRiskImpactEnvelopeResponse:
    return await _get_proposal_risk_impact(proposal_id=proposal_id)
