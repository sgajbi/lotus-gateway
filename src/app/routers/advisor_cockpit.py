from fastapi import APIRouter, Query

from app.contracts.advisor_cockpit import AdvisorCockpitEnvelopeResponse
from app.middleware.correlation import correlation_id_var
from app.routers.advisor_cockpit_common import (
    ADVISOR_COCKPIT_READ_RESPONSES,
    cockpit_params,
)
from app.routers.advisor_cockpit_request import (
    AdvisorCockpitCaller,
    authorize_advisor_cockpit_request,
)
from app.services.advisor_cockpit_access_policy import ADVISOR_COCKPIT_READ_CAPABILITY
from app.services.advisory_service_provider import advisor_cockpit_service

router = APIRouter(prefix="/api/v1/advisor-cockpit", tags=["advisor-cockpit"])


async def _list_advisor_cockpit_actions(
    *,
    caller: AdvisorCockpitCaller,
    portfolio_id: str | None,
    limit: int,
    cursor: str | None,
) -> AdvisorCockpitEnvelopeResponse:
    entitled_portfolio_id = authorize_advisor_cockpit_request(
        caller,
        capability=ADVISOR_COCKPIT_READ_CAPABILITY,
        portfolio_id=portfolio_id,
    )
    return await advisor_cockpit_service().list_actions(
        params=cockpit_params(
            portfolio_id=entitled_portfolio_id,
            limit=limit,
            cursor=cursor,
        ),
        caller_headers=caller.upstream_headers(),
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/actions",
    response_model=AdvisorCockpitEnvelopeResponse,
    summary="List Advisor Cockpit Actions",
    description=(
        "Lists source-owned advisor cockpit action items from lotus-advise. Gateway preserves "
        "Advise-owned action status, priority, owner role, reason codes, evidence refs, lineage "
        "refs, and unsupported-capability posture without reconstructing advisory semantics. "
        "Advisor identity and role are derived from trusted caller context."
    ),
    responses=ADVISOR_COCKPIT_READ_RESPONSES,
)
async def list_advisor_cockpit_actions(
    caller: AdvisorCockpitCaller,
    portfolio_id: str | None = Query(
        default=None,
        description="Optional portfolio identifier forwarded to lotus-advise.",
        examples=["PB_SG_GLOBAL_BAL_001"],
    ),
    limit: int = Query(
        default=25,
        ge=1,
        le=100,
        description="Bounded cockpit action page size forwarded to lotus-advise.",
        examples=[25],
    ),
    cursor: str | None = Query(
        default=None,
        description="Opaque action cursor returned by lotus-advise.",
        examples=["cockpit_action_001"],
    ),
) -> AdvisorCockpitEnvelopeResponse:
    return await _list_advisor_cockpit_actions(
        caller=caller,
        portfolio_id=portfolio_id,
        limit=limit,
        cursor=cursor,
    )
