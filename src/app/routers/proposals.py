from dataclasses import dataclass
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.contracts.proposals import ProposalListEnvelopeResponse
from app.middleware.correlation import correlation_id_var
from app.services.advisory_service_provider import proposal_service

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


ProposalPortfolioIdQuery = Annotated[
    str | None,
    Query(
        description="Optional portfolio identifier used to scope the proposal list.",
        examples=["PF_1001"],
    ),
]
ProposalStateQuery = Annotated[
    str | None,
    Query(
        description="Optional workflow state filter such as DRAFT or RISK_REVIEW.",
        examples=["DRAFT"],
    ),
]
ProposalCreatedByQuery = Annotated[
    str | None,
    Query(
        description="Optional actor identifier used to filter proposals by creator.",
        examples=["advisor_1"],
    ),
]
ProposalCreatedFromQuery = Annotated[
    str | None,
    Query(
        description="Inclusive creation-date lower bound in YYYY-MM-DD format.",
        examples=["2026-01-01"],
    ),
]
ProposalCreatedToQuery = Annotated[
    str | None,
    Query(
        description="Inclusive creation-date upper bound in YYYY-MM-DD format.",
        examples=["2026-03-31"],
    ),
]
ProposalLimitQuery = Annotated[
    int,
    Query(
        ge=1,
        le=100,
        description="Maximum number of proposals returned in one page.",
        examples=[20],
    ),
]
ProposalCursorQuery = Annotated[
    str | None,
    Query(
        description="Opaque pagination cursor returned by the previous proposal list response.",
        examples=["pp_00042"],
    ),
]


@dataclass(frozen=True)
class ProposalListQuery:
    portfolio_id: str | None
    state: str | None
    created_by: str | None
    created_from: str | None
    created_to: str | None
    limit: int
    cursor: str | None


def build_proposal_list_query(
    portfolio_id: ProposalPortfolioIdQuery = None,
    state: ProposalStateQuery = None,
    created_by: ProposalCreatedByQuery = None,
    created_from: ProposalCreatedFromQuery = None,
    created_to: ProposalCreatedToQuery = None,
    limit: ProposalLimitQuery = 20,
    cursor: ProposalCursorQuery = None,
) -> ProposalListQuery:
    return ProposalListQuery(
        portfolio_id=portfolio_id,
        state=state,
        created_by=created_by,
        created_from=created_from,
        created_to=created_to,
        limit=limit,
        cursor=cursor,
    )


async def _list_proposals(
    *,
    query: ProposalListQuery,
) -> ProposalListEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    filters = {
        "portfolio_id": query.portfolio_id,
        "state": query.state,
        "created_by": query.created_by,
        "created_from": query.created_from,
        "created_to": query.created_to,
        "limit": query.limit,
        "cursor": query.cursor,
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
    query: ProposalListQuery = Depends(build_proposal_list_query),
) -> ProposalListEnvelopeResponse:
    return await _list_proposals(query=query)
