from fastapi import APIRouter, Query

from app.contracts.proposals import ProposalListEnvelopeResponse
from app.middleware.correlation import correlation_id_var
from app.services.advisory_service_provider import proposal_service

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


async def _list_proposals(
    *,
    portfolio_id: str | None,
    state: str | None,
    created_by: str | None,
    created_from: str | None,
    created_to: str | None,
    limit: int,
    cursor: str | None,
) -> ProposalListEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    filters = {
        "portfolio_id": portfolio_id,
        "state": state,
        "created_by": created_by,
        "created_from": created_from,
        "created_to": created_to,
        "limit": limit,
        "cursor": cursor,
    }
    return await service.list_proposals(filters=filters, correlation_id=correlation_id)


@router.get(
    "",
    response_model=ProposalListEnvelopeResponse,
    summary="List Proposals",
    description=(
        "Lists advisory proposals from lotus-advise using optional portfolio, workflow-state, "
        "creator, and creation-window filters."
    ),
)
async def list_proposals(
    portfolio_id: str | None = Query(
        default=None,
        description="Optional portfolio identifier used to scope the proposal list.",
        examples=["PF_1001"],
    ),
    state: str | None = Query(
        default=None,
        description="Optional workflow state filter such as DRAFT or RISK_REVIEW.",
        examples=["DRAFT"],
    ),
    created_by: str | None = Query(
        default=None,
        description="Optional actor identifier used to filter proposals by creator.",
        examples=["advisor_1"],
    ),
    created_from: str | None = Query(
        default=None,
        description="Inclusive creation-date lower bound in YYYY-MM-DD format.",
        examples=["2026-01-01"],
    ),
    created_to: str | None = Query(
        default=None,
        description="Inclusive creation-date upper bound in YYYY-MM-DD format.",
        examples=["2026-03-31"],
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of proposals returned in one page.",
        examples=[20],
    ),
    cursor: str | None = Query(
        default=None,
        description="Opaque pagination cursor returned by the previous proposal list response.",
        examples=["pp_00042"],
    ),
) -> ProposalListEnvelopeResponse:
    return await _list_proposals(
        portfolio_id=portfolio_id,
        state=state,
        created_by=created_by,
        created_from=created_from,
        created_to=created_to,
        limit=limit,
        cursor=cursor,
    )
